import re

# Each entry: (regex pattern, human-readable reason)
# Patterns are checked against title + description + requirements combined.
RED_FLAG_PATTERNS = [
    (r'\bregistration fee\b', 'Requests a registration fee'),
    (r'\btraining fee\b', 'Requests a training fee'),
    (r'\bprocessing fee\b', 'Requests a processing fee'),
    (r'\bpay before\b', 'Asks for payment before hiring'),
    (r'\bsend money\b', 'Asks the applicant to send money'),
    (r'\bapply immediately\b', 'Uses high-pressure urgency language'),
    (r'\burgent(ly)? hiring\b', 'Uses high-pressure urgency language'),
    (r'\blimited slots?\b', 'Uses high-pressure urgency language'),
    (r'\bwhatsapp only\b', 'Only accepts contact via WhatsApp (no verifiable company channel)'),
    (r'\bno experience needed\b.*\bhigh pay\b', 'Promises high pay with no experience required'),
]

MIN_DESCRIPTION_LENGTH = 100


def analyze_job_for_scam(job):
    """
    Runs a rule-based check against a Job instance and returns
    (is_scam: bool, reasons: list[str]).
    Does NOT save the job — caller decides what to do with the result.
    """
    combined_text = f"{job.title} {job.description} {job.requirements}".lower()
    reasons = []

    for pattern, reason in RED_FLAG_PATTERNS:
        if re.search(pattern, combined_text):
            reasons.append(reason)

    if len(job.description.strip()) < MIN_DESCRIPTION_LENGTH:
        reasons.append('Description is suspiciously short or vague')

    if not job.company_name.strip():
        reasons.append('Missing company name')

    is_scam = len(reasons) > 0
    return is_scam, reasons