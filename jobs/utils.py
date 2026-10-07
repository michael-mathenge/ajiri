import re

# Matches a standard email address anywhere in a block of text.
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')


def detect_application_method(description: str) -> tuple[str, str]:
    """
    Scans job description text for an email address.

    Returns a tuple: (application_method, application_email)
    - If an email is found: ('email', 'the@address.com')
    - If no email is found: ('external_link', '')  -> caller falls back
      to the job's own source_url for the applicant to click through.

    See docs/CONCEPTS.md#application-method-detection
    """
    match = EMAIL_REGEX.search(description or '')
    if match:
        return 'email', match.group(0)
    return 'external_link', ''


def fix_mojibake(text: str) -> str:
    """
    Repairs a specific, common encoding bug: text that was originally
    valid UTF-8 (e.g. containing an en-dash, curly quote, etc.) but got
    wrongly decoded as Windows-1252 somewhere upstream — producing
    garbled sequences like 'â€"' in place of '–'. See docs/CONCEPTS.md#mojibake

    The fix works because no information was actually lost: re-encoding
    the WRONG string back to cp1252 bytes recovers the ORIGINAL correct
    UTF-8 bytes, which can then be decoded properly. Wrapped in a
    try/except because running this on text that was NEVER corrupted
    will usually raise (there's nothing wrong to reverse) — in that
    case we just return the original text unchanged, so this is always
    safe to call on any string, corrupted or not.
    """
    if not text:
        return text
    try:
        return text.encode('cp1252').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text
