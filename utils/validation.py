import re

def validate_license_key(license_key: str) -> str:
    """Validate and normalize a license key. Returns the uppercased key."""
    normalized = license_key.strip().upper().replace(" ", "")

    # Auto-format if user entered 20 chars without hyphens
    if re.match(r"^[A-Z0-9]{20}$", normalized):
        normalized = f"{normalized[0:5]}-{normalized[5:10]}-{normalized[10:15]}-{normalized[15:20]}"

    pattern = r"^[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}-[A-Z0-9]{5}$"
    if not re.match(pattern, normalized):
        raise ValueError("Invalid license key format. Ensure it follows 00000-00000-00000-00000 format.")
    return normalized
