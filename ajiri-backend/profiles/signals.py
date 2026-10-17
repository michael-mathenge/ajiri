# A Django "signal" = code that runs automatically when something happens
# elsewhere in the app, without that other code needing to know this file exists.
# Here: EVERY time a User is saved for the first time (created=True), Django
# automatically fires post_save, and this function creates their blank Profile.
# This guarantees no User can ever exist without a Profile — no matter whether
# they registered via the API, admin panel, or createsuperuser.
#
# GOTCHA: this only works because profiles/apps.py has `ready()` importing this
# file. Without that import, this decorator never actually connects to Django's
# signal system — the code just sits here, unused, doing nothing.

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models.signals import post_delete
from .models import Profile, CVApproval


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_delete, sender=CVApproval)
def remove_approved_cv(sender, instance, **kwargs):
    # A rolled-back deletion must not remove a still-referenced private file.
    # see docs/CONCEPTS.md#cv-builder-flow
    name, storage = instance.document.name, instance.document.storage
    def cleanup():
        try:
            if name:
                storage.delete(name)
        except OSError:
            # The row deletion already committed. Report-only orphan review is
            # documented; never expose filenames or exception text to callers.
            pass
    transaction.on_commit(cleanup)
