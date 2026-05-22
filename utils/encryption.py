from cryptography.fernet import Fernet, MultiFernet
import os
from dotenv import load_dotenv
from utils.errors import ConfigurationError, EncryptionError

load_dotenv()

keys_str = os.getenv("ENCRYPTION_KEYS") or os.getenv("ENCRYPTION_KEY")
if not keys_str:
    raise ConfigurationError("No encryption keys found in .env (ENCRYPTION_KEYS or ENCRYPTION_KEY).")

# key[0] is the Primary (New) key. key[1+] are Old keys used for decryption only.
keys = [k.strip() for k in keys_str.split(",") if k.strip()]
try:
    fernet_instances = [Fernet(k.encode()) for k in keys]
except Exception as e:
    raise ConfigurationError(f"Invalid Fernet key format in ENCRYPTION_KEYS.") from e

cipher_suite = MultiFernet(fernet_instances)


def encrypt_data(data: str) -> str:
    """Encrypts data using the PRIMARY (Newest) key."""
    try:
        return cipher_suite.encrypt(data.encode()).decode()
    except Exception as e:
        raise EncryptionError("Failed to encrypt data.") from e


def decrypt_data(data: str) -> str:
    """Decrypts data using any valid key."""
    try:
        return cipher_suite.decrypt(data.encode()).decode()
    except Exception as e:
        raise EncryptionError("Failed to decrypt data — key may be missing or data is corrupt.") from e


def reencrypt_if_needed(token: str) -> str:
    """
    Takes an encrypted string.
    - If it's already encrypted with the New Key, returns it unchanged.
    - If it's encrypted with an Old Key, decrypts it and re-encrypts with the New Key.
    """
    if not token:
        return token
    try:
        return cipher_suite.rotate(token.encode()).decode()
    except Exception as e:
        raise EncryptionError("Failed to re-encrypt token during key rotation.") from e
