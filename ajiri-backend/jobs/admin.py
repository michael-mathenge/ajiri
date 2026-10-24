from django.contrib import admin
from django import forms
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, OperationalError
from django.http import Http404, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Application, Job, Notification, JobModerationReview
from .moderation import review, snapshot, fingerprint, StaleReview


class JobReviewForm(forms.Form):
    expected = forms.CharField(widget=forms.HiddenInput, max_length=64)
    decision = forms.ChoiceField(choices=[('uphold', 'Keep scam flag'), ('clear', 'Clear scam flag')])
    reason = forms.CharField(max_length=1000, widget=forms.Textarea,
        help_text='Record checked source evidence and reasoning. Do not include applicant or private account information.')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'company_name', 'location', 'job_type',
        'is_active', 'is_flagged_scam', 'source_name', 'posted_at', 'review_link',
    )
    list_filter = ('job_type', 'is_active', 'is_flagged_scam', 'source_name')
    search_fields = ('title', 'company_name', 'location')
    filter_horizontal = ('skills_required',)
    readonly_fields = ('scam_flags', 'is_flagged_scam', 'is_active', 'review_link')
    actions = None

    @admin.display(description='Moderation')
    def review_link(self, obj):
        if obj is None or not obj.pk or not obj.is_flagged_scam:
            return 'No flagged review pending'
        return format_html('<a href="{}">Review this flagged job</a>',
            reverse('admin:jobs_job_moderate', args=[obj.pk]))

    def get_urls(self):
        return [path('<int:object_id>/moderate/', self.admin_site.admin_view(self.moderate),
            name='jobs_job_moderate')] + super().get_urls()

    def moderate(self, request, object_id):
        # see docs/CONCEPTS.md#reasoned-job-moderation
        obj = self.get_object(request, str(object_id))
        if obj is None:
            raise Http404
        if not self.has_change_permission(request, obj):
            raise PermissionDenied
        evidence = snapshot(obj)
        form = JobReviewForm(request.POST if request.method == 'POST' else None,
            initial={'expected': fingerprint(evidence)})
        status = 200
        if request.method == 'POST' and form.is_valid():
            try:
                result = review(request.user, obj.pk, **form.cleaned_data)
            except (StaleReview, IntegrityError) as error:
                form.add_error(None, str(error) if isinstance(error, StaleReview) else
                    'This evidence has already been reviewed. Reload before deciding.')
                status = 409
            except OperationalError:
                form.add_error(None, 'Review storage is busy. Reload review history before retrying.')
                status = 503
            except ValidationError as error:
                form.add_error(None, error)
            else:
                self.log_change(request, obj, f'Moderation review {result.pk}: {result.decision}')
                self.message_user(request, 'Review recorded. Current publication evidence still controls listing visibility.')
                return HttpResponseRedirect(reverse('admin:jobs_job_change', args=[obj.pk]))
        response = TemplateResponse(request, 'admin/jobs/job/moderate.html', {
            **self.admin_site.each_context(request), 'title': 'Review one flagged job',
            'opts': self.model._meta, 'original': obj, 'form': form,
            'evidence': evidence, 'reviews': obj.moderation_reviews.select_related('actor').order_by('-pk')[:20],
        }, status=status)
        response['Cache-Control'] = 'private, no-store'
        return response


@admin.register(JobModerationReview)
class JobModerationReviewAdmin(admin.ModelAdmin):
    list_display = ('job', 'actor', 'decision', 'created_at')
    list_filter = ('decision',)
    readonly_fields = ('job', 'actor', 'reviewed_fingerprint', 'decision', 'reason', 'before', 'after', 'created_at')
    actions = None

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
