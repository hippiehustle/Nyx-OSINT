"""Encryption and secure storage for sensitive data."""

import os
from base64 import b64decode, b64encode
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionManager:
    """Manage encryption of sensitive configuration data."""

    def __init__(self, master_password: Optional[str] = None, salt: Optional[bytes] = None):
        """Initialize encryption manager with master password."""
        self.salt = salt or os.urandom(16)
        if master_password:
            self.cipher = self._derive_cipher(master_password)
        else:
            self.cipher = None

    def _derive_cipher(self, password: str) -> Fernet:
        """Derive Fernet cipher from master password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = b64encode(kdf.derive(password.encode()))
        return Fernet(key)

    def set_password(self, password: str) -> None:
        """Set or change the master password."""
        self.cipher = self._derive_cipher(password)

    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        if not self.cipher:
            raise ValueError("Cipher not initialized. Set master password first.")
        encrypted = self.cipher.encrypt(data.encode())
        return b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not self.cipher:
            raise ValueError("Cipher not initialized. Set master password first.")
        decrypted = self.cipher.decrypt(b64decode(encrypted_data.encode()))
        return decrypted.decode()

    def get_salt(self) -> bytes:
        """Get the salt for storage."""
        return self.salt

    @staticmethod
    def from_salt(password: str, salt: bytes) -> "EncryptionManager":
        """Create manager from stored salt."""
        manager = EncryptionManager(salt=salt)
        manager.set_password(password)
        return manager
