"""Bounded literal-term search; user text is never SQL or FTS syntax."""
import re
import unicodedata
from django.db.models.expressions import RawSQL
from rest_framework.exceptions import ValidationError


def expression(value):
    if len(value) > 255:
        raise ValidationError({'q': ['Use 255 characters or fewer.']})
    words = re.findall(r'[^\W_]+', unicodedata.normalize('NFKC', value), flags=re.UNICODE)
    if len(words) > 12 or any(len(word) > 64 for word in words):
        raise ValidationError({'q': ['Use at most 12 words, each at most 64 characters.']})
    # Quotes make OR/NOT/NEAR ordinary terms; prefix supports mobile partial typing.
    return ' AND '.join('"' + word + '"*' for word in words)


def search_jobs(queryset, value):
    # see docs/CONCEPTS.md#job-full-text-search
    query = expression(value.strip())
    if not query:
        return queryset.none() if value.strip() else queryset
    # Join the matching FTS rows once. A correlated MATCH subquery per job
    # repeatedly scans broad matches and made production p95 exceed the budget.
    matches = queryset.extra(tables=['jobs_job_search'], where=[
        'jobs_job.id = jobs_job_search.rowid', 'jobs_job_search MATCH %s'], params=[query])
    relevance = RawSQL('bm25(jobs_job_search, 8.0, 3.0, 1.0, 1.0, 2.0)', [])
    return matches.alias(search_rank=relevance).order_by('search_rank', '-posted_at', '-pk')
