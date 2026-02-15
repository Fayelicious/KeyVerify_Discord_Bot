from cryptography.fernet import Fernet, MultiFernet
import os
from dotenv import load_dotenv

load_dotenv()

keys_str = os.getenv("ENCRYPTION_KEYS") or os.getenv("ENCRYPTION_KEY")
if not keys_str:
    raise ValueError("No encryption keys found in .env.")

# Create the list of keys. 
# key[0] is the Primary (New) key. key[1+] are Old keys.
keys = [k.strip() for k in keys_str.split(",") if k.strip()]
fernet_instances = [Fernet(k.encode()) for k in keys]
cipher_suite = MultiFernet(fernet_instances)

def encrypt_data(data: str) -> str:
    """Encrypts data using the PRIMARY (Newest) key."""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    """Decrypts data using any valid key."""
    return cipher_suite.decrypt(data.encode()).decode()

def reencrypt_if_needed(token: str) -> str:
    """
    Takes an encrypted string.
    - If it's already encrypted with the New Key, returns it unchanged.
    - If it's encrypted with an Old Key, decrypts it and re-encrypts with the New Key.
    """
    if not token: return token
    return cipher_suite.rotate(token.encode()).decode()