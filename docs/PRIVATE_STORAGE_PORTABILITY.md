# Private storage portability

AJ-47/AJ-79, implementation started16November2026; review continued20November2026.
The default production backend remains the existing local FileSystemStorage.
No object-store account, bucket, credential, public download URL or host is created.

## Boundary and compatibility

`profiles.private_storage` supplies bounded reads, verified unique writes and
identity-bound cleanup for local files and explicitly reviewed pathless backends.
Local files retain traversal, link/junction, hard-link and regular-file checks.
Each object is limited to5MiB; generated CVs/application packages retain their
existing2MiB limits. Stored approval hashes/sizes remain authoritative.

An arbitrary backend raising NotImplementedError for path() is no longer silently
trusted. A pathless backend must implement VersionedPrivateStorage, declare a
private namespace, identify immutable versions and implement bounded exact reads
and idempotent deletion of only captured versions. Replacement versions must be
refused. Partial removal of captured versions must remain resumable. These rules
are a backend contract, not evidence that an external provider meets it.

Uploaded CVs, immutable CV approvals, legacy application snapshots, approved
application packages and certificate quarantine use the boundary. Changed hashes,
sizes or object identities fail closed. Lost commit acknowledgements preserve
potentially committed document pointers/bytes; uncertain cleanup retains orphans
for report-only reconciliation. Normal uploads, scanning and sending are not enabled.

Public JSON field names and string/null shapes stay unchanged. The cv_file,
generated_cv and generated_cover_letter strings now identify existing authenticated
download routes instead of asking storage for URLs. Anonymous/other-owner requests
remain denied. The profile upload filename limit remains100 characters. No new
endpoint, authentication redesign or database migration is required.

## Export, erasure and recovery

Account exports read exact private objects into new private operator directories,
using neutral generated names, bounded inventories and final hash verification.
They never include another owner's records, storage URLs or provider credentials.

Existing local format-1 signed erasure journals remain readable and retain their
current replay behaviour. Pathless erasure creates format-2 journals with bounded
versioned object identities, signed with the same existing journal mechanism.
Changed identities block before account rows are erased. Post-commit failures keep
the journal pending; retry can remove only the remaining captured immutable versions.
Oversized journals are refused before writing an unresumable recovery record.
No real account erasure is authorised or performed by this package.

A storage-type change while a journal exists requires an explicitly reviewed
identity mapping; do not point old local journals at a new bucket and infer that
they still authorise cleanup. Existing backup/ledger verification retains the
private signed journals. The current production backup command remains a SQLite/
local-media command, not a cloud backup implementation.

`profiles.private_copy` inventories at most1000 objects/200MiB, rejects overlapping
local roots, credentials, links, duplicate references and conflicting/extraneous
destination objects. Explicitly resumed copies verify and reuse exact completed
objects, preserving immutable keys; unknown writes retain bytes for reconciliation.
An independent destination must already exist and be private. No settings switch,
automatic retry/pruning or production cutover is performed by this helper.

## Isolated S3 emulator

```powershell
python scripts/prepare_private_s3_rehearsal.py
docker build -t ajiri-private-s3:synthetic <printed-context>
docker run --name ajiri-private-s3-run --label ajiri.lab=private-s3 --network none --read-only --tmpfs /tmp:rw,nosuid,size=192m ajiri-private-s3:synthetic
```

Use an unused dedicated container name and preserve all existing Docker resources.
The tracked-source exporter excludes environment files, databases, private documents
and recovery archives. Moto binds only loopback inside a network-none container;
boto3 can address only that fixed synthetic endpoint and two named synthetic buckets.
No Docker socket, host mounts, published ports, real documents or live credentials
enter the image. Its55 resolved extra dependency pins remain lab-only, alongside
the unchanged33 production pins.

The emulator adapter conditionally creates objects and binds the entire bounded
historical version inventory to deletion, avoiding resurrection of old private
versions. It checks partial version deletion/retry, normal private workflows,
interrupted-copy reuse, conflict refusal and a three-object isolated restore.
Public URLs are disabled. Moto is an HTTP protocol emulator, not evidence of cloud
IAM, encryption, availability, provider retention/terms or hosted recovery acceptance.

Historical16November evidence:689 full backend tests passed in314.917s, one existing
platform skip; the then-current10-test emulator run passed in6.614s. Subsequent
20November changes extend partial-version retry and legacy application handling;
that older run does not verify the newer source. Current final gates and emulator
results belong in JIRA_ROADMAP_PROGRESS.md. On20November Docker reported missing
VirtualMachinePlatform; Michael enabled the feature, with a Windows restart still
required before the updated container rehearsal can run.

## Release and rollback

Run the repository gates and exact-head CI before merging. Before production,
remeasure capacity and verify a consistent private backup, off-server hashes and
isolated restoration. Keep SQLite/local storage and all current operational gates.
Verify existing owner/profile/application reads, exact private document bytes,
anonymous denial, no new delivery attempts and restored writer workflows.

Rollback is source-only, retaining current rows, private objects and journals.
Older source cannot interpret format-2 journals: suspend erasure operations under
that source until forward support is restored. Never reverse migrations, replace
live data with fixtures or remove recovery copies to make room without concrete
deletion authority. Real object-store/provider activation remains a separate decision.

Reference: [Moto server mode](https://docs.getmoto.org/en/latest/docs/server_mode.html),
[S3 conditional writes](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/put_object.html),
[version-specific deletion](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/delete_object.html).
