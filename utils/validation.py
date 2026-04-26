import re

def validate_license_key(license_key: str) -> str:
    """Validate and normalize a license key. Returns the uppercased key."""
    normalized = license_key.strip().upper()
    pattern = r"^[A-Z0-9-]{10,50}$"
    if not re.match(pattern, normalized):
        raise ValueError("Invalid license key format. Ensure it follows 00000-00000-00000-00000 format.")
    return normalized
