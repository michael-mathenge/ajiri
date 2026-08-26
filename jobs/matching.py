from django.conf import settings
from django.core.mail import send_mail
from .models import Job, Notification

# A job scoring at or above this against a profile is considered a strong
# enough match to interrupt the user with an alert. See docs/CONCEPTS.md#job-alerts
MATCH_ALERT_THRESHOLD = 70


def calculate_match_score(profile, job):
    """
    Returns a 0-100 integer representing how well a profile's skills
    overlap with a job's required skills.

    Deliberately simple for v1: percentage of the job's required skills
    that the profile actually has. A job with no listed skills always
    scores 0 — there's nothing concrete to match against, so we don't
    want to claim a false 100% match.
    """
    job_skill_ids = set(job.skills_required.values_list('id', flat=True))

    if not job_skill_ids:
        return 0

    profile_skill_ids = set(profile.skills.values_list('id', flat=True))

    matched = job_skill_ids & profile_skill_ids
    score = round((len(matched) / len(job_skill_ids)) * 100)

    return score


def send_match_email(user, job, score):
    """
    Sends a plain-text job-match alert email. fail_silently=True because a
    delivery hiccup here shouldn't ever break the ingestion/sweep flow that
    calls this — worst case, the user still sees the in-app Notification.
    """
    subject = f"New job match: {job.title} at {job.company_name}"
    message = (
        f"Hi {user.full_name or user.email},\n\n"
        f"We found a job that matches your profile at {score}%:\n\n"
        f"{job.title} at {job.company_name}\n"
        f"Location: {job.location or 'Not specified'}\n\n"
        f"Log in to Ajiri to view the listing and apply."
    )
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )


def notify_matching_profiles(job):
    """
    Checks every profile against a single job and creates a Notification
    (+ sends an email, if the user opted in) for anyone scoring at or above
    MATCH_ALERT_THRESHOLD who hasn't already been notified about this job.

    Called immediately after a job is ingested (see ingestion.py) so users
    hear about strong matches right away, without waiting for the periodic
    sweep. Skips scam-flagged or inactive jobs entirely — no point alerting
    anyone to a listing we've already decided not to show.

    Returns the number of NEW notifications created.
    """
    from profiles.models import Profile  # local import avoids a circular
    # import at module load time: profiles/models.py doesn't import jobs,
    # but importing it at the top of this file alongside Job would still
    # work fine today — kept local here mainly so this function's
    # dependencies are obvious at a glance.

    if not job.is_active or job.is_flagged_scam:
        return 0

    notified_count = 0

    for profile in Profile.objects.select_related('user'):
        score = calculate_match_score(profile, job)
        if score < MATCH_ALERT_THRESHOLD:
            continue

        notification, created = Notification.objects.get_or_create(
            user=profile.user,
            job=job,
            defaults={'match_score': score},
        )
        if not created:
            # Already notified this user about this job — the unique_together
            # constraint would have raised anyway, but checking `created`
            # here avoids relying on catching an IntegrityError.
            continue

        if profile.notify_email:
            send_match_email(profile.user, job, score)
            notification.sent_email = True
            notification.save(update_fields=['sent_email'])

        notified_count += 1

    return notified_count


def sweep_all_active_jobs_for_matches():
    """
    Periodic (Celery Beat) safety net: re-checks every active, non-scam job
    against every profile. Exists to catch matches the immediate ingest-time
    check would miss — e.g. a profile created, or its skills edited, AFTER
    a job was already ingested.

    Deliberately runs infrequently (every 6 hours, see CELERY_BEAT_SCHEDULE)
    since this is an O(jobs x profiles) scan — the same cost-conscious
    thinking applied to Auto-Apply applies here too.
    """
    total_notified = 0
    for job in Job.objects.filter(is_active=True, is_flagged_scam=False):
        total_notified += notify_matching_profiles(job)
    return total_notified