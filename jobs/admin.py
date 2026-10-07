from django.contrib import admin
from .models import Application, Job, Notification


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'company_name', 'location', 'job_type',
        'is_active', 'is_flagged_scam', 'source_name', 'posted_at',
    )
    list_filter = ('job_type', 'is_active', 'is_flagged_scam', 'source_name')
    search_fields = ('title', 'company_name', 'location')
    filter_horizontal = ('skills_required',)
    readonly_fields = ('scam_flags',)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'status', 'application_method', 'created_at', 'sent_at')
    list_filter = ('status', 'application_method')
    search_fields = ('user__email', 'job__title', 'job__company_name')
    readonly_fields = ('created_at', 'updated_at', 'sent_at')
    # A dropdown of every user/job would be enormous; look them up by id instead.
    raw_id_fields = ('user', 'job')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'match_score', 'is_read', 'sent_email', 'created_at')
    list_filter = ('is_read', 'sent_email')
    search_fields = ('user__email', 'job__title', 'job__company_name')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'job')
