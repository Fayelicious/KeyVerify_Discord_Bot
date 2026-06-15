import re
from utils.errors import ValidationError


def validate_license_key(license_key: str) -> str:
    """Sanitize and normalize a license key before passing to the Payhip API."""
    normalized = license_key.strip().upper().replace(" ", "")

    if not normalized or len(normalized) > 50:
        raise ValidationError("Invalid license key.")

    if not re.match(r"^[A-Z0-9\-]+$", normalized):
        raise ValidationError("License key may only contain letters, numbers, and hyphens.")

    return normalized
