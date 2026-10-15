"""Synthetic document builders used only by tests."""
import io
import struct
from docx import Document


def pdf_bytes(size=None):
    data = b'%PDF-1.4\nSynthetic test CV\n%%EOF\n'
    if size:
        data = data[:-6] + b' ' * (size - len(data)) + data[-6:]
    return data


def docx_bytes():
    output = io.BytesIO()
    document = Document()
    document.add_paragraph('Synthetic test CV')
    document.save(output)
    return output.getvalue()


def doc_bytes():
    header = bytearray(512)
    header[:8] = bytes.fromhex('d0cf11e0a1b11ae1')
    struct.pack_into('<HHHH', header, 26, 3, 0xfffe, 9, 6)
    struct.pack_into('<I', header, 44, 1)
    struct.pack_into('<I', header, 48, 1)
    struct.pack_into('<109I', header, 76, 0, *([0xffffffff] * 108))
    fat = struct.pack('<128I', 0xfffffffd, 0xfffffffe, 0xfffffffe, *([0xffffffff] * 125))
    directory = bytearray(512)
    name = 'WordDocument'.encode('utf-16le') + b'\0\0'
    directory[:len(name)] = name
    struct.pack_into('<H', directory, 64, len(name))
    directory[66] = 2
    return bytes(header) + fat + bytes(directory) + b'\0' * 512
