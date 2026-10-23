"""Give threaded HTTP acceptance tests their own disposable SQLite file."""
from pathlib import Path
from tempfile import TemporaryDirectory

from django.db import connections
from django.test.runner import DiscoverRunner


class DisposableBrowserRunner(DiscoverRunner):
    # see docs/CONCEPTS.md#browser-database-isolation
    def run_tests(self, test_labels, **kwargs):
        browser = any(label == 'browser_tests' or label.startswith('browser_tests.')
                      for label in (test_labels or []))
        connection = connections['default']
        if not browser or connection.vendor != 'sqlite':
            return super().run_tests(test_labels, **kwargs)
        original_name = connection.settings_dict['NAME']
        original_test_name = connection.settings_dict['TEST'].get('NAME')
        # LiveServer otherwise shares one in-memory SQLite connection across
        # HTTP threads. A file gives each thread its normal independent connection.
        with TemporaryDirectory(prefix='ajiri-browser-db-') as directory:
            connection.settings_dict['TEST']['NAME'] = str(Path(directory) / 'browser.sqlite3')
            try:
                return super().run_tests(test_labels, **kwargs)
            finally:
                connection.close()
                connection.settings_dict['NAME'] = original_name
                connection.settings_dict['TEST']['NAME'] = original_test_name
