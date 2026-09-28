"""
Unit tests for steganography.payload module.
Tests binary header packing, unpacking, magic bytes verification, and SHA-256 checksum validation.
"""

import unittest
from steganography.payload import (
    StegoPayload,
    HEADER_SIZE,
    MAGIC_HEADER,
    NoStegoHeaderError,
    HeaderCorruptionError
)


class TestPayload(unittest.TestCase):

    def test_pack_and_unpack_header_plain(self):
        data = b"Hello world steganography test data"
        packed = StegoPayload.pack(data, is_encrypted=False)
        
        self.assertEqual(len(packed), HEADER_SIZE + len(data))
        header_bytes = packed[:HEADER_SIZE]
        
        info = StegoPayload.unpack_header(header_bytes)
        self.assertEqual(info["version"], 1)
        self.assertFalse(info["is_encrypted"])
        self.assertEqual(info["payload_length"], len(data))
        self.assertEqual(len(info["checksum"]), 32)
        
        # Verify checksum
        self.assertTrue(StegoPayload.verify_and_extract(data, info["checksum"]))

    def test_pack_and_unpack_header_encrypted(self):
        data = b"SimulatedEncryptedEnvelopeData1234567890"
        packed = StegoPayload.pack(data, is_encrypted=True)
        
        header_bytes = packed[:HEADER_SIZE]
        info = StegoPayload.unpack_header(header_bytes)
        self.assertTrue(info["is_encrypted"])
        self.assertEqual(info["payload_length"], len(data))

    def test_invalid_magic_raises_no_stego_header(self):
        corrupted_header = b"BADMAGIC" + b"\x00" * (HEADER_SIZE - 8)
        with self.assertRaises(NoStegoHeaderError):
            StegoPayload.unpack_header(corrupted_header)

    def test_tampered_payload_fails_checksum_verification(self):
        data = b"Original reliable payload"
        packed = StegoPayload.pack(data, is_encrypted=False)
        
        info = StegoPayload.unpack_header(packed[:HEADER_SIZE])
        
        tampered_data = b"Tampered unreliable payld"
        with self.assertRaises(HeaderCorruptionError):
            StegoPayload.verify_and_extract(tampered_data, info["checksum"])

    def test_empty_payload_raises_value_error(self):
        with self.assertRaises(ValueError):
            StegoPayload.pack(b"", is_encrypted=False)


if __name__ == '__main__':
    unittest.main()
