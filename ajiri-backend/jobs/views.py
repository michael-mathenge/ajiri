import hmac
import feedparser
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.utils.http import content_disposition_header
from profiles.download_names import document_name
from django.utils import timezone
from .models import Job, Application, Notification
from .serializers import (
    JobListSerializer,
    JobDetailSerializer,
    ApplicationSerializer,
    NotificationSerializer,
)
from .filters import JobFilter
from accounts.throttles import EndpointThrottle
from .ingestion import ingest_feed
from .matching import sweep_all_active_jobs_for_matches
from .cover_letter_generator import generate_cover_letter_docx
from profiles.models import CVApproval
from profiles.cv_builder import CVUnavailable
from profiles.cv_validation import StrictSerializer
from rest_framework import serializers
from django.db import OperationalError
from .application_drafting import prepare_application


class JobListView(generics.ListAPIView):
    serializer_class = JobListSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = JobFilter
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False).order_by('-posted_at')


class JobDetailView(generics.RetrieveAPIView):
    serializer_class = JobDetailSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)


class GenerateCoverLetterView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)

    def get(self, request, pk):
        job = get_object_or_404(self.get_queryset(), pk=pk)
        profile = request.user.profile
        buffer = generate_cover_letter_docx(profile, job)

        response = HttpResponse(
            buffer.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        response['Content-Disposition'] = content_disposition_header(True,
            document_name(request.user.full_name, 'Cover_Letter', job.company_name))
        response['Cache-Control'] = 'private, no-store'
        return response


class ApplyToJobView(generics.GenericAPIView):
    """
    POST /jobs/<pk>/apply/ — the on-demand replacement for automatic
    Application drafting. Copies the selected approved CV + generates a letter ONCE and saves
    them as real files on the new Application (unlike the on-the-fly,
    regenerate-every-time GenerateCoverLetterView above), then sets
    status straight to ready_for_review — see docs/CONCEPTS.md#application-lifecycle.

    Idempotent: if the user already applied to this job, returns the
    existing Application instead of creating a duplicate (the model's
    unique_together=('user','job') would reject a second row anyway).
    """
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)

    def post(self, request, pk):
        job = get_object_or_404(self.get_queryset(), pk=pk)
        profile = request.user.profile

        existing = Application.objects.filter(user=request.user, job=job).first()
        if existing:
            serializer = ApplicationSerializer(existing, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        if isinstance(request.data, dict) and not request.data.get('cv_version'):
            return Response({'detail': 'Choose an approved CV version in the CV builder before preparing an application.',
                             'code': 'cv_approval_required'}, status=409)
        selection = ApplicationCVInput(data=request.data)
        selection.is_valid(raise_exception=True)
        approval = get_object_or_404(CVApproval, pk=selection.validated_data['cv_version'], profile=profile)
        try:
            application, created = prepare_application(request.user, job, approval)
        except (OSError, OperationalError):
            raise CVUnavailable('Application preparation could not be confirmed. Check My applications before retrying.') from None

        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ApplicationCVInput(StrictSerializer):
    cv_version = serializers.UUIDField()


class ApplicationListView(generics.ListAPIView):
    """
    GET /jobs/applications/ — every Application belonging to the logged-in
    user, most recent first. Powers the frontend's My Applications page.
    Scoped to request.user so nobody can list another user's applications
    just by knowing this endpoint exists.
    """
    serializer_class = ApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Application.objects.filter(user=self.request.user).order_by('-created_at')


class SendApplicationView(generics.GenericAPIView):
    """
    POST /jobs/applications/<pk>/send/ — the final step in the Application
    lifecycle. Behavior branches on application_method:

    - EMAIL: disabled pending separate exact-package authorization and delivery review.
    - EXTERNAL_LINK: there's nothing for us to send — the user applies
      manually on the employer's own site. This just records that they've
      confirmed doing so.

    Either way, status moves to SENT and sent_at is stamped. Only works on
    an application still in READY_FOR_REVIEW — prevents re-sending an
    already-sent application or "sending" a dismissed one.
    """
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'send'
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Application.objects.all()

    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk, user=request.user)

        if application.status != Application.Status.READY_FOR_REVIEW:
            return Response(
                {"detail": f"Cannot send an application with status '{application.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # No legacy console/SMTP bypass of the package review and sending boundary.
        # see docs/CONCEPTS.md#application-package-editor
        if application.application_method == Job.ApplicationMethod.EMAIL:
            return Response({'detail': 'Managed application sending is awaiting activation. No email was sent.',
                             'code': 'application_sending_disabled'}, status=409)

        # One autocommitted conditional write wins even when both callers read READY.
        # External submission is a user report, never provider delivery.
        # see docs/CONCEPTS.md#application-send-claim
        claimed_at = timezone.now()
        claimed = Application.objects.filter(
            pk=application.pk, user=request.user, status=Application.Status.READY_FOR_REVIEW,
        ).update(status=Application.Status.SENT, sent_at=claimed_at)
        if not claimed:
            return Response({'detail': 'This application has already been claimed or is no longer reviewable.'}, status=400)
        application.status = Application.Status.SENT
        application.sent_at = claimed_at

        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ApplicationDocumentView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, pk, kind):
        application = get_object_or_404(Application, pk=pk, user=request.user)
        document = {'cv': application.generated_cv, 'cover-letter': application.generated_cover_letter}.get(kind)
        if not document:
            return Response({'detail': 'Document not found.'}, status=404)
        # Stream the saved snapshot belonging to this user, not a freshly generated file.
        # see docs/CONCEPTS.md#authenticated-document-downloads
        try:
            response = FileResponse(document.open('rb'), as_attachment=True,
                filename=document_name(request.user.full_name,
                    'CV' if kind == 'cv' else 'Cover_Letter', application.job.company_name))
        except FileNotFoundError:
            return Response({'detail': 'The document file is unavailable.'}, status=404)
        response['Cache-Control'] = 'private, no-store'
        return response


class DismissApplicationView(generics.GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk, user=request.user)
        # A dismissed draft stays available as history; sending cannot be undone.
        # see docs/CONCEPTS.md#application-dismissal
        if application.status == Application.Status.SENT:
            return Response({'detail': 'Sent applications cannot be dismissed.'}, status=400)
        if application.status != Application.Status.DISMISSED:
            # A stale dismiss request must not undo a concurrently claimed send.
            Application.objects.filter(pk=pk, user=request.user).exclude(
                status=Application.Status.SENT,
            ).update(status=Application.Status.DISMISSED, updated_at=timezone.now())
            application.refresh_from_db()
            if application.status == Application.Status.SENT:
                return Response({'detail': 'Sent applications cannot be dismissed.'}, status=400)
        return Response(ApplicationSerializer(application, context={'request': request}).data)


class NotificationListView(generics.ListAPIView):
    """
    GET /jobs/notifications/ — every job-match alert belonging to the
    logged-in user, most recent first. Powers the frontend's Notifications
    page. Scoped to request.user, same reasoning as ApplicationListView.
    """
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, in_app=True).order_by('-created_at')


