# WP16 dependency advisory reconciliation

16 October 2026. Deployment base stays c4b93647f65618e8d13f9baa47ded6d22a28f0fb.
No requirements file changed: Dependabot commit 91ce77f already upgraded runtime
and dev pins consistently. Scanner pip-audit 2.10.1 ran against BOTH requirement
files, not just installed packages. Exact commands/output are in
audit-evidence/2026-10-16/{production,development}.txt. Both exit 0 with
`No known vulnerabilities found`. This is an advisory snapshot, not proof of safety.

The original local venv still held Django 6.1/PyJWT 2.13.0. It was preserved;
tests use a new isolated Python 3.12 environment with Django 6.1.2,
PyJWT 2.15.1 and SimpleJWT 5.5.1 from the existing requirements. `pip check` reports
`No broken requirements found.` Scanner resolution and installed-runtime scans
are different inputs; never infer one from the other.

## All 15 historical findings

Original scan reported Django 6.1 and PyJWT 2.13.0. The table gives the current
primary advisory's fix metadata, not a claim that every reported issue was reachable.
Read each record at https://api.osv.dev/v1/vulns/ID (replace ID with its table ID),
backed by https://github.com/pypa/advisory-database .

| ID | Old package | Fix metadata | Ajiri applicability at the old pins |
|---|---|---|---|
| PYSEC-2026-3717 | Django 6.1 | Current record: 5.2.17 / 6.0.8 | GeoDjango deeply nested geometry denial of service; no GIS app/fields in Ajiri. Historical scanner also listed 6.1.1, absent from current record: metadata discrepancy retained, not silently asserted fixed by that version. |
| PYSEC-2026-4140 | PyJWT 2.13.0 | 2.14.0 | Unknown-kid JWKS request amplification; Ajiri uses symmetric HS256, no JWK_URL. Not an observed path. |
| PYSEC-2026-4141 | PyJWT 2.13.0 | 2.15.0 | Recursive pre-verification payload parsing; no app-level unverified/JWKS parsing found. Dependency path reviewed; no exploit asserted. |
| PYSEC-2026-4142 | PyJWT 2.13.0 | 2.14.0 | Deep token headers can enter JWT validation from public requests; relevant defensive upgrade. |
| PYSEC-2026-4143 | PyJWT 2.13.0 | 2.14.0 | Empty JWK HMAC keys; no JWK configuration in this app. |
| PYSEC-2026-4144 | PyJWT 2.13.0 | 2.14.0 | JWKS redirect following; no remote JWKS configured. |
| PYSEC-2026-4145 | PyJWT 2.13.0 | 2.14.0 | Mutated asymmetric PEM treated as HMAC; server-controlled symmetric key, not applicant-supplied PEM. |
| PYSEC-2026-4146 | PyJWT 2.13.0 | No explicit fixed event; last_affected=2.13.0 | Reused mutable verification options; no shared app options switching from unverified to verified found. 2.15.1 outside reported affected range; do not invent a fix version. |
| PYSEC-2026-4147 | PyJWT 2.13.0 | 2.14.0 | Noncanonical signatures versus raw-token revocation; relevant to authentication review, but SimpleJWT blacklists jti, not a raw-token string list. Keep replay tests. |
| PYSEC-2026-4148 | PyJWT 2.13.0 | 2.14.0 | PEM-format regex resource exhaustion; key is controlled configuration, no public key input. |
| PYSEC-2026-4149 | PyJWT 2.13.0 | 2.14.0 | DER public key used as HMAC secret; no DER-key authentication configured. |
| PYSEC-2026-4150 | PyJWT 2.13.0 | 2.14.0 | BOM/key-format bypass; server-controlled symmetric key limits the identified key-input path. |
| PYSEC-2026-4151 | PyJWT 2.13.0 | 2.14.0 | Public JWK container accepted as HMAC secret; no JWK containers accepted by Ajiri. |
| PYSEC-2026-4152 | PyJWT 2.13.0 | 2.14.0 | Malformed RSA JWK aborts JWK set; no remote JWK set configured. |
| PYSEC-2026-4183 | PyJWT 2.13.0 | 2.15.0 | Mismatched OKP private/public JWK material; no proof-header/private-JWK import flow in Ajiri. |

Evidence: config/settings.py SIMPLE_JWT has no algorithm override or JWK_URL;
installed SimpleJWT TokenBackend defaults HS256 and passes its own decode options.
No app-level jwt.decode/options/JWK imports were found. This is static applicability
assessment, not penetration testing or a waiver to retain vulnerable versions.

## Why results differ

The recorded 15-finding snapshot used older pins, while today's requirements resolve
the already-merged patch/minor upgrades. Current OSV metadata also differs for the
Django record. Do not attribute the change solely to new publication dates. A prior
claimed clean Python scan without saved commands/output is UNVERIFIED; the older
audit's npm clean result and pip check result were not Python vulnerability scans.
No major upgrade, auth logic change, ignore list or automatic audit fix was needed.

Deployment-stage reminder: this local evidence does not establish which versions
Michael has installed on production. He owns c4b9364 deployment; no silent SHA change.

## Executed WP16 gates

Python 3.12.6, Django 6.1.2, PyJWT 2.15.1: pip check/check/migration check pass;
90 tests run, 89 pass, one Windows symlink skip. Production-like check --deploy
retains only intentional W005/W021 (no subdomains/preload). Node 24.19: npm ci,
lint, 25 component tests and build pass. No frontend package regeneration.
