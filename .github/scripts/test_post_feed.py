from email.message import Message
from io import BytesIO
from unittest import TestCase
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
from post_feed import IngestFailure, NoRedirect, submit

BASE = 'https://example.invalid'
KEY = 'synthetic-test-key'
COUNTERS = b'{"created":2,"skipped":3,"flagged":0,"notified":1}'


class Response(BytesIO):
    def __init__(self, data=b'{"status":"ok"}', status=200, content_type='application/json'):
        super().__init__(data)
        self.status = status
        self.headers = Message()
        self.headers['Content-Type'] = content_type


class PostFeedTests(TestCase):
    def run_submit(self, responses):
        opener, sleeper, report = Mock(), Mock(), Mock()
        opener.open.side_effect = responses
        submit(BASE, KEY, b'<rss/>', opener=opener, sleep=sleeper, report=report)
        return opener, sleeper, report

    def test_healthy_host_receives_one_credentialled_post_and_only_counters_logged(self):
        opener, sleeper, report = self.run_submit([Response(), Response(COUNTERS)])
        self.assertEqual(opener.open.call_count, 2)
        health, post = [call.args[0] for call in opener.open.call_args_list]
        self.assertEqual((health.get_method(), post.get_method()), ('GET', 'POST'))
        self.assertIsNone(health.get_header('X-ingest-key'))
        self.assertEqual(post.get_header('X-ingest-key'), KEY)
        self.assertEqual(post.data, b'<rss/>')
        self.assertFalse(sleeper.called)
        self.assertNotIn(KEY, str(report.call_args_list))
        self.assertIn('created=2', str(report.call_args_list))

    def test_host_404_is_bounded_and_never_posts_or_logs_response(self):
        opener, sleeper, report = Mock(), Mock(), Mock()
        opener.open.side_effect = [HTTPError(BASE, 404, 'private body', {}, BytesIO(b'Coming Soon private text')) for _ in range(3)]
        with self.assertRaisesRegex(IngestFailure, 'No feed was posted') as caught:
            submit(BASE, KEY, b'xml', opener=opener, sleep=sleeper, report=report)
        self.assertEqual(opener.open.call_count, 3)
        self.assertEqual(sleeper.call_count, 2)
        self.assertTrue(all(call.args[0].get_method() == 'GET' for call in opener.open.call_args_list))
        self.assertNotIn('private', str(report.call_args_list) + str(caught.exception))

    def test_temporary_host_failure_recovers_before_post(self):
        opener, sleeper, _ = self.run_submit([URLError('private network data'), Response(), Response(COUNTERS)])
        self.assertEqual(sleeper.call_count, 1)
        self.assertEqual(sum(call.args[0].get_method() == 'POST' for call in opener.open.call_args_list), 1)

    def test_200_html_is_not_health_success(self):
        opener = Mock()
        opener.open.side_effect = [Response(b'<html/>', content_type='text/html') for _ in range(3)]
        with self.assertRaises(IngestFailure):
            submit(BASE, KEY, b'xml', opener=opener, sleep=Mock(), report=Mock())
        self.assertEqual(opener.open.call_count, 3)

    def test_uncertain_post_is_never_replayed(self):
        for failure in [URLError('private credentials'), TimeoutError('private filename'), Response(b'not-json'),
                        HTTPError(BASE, 503, 'private detail', {}, BytesIO(b'private body'))]:
            opener = Mock()
            opener.open.side_effect = [Response(), failure]
            with self.subTest(failure=type(failure).__name__), self.assertRaisesRegex(IngestFailure, 'uncertain') as caught:
                submit(BASE, KEY, b'xml', opener=opener, sleep=Mock(), report=Mock())
            self.assertEqual(opener.open.call_count, 2)
            self.assertNotIn('private', str(caught.exception))

    def test_auth_and_route_errors_are_distinguished(self):
        for status in (403, 404):
            opener = Mock()
            opener.open.side_effect = [Response(), HTTPError(BASE, status, 'hidden', {}, BytesIO())]
            with self.subTest(status=status), self.assertRaisesRegex(IngestFailure, str(status)):
                submit(BASE, KEY, b'xml', opener=opener, sleep=Mock(), report=Mock())
            self.assertEqual(opener.open.call_count, 2)

    def test_bad_configuration_and_empty_feed_never_make_network_calls(self):
        for base, key, feed in [('http://example.invalid', KEY, b'xml'),
            ('https://user:secret@example.invalid', KEY, b'xml'), (BASE + '/api', KEY, b'xml'),
            (BASE, '', b'xml'), (BASE, 'bad\nheader', b'xml'), (BASE, KEY, b'')]:
            opener = Mock()
            with self.subTest(base=base), self.assertRaises(IngestFailure):
                submit(base, key, feed, opener=opener)
            opener.open.assert_not_called()

    def test_redirects_never_forward_credentials(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, 'redirect', {}, 'https://other.invalid'))

    def test_success_requires_valid_bounded_nonnegative_counters(self):
        for body in [b'{}', b'{"created":true}', b'x' * 4097]:
            with self.subTest(body=body[:10]), self.assertRaises(IngestFailure):
                self.run_submit([Response(), Response(body)])
