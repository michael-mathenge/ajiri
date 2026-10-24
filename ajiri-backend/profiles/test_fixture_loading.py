"""A fixture supplies its own profile; raw user saves must not invent one."""
from io import StringIO
from pathlib import Path
import tempfile

from django.contrib.auth import get_user_model
from django.core import serializers
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from .models import Profile


class ProfileFixtureTests(TestCase):
    def test_raw_user_save_does_not_create_an_unsupplied_profile(self):
        user = get_user_model()(email='raw-fixture@example.invalid', date_joined=timezone.now())
        user.set_unusable_password()
        user.save_base(raw=True)
        self.assertFalse(Profile.objects.filter(user=user).exists())

    def test_serialized_user_and_profile_restore_without_a_duplicate_profile(self):
        user = get_user_model().objects.create_user(email='restore-fixture@example.invalid')
        profile = user.profile
        profile.headline = 'Synthetic retained headline'
        profile.notify_email = False
        profile.save()
        data = serializers.serialize('json', [user, profile])
        identity, profile_id = user.pk, profile.pk
        user.delete()
        with tempfile.TemporaryDirectory(prefix='ajiri-synthetic-fixture-') as folder:
            path = Path(folder)/'synthetic.json'
            path.write_text(data, encoding='utf-8')
            call_command('loaddata', str(path), stdout=StringIO())
        restored = Profile.objects.get(user_id=identity)
        self.assertEqual((restored.pk, restored.headline, restored.notify_email),
            (profile_id, 'Synthetic retained headline', False))
        self.assertEqual(Profile.objects.filter(user_id=identity).count(), 1)
