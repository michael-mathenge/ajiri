"""Offline schema annotations kept separate from authentication/delivery code."""
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.utils import OpenApiParameter
from accounts.csrf import CookieCSRFViewMixin
import re
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers
from accounts.serializers import RegisterSerializer
from accounts.recovery_views import EmailInput, ResetInput, RequestInput, VerificationInput
from profiles.cv_views import SaveInput, ApproveInput
from profiles.certificate_views import EvidenceInput, RemoveEvidenceInput
from profiles.alert_views import ChoiceSerializer
from jobs.views import ApplicationCVInput
from jobs.package_views import DraftInput, PackageInput, ApprovalInput
from jobs.send_views import AuthorizationInput
from jobs.employer_views import ReviewInput
from jobs.saved_search_views import SearchInput
from jobs.application_progress import ProgressInput


class LoginInput(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class AccessOutput(serializers.Serializer):
    access = serializers.CharField(read_only=True)


class ErrorOutput(serializers.Serializer):
    detail = serializers.CharField(required=False)
    code = serializers.CharField(required=False)


INPUTS = {
    ('CertificateDetail', 'PUT'): EvidenceInput,
    ('CertificateDetail', 'DELETE'): RemoveEvidenceInput,
    ('ApplicationProgressView', 'PATCH'): ProgressInput,
    ('OrganisationReview', 'POST'): ReviewInput,
    ('DraftReview', 'POST'): ReviewInput,
    ('RegisterView', 'POST'): RegisterSerializer,
    ('LoginView', 'POST'): LoginInput,
    ('PasswordResetRequest', 'POST'): EmailInput,
    ('PasswordResetConfirm', 'POST'): ResetInput,
    ('VerificationRequest', 'POST'): RequestInput,
    ('VerificationConfirm', 'POST'): VerificationInput,
    ('CVDraftView', 'PATCH'): SaveInput,
    ('CVApproveView', 'POST'): ApproveInput,
    ('AlertPreferenceView', 'POST'): ChoiceSerializer,
    ('ApplyToJobView', 'POST'): ApplicationCVInput,
    ('PackageDraftView', 'POST'): DraftInput,
    ('PackageListView', 'POST'): PackageInput,
    ('PackageApprovalView', 'POST'): ApprovalInput,
    ('SendAuthorizationListView', 'POST'): AuthorizationInput,
}
DOWNLOADS = {'DownloadUploadedCVView', 'CVVersionDownloadView', 'CurrentCVDownloadView',
             'GenerateCoverLetterView', 'ApplicationDocumentView', 'PackageDocumentView', 'CertificateDetail'}


def version_one_only(endpoints):
    # Enumeration only. No request, provider call or database query is needed.
    return [endpoint for endpoint in endpoints if endpoint[0].startswith('/api/v1/')]


class ContractGenerator(SchemaGenerator):
    def create_view(self, callback, method, request=None):
        view = super().create_view(callback, method, request)
        model = getattr(getattr(getattr(view, 'serializer_class', None), 'Meta', None), 'model', None)
        if model is not None and getattr(view, 'queryset', None) is None:
            view.queryset = model.objects.none()
        return view


class ContractSchema(AutoSchema):
    def get_auth(self):
        if type(self.view).__name__ == 'RefreshView':
            return [{'refreshCookie': []}]
        return super().get_auth()

    def get_operation_id(self):
        return self.method.lower() + '_' + re.sub(r'[^a-zA-Z0-9]+', '_', self.path).strip('_')

    def _map_serializer_field(self, field, direction, bypass_extensions=False):
        if isinstance(field, serializers.SerializerMethodField) and field.method_name == 'get_match_score':
            return {'type': 'number', 'minimum': 0, 'maximum': 100, 'readOnly': True}
        return super()._map_serializer_field(field, direction, bypass_extensions)

    def get_override_parameters(self):
        parameters = super().get_override_parameters()
        if isinstance(self.view, CookieCSRFViewMixin) and self.method not in ('GET', 'HEAD', 'OPTIONS'):
            parameters += [OpenApiParameter('X-CSRFToken', str, OpenApiParameter.HEADER, required=True,
                description='Obtain from the same-origin CSRF endpoint; use credentials and a valid Origin header.')]
        return parameters

    # see docs/CONCEPTS.md#api-version-contract
    def get_request_serializer(self):
        if type(self.view).__name__ in ('SavedSearchList', 'SavedSearchDetail') and self.method in ('POST', 'PATCH'):
            return SearchInput()
        configured = INPUTS.get((type(self.view).__name__, self.method))
        if configured:
            return configured()
        if getattr(self.view, 'serializer_class', None):
            return super().get_request_serializer()
        if self.method in ('GET', 'HEAD', 'DELETE'):
            return None
        return OpenApiTypes.OBJECT

    def get_response_serializers(self):
        name = type(self.view).__name__
        if name in DOWNLOADS and self.method == 'GET':
            success = OpenApiTypes.BINARY
        elif name in ('LoginView', 'RefreshView'):
            success = AccessOutput
        elif getattr(self.view, 'serializer_class', None):
            success = super().get_response_serializers()
        else:
            success = OpenApiTypes.OBJECT
        # Error dictionaries may also include field-keyed nested validation arrays.
        return {200: success, **({201: success} if name in ('RegisterView', 'ApplyToJobView', 'PackageListView', 'SendAuthorizationListView') and self.method == 'POST' else {}), 400: OpenApiTypes.OBJECT, 401: ErrorOutput,
                403: ErrorOutput, 404: ErrorOutput, 409: ErrorOutput,
                429: ErrorOutput, 503: ErrorOutput}

    def get_description(self):
        name = type(self.view).__name__
        description = 'Same owner permissions, validation, throttles and explicit-action requirements as the legacy route.'
        if not getattr(self.view, 'serializer_class', None) and name not in DOWNLOADS:
            description += ' Custom success response is an extensible JSON object; additional fields are not exhaustively typed in this contract.'
        if name in ('RefreshView', 'LogoutView'):
            description += ' Requires the existing httpOnly refresh cookie and CSRF protocol; refresh tokens are never accepted from or returned in JSON.'
        return description
