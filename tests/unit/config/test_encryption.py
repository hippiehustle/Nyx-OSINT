"""Tests for encryption management."""

import pytest

from nyx.config.encryption import EncryptionManager


class TestEncryptionManager:
    """Test EncryptionManager class."""

    def test_encryption_manager_creation(self) -> None:
        """Test creating encryption manager."""
        manager = EncryptionManager(master_password="test_password")
        assert manager.cipher is not None

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """Test encrypting and decrypting data."""
        manager = EncryptionManager(master_password="test_password")
        original_data = "sensitive data"

        encrypted = manager.encrypt(original_data)
        assert encrypted != original_data

        decrypted = manager.decrypt(encrypted)
        assert decrypted == original_data

    def test_encrypt_without_password(self) -> None:
        """Test encryption fails without password."""
        manager = EncryptionManager()
        with pytest.raises(ValueError):
            manager.encrypt("data")

    def test_set_password(self) -> None:
        """Test setting password."""
        manager = EncryptionManager()
        manager.set_password("new_password")
        assert manager.cipher is not None

        encrypted = manager.encrypt("data")
        assert encrypted != "data"

    def test_salt_handling(self) -> None:
        """Test salt retrieval and reuse."""
        manager = EncryptionManager(master_password="password")
        salt = manager.get_salt()
        assert len(salt) == 16

        # Create new manager with same salt
        manager2 = EncryptionManager.from_salt("password", salt)
        encrypted = manager.encrypt("test")
        decrypted = manager2.decrypt(encrypted)
        assert decrypted == "test"

    def test_different_passwords_different_results(self) -> None:
        """Test that different passwords produce different encrypted results."""
        salt = b"x" * 16

        manager1 = EncryptionManager.from_salt("password1", salt)
        manager2 = EncryptionManager.from_salt("password2", salt)

        data = "test data"
        encrypted1 = manager1.encrypt(data)
        encrypted2 = manager2.encrypt(data)

        # Different passwords should produce different ciphertexts
        assert encrypted1 != encrypted2
