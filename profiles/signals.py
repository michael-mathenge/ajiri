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
from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)