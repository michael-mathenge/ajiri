"""Offline aggregate/choice fixture; no production instrumentation or transport.

see docs/CONCEPTS.md#analytics-test-contract
"""
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from threading import Lock
from zoneinfo import ZoneInfo

POLICY = 'analytics-contract-proposal-v1'
EVENTS = frozenset(('search_used', 'cv_review_opened', 'application_review_opened'))


@dataclass(frozen=True)
class TestChoice:
    accepted: bool
    at: datetime
    policy_version: str
    channel: str = 'analytics'


class AggregateFixture:
    """Memory-only counts; no identifiers, raw events, URLs or network adapter."""
    def __init__(self):
        self._counts = Counter()
        self._lock = Lock()

    def add(self, day, event):
        if type(day) is not str or date.fromisoformat(day).isoformat() != day or event not in EVENTS:
            raise ValueError('Only a coarse date and allowlisted event are accepted.')
        with self._lock:
            self._counts[(day, event)] += 1

    def counts(self):
        with self._lock:
            return dict(self._counts)


class AnalyticsTestSession:
    def __init__(self, aggregate, clock, *, enabled=False):
        if type(aggregate) is not AggregateFixture or type(enabled) is not bool:
            raise ValueError('Only the offline aggregate fixture is supported.')
        self.aggregate = aggregate
        self.clock = clock
        self.enabled = enabled
        self.choice = None
        self._lock = Lock()

    def now(self):
        value = self.clock()
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('An aware fixture clock is required.')
        return value

    def choose(self, accepted, *, policy_version):
        if type(accepted) is not bool or policy_version != POLICY:
            raise ValueError('An explicit independent choice and current proposal version are required.')
        with self._lock:
            self.choice = TestChoice(accepted, self.now(), policy_version)
            return self.choice

    def record(self, event, **attributes):
        if type(event) is not str or event not in EVENTS or attributes:
            raise ValueError('Use an allowlisted event name without attributes.')
        with self._lock:
            if not self.enabled or self.choice is None or not self.choice.accepted:
                return False
            at = self.now()
            if at < self.choice.at or self.choice.policy_version != POLICY:
                return False
            self.aggregate.add(at.astimezone(ZoneInfo('Africa/Nairobi')).date().isoformat(), event)
            return True
