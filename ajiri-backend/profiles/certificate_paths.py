"""Migration-safe private filename helper, independent of the active app model."""
import uuid


def certificate_path(instance, filename):
    # see docs/CONCEPTS.md#private-certificate-evidence
    return f'quarantine/certificates/{uuid.uuid4().hex}.pdf'
