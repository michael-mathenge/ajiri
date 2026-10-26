# Isolated real scanner binary rehearsal

25 October2026, AJ52. The earlier memory-only contract remains separate. This lab
uses actual ClamAV1.5.4 with one custom SHA256 signature for harmless generated
binary bytes, not real malware, EICAR, vendor definitions or private files. The
engine matched that fixture (exit1), left a different fixture unmatched (exit0),
and failed on a missing database (exit2). Actual run passed after correcting Windows
text-mode stdin translation: UTF-8 bytes now preserve LF for the Linux shell.
The initial shell failure was not a scan result.

The official image digest is pinned in scripts/scanner_engine_rehearsal.py. Its
Docker entrypoint is overridden, so FreshClam/ClamD never start and no signatures
are downloaded. The script uses the local desktop-linux context and --pull=never,
no network/host mounts, read-only root, unprivileged UID, dropped capabilities,
no-new-privileges,256MiB/one CPU/32 process limits and16MiB disposable tmpfs. All
fixture data originates inside the script; no filename/upload input is accepted.
An explicit --synthetic-only flag is required before any Docker call. A45-second
deadline and exact generated name/label cleanup prevent leftover test containers.

```powershell
# Use the repository virtualenv Python and the already verified pinned image.
python scripts/scanner_engine_rehearsal.py --synthetic-only
```

Expected: AJIRI_SCANNER_REHEARSAL_RESULT reports engine ClamAV1.5.4, fixture
infected/clean and missing_database unavailable, with private_files/network/
production_scanning/vendor_signature_database all false. The infected label here
means the deliberately matched harmless fixture only. It establishes neither
current malware detection coverage nor signature-update/expiry guarantees.

Official references checked25October: [Docker images](https://docs.clamav.net/manual/Installing/Docker.html)
and [SHA256 hash signatures](https://docs.clamav.net/manual/Signatures/HashSignatures.html).
Official guidance recommends substantially more memory for standard definitions;
the small custom-signature lab is not evidence that the free production host can
run a real scanning service. A custom hash signature matches exact bytes only.

No production import/caller, upload route, dependency, migration, quarantine store
or scanner service is added. Existing uploads remain content-validated, not
malware-scanned. Real engine/signature freshness, durable private quarantine,
download/replacement enforcement, timeout/resource policy, legacy/restored-file
handling, actual host and processing/privacy decisions remain open in
SCANNER_TEST_CONTRACT.md. Rollback removes only this unused lab, retaining all
production files and historical evidence. Required package results are recorded in
JIRA_ROADMAP_PROGRESS.md; AJ52 remains In Progress.
