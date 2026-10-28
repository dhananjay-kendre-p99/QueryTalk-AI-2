"""
tests/test_authentic_encryption.py — Authentic unit tests for core/encryption.py.

Validates Fernet symmetric encryption and decryption for database passwords at rest.
"""

import pytest
from core.encryption import encrypt_password, decrypt_password


class TestCredentialEncryption:
    """Authentic tests for Fernet password encryption and decryption."""

    def test_encrypt_and_decrypt_roundtrip(self):
        """Verifies that a plaintext database password can be encrypted and accurately decrypted."""
        original_pass = "P@ssw0rd_with_Special_!#$&*()Chars"
        encrypted = encrypt_password(original_pass)

        # Ciphertext must not match raw plaintext
        assert encrypted != original_pass
        assert isinstance(encrypted, str)
        assert len(encrypted) > len(original_pass)

        decrypted = decrypt_password(encrypted)
        assert decrypted == original_pass

    def test_empty_password_handling(self):
        """Verifies that empty string passwords return empty strings without raising exceptions."""
        assert encrypt_password("") == ""
        assert decrypt_password("") == ""

    def test_different_ciphertexts_for_same_input(self):
        """
        Fernet incorporates a random IV/timestamp on every encryption call.
        Two encryptions of the same password should produce distinct ciphertexts,
        yet both decrypt to identical plaintext.
        """
        password = "ProductionSecurePostgresPassword2026!"
        cipher1 = encrypt_password(password)
        cipher2 = encrypt_password(password)

        assert cipher1 != cipher2
        assert decrypt_password(cipher1) == password
        assert decrypt_password(cipher2) == password

    def test_unicode_and_complex_strings(self):
        """Verifies encryption and decryption for non-ASCII and complex UTF-8 strings."""
        unicode_pass = "🔐Pässwórd_日本語_12345!✨"
        encrypted = encrypt_password(unicode_pass)
        assert decrypt_password(encrypted) == unicode_pass

