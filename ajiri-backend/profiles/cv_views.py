from django.db import OperationalError
from django.http import HttpResponse
from django.utils.http import content_disposition_header
from .download_names import document_name
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .cv_builder import (CVConflict, CVUnavailable, approve_workspace, content_hash,
                         document_bytes, layout, save_workspace, start_workspace)
from .cv_validation import StrictBoolean, StrictSerializer, SchemaVersion, validate_content
from .models import CVApproval, CVWorkspace


class SaveInput(StrictSerializer):
    expected_revision = SchemaVersion(min_value=1, max_value=2147483647)
    content = serializers.DictField()


class ApproveInput(StrictSerializer):
    expected_revision = SchemaVersion(min_value=1, max_value=2147483647)
    content_sha256 = serializers.RegexField(r'^[0-9a-f]{64}$')
    approval = StrictBoolean()

    def validate_approval(self, value):
        if value is not True:
            raise serializers.ValidationError('Explicit approval is required.')
        return value


def workspace_data(workspace):
    # No storage paths, profile IDs or file URLs are exposed to the client.
    approvals = list(CVApproval.objects.filter(profile_id=workspace.profile_id).order_by('-revision')
                     .values('id', 'revision', 'approved_at')[:20])
    current = next((row for row in approvals if row['revision'] == workspace.revision), None)
    content = workspace.content or validate_content({'schema_version': 1, 'contact': {}})
    return {'content': content, 'revision': workspace.revision,
            'content_sha256': content_hash(workspace.content), 'preview': layout(content),
            'approval_id': current['id'] if current else None, 'versions': approvals}


class PrivateCVView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    parser_classes = (JSONParser,)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response

    def handle_exception(self, exc):
        if isinstance(exc, (OperationalError, OSError)):
            exc = CVUnavailable()
        return super().handle_exception(exc)


class CVDraftView(PrivateCVView):
    def get(self, request):
        workspace = CVWorkspace.objects.filter(profile=request.user.profile).first()
        return Response(workspace_data(workspace) if workspace else {'content': None})

    def post(self, request):
        StrictSerializer(data=request.data).is_valid(raise_exception=True)
        return Response(workspace_data(start_workspace(request.user.profile)))

    def patch(self, request):
        serializer = SaveInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = get_object_or_404(CVWorkspace, profile=request.user.profile)
        return Response(workspace_data(save_workspace(workspace, **{
            'expected_revision': serializer.validated_data['expected_revision'],
            'patch': serializer.validated_data['content']})))


class CVApproveView(PrivateCVView):
    def post(self, request):
        serializer = ApproveInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = get_object_or_404(CVWorkspace, profile=request.user.profile)
        data = serializer.validated_data
        approval = approve_workspace(workspace, data['expected_revision'], data['content_sha256'])
        return Response({'approval_id': approval.pk, 'revision': approval.revision})


class CVVersionDownloadView(PrivateCVView):
    def get(self, request, version):
        approval = get_object_or_404(CVApproval, pk=version, profile=request.user.profile)
        return cv_response(approval)


class CVVersionListView(PrivateCVView):
    def get(self, request):
        # Job pages need version labels, never the CV's contact/history content.
        # see docs/CONCEPTS.md#approved-cv-applications
        workspace = CVWorkspace.objects.filter(profile=request.user.profile).only('revision').first()
        versions = list(CVApproval.objects.filter(profile=request.user.profile).order_by('-revision')
                        .values('id', 'revision', 'approved_at')[:20])
        revision = workspace.revision if workspace else None
        current = next((version for version in versions if version['revision'] == revision), None)
        return Response({'revision': revision, 'approval_id': current['id'] if current else None, 'versions': versions})


def cv_response(approval):
    response = HttpResponse(document_bytes(approval), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = content_disposition_header(True,
        document_name(approval.content.get('contact', {}).get('name', '')))
    response['Cache-Control'] = 'private, no-store'
    return response


class CurrentCVDownloadView(PrivateCVView):
    """Retained legacy URL, with the same approval gate as the new UI."""
    def get(self, request):
        workspace = CVWorkspace.objects.filter(profile=request.user.profile).first()
        if workspace:
            approval = CVApproval.objects.filter(profile=request.user.profile, revision=workspace.revision).first()
            if approval and approval.content_sha256 == content_hash(workspace.content):
                return cv_response(approval)
        raise CVConflict('Review and approve your current CV in the CV builder before downloading.')
