from unittest.mock import patch

from django.test import TransactionTestCase, override_settings

from . import test_saved_searches as fixtures
from .brevo_transport import BrevoTransport, Result
from .general_saved_search_email import deliver_due, SearchTransport
from .models import DeliveryAttempt, DeliveryDailyBudget, SavedSearch


@override_settings(REAL_EMAIL_ENABLED=True, ACCOUNT_SECURITY_EMAIL_ENABLED=True,
    SAVED_SEARCH_EMAIL_ENABLED=True, ALERT_EMAIL_ENABLED=True, SAVED_SEARCHES_ENABLED=True,
    JOB_FRESHNESS_ENFORCED=True, EMAIL_DELIVERY_MODE='account_security', ACCOUNT_EMAIL_TEST_CAPTURE=False,
    EMAIL_PLATFORM_FROM='platform@example.invalid', BREVO_TIMEOUT_SECONDS=10,
    ACCOUNT_LINK_ORIGIN='https://example.invalid', BREVO_API_KEY='synthetic-test-only',
    EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class GeneralSearchTests(fixtures.SearchFixtures, TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.consent()
        self.saved = self.search(email_frequency='daily')
        self.job()
        sender = patch.object(BrevoTransport, 'send', return_value=Result('accepted', '<synthetic>'))
        self.send = sender.start()
        self.addCleanup(sender.stop)

    def test_real_adapter_uses_durable_window_and_deduplicates_overlapping_searches(self):
        other = self.search(email_frequency='daily')
        self.assertEqual(deliver_due(self.saved.pk), ['accepted'])
        self.assertEqual(deliver_due(self.saved.pk), [])
        self.assertEqual(deliver_due(other.pk), ['accepted'])
        self.send.assert_called_once()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
        self.assertEqual(DeliveryDailyBudget.objects.get(scope='global').alert_reserved, 1)

    def test_unknown_handoff_never_repeats(self):
        self.send.return_value = Result('unknown', failure_category='timeout')
        self.assertEqual(deliver_due(self.saved.pk), ['unknown'])
        self.assertEqual(deliver_due(self.saved.pk), [])
        self.send.assert_called_once()

    def test_disabled_does_not_collect_or_reserve(self):
        with override_settings(SAVED_SEARCH_EMAIL_ENABLED=False):
            self.assertEqual(deliver_due(self.saved.pk), [])
        self.assertFalse(self.saved.matches.exists())
        self.assertFalse(DeliveryAttempt.objects.exists())
        self.send.assert_not_called()

    def test_edit_at_handoff_blocks_provider_and_keeps_receipt(self):
        original = SearchTransport.send

        def edit(sink, payload):
            SavedSearch.objects.filter(pk=self.saved.pk).update(revision=2)
            return original(sink, payload)

        with patch.object(SearchTransport, 'send', edit):
            self.assertEqual(deliver_due(self.saved.pk), ['definite_failure'])
        self.send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)
