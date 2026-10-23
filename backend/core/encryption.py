"""
Fernet symmetric encryption helpers for storing DB passwords at rest.

The FERNET_KEY environment variable must contain a URL-safe base64-encoded 32-byte key.
Generate one with:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

If FERNET_KEY is empty/missing, a random key is generated at startup (not suitable
for production — all previously stored passwords become unreadable on restart).
"""

import os
import warnings
from cryptography.fernet import Fernet

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Lazily initialise and cache the Fernet instance."""
    global _fernet
    if _fernet is not None:
        return _fernet

    key = os.getenv("FERNET_KEY", "").strip()
    if not key:
        warnings.warn(
            "FERNET_KEY is not set. Generating a temporary key — "
            "previously encrypted passwords will be unreadable after restart. "
            "Set FERNET_KEY in backend/.env for production.",
            RuntimeWarning,
            stacklevel=2,
        )
        key = Fernet.generate_key().decode()

    _fernet = Fernet(key.encode())
    return _fernet


def encrypt_password(plain: str) -> str:
    """Encrypt a plaintext password and return a URL-safe base64 ciphertext string."""
    if not plain:
        return ""
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_password(ciphertext: str) -> str:
    """Decrypt a Fernet ciphertext string and return the plaintext password."""
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except Exception:
        # Return empty string on decryption failure (e.g. key rotation)
        return ""
