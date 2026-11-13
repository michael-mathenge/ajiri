import django_filters
from django import forms
from .models import Job
from .search import search_jobs
from .vacancy_metadata import COUNTIES, WORK_ARRANGEMENTS, MAX_EXPERIENCE_YEARS


class ExperienceFilter(django_filters.Filter):
    field_class = forms.IntegerField


class JobFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='full_text', label='Keywords', max_length=255)

    def full_text(self, queryset, name, value):
        return search_jobs(queryset, value)

    location = django_filters.CharFilter(lookup_expr='icontains')
    title = django_filters.CharFilter(lookup_expr='icontains')
    skill = django_filters.CharFilter(field_name='skills_required__name', lookup_expr='iexact')
    county = django_filters.ChoiceFilter(choices=COUNTIES)
    work_arrangement = django_filters.ChoiceFilter(choices=WORK_ARRANGEMENTS)
    # A chosen bound excludes unknown requirements; zero is an explicit value.
    # see docs/CONCEPTS.md#normalized-vacancy-filters
    max_experience_years = ExperienceFilter(field_name='min_experience_years', lookup_expr='lte',
        min_value=0, max_value=MAX_EXPERIENCE_YEARS)

    class Meta:
        model = Job
        fields = ['q', 'location', 'title', 'job_type', 'skill', 'county', 'work_arrangement', 'max_experience_years']
