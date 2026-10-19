# Certificate upload decisions

19 October 2026. D2 document only; no upload API, schema, migration, scanner,
retention job or employer sharing implemented. Read with CERTIFICATE_UPLOAD_DESIGN.md.
Each default below is a PROPOSED design assumption, not approval to build or release.
Michael must approve the choices before implementation; a changed choice requires
its impact on storage/schema/privacy to be reviewed again.

## Approval matrix

| Choice | Options | Recommendation and proposed default | Approval |
|---|---|---|---|
| Formats | PDF only; PDF plus JPEG/PNG; office documents | PDF only initially; images/office formats deferred | Pending |
| Per-file size | 1 MiB; 5 MiB; 10 MiB | 5 MiB (5*1024*1024 bytes), bounded while reading | Pending |
| PDF content validation | Extension/MIME; bounded signature/structure validation; sanitizer/scanner | Reuse reviewed PDF content validation, require PDF extension and content, reject empty/spoofed/oversized/truncated files; MIME alone never sufficient | Pending |
| Malware handling | Content checks only; local scanner/sanitizer; external service | Private pilot only with explicit content-check limitation, attachment-only download; no external transfer or scanner dependency | Pending; public release needs risk review |
| Owner quota | Unlimited; five files/20 MiB; stricter two-file pilot | Five active files and 20 MiB per owner, one file per certification; shared account disk quota reviewed before release | Pending |
| Private storage | Existing private MEDIA_ROOT; public media; third-party bucket | Existing private storage, UUID paths, no original filename, no public mapping | Pending |
| Ownership | Profile owner only; share links; employer access | Authenticated owner only; cross-owner/unknown returns 404, anonymous denied | Pending |
| Upload trigger | Automatic on selection; explicit Upload | Save certification text first, then explicit Upload; file selection alone transmits nothing | Pending |
| Meaning | Verified qualification; unverified supporting evidence | Explicitly unverified evidence; no OCR, qualification inference or URL fetching | Pending |
| Download | Inline PDF; private attachment | Attachment-only, no-store, nosniff, neutral certificate.pdf; integrity checked | Pending |
| Replacement | Overwrite in-place; atomic pointer swap | Validate new UUID file, swap DB reference atomically, remove old bytes after commit | Pending |
| Explicit removal | Immediate silent removal; confirmation | Confirm loss of active private evidence; delete metadata atomically and bytes after commit | Pending |
| Certification removal | Keep orphan; remove silently; confirm and remove together | Warn before draft save and remove associated evidence atomically with entry removal | Pending |
| Account deletion | Retain active evidence; cascade ownership | Cascade metadata and remove active files after commit; backup limits disclosed | Pending |
| Backups | Exclude certificates; include private media | Include in paused-writer media backups and isolated restore rehearsal | Pending |
| Backup retention | Immediate erasure everywhere; approved expiry; current draft policy | Existing 30-day DRAFT, report-only candidates; no automated pruning or promise of immediate backup erasure | Pending privacy/retention decision |
| Employer sharing | Automatically attach; share link; separately select later | Upload never authorizes sharing; no embedding/public link/bundling in CV or application, no email attachment now | Pending; prohibition retained by default |
| Schema | Embed in CV JSON; additive evidence table | Separate additive CertificateEvidence table described below; no User change or backfill | Pending exact schema |
| Concurrency | Last write wins; checked version and atomic quota | Expected workspace revision plus expected evidence ID/hash for replacement; serialize quota checks per owner | Pending |
| Crash/orphan cleanup | Automatic delete sweep; report-only reconciliation | Report-only; remove only request-owned uncommitted files on ordinary failure | Pending |
| Rollback | Reverse populated schema; retain data and roll code back | Retain table/files/newer writes; disable feature and roll reviewed client/server pair back | Pending |

Quotas concern active evidence, not backup/restore copies or immutable CV approvals.
Five files do not guarantee total hosting capacity: PythonAnywhere's recorded account
quota is small. Check account quota and projected users/backup space privately before
release. Do not use shared filesystem free space as account quota evidence. Lower
pilot limits may be chosen; never silently increase them to solve an error.

## Additive schema for explicit approval

Propose profiles.CertificateEvidence: UUID primary key (uuid4), non-null Profile FK
CASCADE, non-null certification_id UUID with no default, non-null private document
FileField max_length=100, SHA-256 CharField(64), positive size_bytes integer, and
created_at timestamp. Unique (profile, certification_id); size constrained to
1..5 MiB. Existing certification entry UUIDs must validate and belong to the saved
owner draft. No original name, verified flag, extracted text or historical backfill.
Existing accounts/documents gain no evidence records automatically. Existing CV
JSON and immutable approval snapshots stay unchanged.

The new table is additive and old code ignores it. Exact migration and deletion
hooks require separate review; Phase C creates none. Reversing a populated table
would destroy evidence, so it is not routine rollback. Keep schema and files while
disabling new routes/UI; retain newer database writes. Removal from active storage
is irreversible after commit and must be clearly confirmed, not framed as trash.

## Storage and API rules for the later package

Proposed owner-scoped list/upload/replace/download/remove routes under
/api/profiles/me/ require current auth, existing throttling and private/no-store
responses. Return safe evidence ID/size/status metadata, never physical paths or
public URLs. Selecting a file is local only; cancellation must preserve draft text.
Wrong owner receives no existence disclosure.

Check bounded content and quotas, then conditionally lock the owner's existing
CVWorkspace in a transaction, recheck certification membership/revision and sum
active evidence bytes/count. SQLite requires a real conditional write; do not rely
on select_for_update alone. Competing last-slot uploads must not exceed quotas.
Stage new bytes under a fresh UUID before the swap. Rollback cleans only that
request's new file; on_commit removes replaced/deleted active bytes. Reconcile GET
metadata/hash after an uncertain response; never automatically replay a mutation.

PDF content checks do not prove a PDF safe to open or free of active content.
Attachment-only delivery limits browser rendering, not malware risk in a viewer.
No dependency or external scanner is approved; propose any additional validation
capability before adding it. Scanner/sanitizer services would require separate
hosting, cost, data-transfer and privacy approval.

## Acceptance and tests before release

Test owner/anonymous/cross-owner access; no path disclosure; valid, HTML/executable
spoof, empty, truncated and oversized PDFs; path/control filename input; quota and
simultaneous last-slot uploads; stale replacement/removal races; DB/file failure,
rollback and on-commit cleanup; crash reconciliation; no automatic retries; download
hash; no changes to approval bytes/revision; no email/application attachment.
Rehearse backup/restore with evidence and confirm quota accounting after restore.

Manual checks: narrow phone layout, touch file picker, cancel, explicit upload,
progress, retry guidance, replace/remove confirmation and retained unsaved text.
Review longer-term retention/deletion/privacy and acceptable malware risk before
public availability. None of these design defaults enables certificate uploads.
