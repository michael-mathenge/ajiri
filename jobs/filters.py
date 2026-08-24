import django_filters
from .models import Job


class JobFilter(django_filters.FilterSet):
    location = django_filters.CharFilter(lookup_expr='icontains')
    title = django_filters.CharFilter(lookup_expr='icontains')
    skill = django_filters.CharFilter(field_name='skills_required__name', lookup_expr='iexact')

    class Meta:
        model = Job
        fields = ['location', 'title', 'job_type', 'skill']