import io
import zipfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError
from .upload_validation import validate_cv_upload
from .upload_fixtures import pdf_bytes, docx_bytes, doc_bytes


def zipped(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries:
            archive.writestr(name, content)
    return output.getvalue()


class UploadContentTests(SimpleTestCase):
    def test_valid_types_cursor_safe_name_and_size_boundary(self):
        for extension, content in [('pdf', pdf_bytes()), ('docx', docx_bytes()), ('doc', doc_bytes()), ('PDF', pdf_bytes(5 * 1024 * 1024))]:
            upload = SimpleUploadedFile('personal-name.' + extension, content, content_type='application/octet-stream')
            result = validate_cv_upload(upload)
            self.assertEqual(result.tell(), 0)
            self.assertRegex(result.name, r'^[a-f0-9]{32}\.(pdf|doc|docx)$')
            self.assertEqual(result.read(), content)

    def test_spoofed_empty_truncated_and_oversized_files(self):
        cases = [('cv.pdf', b'MZ executable'), ('cv.pdf', b'<html>not PDF</html>'), ('cv.pdf', b''),
                 ('cv.pdf', pdf_bytes(5 * 1024 * 1024 + 1)), ('cv.doc', b'not DOC'),
                 ('cv.doc', doc_bytes()[:600]), ('cv.docx', b'PK not a zip'),
                 ('cv.docx', zipped([('word/document.xml', b'<bad/>')]))]
        for name, content in cases:
            with self.subTest(name=name, size=len(content)):
                with self.assertRaises(ValidationError):
                    validate_cv_upload(SimpleUploadedFile(name, content))

    def test_zip_bombs_unsafe_paths_duplicates_and_corrupt_parts(self):
        for entries in [[('large', b'x' * (11 * 1024 * 1024))],
                        [('a' + str(i), b'x') for i in range(201)],
                        [('../outside', b'x')], [('same', b'x'), ('same', b'y')],
                        [('[Content_Types].xml', b'<!DOCTYPE x [<!ENTITY x "bad">]><x/>'),
                         ('_rels/.rels', b'<x/>'), ('word/document.xml', b'<x/>')]]:
            with self.subTest(names=len(entries)):
                with self.assertRaises(ValidationError):
                    validate_cv_upload(SimpleUploadedFile('cv.docx', zipped(entries)))

    def test_doc_directory_chain_loop_rejected(self):
        content = bytearray(doc_bytes())
        import struct
        struct.pack_into('<I', content, 512 + 4, 1)
        with self.assertRaises(ValidationError):
            validate_cv_upload(SimpleUploadedFile('cv.doc', bytes(content)))
