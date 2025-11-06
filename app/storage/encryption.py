"""Encryption utilities for OAuth tokens and sensitive data."""

from cryptography.fernet import Fernet
import base64
import os
from typing import Optional


class TokenEncryption:
    """Encrypt/decrypt OAuth tokens using Fernet symmetric encryption."""

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize with encryption key.
        In production, get key from environment variable or key management service.
        """
        if key is None:
            key_str = os.getenv("ENCRYPTION_KEY")
            if not key_str:
                # Generate key if not set (for development only)
                key = Fernet.generate_key()
                print(f"⚠️  Generated encryption key. Set ENCRYPTION_KEY={key.decode()}")
            else:
                key = key_str.encode()
        self.cipher = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        encrypted = self.cipher.encrypt(plaintext.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a base64-encoded ciphertext and return plaintext."""
        encrypted = base64.b64decode(ciphertext.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return decrypted.decode()


# Global instance (initialize once)
_encryption = None


def get_encryption() -> TokenEncryption:
    """Get global encryption instance."""
    global _encryption
    if _encryption is None:
        _encryption = TokenEncryption()
    return _encryption


def encrypt_token(token: str) -> str:
    """Convenience function to encrypt a token."""
    return get_encryption().encrypt(token)


def decrypt_token(encrypted_token: str) -> str:
    """Convenience function to decrypt a token."""
    try:
        return get_encryption().decrypt(encrypted_token)
    except Exception:
        # If decryption fails, assume it's already plaintext (for local dev)
        # In production, this should never happen
        return encrypted_token

