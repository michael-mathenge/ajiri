from django.core import signing
from django.test import SimpleTestCase
from .delivery_batches import decode, validate_limit


class DeliveryCursorValidationTests(SimpleTestCase):
    def test_malformed_signed_shapes_and_limits_are_rejected(self):
        for value in ([], None, {}, {'scope': 'x', 'after': True, 'through': 3},
                      {'scope': 'x', 'after': 4, 'through': 3}):
            with self.assertRaises(ValueError):
                decode(signing.dumps(value, salt='jobs.delivery-batch.v1'), 'x')
        for value in (0, 51, True, '2', None):
            with self.assertRaises(ValueError):
                validate_limit(value)
