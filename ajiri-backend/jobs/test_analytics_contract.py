"""Synthetic choice is never production consent or production collection."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from django.test import SimpleTestCase

from .analytics_test_contract import AggregateFixture, AnalyticsTestSession, POLICY


class AnalyticsContractTests(SimpleTestCase):
    def setUp(self):
        self.at = datetime(2026, 10, 24, 20, 59, tzinfo=timezone.utc)
        self.aggregate = AggregateFixture()
        self.session = AnalyticsTestSession(self.aggregate, lambda: self.at, enabled=True)

    def test_default_disabled_even_with_separate_explicit_fixture_choice(self):
        session = AnalyticsTestSession(self.aggregate, lambda: self.at)
        session.choose(True, policy_version=POLICY)
        self.assertFalse(session.record('search_used'))
        self.assertEqual(self.aggregate.counts(), {})

    def test_enabled_does_not_create_or_infer_consent(self):
        self.assertIsNone(self.session.choice)
        self.assertFalse(self.session.record('cv_review_opened'))
        self.assertEqual(self.aggregate.counts(), {})

    def test_choice_requires_boolean_and_matching_policy(self):
        for accepted, policy in [('yes', POLICY), (1, POLICY), (True, 'old-policy')]:
            with self.assertRaises(ValueError):
                self.session.choose(accepted, policy_version=policy)
        self.assertIsNone(self.session.choice)

    def test_revocation_stops_future_collection_without_rewriting_earlier_counts(self):
        choice = self.session.choose(True, policy_version=POLICY)
        self.assertEqual((choice.at, choice.policy_version), (self.at, POLICY))
        self.assertTrue(self.session.record('application_review_opened'))
        before = self.aggregate.counts()
        self.session.choose(False, policy_version=POLICY)
        self.assertFalse(self.session.record('application_review_opened'))
        self.assertEqual(self.aggregate.counts(), before)

    def test_names_and_attributes_cannot_smuggle_queries_or_private_documents(self):
        self.session.choose(True, policy_version=POLICY)
        for event, attrs in [('unknown', {}), ('https://example.invalid/private', {}),
                             ('search_used', {'q': 'private synthetic query'}),
                             ('cv_review_opened', {'document': 'private.docx'}),
                             ('search_used', {'email_consent': True})]:
            with self.assertRaises(ValueError):
                self.session.record(event, **attrs)
        self.assertEqual(self.aggregate.counts(), {})

    def test_only_coarse_nairobi_day_and_allowlisted_name_are_retained(self):
        self.session.choose(True, policy_version=POLICY)
        self.session.record('search_used')
        self.at += timedelta(minutes=2)
        self.session.record('search_used')
        self.assertEqual(self.aggregate.counts(), {
            ('2026-10-24', 'search_used'): 1, ('2026-10-25', 'search_used'): 1})
        copy = self.aggregate.counts(); copy.clear()
        self.assertEqual(len(self.aggregate.counts()), 2)

    def test_concurrent_fixture_counts_are_not_lost_and_revocation_is_final(self):
        self.session.choose(True, policy_version=POLICY)
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertTrue(all(pool.map(lambda _: self.session.record('search_used'), range(40))))
        self.session.choose(False, policy_version=POLICY)
        with ThreadPoolExecutor(max_workers=4) as pool:
            self.assertFalse(any(pool.map(lambda _: self.session.record('search_used'), range(20))))
        self.assertEqual(self.aggregate.counts(), {('2026-10-24', 'search_used'): 40})

    def test_no_network_adapter_or_naive_clock_is_accepted(self):
        with self.assertRaises(ValueError):
            AnalyticsTestSession(object(), lambda: self.at, enabled=True)
        session = AnalyticsTestSession(self.aggregate, lambda: datetime(2026, 10, 24), enabled=True)
        with self.assertRaises(ValueError):
            session.choose(True, policy_version=POLICY)
        self.session.choose(True, policy_version=POLICY)
        self.at -= timedelta(seconds=1)
        self.assertFalse(self.session.record('search_used'))
