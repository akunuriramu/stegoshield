"""
StegoShield Binary Payload Module
Defines the binary header structure, serialization, deserialization, and integrity validation.
"""

import struct
import hashlib

# Constants
MAGIC_HEADER = b"STGSHLD!"  # 8 bytes magic identifier
CURRENT_VERSION = 1         # 1 byte version
FLAG_PLAIN = 0x00           # Unencrypted payload
FLAG_ENCRYPTED = 0x01       # AES-256-GCM encrypted payload

# Struct format for header:
# 8s: Magic (8B)
# B:  Version (1B)
# B:  Flags (1B)
# H:  Reserved (2B)
# I:  Payload Length (4B, big-endian uint32)
# 32s: SHA-256 Checksum (32B)
HEADER_STRUCT_FORMAT = ">8sBBHI32s"
HEADER_SIZE = struct.calcsize(HEADER_STRUCT_FORMAT)  # exactly 48 bytes


class PayloadError(Exception):
    """Base exception for payload handling errors."""
    pass


class NoStegoHeaderError(PayloadError):
    """Raised when the StegoShield magic header is missing or invalid."""
    pass


class HeaderCorruptionError(PayloadError):
    """Raised when the payload length or checksum indicates data corruption."""
    pass


class StegoPayload:
    """
    Handles packing and unpacking of StegoShield structured binary payloads.
    """

    @staticmethod
    def pack(payload_data: bytes, is_encrypted: bool = False) -> bytes:
        """
        Packs raw payload bytes with a 48-byte StegoShield binary header.
        
        :param payload_data: Payload bytes (either plaintext UTF-8 or encrypted envelope)
        :param is_encrypted: True if payload is encrypted with AES-256-GCM
        :return: Complete binary sequence (48-byte header + payload_data)
        """
        if not isinstance(payload_data, bytes):
            raise TypeError("payload_data must be bytes.")
        
        payload_len = len(payload_data)
        if payload_len == 0:
            raise ValueError("Payload data cannot be empty.")
        if payload_len > 0xFFFFFFFF:
            raise ValueError("Payload size exceeds maximum 32-bit integer limit.")
        
        # Calculate SHA-256 checksum across the raw payload data
        checksum = hashlib.sha256(payload_data).digest()
        flags = FLAG_ENCRYPTED if is_encrypted else FLAG_PLAIN
        reserved = 0
        
        header = struct.pack(
            HEADER_STRUCT_FORMAT,
            MAGIC_HEADER,
            CURRENT_VERSION,
            flags,
            reserved,
            payload_len,
            checksum
        )
        
        return header + payload_data

    @staticmethod
    def unpack_header(header_bytes: bytes) -> dict:
        """
        Unpacks and validates the 48-byte StegoShield header.
        
        :param header_bytes: Exactly 48 bytes extracted from the image
        :return: Dictionary with header metadata: version, is_encrypted, payload_length, checksum
        :raises NoStegoHeaderError: If magic bytes don't match
        :raises HeaderCorruptionError: If header fields are corrupted
        """
        if len(header_bytes) < HEADER_SIZE:
            raise NoStegoHeaderError("Insufficient data for StegoShield header.")
        
        try:
            magic, version, flags, reserved, payload_len, checksum = struct.unpack(
                HEADER_STRUCT_FORMAT,
                header_bytes[:HEADER_SIZE]
            )
        except struct.error:
            raise NoStegoHeaderError("No StegoShield message detected in this image.")

        if magic != MAGIC_HEADER:
            raise NoStegoHeaderError("No StegoShield message detected in this image.")
        
        if version != CURRENT_VERSION:
            raise HeaderCorruptionError(f"Unsupported StegoShield version: {version}.")

        is_encrypted = bool(flags & FLAG_ENCRYPTED)
        
        return {
            "version": version,
            "is_encrypted": is_encrypted,
            "payload_length": payload_len,
            "checksum": checksum
        }

    @staticmethod
    def verify_and_extract(payload_bytes: bytes, expected_checksum: bytes) -> bool:
        """
        Verifies the SHA-256 integrity checksum of the extracted payload.
        
        :param payload_bytes: Extracted payload bytes
        :param expected_checksum: 32-byte expected checksum from header
        :return: True if checksum matches
        :raises HeaderCorruptionError: If checksum verification fails
        """
        actual_checksum = hashlib.sha256(payload_bytes).digest()
        if actual_checksum != expected_checksum:
            raise HeaderCorruptionError("The hidden message appears to be corrupted or modified.")
        return True
