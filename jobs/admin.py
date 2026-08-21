from django.contrib import admin
from .models import Job


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'company_name', 'location', 'job_type',
        'is_active', 'is_flagged_scam', 'source_name', 'posted_at',
    )
    list_filter = ('job_type', 'is_active', 'is_flagged_scam', 'source_name')
    search_fields = ('title', 'company_name', 'location')
    filter_horizontal = ('skills_required',)