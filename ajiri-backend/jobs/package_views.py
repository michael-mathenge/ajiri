"""Private drafting endpoints; approval and sending remain separate packages."""
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.throttles import EndpointThrottle
from profiles.cv_builder import content_hash
from profiles.cv_validation import StrictSerializer, StrictText, SchemaVersion
from profiles.cv_views import PrivateCVView
from .models import Application
from .application_packages import (context, blocked, require_editable, selected_cv,
    draft_letter, package_data, save_package, PackageConflict)


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
            editable=not blocked(app) and app.job.is_active and not app.job.is_flagged_scam)
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
