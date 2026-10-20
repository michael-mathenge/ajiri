# Backlog spike decisions

20 October 2026. These decisions distinguish implemented baseline from future
work. They do not claim a production feature merely because its design is recorded.

## AJ-31 — build artifacts and line endings

Retain committed `frontend_build` for PythonAnywhere's current deployment: the
server has no Node build step. CI builds from the locked frontend and compares
the output; releases pin reviewed Git SHAs. The existing `.gitattributes` already
forces LF for Vite HTML, public files and committed build assets. Preserve binary
assets and do not change developers' Git configuration. Regenerate assets once
at the end of each frontend package; remove superseded hashed assets only through
that verified build replacement. A later CI artifact deployment must first provide
immutable provenance, checksum verification and recoverable preceding artifacts;
do not change the current deploy mechanism halfway through a release.

## AJ-36 — staging

Use an isolated local container/test database and synthetic data, plus required
CI checks, as the current no-purchase staging arrangement. It is not a second
public PythonAnywhere site and must never point at the production database/media
or real mail provider. A separate hosted staging environment remains conditional
on an eligible account and access; no hosting upgrade is authorized by this
decision. Verify container permissions, migrations, health and the user journey
before claiming the local setup is ready. The original Docker lesson stays intact.

## AJ-38 — public jobs and SEO

Recommend server-rendered public job detail pages with minimal job metadata,
canonical URLs, sitemap and eligible JobPosting structured data (AJ-42). Keep
profile, skills, match scores, applications, documents and account information
private. Exclude inactive/scam-flagged listings from discovery and return a truthful
unavailable response when removed; do not publish invented salaries/deadlines.
Keep third-party application destinations explicit. Search engines need reviewable
HTML rather than relying on an authenticated React page. This is a decision only:
the current job API remains authenticated until the refined AJ-42 contract is built.

## AJ-41 — Swahili

Recommend a locale dictionary with `en-KE` as fallback and `sw-KE` as the first
additional locale, using a maintained React i18n library when implementation is
scheduled. Persist the user's explicit locale without relying on inferred identity.
Translate application chrome, errors, dates, privacy/consent text and accessibility
labels; require human review for legal and account-security wording. Source job
descriptions and approved CV/application snapshots must not be silently translated.
Estimate implementation after inventorying strings and obtaining reviewed Swahili
copy; do not add an unused dependency or promise automatic translation in this spike.
