"""Signed, scope-bound keyset continuation for manual delivery batches.

see docs/CONCEPTS.md#bounded-delivery-continuation
"""
from django.core import signing


def validate_limit(limit):
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError('Limit must be between 1 and 50.')


def decode(cursor, scope):
    if not cursor:
        return None
    try:
        value = signing.loads(cursor, salt='jobs.delivery-batch.v1')
        if (value['scope'] != scope or type(value['after']) is not int
                or type(value['through']) is not int or not 0 <= value['after'] <= value['through']):
            raise ValueError
        return value
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        raise ValueError('Invalid or stale delivery cursor.') from None


def page(rows, scope, cursor, limit):
    validate_limit(limit)
    position = decode(cursor, scope)
    if position is None:
        through = rows.order_by('-pk').values_list('pk', flat=True).first() or 0
        position = {'scope': scope, 'after': 0, 'through': through}
    remaining = rows.filter(pk__gt=position['after'], pk__lte=position['through'])
    identities = list(remaining.order_by('pk').values_list('pk', flat=True)[:limit])
    after = identities[-1] if identities else position['after']
    more = remaining.filter(pk__gt=after).exists()
    token = signing.dumps(dict(position, after=after), salt='jobs.delivery-batch.v1') if more else None
    return identities, token


def report(outcomes, examined, cursor):
    return {'examined': examined, 'outcomes': {state: outcomes.count(state) for state in sorted(set(outcomes))},
            'next_cursor': cursor, 'exhausted': cursor is None}
