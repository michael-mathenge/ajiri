# CV layout verification

19 October 2026. C2, local only. New approvals use cv-v2. Existing stored approvals
and application snapshots are not regenerated. Structural tests inspect styles,
fonts/sizes, heading hierarchy, numbering, tab use, tables, positive page bounds,
separate dates and omitted optional sections. Normal text and bullets are Calibri
11 pt; Title 22, Heading 1 14, Heading 2 12. All are black, with explicit fonts.
The inherited Title border/theme styling was found in the actual OOXML and removed.
Dates remain below headings, not aligned beside long titles using undefined tabs.

## Actual rendering

Existing Microsoft Word COM automation opened synthetic DOCX files read-only,
exported PDFs and closed that automation instance. Installed Poppler pdftoppm
converted PDFs to PNGs. All six pages of long-cv-v2 and the single short-cv-v2 page
were visually inspected: text wrapped inside margins, dates did not collide with
titles, lists remained readable and there was no clipping. Long paragraphs/bullets
may continue over page breaks; fixed page-count parity with the preview is not
promised. LibreOffice was not found at the checked standard location. Google Docs
and phone rendering remain UNVERIFIED. An initial attempt used unavailable fitz;
no package was installed and installed Poppler succeeded instead. Outputs are
temporary synthetic QA artifacts, not repository content or user documents.

## Reproduce on Windows

From the isolated backend directory, use the existing project virtualenv:

```powershell
$env:PYTHON_DOTENV_DISABLED = '1'
$env:DEBUG = 'True'
$env:REAL_EMAIL_ENABLED = 'False'
$python = 'C:\dev\ajiri\.worktrees\checkpoint-3b\ajiri-backend\.venv\Scripts\python.exe'
& $python manage.py test profiles.test_cv_layout --noinput
@'
from pathlib import Path
from profiles.test_cv_layout import layout_fixture
from profiles.cv_builder import render_docx
import tempfile
root = Path(tempfile.gettempdir()) / 'ajiri-layout-manual'
root.mkdir(exist_ok=True)
for name, long in [('short', False), ('long', True)]:
    (root / (name + '.docx')).write_bytes(render_docx(layout_fixture(long)))
print(root)
'@ | & $python manage.py shell
```

Expected: three structural tests pass and two synthetic DOCX files are created in
the printed local temp folder. Do not use real personal CVs for sharing QA.

1. Microsoft Word: open both fixtures, use Print Layout and 100% zoom, inspect
   every page. Confirm fonts, dates below headings, wrapping, bullets, margins,
   section order and no overlap/clipping. Export to PDF and inspect again.
2. Google Docs: Michael may upload only synthetic fixtures to his own Drive;
   no agent upload is included. Open as Google Docs, compare text/order, long entry
   wrapping and page breaks. Different pagination is acceptable; lost text is not.
3. Phone: transfer the synthetic DOCX privately and open in your normal Word/Docs
   viewer. Check fit-width readability, zoom, long names, dates and all pages.
4. In local Ajiri, approve a new synthetic CV and compare preview text with its
   DOCX. An earlier approval must keep its original file/hash/template version.

Rollback source for future generation only; keep existing files and records. Do
not rewrite approved documents or restore an older database. Full package gate
results are recorded in CHECKPOINT4_PHASE_C_REVIEW.md.
