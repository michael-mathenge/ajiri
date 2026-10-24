"""Owner-scoped saved preferences. Mutations never send or grant email consent."""
from django.conf import settings
from django.db import transaction, OperationalError
from django.db.models import F
from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.throttles import EndpointThrottle
from profiles.cv_validation import StrictSerializer
from .freshness import eligible_jobs
from .models import Job, SavedSearch, SavedSearchMatch
from .saved_searches import MAX_SEARCHES, reset_windows
from .search import expression
from .serializers import JobListSerializer


class SearchInput(StrictSerializer):
    name = serializers.CharField(max_length=80)
    q = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    location = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    job_type = serializers.ChoiceField(choices=Job.JobType.choices, required=False, allow_blank=True, default='')
    in_app_frequency = serializers.ChoiceField(choices=SavedSearch.Frequency.choices, required=False, default='off')
    email_frequency = serializers.ChoiceField(choices=SavedSearch.Frequency.choices, required=False, default='off')
    expected_revision = serializers.IntegerField(min_value=1, required=False, write_only=True)

    def validate_q(self, value):
        expression(value)
        return value

    def validate(self, attrs):
        if self.context.get('updating') and 'expected_revision' not in attrs:
            raise ValidationError({'expected_revision': ['Reload the search and include its current revision.']})
        return attrs


class SearchOutput(serializers.ModelSerializer):
    email_delivery = serializers.SerializerMethodField()

    def get_email_delivery(self, obj) -> str:
        return 'disabled'  # Frequency storage is not an enabled delivery transport.

    class Meta:
        model = SavedSearch
        fields = ('id', 'name', 'q', 'location', 'job_type', 'in_app_frequency', 'email_frequency',
                  'revision', 'next_in_app_at', 'next_email_at', 'email_delivery')


class SearchEnabled(permissions.BasePermission):
    message = 'Saved searches are temporarily unavailable.'

    def has_permission(self, request, view):
        return settings.SAVED_SEARCHES_ENABLED


class SearchConflict(APIException):
    status_code = 409
    default_detail = 'The saved search changed. Reload before saving again.'


class SearchBusy(APIException):
    status_code = 503
    default_detail = 'Saved searches are busy. Reload the current state before trying again.'


class PrivateSearchMixin:
    permission_classes = (permissions.IsAuthenticated, SearchEnabled)

    def get_throttles(self):
        self.throttle_scope = 'saved_search_mutation'
        return [EndpointThrottle()] if self.request.method not in permissions.SAFE_METHODS else []

    def handle_exception(self, exc):
        return super().handle_exception(SearchBusy() if isinstance(exc, OperationalError) else exc)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response['Cache-Control'] = 'private, no-store'
        return response


class SavedSearchList(PrivateSearchMixin, generics.ListAPIView):
    serializer_class = SearchOutput

    def get_queryset(self):
        return SavedSearch.objects.filter(owner=self.request.user).order_by('-created_at', 'pk')

    def post(self, request):
        form = SearchInput(data=request.data)
        form.is_valid(raise_exception=True)
        values = dict(form.validated_data)
        values.pop('expected_revision', None)
        with transaction.atomic():
            search = SavedSearch(owner=request.user, **values)
            reset_windows(search, timezone.now())
            search.save()
            if SavedSearch.objects.filter(owner=request.user).count() > MAX_SEARCHES:
                raise ValidationError({'name': ['Keep at most ten saved searches.']})
        return Response(SearchOutput(search).data, status=201)


class SavedSearchDetail(PrivateSearchMixin, APIView):
    serializer_class = SearchOutput

    def get(self, request, pk):
        return Response(SearchOutput(generics.get_object_or_404(SavedSearch, pk=pk, owner=request.user)).data)

    def patch(self, request, pk):
        form = SearchInput(data=request.data, partial=True, context={'updating': True})
        form.is_valid(raise_exception=True)
        values = dict(form.validated_data)
        revision = values.pop('expected_revision')
        with transaction.atomic():
            claimed = SavedSearch.objects.filter(pk=pk, owner=request.user, revision=revision).update(revision=F('revision')+1)
            search = generics.get_object_or_404(SavedSearch, pk=pk, owner=request.user)
            if not claimed:
                raise SearchConflict()
            for key, value in values.items():
                setattr(search, key, value)
            reset_windows(search, timezone.now())
            search.save()
        return Response(SearchOutput(search).data)

    def delete(self, request, pk):
        search = generics.get_object_or_404(SavedSearch, pk=pk, owner=request.user)
        search.delete()  # Stops this preference; shared delivery receipts remain intact.
        return Response(status=204)


class SavedSearchMatches(PrivateSearchMixin, generics.ListAPIView):
    serializer_class = JobListSerializer

    def get_queryset(self):
        search = generics.get_object_or_404(SavedSearch, pk=self.kwargs['pk'], owner=self.request.user)
        ids = SavedSearchMatch.objects.filter(search=search, revision=search.revision, channel='in_app').values('job_id')
        return eligible_jobs().filter(pk__in=ids).select_related('publication').order_by('-scraped_at', '-pk')
