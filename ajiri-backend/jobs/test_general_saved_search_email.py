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

    def test_current_normalized_filters_are_retained_when_collecting_real_transport_windows(self):
        SavedSearch.objects.filter(pk=self.saved.pk).update(county='nairobi-city', work_arrangement='remote',
                                                          max_experience_years=2)
        matching = self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=1)
        self.job(county='nairobi-city', work_arrangement='remote', min_experience_years=5)
        self.assertEqual(deliver_due(self.saved.pk), ['accepted'])
        self.assertEqual(list(self.saved.matches.values_list('job_id', flat=True)), [matching.pk])
        self.send.assert_called_once()

    def test_disabled_search_at_handoff_keeps_failure_and_does_not_retry(self):
        original = SearchTransport.send

        def disable(sink, payload):
            with override_settings(SAVED_SEARCHES_ENABLED=False):
                return original(sink, payload)

        with patch.object(SearchTransport, 'send', disable):
            self.assertEqual(deliver_due(self.saved.pk), ['definite_failure'])
        self.assertEqual(deliver_due(self.saved.pk), [])
        self.send.assert_not_called()
        self.assertEqual(DeliveryAttempt.objects.count(), 1)

    def test_continuation_skips_old_ineligible_rows_without_recollecting(self):
        from .general_saved_search_email import deliver_batch, current
        from .saved_searches import collect_due
        self.job()
        self.job()
        collect_due(self.saved.pk, 'email')
        identities = list(self.saved.matches.order_by('pk').values_list('pk', flat=True))
        self.assertEqual(len(identities), 3)
        with patch('jobs.general_saved_search_email.current',
                   side_effect=lambda row: row.pk == identities[-1] and current(row)), \
                patch('jobs.general_saved_search_email.collect_due') as collect:
            first = deliver_batch(self.saved.pk, limit=1)
            second = deliver_batch(self.saved.pk, limit=1, cursor=first['next_cursor'])
            last = deliver_batch(self.saved.pk, limit=1, cursor=second['next_cursor'])
        self.assertEqual(first['examined'], 1)
        self.assertFalse(second['exhausted'])
        self.assertTrue(last['exhausted'])
        self.assertEqual(last['results'], ['accepted'])
        self.assertEqual(collect.call_count, 1)
        self.send.assert_called_once()

    def test_cursor_cannot_cross_search_or_revision(self):
        from .general_saved_search_email import deliver_batch
        self.job()
        first = deliver_batch(self.saved.pk, limit=1)
        self.assertIsNotNone(first['next_cursor'])
        other = self.search(email_frequency='daily')
        with self.assertRaises(ValueError):
            deliver_batch(other.pk, cursor=first['next_cursor'])
        SavedSearch.objects.filter(pk=self.saved.pk).update(revision=2)
        with self.assertRaises(ValueError):
            deliver_batch(self.saved.pk, cursor=first['next_cursor'])
        self.send.assert_called_once()

    def test_command_rejects_invalid_programmatic_limit_without_collection(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        for limit in (0, 51, True, '2'):
            with self.assertRaises(CommandError):
                call_command('deliver_saved_search_emails', search_id=self.saved.pk,
                             limit=limit, stdout=StringIO())
        self.assertFalse(self.saved.matches.exists())
        self.send.assert_not_called()
