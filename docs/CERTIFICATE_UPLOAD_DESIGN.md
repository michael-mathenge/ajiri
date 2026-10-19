# Certificate uploads design for review

17 October 2026. Proposal only. No models, migrations, upload endpoint, credentials,
production changes or new dependencies implemented. The user requested certificate
uploads during the registration-to-CV journey. AGENTS.md requires schema review.

## User flow and meaning

Each optional certification entry keeps its manually entered name, issuer and
issue/expiry dates. It gains an optional Upload certificate action after saving
the draft. Initial recommended format: PDF only, 5 MiB per file, one active file
per certification, five files and 20 MiB total per owner. These limits need approval
given the production 512 MiB account quota; metadata-only certifications stay usable
without an upload. Phone image support is a separate format-validation decision.

Show selected file, validation progress, saved status, size, Download, Replace and
Remove. Require an explicit upload; selecting a file alone must not transmit it.
Keep selected files only in memory. Native file selection does not lose draft text.
Save the certification first so its stable entry UUID is available. State clearly
that the file is private supporting evidence and has not been verified by Ajiri.
Do not extract text, infer qualifications, scan third-party services or fetch URLs.

The CV preview/DOCX uses the user-reviewed textual certification details only.
Do not embed the PDF, add a public URL, or bundle evidence into the CV download.
Application attachment selection and real delivery remain a separately approved
feature: uploading never authorizes sharing with an employer. Existing CV approval
snapshots and application files remain unchanged by evidence upload/removal.

## Proposed additive model

New `profiles.CertificateEvidence`, separate from User and Profile fields:

| Field | Type and default | Purpose |
|---|---|---|
| id | UUID primary key, uuid4, non-null | Opaque owner-authorized download identifier |
| profile | ForeignKey Profile, CASCADE, non-null | Ownership and account deletion |
| certification_id | UUID, non-null, no default | Stable existing draft entry UUID |
| document | FileField max_length 100, non-null | Existing private storage; random UUID path |
| sha256 | CharField 64, non-null | Exact byte integrity and reconciliation |
| size_bytes | PositiveIntegerField, non-null | Enforce file and owner quotas |
| created_at | DateTimeField timezone.now, non-null | Operational record, no inferred issue date |

Unique `(profile, certification_id)`; positive bounded size constraint. No original
filename retained: display a neutral certificate.pdf name. No `verified` field.
No historical backfill or inferred ownership/consent. Existing rows unaffected.
Existing string certification entry IDs must validate as UUID before accepting a
file. A new text-only draft still needs no evidence record or file.

The additive migration creates only this table/constraints. Old code ignores it.
Rollback code/client together while retaining the table/files and newer writes;
do not reverse/drop a populated table or restore an old DB as a routine rollback.
Deploy backup → stage reviewed migration source → review/apply migration → activate
paired code/client. The dates UI is independent and requires no schema change.

## Storage API and concurrency

Proposed authenticated endpoints scoped under `/api/profiles/me/`: evidence list,
explicit multipart upload/replace for an existing certification UUID, private
download by evidence UUID, and explicit remove. Wrong-owner records return 404.
Return safe metadata only, never physical paths/public media URLs. All responses
private/no-store, downloads attachment-only with nosniff and neutral filenames.
Use existing auth and upload throttling infrastructure, without changing CORS or
JWT behavior. No bulk upload or real email side effects.

Validate size while reading bounded chunks and PDF content using reviewed shared
validation helpers; never trust extension/client MIME. Reject empty, spoofed,
oversized files, links and path traversal. Do not claim content validation equals
malware scanning. PDFs can carry active content; attachment-only delivery prevents
inline rendering but cannot guarantee safety when opened. Malware scanning or
content sanitization feasibility/hosting approval remains a release decision;
never silently send private certificates to an external scanner.

Within a transaction, take a conditional write lock on the owner's CVWorkspace,
require expected workspace revision and expected evidence ID/hash for replacement,
confirm the certification still exists, and recalculate active file count/bytes.
This serializes quota checks against concurrent uploads/draft edits on SQLite.
Evidence-only changes do not change approved CV text or its revision/hash. A stale
text revision/removal race returns 409; preserve unsaved form text and selected file.

Store a newly validated file under a new random path before swapping the database
reference. Rollback removes only that new file; commit removes replaced bytes using
on_commit. A lost response may mean upload succeeded: GET metadata/hash to reconcile,
never automatically repeat a mutation. Process crashes can leave orphan files;
reconciliation is report-only, no automatic orphan deletion.

Remove asks the user to confirm loss of private evidence; delete the row in the
transaction and remove bytes after commit. Removing a certification with evidence
must warn before saving and remove its evidence atomically with that draft edit.
Account deletion cascades metadata and deletes files after commit. Existing approved
CV text remains independent; do not rewrite historical documents. Backups retain
copies under the reviewed backup/privacy retention policy, not immediate erasure.
No new automatic retention pruning or expiry-triggered deletion is proposed.

## Required tests and release decisions

Cover owner/anonymous access, no URL disclosure, valid/spoofed/empty/oversized PDF,
filename traversal, total quota and simultaneous last-slot uploads, stale revision,
replace/delete versus draft-entry removal, file/DB failures, rollback cleanup,
post-commit cleanup, interrupted upload reconciliation, no retry, download exact
hash, no approval changes, no application attachment/send, and isolated backup and
restore including evidence. Frontend tests cover cancel, clear validation, progress,
saved/error states, keyboard/mobile use and preservation of unsaved draft text.

Approval requested before implementation: PDF-only formats and quotas above; this
exact additive table/constraints; evidence kept separate from CV/application
attachments; deletion/backup semantics; acceptable malware handling for the private
pilot. Open policy: longer-term retention and future image/scanning support.
