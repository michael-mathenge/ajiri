# AJ-12 production HTTPS activation

Completed 20 October 2026 on unchanged production code
`647449851c98f5b22e0419db673f2500c86d1e86`, under Michael's roadmap authorization.

PythonAnywhere's support reply confirms native WSGI HTTPS recognition and stripping
of all client-supplied X-Forwarded-Proto fields, including duplicates and lists.
A temporary private WSGI probe recorded only three booleans on a real HTTPS health
request: native scheme HTTPS, `request.is_secure()` true and proxy SSL setting None.
All three passed with a spoofed comma-separated header. The original WSGI file was
restored exactly before activating the settings; no public diagnostic route remains.

Only five private configuration values changed:

```text
TRUST_PROXY_SSL_HEADER=False
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=300
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```

Other parsed configuration values were compared and preserved; file mode remains
0600. Host Force HTTPS stays enabled. No code, schema or email change occurred.

After reload, live health, login and CSRF bootstrap each returned 200 and exactly
`Strict-Transport-Security: max-age=300`. HTTP redirected to HTTPS without looping.
Duplicate spoofed forwarding headers still returned HTTPS 200. Authenticated
server-side owner profile/jobs/applications reads and private CV download returned
200. A new browser password login was not performed. `manage.py check` passed;
`check --deploy` retained only W005/W021 because subdomains/preload intentionally
remain disabled, as required. Do not enable those options merely to silence warnings.

Jira AJ-12 was moved to Done with the evidence comment, and its status was reread
and confirmed. Private rollback material is outside the repository under the
owner's `.config/ajiri-https-check-20261020` directory. Restore only these five
settings to their prior values and reload if necessary; retain host HTTPS and all
database writes. HSTS can persist in browsers for its remaining five-minute lifetime.
Never restore a database for this configuration rollback.

## Stage B reconfirmation — 1 November 2026

At15:14EAT a live HTTPS GET /api/health/ returned HTTP200, {"status":"ok"},
and exactly Strict-Transport-Security: max-age=300, without subdomains/preload.
This corroborates the completed native-WSGI activation above; no settings or code
were changed. AJ-12 remains Done; comment10172 and its reconciled description record
the current evidence while retaining historical blocked notes as superseded.

## Seven-day HSTS rollout — 1 November 2026

Michael explicitly authorized updating only the nonsecret SECURE_HSTS_SECONDS
entry from300 to604800. A guarded byte replacement required exactly one matching
entry, preserved every other byte and the existing file mode, and printed no file
contents or credentials. No environment copy or new secret-bearing backup was made.
Django check passed before reloading the existing web app. Live HTTPS health at
17:08:56UTC returned200/statusok and exactly Strict-Transport-Security:
max-age=604800, without subdomains/preload. The earlier300-second records above
remain historical Stage B evidence, not the current operator target.

Seven days is the next gradual rollout stage, following Django's guidance to
increase after HTTPS verification:
https://docs.djangoproject.com/en/6.0/ref/middleware/#http-strict-transport-security
The code's fallback remains staged300; the production override is604800. Keep
native HTTPS/proxy handling, redirect and host Force HTTPS unchanged. Rollback of
this one value is300 plus reload, but browsers retain an already received HSTS
policy until it expires or a later valid HTTPS response updates it. No database,
application eligibility, sending or feed-display setting changed in this operation.
