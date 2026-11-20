"""Dormant PostgreSQL search candidate; schema is installed only by the lab.

see docs/CONCEPTS.md#postgres-bootstrap-candidate
"""
import re
import unicodedata
from django.db.models import BooleanField
from django.db.models.expressions import RawSQL


# Preserve literal ligatures/stroked letters: generic unaccent expands them,
# unlike SQLite unicode61. Fold only decomposable Latin accents, without stemming.
LATIN_FOLD = {}
for codepoint in range(0xC0, 0x2000):
    character = chr(codepoint)
    decomposed = unicodedata.normalize('NFD', character)
    if ('LATIN' in unicodedata.name(character, '') and len(decomposed) > 1
            and decomposed[0] in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            and all(unicodedata.category(c) == 'Mn' for c in decomposed[1:])):
        LATIN_FOLD[ord(character)] = decomposed[0].lower()
FOLD_FROM = ''.join(map(chr, LATIN_FOLD))
FOLD_TO = ''.join(LATIN_FOLD.values())

# Fixed tokenizer rules are part of the lab schema contract. Future rule changes
# need a reviewed index rebuild; this schema is never installed on production.
SCHEMA_SQL = """
CREATE FUNCTION public.ajiri_keyword_text(value text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
 SELECT regexp_replace(regexp_replace(translate(lower(coalesce(value,'')),
   '{fold_from}', '{fold_to}'), '[\u0300-\u036f]', '', 'g'), '[^[:alnum:]]+', ' ', 'g')
$$;
CREATE FUNCTION public.ajiri_job_vector(title text, company text, location text,
 description text, requirements text) RETURNS tsvector
LANGUAGE sql IMMUTABLE PARALLEL SAFE AS $$
 SELECT setweight(to_tsvector('simple',public.ajiri_keyword_text(title)),'A')
 || setweight(to_tsvector('simple',public.ajiri_keyword_text(company)),'B')
 || setweight(to_tsvector('simple',public.ajiri_keyword_text(requirements)),'B')
 || setweight(to_tsvector('simple',public.ajiri_keyword_text(description)),'C')
 || setweight(to_tsvector('simple',public.ajiri_keyword_text(location)),'D')
$$;
CREATE INDEX jobs_job_pg_search_gin ON jobs_job USING gin
 (public.ajiri_job_vector(title, company_name, location, description, requirements));
""".format(fold_from=FOLD_FROM, fold_to=FOLD_TO)

VECTOR = 'public.ajiri_job_vector(jobs_job.title,jobs_job.company_name,jobs_job.location,jobs_job.description,jobs_job.requirements)'
QUERY = "to_tsquery('simple',%s)"


def search(queryset, literal_expression):
    # expression() has already bounded and quoted only literal Unicode words.
    words = re.findall(r'"([^\"]+)"\*', literal_expression)
    query = ' & '.join("'"+word.translate(LATIN_FOLD).lower()+"':*" for word in words)
    if not words:
        return queryset.none()
    return queryset.alias(
        postgres_matches=RawSQL(VECTOR+' @@ '+QUERY, [query], output_field=BooleanField()),
        search_rank=RawSQL('ts_rank(ARRAY[1,1,3,8]::real[],'+VECTOR+','+QUERY+')', [query]),
    ).filter(postgres_matches=True).order_by('-search_rank', '-posted_at', '-pk')
