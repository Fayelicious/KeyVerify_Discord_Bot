class BotError(Exception):
    """Base class for all bot domain errors."""


class ConfigurationError(BotError):
    """Missing or invalid environment variable or startup configuration."""


class DatabaseError(BotError):
    """Wraps asyncpg/database failures. Cause chain preserved via 'raise X from e'."""


class EncryptionError(BotError):
    """Cipher setup or encrypt/decrypt failure."""


class APIError(BotError):
    """Wraps Payhip or other external API failures."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class ValidationError(BotError):
    """Invalid user-provided input."""
