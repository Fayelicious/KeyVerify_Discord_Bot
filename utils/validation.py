import re

def validate_license_key(license_key: str) -> str:
    """Sanitize and normalize a license key before passing to the Payhip API."""
    normalized = license_key.strip().upper().replace(" ", "")

    if not normalized or len(normalized) > 50:
        raise ValueError("Invalid license key.")

    if not re.match(r"^[A-Z0-9\-]+$", normalized):
        raise ValueError("License key may only contain letters, numbers, and hyphens.")

    # Auto-insert hyphens if user entered 20 chars without them
    if re.match(r"^[A-Z0-9]{20}$", normalized):
        normalized = f"{normalized[0:5]}-{normalized[5:10]}-{normalized[10:15]}-{normalized[15:20]}"

    return normalized
