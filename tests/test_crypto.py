"""
Unit tests for steganography.crypto module.
Tests AES-256-GCM encryption, decryption, PBKDF2 key derivation, wrong password handling, and tamper resistance.
"""

import unittest
from steganography.crypto import (
    encrypt_message,
    decrypt_message,
    DecryptionError,
    derive_key
)


class TestCrypto(unittest.TestCase):

    def test_encrypt_decrypt_valid(self):
        message = "Meet me at 5 PM tomorrow."
        password = "TestPassword123!"
        envelope = encrypt_message(message, password)
        
        self.assertIsInstance(envelope, bytes)
        self.assertGreater(len(envelope), 44)  # 16 salt + 12 nonce + 16 tag + len(msg)
        
        decrypted = decrypt_message(envelope, password)
        self.assertEqual(decrypted, message)

    def test_encrypt_decrypt_unicode(self):
        message = "Hello 🚀 नमస్కారం こんにちは Special: §±!@#$%^&*()_+"
        password = "ComplexSecurePassword999!"
        envelope = encrypt_message(message, password)
        decrypted = decrypt_message(envelope, password)
        self.assertEqual(decrypted, message)

    def test_wrong_password_raises_decryption_error(self):
        message = "Top Secret Information"
        password = "CorrectPassword123"
        envelope = encrypt_message(message, password)
        
        with self.assertRaises(DecryptionError):
            decrypt_message(envelope, "WrongPassword456")

    def test_corrupted_ciphertext_raises_decryption_error(self):
        message = "Authentication tag must fail on modification"
        password = "PassWord123!"
        envelope = bytearray(encrypt_message(message, password))
        
        # Tamper with the last byte (part of ciphertext/tag)
        envelope[-1] ^= 0xFF
        
        with self.assertRaises(DecryptionError):
            decrypt_message(bytes(envelope), password)

    def test_empty_message_raises_value_error(self):
        with self.assertRaises(ValueError):
            encrypt_message("", "password123")

    def test_empty_password_raises_value_error(self):
        with self.assertRaises(ValueError):
            encrypt_message("Some message", "")

    def test_short_envelope_raises_decryption_error(self):
        with self.assertRaises(DecryptionError):
            decrypt_message(b"too_short", "password123")

    def test_key_derivation_deterministic_with_same_salt(self):
        salt = b"0123456789abcdef"
        key1 = derive_key("password", salt, iterations=1000)
        key2 = derive_key("password", salt, iterations=1000)
        self.assertEqual(key1, key2)
        self.assertEqual(len(key1), 32)


if __name__ == '__main__':
    unittest.main()
