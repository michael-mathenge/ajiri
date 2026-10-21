import django_filters
from .models import Job
from .search import search_jobs


class JobFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='full_text', label='Keywords', max_length=255)

    def full_text(self, queryset, name, value):
        return search_jobs(queryset, value)

    location = django_filters.CharFilter(lookup_expr='icontains')
    title = django_filters.CharFilter(lookup_expr='icontains')
    skill = django_filters.CharFilter(field_name='skills_required__name', lookup_expr='iexact')

    class Meta:
        model = Job
        fields = ['q', 'location', 'title', 'job_type', 'skill']