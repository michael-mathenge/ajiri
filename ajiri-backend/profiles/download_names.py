"""Public download labels, independent of private storage paths.

see docs/CONCEPTS.md#readable-document-downloads
"""
import re
import unicodedata


def name_part(value, fallback):
    value = unicodedata.normalize('NFKC', value or '')
    value = ''.join(c if c.isalnum() or unicodedata.category(c).startswith('M') or c in '-_' else
                    '_' if c.isspace() else '' for c in value
                    if not unicodedata.category(c).startswith('C'))
    value = re.sub('_+', '_', value).strip('_-')[:60].rstrip('_-') or fallback
    if re.fullmatch(r'CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]', value, re.IGNORECASE):
        value += '_'
    return value


def document_name(name, kind='CV', company=None):
    parts = [name_part(name, 'Applicant'), kind]
    if company is not None:
        parts.append(name_part(company, 'Company'))
    return '_'.join(parts) + '.docx'
