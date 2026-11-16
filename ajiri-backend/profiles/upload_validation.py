"""Bounded format checks, not a malware scanner or full document renderer."""
import io
import re
import struct
import uuid
import zipfile
from pathlib import PurePosixPath
from xml.etree import ElementTree
from rest_framework import serializers
from django.conf import settings

MAX_BYTES = 5 * 1024 * 1024
MAX_EXPANDED = 20 * 1024 * 1024
MAX_MEMBER = 10 * 1024 * 1024
MAX_MEMBERS = 200


def _xml(content):
    if b'\x00' in content:
        raise ValueError('Only UTF-8 compatible package XML is supported.')
    if b'<!DOCTYPE' in content.upper() or b'<!ENTITY' in content.upper():
        raise ValueError('Document declarations are not supported.')
    return ElementTree.fromstring(content)


def _docx(data):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        members = archive.infolist()
        if not members or len(members) > MAX_MEMBERS:
            raise ValueError('Too many ZIP members.')
        names = set()
        expanded = 0
        for member in members:
            path = PurePosixPath(member.filename)
            if (member.filename in names or path.is_absolute() or '..' in path.parts
                    or '\\' in member.filename or ':' in member.filename
                    or member.flag_bits & 1
                    or member.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                raise ValueError('Unsafe ZIP package.')
            names.add(member.filename)
            expanded += member.file_size
            if (expanded > MAX_EXPANDED or member.file_size > MAX_MEMBER
                    or member.file_size > max(member.compress_size, 1) * 100):
                raise ValueError('Expanded document exceeds safe limits.')
            # Consume every member with a bounded read to validate actual size/CRC.
            with archive.open(member) as stream:
                actual = 0
                while chunk := stream.read(65536):
                    actual += len(chunk)
                    if actual > MAX_MEMBER or actual > member.file_size:
                        raise ValueError('Invalid ZIP size.')
                if actual != member.file_size:
                    raise ValueError('Invalid ZIP size.')
        required = {'[Content_Types].xml', '_rels/.rels', 'word/document.xml'}
        if not required <= names or any('vbaproject' in name.lower() for name in names):
            raise ValueError('Missing Word package parts or macro content.')
        types = _xml(archive.read('[Content_Types].xml'))
        rels = _xml(archive.read('_rels/.rels'))
        document = _xml(archive.read('word/document.xml'))
        if types.tag != '{http://schemas.openxmlformats.org/package/2006/content-types}Types':
            raise ValueError('Invalid content types.')
        if not any(item.get('PartName') == '/word/document.xml' and item.get('ContentType') ==
                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml'
                   for item in types):
            raise ValueError('Not a DOCX document.')
        if rels.tag != '{http://schemas.openxmlformats.org/package/2006/relationships}Relationships':
            raise ValueError('Invalid relationships.')
        if not any(item.get('Type', '').endswith('/officeDocument') and
                   item.get('Target', '').lstrip('/') == 'word/document.xml' and
                   item.get('TargetMode') != 'External' for item in rels):
            raise ValueError('Missing Word relationship.')
        if document.tag not in {
            '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document',
            '{http://purl.oclc.org/ooxml/wordprocessingml/main}document',
        }:
            raise ValueError('Invalid Word document XML.')


def _doc(data):
    if len(data) < 512 or data[:8] != bytes.fromhex('d0cf11e0a1b11ae1'):
        raise ValueError('Invalid DOC signature.')
    major, byte_order, shift = struct.unpack_from('<HHH', data, 26)
    if byte_order != 0xfffe or (major, shift) not in {(3, 9), (4, 12)}:
        raise ValueError('Invalid compound-file header.')
    size = 1 << shift
    if len(data) % size or len(data) < size * 3:
        raise ValueError('Truncated compound file.')
    def sector(index):
        start = (index + 1) * size
        if index >= 0xfffffffa or start + size > len(data):
            raise ValueError('Invalid sector.')
        return data[start:start + size]
    count = struct.unpack_from('<I', data, 44)[0]
    if not 1 <= count <= 109:
        raise ValueError('Unsupported compound-file allocation table.')
    fat_ids = struct.unpack_from('<109I', data, 76)[:count]
    fat_bytes = b''.join(sector(index) for index in fat_ids)
    fat = struct.unpack('<' + 'I' * (len(fat_bytes) // 4), fat_bytes)
    current = struct.unpack_from('<I', data, 48)[0]
    seen = set()
    found_word = False
    while current != 0xfffffffe:
        if current in seen or len(seen) >= 32 or current >= len(fat):
            raise ValueError('Invalid directory chain.')
        seen.add(current)
        content = sector(current)
        for offset in range(0, size, 128):
            entry = content[offset:offset + 128]
            length = struct.unpack_from('<H', entry, 64)[0]
            if entry[66] == 2 and 2 <= length <= 64 and length % 2 == 0:
                name = entry[:length - 2].decode('utf-16le')
                found_word |= name == 'WordDocument'
        current = fat[current]
    if not found_word:
        raise ValueError('No WordDocument stream.')


def validate_cv_upload(upload, *, scan=True):
    # Preserve the cursor for Django storage; never extract ZIPs or open private URLs.
    # see docs/CONCEPTS.md#cv-content-validation
    from .scanner import ScanUnavailable
    if getattr(settings, 'PRIVATE_UPLOADS_SUSPENDED', False):
        raise ScanUnavailable()
    extension = PurePosixPath(upload.name).suffix.lower()
    if extension not in {'.pdf', '.doc', '.docx'}:
        raise serializers.ValidationError('Allowed CV formats: PDF, DOC and DOCX.')
    if not 0 < upload.size <= MAX_BYTES:
        raise serializers.ValidationError('CV must be non-empty and no larger than 5 MB.')
    position = upload.tell()
    try:
        upload.seek(0)
        data = upload.read(MAX_BYTES + 1)
        if len(data) != upload.size or len(data) > MAX_BYTES:
            raise ValueError('Invalid file size.')
        if extension == '.pdf':
            if not re.match(rb'%PDF-(?:1\.[0-7]|2\.0)[\r\n]', data) or b'%%EOF' not in data[-1024:]:
                raise ValueError('Invalid PDF signature or end marker.')
        elif extension == '.docx':
            _docx(data)
        else:
            _doc(data)
        if scan and getattr(settings, 'MALWARE_SCANNING_ENABLED', False):
            from .scanner import require_clean
            require_clean(data)
    except (ValueError, zipfile.BadZipFile, RuntimeError, OSError, ElementTree.ParseError, NotImplementedError, struct.error) as error:
        raise serializers.ValidationError('CV content does not match a supported, valid document package.') from error
    finally:
        upload.seek(position)
    upload.name = uuid.uuid4().hex + extension
    return upload
