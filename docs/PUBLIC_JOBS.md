# Public job pages: AJ-42 test integration

23 October 2026. This package implements the provisional backlog's synthetic
publication contract. Publication is disabled by default; it is not evidence of
Google indexing, rich-result eligibility or production activation.

`PUBLIC_JOBS_ENABLED=True` and a fixed HTTPS `PUBLIC_JOB_ORIGIN` opt in to
`/vacancies/<id>/<slug>/`, `/sitemap.xml`, paginated job sitemaps and `/robots.txt`.
Only active, non-scam jobs with nonblank titles and employers are exposed. Existing
authenticated APIs and private documents retain their access rules. Robots rules
are crawler guidance, never access control. Authenticated and anonymous visitors
receive identical job-only content without request context processors.

JobPosting metadata requires an original, nonfuture publication date, full bounded
description, safe source link and an explicit physical country in source location
text (for example `Nairobi, Kenya`). Unknown country, remote roles and shortened
content omit metadata. Salary, expiry and direct-apply claims are not invented.
Canonical URLs use the configured origin, never the request Host or source URL.
Source descriptions are escaped text; the page loads no scripts or third-party
resources apart from its inert JSON-LD metadata.

Before publication, confirm source republication rights, attribution, stale-job
handling and real source quality. Keep the flag off until these release conditions
are resolved. Rollback disables publication without changing job rows, approvals
or files. No migration or dependency is needed.

Focused command (from `ajiri-backend`):
`python manage.py test jobs.test_public_jobs` — seven tests passed in 0.304s.
The first run found a non-UTF-8 template; re-encoding the template fixed that
demonstrated defect. Full package gates and production activation remain pending.
