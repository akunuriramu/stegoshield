"""
Unit tests for steganography.encoder module.
Tests capacity calculation, LSB embedding, validation of inputs, and capacity limits.
"""

import unittest
from PIL import Image
from steganography.encoder import (
    calculate_image_capacity,
    hide_message_in_image,
    CapacityExceededError
)
from steganography.payload import HEADER_SIZE


class TestEncoder(unittest.TestCase):

    def test_capacity_calculation(self):
        # 100 x 100 image has 10,000 pixels = 30,000 bits = 3,750 bytes
        cap = calculate_image_capacity(100, 100)
        self.assertEqual(cap["total_pixels"], 10000)
        self.assertEqual(cap["total_capacity_bytes"], 3750)
        self.assertEqual(cap["usable_payload_bytes"], 3750 - HEADER_SIZE)

    def test_hide_message_rgb(self):
        img = Image.new('RGB', (100, 100), color=(120, 150, 180))
        stego_img, meta = hide_message_in_image(img, "Confidential Project Phoenix")
        
        self.assertEqual(stego_img.size, (100, 100))
        self.assertEqual(stego_img.mode, 'RGB')
        self.assertFalse(meta["is_encrypted"])
        self.assertGreater(meta["total_embedded_bytes"], HEADER_SIZE)

    def test_hide_message_rgba(self):
        img = Image.new('RGBA', (100, 100), color=(100, 150, 200, 255))
        stego_img, meta = hide_message_in_image(img, "RGBA Message Embedding Test")
        
        self.assertEqual(stego_img.size, (100, 100))
        self.assertEqual(stego_img.mode, 'RGBA')
        
        # Verify alpha channel remains completely untouched (all 255)
        alpha_channel = [p[3] for p in stego_img.getdata()]
        self.assertTrue(all(a == 255 for a in alpha_channel))

    def test_oversized_message_raises_capacity_error(self):
        # 15 x 15 image has 225 pixels = 675 bits = 84 bytes.
        # Header is 48 bytes. Usable space is 36 bytes.
        tiny_img = Image.new('RGB', (15, 15), color=(50, 50, 50))
        huge_message = "A" * 100  # 100 bytes > 36 bytes usable
        
        with self.assertRaises(CapacityExceededError):
            hide_message_in_image(tiny_img, huge_message)

    def test_empty_message_raises_value_error(self):
        img = Image.new('RGB', (50, 50), color=(20, 20, 20))
        with self.assertRaises(ValueError):
            hide_message_in_image(img, "")
        with self.assertRaises(ValueError):
            hide_message_in_image(img, "   ")


if __name__ == '__main__':
    unittest.main()
