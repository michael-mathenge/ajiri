# PR22 dependency build repair

19 October 2026. Prepared from PR22 head 8cbcbf9, preserving its dependency
versions and lockfile. Includes the separately reviewed concurrency-test correction
from 47783e9 (PR24), with no application runtime or CI workflow changes.

The frontend failure was a committed-build mismatch after dependency updates.
Locked npm ci, lint, all 66 component tests and build passed on Node 24.19.0.
Generated frontend_build is refreshed and index.html LF-normalized. File/hash
comparison with dist passed; the generated entry is index-UFH464Hx.js, matching
the output expected by the failed CI run. No lockfile modification was needed.

On this combined branch, backend check and migration drift passed; all 210 Django
tests passed in 119.030s, with one existing Windows symlink skip. Real email was
disabled and only disposable test database/private media were used.

No main merge or production deployment. CI remains required before merging this
PR. Review PR24 separately for the shared test correction. Roll back dependency
manifest, lockfile and generated build together; no migration/data rollback.
