import re

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from accounts.throttles import EndpointThrottle
from .certificates import downloadable, metadata, put, remove
from .cv_validation import SchemaVersion, StrictBoolean, StrictSerializer
from .cv_views import PrivateCVView
from .models import CertificateEvidence


class MultipartRevision(serializers.IntegerField):
    def to_internal_value(self, data):
        # Multipart fields arrive as text; accept canonical positive integers only.
        if type(data) is not int and not (isinstance(data, str) and re.fullmatch(r'[1-9][0-9]{0,9}', data)):
            raise serializers.ValidationError('Expected a positive integer revision.')
        return super().to_internal_value(data)


class EvidenceInput(StrictSerializer):
    expected_revision = MultipartRevision(min_value=1, max_value=2147483647)
    expected_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    expected_hash = serializers.RegexField(r'^[0-9a-f]{64}$', required=False, allow_blank=True, default='')
    document = serializers.FileField()


class RemoveEvidenceInput(StrictSerializer):
    expected_revision = SchemaVersion(min_value=1, max_value=2147483647)
    expected_id = serializers.UUIDField()
    expected_hash = serializers.RegexField(r'^[0-9a-f]{64}$')
    confirm = StrictBoolean()

    def validate_confirm(self, value):
        if value is not True:
            raise serializers.ValidationError('Confirm removal of active evidence. Backups follow separate retention.')
        return value


class PrivateEvidenceView(PrivateCVView):
    parser_classes = (JSONParser, MultiPartParser)
    throttle_classes = (EndpointThrottle,)
    throttle_scope = 'apply'

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not getattr(settings, 'CERTIFICATE_EVIDENCE_ENABLED', False):
            raise Http404


class CertificateList(PrivateEvidenceView):
    def get(self, request):
        return Response({'results': [metadata(row) for row in CertificateEvidence.objects.filter(
            profile=request.user.profile).order_by('created_at')[:5]]})


class CertificateDetail(PrivateEvidenceView):
    def put(self, request, certification_id):
        serializer = EvidenceInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        upload = data.pop('document')
        return Response(metadata(put(request.user.profile, certification_id, upload=upload, **data)))

    def delete(self, request, certification_id):
        serializer = RemoveEvidenceInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.pop('confirm')
        remove(request.user.profile, certification_id, **data)
        return Response(status=204)

    def get(self, request, certification_id):
        row = get_object_or_404(CertificateEvidence, profile=request.user.profile, certification_id=certification_id)
        response = HttpResponse(downloadable(row), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="certificate.pdf"'
        response['X-Content-Type-Options'] = 'nosniff'
        return response
