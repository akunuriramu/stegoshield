"""
Unit tests for steganography.decoder module.
Tests detection of StegoShield headers, extraction of plain and encrypted messages,
and handling of non-stego and corrupted images.
"""

import unittest
from PIL import Image
from steganography.encoder import hide_message_in_image
from steganography.decoder import (
    inspect_image_header,
    extract_message_from_image,
    NoStegoHeaderError,
    HeaderCorruptionError,
    DecryptionError
)


class TestDecoder(unittest.TestCase):

    def test_inspect_plain_image_returns_no_stego(self):
        plain_img = Image.new('RGB', (80, 80), color=(10, 20, 30))
        info = inspect_image_header(plain_img)
        self.assertFalse(info["has_stego"])
        self.assertIn("No StegoShield message", info["error"])

    def test_inspect_tiny_image_returns_no_stego(self):
        tiny_img = Image.new('RGB', (5, 5), color=(10, 20, 30))
        info = inspect_image_header(tiny_img)
        self.assertFalse(info["has_stego"])
        self.assertIn("too small", info["error"])

    def test_extract_plain_message(self):
        original_msg = "StegoShield LSB Extraction Test Message 2026"
        base_img = Image.new('RGB', (60, 60), color=(40, 50, 60))
        stego_img, _ = hide_message_in_image(base_img, original_msg)
        
        # Verify inspection
        info = inspect_image_header(stego_img)
        self.assertTrue(info["has_stego"])
        self.assertFalse(info["is_encrypted"])
        
        # Verify extraction
        recovered, meta = extract_message_from_image(stego_img)
        self.assertEqual(recovered, original_msg)
        self.assertFalse(meta["is_encrypted"])

    def test_extract_encrypted_message(self):
        original_msg = "Super Classified Intel Payload"
        password = "StegoShieldPass99#"
        base_img = Image.new('RGB', (80, 80), color=(80, 90, 100))
        stego_img, _ = hide_message_in_image(base_img, original_msg, password=password)
        
        # Check inspection acknowledges encryption
        info = inspect_image_header(stego_img)
        self.assertTrue(info["has_stego"])
        self.assertTrue(info["is_encrypted"])
        
        # Extraction without password must fail
        with self.assertRaises(DecryptionError):
            extract_message_from_image(stego_img, password=None)
            
        # Extraction with wrong password must fail
        with self.assertRaises(DecryptionError):
            extract_message_from_image(stego_img, password="WrongPassword!")
            
        # Extraction with correct password succeeds
        recovered, meta = extract_message_from_image(stego_img, password=password)
        self.assertEqual(recovered, original_msg)
        self.assertTrue(meta["is_encrypted"])

    def test_corrupted_stego_image_raises_integrity_error(self):
        base_img = Image.new('RGB', (80, 80), color=(150, 160, 170))
        stego_img, _ = hide_message_in_image(base_img, "Data to be corrupted")
        
        # Corrupt pixels inside the payload region
        raw_bytes = bytearray(stego_img.tobytes())
        # Header is 48 bytes = 384 bits. Flip bit at offset 500 (inside payload)
        raw_bytes[500] ^= 1
        corrupted_img = Image.frombytes(stego_img.mode, stego_img.size, bytes(raw_bytes))
        
        with self.assertRaises(HeaderCorruptionError):
            extract_message_from_image(corrupted_img)


if __name__ == '__main__':
    unittest.main()
