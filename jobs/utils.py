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