class MarkNotificationReadView(generics.GenericAPIView):
    """
    POST /jobs/notifications/<pk>/mark-read/ — flips is_read to True.
    Deliberately a separate endpoint rather than a general PATCH, since
    is_read is the only field a user should ever be able to change on a
    Notification (match_score, sent_email etc. are system-set facts).
    """
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Notification.objects.all()

    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user, in_app=True)
        notification.is_read = True
        notification.save(update_fields=['is_read'])

        serializer = NotificationSerializer(notification, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


def has_valid_ingest_key(request):
    """
    True only if the request carries the correct X-Ingest-Key header.

    An UNSET server key must DISABLE the endpoints, never open them —
    otherwise forgetting the environment variable would leave them
    unprotected. hmac.compare_digest compares in constant time so response
    timing can't be used to guess the key one character at a time.
    Shared by IngestFeedView and SweepMatchesView.
    """
    expected_key = settings.INGEST_API_KEY
    provided_key = request.headers.get('X-Ingest-Key', '')
    return bool(expected_key) and hmac.compare_digest(
        provided_key.encode('utf-8'), expected_key.encode('utf-8')
    )


class IngestFeedView(generics.GenericAPIView):
    """
    POST /api/jobs/ingest/ — receives a raw job-feed XML body and runs it
    through the same ingest_feed() pipeline the Celery task uses.

    Exists because some hosts (PythonAnywhere's free tier) block outbound
    requests to sites not on a whitelist, so the server can't fetch the
    feed itself. Instead, something with open internet (a scheduled GitHub
    Actions job) fetches it and POSTs it here. See docs/CONCEPTS.md#remote-ingestion

    Deliberately NOT JWT-authenticated: callers are a machine, not a user.
    A shared secret in the X-Ingest-Key header (settings.INGEST_API_KEY,
    set from an environment variable) is the credential instead.
    authentication_classes = [] also means a stale user token can never
    break this endpoint — see docs/CONCEPTS.md#stale-token-on-public-endpoints
    """
    authentication_classes = []
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if not has_valid_ingest_key(request):
            return Response(
                {'detail': 'Invalid or missing ingest key.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse the raw BYTES, not a decoded string: feedparser then reads
        # the encoding from the XML itself instead of guessing from HTTP
        # headers (the guess that caused the mojibake bug).
        feed = feedparser.parse(request.body)
        if not feed.entries:
            return Response(
                {'detail': 'No feed entries found in request body.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(ingest_feed(feed), status=status.HTTP_200_OK)


class SweepMatchesView(generics.GenericAPIView):
    """
    POST /api/jobs/sweep/ — runs the match sweep (re-checks every active job
    against every profile and sends alerts not yet sent). The scheduled
    GitHub Actions workflow calls this where Celery Beat isn't available.
    Same machine-to-machine protection as IngestFeedView.
    See docs/CONCEPTS.md#remote-ingestion
    """
    authentication_classes = []
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if not has_valid_ingest_key(request):
            return Response(
                {'detail': 'Invalid or missing ingest key.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        notified = sweep_all_active_jobs_for_matches()
        return Response({'notified': notified}, status=status.HTTP_200_OK)
