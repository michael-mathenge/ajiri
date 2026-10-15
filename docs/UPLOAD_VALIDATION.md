# Checkpoint 3A upload checks

New CV uploads only: PDF/DOC/DOCX, 5 MB maximum, non-empty, UUID storage basename.
Owner-checked download behaviour and private storage remain unchanged. Historical
files are not rewritten or scanned, and validation failure preserves the previous CV.

PDF checks its version signature at the beginning and EOF marker near the end;
this intentionally is not a full PDF renderer/parser. Legacy DOC checks compound-file
header/sector bounds, a bounded FAT directory chain and a WordDocument stream entry.
DOCX must be a readable ZIP with matching content-type, office-document relationship
and Word XML. All members are CRC-read with limits, never extracted. Supported package
limits: 200 members, 10 MB each, 20 MB total expanded, compression ratio 100:1; no
ZIP encryption, exotic compression, duplicate/unsafe paths, DTD/entities, non-UTF-8
compatible XML or VBA project. Some unusual/large valid documents will be rejected
by these conservative limits; explain the error and export a simpler CV.

## Malware-scanning feasibility (proposal only)

Structural checks cannot certify safety, remove JavaScript/embedded objects or detect
malware. A local ClamAV process needs a maintained signature database, memory/disk and
service support that cannot be assumed on PythonAnywhere free tier. A hosted scanner
adds outbound reachability, cost/quotas, a new data processor receiving sensitive CVs
and credential/dependency considerations. A future design must include consent/legal
review, private quarantine, resource/time bounds, fail-closed policy and deletion
retention; do not upload real documents to a public scanning service. No scanner,
service, dependency or production operation is added in Checkpoint 3A.
