"""
Comprehensive End-to-End Acceptance Tests for StegoShield.
Directly implements and validates all tests specified in the project requirements.
"""

import os
import tempfile
import unittest
from PIL import Image
from steganography.encoder import hide_message_in_image, CapacityExceededError
from steganography.decoder import (
    extract_message_from_image,
    inspect_image_header,
    NoStegoHeaderError,
    DecryptionError
)


class TestEndToEnd(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_acceptance_test_1_basic_png_flow(self):
        """TEST 1: Standard hide -> save PNG -> reload -> extract message."""
        original_msg = "Meet me at 5 PM tomorrow."
        img_path = os.path.join(self.temp_dir.name, "source.png")
        stego_path = os.path.join(self.temp_dir.name, "stego.png")
        
        # 1. Create base PNG
        base_img = Image.new('RGB', (120, 120), color=(85, 110, 140))
        base_img.save(img_path, format="PNG")
        
        # 2. Hide message
        loaded_img = Image.open(img_path)
        stego_img, meta = hide_message_in_image(loaded_img, original_msg)
        stego_img.save(stego_path, format="PNG")
        
        # 3. Extract from saved PNG
        test_img = Image.open(stego_path)
        extracted_msg, ext_meta = extract_message_from_image(test_img)
        
        self.assertEqual(extracted_msg, original_msg)
        self.assertFalse(ext_meta["is_encrypted"])

    def test_acceptance_test_2_password_protection(self):
        """TEST 2: Password protection with AES-256-GCM authenticated encryption."""
        original_msg = "This is a confidential message."
        password = "TestPassword123!"
        stego_path = os.path.join(self.temp_dir.name, "encrypted_stego.png")
        
        base_img = Image.new('RGB', (100, 100), color=(30, 40, 50))
        stego_img, meta = hide_message_in_image(base_img, original_msg, password=password)
        stego_img.save(stego_path, format="PNG")
        
        # Verify inspection flags encryption
        reloaded_img = Image.open(stego_path)
        header_info = inspect_image_header(reloaded_img)
        self.assertTrue(header_info["has_stego"])
        self.assertTrue(header_info["is_encrypted"])
        
        # Extract with password
        extracted_msg, ext_meta = extract_message_from_image(reloaded_img, password=password)
        self.assertEqual(extracted_msg, original_msg)
        self.assertTrue(ext_meta["is_encrypted"])

    def test_acceptance_test_3_wrong_password(self):
        """TEST 3: Graceful failure when incorrect password is provided."""
        original_msg = "Highly Sensitive Document Contents"
        password = "TestPassword123!"
        
        base_img = Image.new('RGB', (100, 100), color=(70, 80, 90))
        stego_img, _ = hide_message_in_image(base_img, original_msg, password=password)
        
        with self.assertRaises(DecryptionError) as ctx:
            extract_message_from_image(stego_img, password="WrongPassword999!")
        self.assertIn("Unable to decrypt", str(ctx.exception))

    def test_acceptance_test_4_ordinary_image_detection(self):
        """TEST 4: Ordinary non-stego image properly rejected."""
        ordinary_img = Image.new('RGB', (100, 100), color=(200, 210, 220))
        info = inspect_image_header(ordinary_img)
        self.assertFalse(info["has_stego"])
        self.assertIn("No StegoShield message was detected", info["error"])
        
        with self.assertRaises(NoStegoHeaderError) as ctx:
            extract_message_from_image(ordinary_img)
        self.assertIn("No StegoShield message was detected", str(ctx.exception))

    def test_acceptance_test_5_oversized_message_rejection(self):
        """TEST 5: Capacity limit checked and rejected before processing."""
        # 16x16 image has 256 pixels = 768 bits = 96 bytes total. Usable = 96 - 48 = 48 bytes.
        small_img = Image.new('RGB', (16, 16), color=(20, 30, 40))
        oversized_msg = "This message is intentionally much longer than the usable 48 bytes of this tiny image!"
        
        with self.assertRaises(CapacityExceededError):
            hide_message_in_image(small_img, oversized_msg)

    def test_acceptance_test_6_unicode_and_emojis(self):
        """TEST 6: Support for English, numbers, symbols, emojis, Telugu, and Japanese."""
        unicode_msg = "Hello 🚀 नमస్కారం こんにちは"
        base_img = Image.new('RGB', (150, 150), color=(45, 65, 85))
        stego_img, _ = hide_message_in_image(base_img, unicode_msg)
        
        recovered_msg, _ = extract_message_from_image(stego_img)
        self.assertEqual(recovered_msg, unicode_msg)

    def test_multiline_text_with_special_characters(self):
        """Test multiline text preservation and formatting."""
        multiline_msg = (
            "Line 1: Operational Directive Alpha\n"
            "Line 2: Coordinates [37.7749° N, 122.4194° W]\n"
            "Line 3: Key fingerprint: SHA256:d8a2...3f\n"
            "\t- Indented subpoint 1\n"
            "\t- Indented subpoint 2"
        )
        base_img = Image.new('RGB', (120, 120), color=(15, 25, 35))
        stego_img, _ = hide_message_in_image(base_img, multiline_msg)
        
        recovered_msg, _ = extract_message_from_image(stego_img)
        self.assertEqual(recovered_msg, multiline_msg)

    def test_non_square_rgba_image(self):
        """Test non-square image dimensions and RGBA mode with transparency."""
        msg = "Secret payload hidden in an RGBA non-square banner"
        base_img = Image.new('RGBA', (73, 129), color=(255, 100, 50, 200))
        stego_img, _ = hide_message_in_image(base_img, msg)
        
        self.assertEqual(stego_img.size, (73, 129))
        self.assertEqual(stego_img.mode, 'RGBA')
        
        recovered_msg, meta = extract_message_from_image(stego_img)
        self.assertEqual(recovered_msg, msg)


if __name__ == '__main__':
    unittest.main()
