"""Private drafting and document approval; dispatch requires separate permission."""
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils.http import content_disposition_header
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.throttles import EndpointThrottle
from profiles.cv_builder import content_hash
from profiles.cv_validation import StrictSerializer, StrictText, SchemaVersion, StrictBoolean
from profiles.download_names import document_name
from profiles.cv_views import PrivateCVView
from .models import Application
from .application_packages import (context, is_editable, require_editable, selected_cv,
    draft_letter, package_data, save_package, PackageConflict)
from .package_review import owner_package, review_data, verified_documents, approve_package


class DraftInput(StrictSerializer):
    cv_version = serializers.UUIDField()


class PackageInput(DraftInput):
    expected_revision = SchemaVersion(min_value=0, max_value=2147483646)
    context_sha256 = serializers.RegexField(r'\A[0-9a-f]{64}\Z')
    letter_text = StrictText(max_length=10000, trim_whitespace=False)
    email_subject = StrictText(max_length=255, allow_blank=True, trim_whitespace=False)
    email_body = StrictText(max_length=10000, allow_blank=True, trim_whitespace=False)

    def validate_letter_text(self, value):
        if not value.strip():
            raise serializers.ValidationError('Enter a cover letter.')
        return value


def owner_application(request, pk):
    return get_object_or_404(Application.objects.select_related('job'), pk=pk, user=request.user)


class PackageListView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'

    def get(self, request, pk):
        app = owner_application(request, pk)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        packages = app.packages.order_by('-revision')
        page = paginator.paginate_queryset(packages, request, view=self)
        result = paginator.get_paginated_response([package_data(row) for row in page])
        current = context(app)
        result.data.update(latest_revision=packages.values_list('revision', flat=True).first() or 0,
            job_context=current, context_sha256=content_hash(current),
            editable=is_editable(app))
        return result

    def post(self, request, pk):
        owner_application(request, pk)
        serializer = PackageInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            package = save_package(request.user, pk, serializer.validated_data)
        except IntegrityError:
            raise PackageConflict() from None
        return Response(package_data(package), status=201)


class PackageDraftView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'

    def post(self, request, pk):
        app = owner_application(request, pk)
        require_editable(app)
        serializer = DraftInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        approval = selected_cv(request.user, serializer.validated_data['cv_version'])
        current = context(app)
        return Response({'letter_text': draft_letter(approval, current),
            'job_context': current, 'context_sha256': content_hash(current),
            'missing_information': [label for key, label in [('summary', 'CV summary'), ('skills', 'CV skills')]
                if not approval.content.get(key)]})


class PackageReviewView(PrivateCVView):
    def get(self, request, pk, package_id):
        return Response(review_data(owner_package(request.user, pk, package_id)))


class ApprovalInput(StrictSerializer):
    expected_revision = SchemaVersion(min_value=1, max_value=2147483647)
    content_sha256 = serializers.RegexField(r'\A[0-9a-f]{64}\Z')
    approval = StrictBoolean()

    def validate_approval(self, value):
        if value is not True:
            raise serializers.ValidationError('Explicit document approval is required.')
        return value


class PackageApprovalView(PrivateCVView):
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'

    def post(self, request, pk, package_id):
        owner_package(request.user, pk, package_id)
        serializer = ApprovalInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        proof, created = approve_package(request.user, pk, package_id,
            data['expected_revision'], data['content_sha256'])
        return Response({'approval': proof}, status=201 if created else 200)


class PackageDocumentView(PrivateCVView):
    def get(self, request, pk, package_id, kind):
        if kind not in ('cv', 'cover-letter'):
            return Response({'detail': 'Document not found.'}, status=404)
        package = owner_package(request.user, pk, package_id)
        data = verified_documents(package)[kind]
        # Serve the verified in-memory bytes, avoiding a second open/path race.
        response = HttpResponse(b'' if request.method == 'HEAD' else data,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Length'] = len(data)
        response['Content-Disposition'] = content_disposition_header(True,
            document_name(request.user.full_name, 'CV' if kind == 'cv' else 'Cover_Letter',
                          package.application.job.company_name))
        return response
