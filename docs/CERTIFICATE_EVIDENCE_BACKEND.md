# Certificate evidence backend — inactive

AJ-79 existed before implementation. The 31 October instruction authorized backend
implementation with reversible defaults; it supersedes the earlier design-only
approval pauses in CERTIFICATES_DECISIONS.md. It does not supply legal facts,
scanner hosting, capacity, consent to sharing, retention approval or activation.

Defaults: PDF only, 5 MiB per file, five active files and 20 MiB per owner. Pending,
unavailable and infected files count toward quota. No original filename, OCR,
qualification verification, public links or employer/application attachments.

With CERTIFICATE_EVIDENCE_ENABLED=False, routes return 404 after authentication.
GET /api/profiles/me/certificates/ lists safe owner metadata. PUT to
/api/profiles/me/certificates/{saved-certification-uuid}/ uses multipart document
and expected_revision. Replacements also require expected_id and expected_hash
from current metadata. New files remain pending in quarantine. GET on the same
owner route downloads only intact evidence with a clean scan no older than 24h.
DELETE accepts JSON expected_revision/expected_id/expected_hash and confirm=true.
Removing evidence is separate from removing its text entry. No automatic mutation
retry is supported: reconcile current metadata after an uncertain response.

Migration profiles.0008 creates only the evidence table/constraints. Existing
accounts, CV JSON and immutable approvals are not backfilled or changed. The
existing export and verified-request erasure inventories include evidence, and
private-media backup covers quarantine bytes. The audit_certificate_evidence
command reports missing/corrupt/unreferenced counts without deleting anything.

Activation prerequisites: reviewed migration and paired source, verified paused-
writer backup/off-server isolated restore including quarantine, actual account
capacity, approved retention/notice wording, operational scanner host/signatures/
resource limits and synthetic concurrency/recovery checks. No real accounts have
been exported or erased and no production migration/flag change is authorized.

Rollback keeps the additive table and private files, disables certificate routes,
and preserves newer account writes. Do not reverse a populated migration or restore
an old database. Scanner outages keep files quarantined; they do not authorize a
download bypass. Ordinary file deletion after commit can fail; run the report-only
audit and investigate, preserving backups and user work.
