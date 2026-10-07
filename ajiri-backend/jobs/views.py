import hmac
import uuid
import feedparser
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from .models import Job, Application, Notification
from .serializers import (
    JobListSerializer,
    JobDetailSerializer,
    ApplicationSerializer,
    NotificationSerializer,
)
from .filters import JobFilter
from .ingestion import ingest_feed
from .matching import sweep_all_active_jobs_for_matches
from .cover_letter_generator import generate_cover_letter_docx
from profiles.cv_generator import generate_cv_docx


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
        safe_company = job.company_name.replace(' ', '_')
        response['Content-Disposition'] = f'attachment; filename="Cover_Letter_{safe_company}.docx"'
        return response


class ApplyToJobView(generics.GenericAPIView):
    """
    POST /jobs/<pk>/apply/ — the on-demand replacement for automatic
    Application drafting. Generates the CV + cover letter ONCE and saves
    them as real files on the new Application (unlike the on-the-fly,
    regenerate-every-time GenerateCoverLetterView above), then sets
    status straight to ready_for_review — see docs/CONCEPTS.md#application-lifecycle.

    Idempotent: if the user already applied to this job, returns the
    existing Application instead of creating a duplicate (the model's
    unique_together=('user','job') would reject a second row anyway).
    """
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Job.objects.filter(is_active=True, is_flagged_scam=False)

    def post(self, request, pk):
        job = get_object_or_404(self.get_queryset(), pk=pk)
        profile = request.user.profile

        existing = Application.objects.filter(user=request.user, job=job).first()
        if existing:
            serializer = ApplicationSerializer(existing, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        cv_buffer = generate_cv_docx(profile)
        cover_letter_buffer = generate_cover_letter_docx(profile, job)
        safe_company = job.company_name.replace(' ', '_')
        # Generated files are served as plain static files, so a guessable name
        # like CV_Acme.docx would let anyone download someone's CV. A random
        # prefix makes each URL unguessable. See docs/CONCEPTS.md#unguessable-filenames
        file_token = uuid.uuid4().hex

        application = Application(
            user=request.user,
            job=job,
            status=Application.Status.READY_FOR_REVIEW,
            # Snapshotted now, per docs/CONCEPTS.md#application-lifecycle —
            # won't silently change if the job listing is edited later.
            application_method=job.application_method,
            application_email=job.application_email,
        )

        # save(..., save=False) writes the file to storage immediately but
        # doesn't hit the DB yet — we want one single application.save()
        # call below, not three separate writes.
        application.generated_cv.save(
            f"{file_token}_CV_{safe_company}.docx", ContentFile(cv_buffer.read()), save=False
        )
        application.generated_cover_letter.save(
            f"{file_token}_Cover_Letter_{safe_company}.docx", ContentFile(cover_letter_buffer.read()), save=False
        )

        if application.application_method == Job.ApplicationMethod.EMAIL:
            applicant_name = request.user.full_name or request.user.email
            application.email_subject = f"Application for {job.title} position"
            application.email_body = (
                f"Dear Hiring Manager,\n\n"
                f"Please find attached my CV and cover letter for the "
                f"{job.title} position at {job.company_name}.\n\n"
                f"Kind regards,\n{applicant_name}"
            )

        application.save()

        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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

    - EMAIL: actually sends the email to application_email, with the
      generated CV and cover letter attached as files. Uses the (possibly
      user-edited) email_subject/email_body already stored on the record.
    - EXTERNAL_LINK: there's nothing for us to send — the user applies
      manually on the employer's own site. This just records that they've
      confirmed doing so.

    Either way, status moves to SENT and sent_at is stamped. Only works on
    an application still in READY_FOR_REVIEW — prevents re-sending an
    already-sent application or "sending" a dismissed one.
    """
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Application.objects.all()

    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk, user=request.user)

        if application.status != Application.Status.READY_FOR_REVIEW:
            return Response(
                {"detail": f"Cannot send an application with status '{application.status}'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if application.application_method == Job.ApplicationMethod.EMAIL:
            email = EmailMessage(
                subject=application.email_subject,
                body=application.email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[application.application_email],
            )
            email.attach_file(application.generated_cv.path)
            email.attach_file(application.generated_cover_letter.path)

            try:
                email.send(fail_silently=False)
            except Exception as e:
                # Deliberately don't touch status/sent_at on failure — the
                # application stays in ready_for_review so the user can
                # just retry the same request once the issue is fixed.
                return Response(
                    {"detail": f"Failed to send email: {str(e)}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        application.status = Application.Status.SENT
        application.sent_at = timezone.now()
        application.save(update_fields=['status', 'sent_at'])

        serializer = ApplicationSerializer(application, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class NotificationListView(generics.ListAPIView):
    """
    GET /jobs/notifications/ — every job-match alert belonging to the
    logged-in user, most recent first. Powers the frontend's Notifications
    page. Scoped to request.user, same reasoning as ApplicationListView.
    """
    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')


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
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
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
