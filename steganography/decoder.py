"""
StegoShield LSB Decoder Module
Extracts and verifies structured binary steganography payloads from images.
"""

from PIL import Image
from .payload import (
    StegoPayload,
    HEADER_SIZE,
    NoStegoHeaderError,
    HeaderCorruptionError
)
from .crypto import decrypt_message, DecryptionError


def extract_bits_from_image(img: Image.Image, max_bits: int) -> bytearray:
    """
    Extracts up to max_bits from the LSBs of RGB channels of the image.
    Skips the Alpha channel for RGBA images.
    Returns extracted data as a bytearray.
    """
    raw_bytes = img.tobytes()
    is_rgba = (img.mode == 'RGBA')
    
    extracted_bytes = bytearray()
    current_byte = 0
    bits_in_current_byte = 0
    total_bits_read = 0
    
    for i, byte_val in enumerate(raw_bytes):
        if is_rgba and (i % 4 == 3):
            # Skip alpha channel
            continue
            
        bit = byte_val & 1
        current_byte = (current_byte << 1) | bit
        bits_in_current_byte += 1
        total_bits_read += 1
        
        if bits_in_current_byte == 8:
            extracted_bytes.append(current_byte)
            current_byte = 0
            bits_in_current_byte = 0
            
        if total_bits_read >= max_bits:
            break
            
    return extracted_bytes


def inspect_image_header(image: Image.Image) -> dict:
    """
    Quickly checks if an image contains a valid StegoShield header.
    Only reads the first 48 bytes (384 bits).
    
    :param image: Input PIL Image
    :return: Dictionary containing header status and metadata
    """
    if image.mode not in ('RGB', 'RGBA'):
        img = image.convert('RGB')
    else:
        img = image
        
    width, height = img.size
    total_available_bits = width * height * 3
    header_bits = HEADER_SIZE * 8
    
    if total_available_bits < header_bits:
        return {
            "has_stego": False,
            "error": "Image is too small to contain a StegoShield message."
        }
        
    header_bytes = extract_bits_from_image(img, max_bits=header_bits)
    if len(header_bytes) < HEADER_SIZE:
        return {
            "has_stego": False,
            "error": "Unable to read header bytes from image."
        }
        
    try:
        header_info = StegoPayload.unpack_header(bytes(header_bytes))
        return {
            "has_stego": True,
            "version": header_info["version"],
            "is_encrypted": header_info["is_encrypted"],
            "payload_length": header_info["payload_length"],
            "checksum_hex": header_info["checksum"].hex(),
            "width": width,
            "height": height
        }
    except NoStegoHeaderError:
        return {
            "has_stego": False,
            "error": "No StegoShield message was detected in this image."
        }
    except HeaderCorruptionError as e:
        return {
            "has_stego": False,
            "error": f"Header corrupted: {str(e)}"
        }


def extract_message_from_image(image: Image.Image, password: str = None) -> tuple[str, dict]:
    """
    Extracts, verifies, and decodes/decrypts the secret message from an image.
    
    :param image: Input PIL Image
    :param password: Password string if payload is encrypted
    :return: (message: str, metadata: dict)
    :raises NoStegoHeaderError: If no StegoShield header is found
    :raises HeaderCorruptionError: If checksum verification fails or payload is corrupt
    :raises DecryptionError: If decryption fails (wrong password or altered ciphertext)
    """
    if image.mode not in ('RGB', 'RGBA'):
        img = image.convert('RGB')
    else:
        img = image
        
    width, height = img.size
    total_available_bytes = (width * height * 3) // 8
    
    # Step 1: Read and validate header
    header_info = inspect_image_header(img)
    if not header_info.get("has_stego"):
        raise NoStegoHeaderError(
            header_info.get("error", "No StegoShield message was detected in this image.")
        )
        
    payload_len = header_info["payload_length"]
    total_bytes_needed = HEADER_SIZE + payload_len
    
    if total_bytes_needed > total_available_bytes:
        raise HeaderCorruptionError(
            "The hidden message appears to be corrupted or modified (declared length exceeds image capacity)."
        )
        
    # Step 2: Read complete payload bits
    total_bits_needed = total_bytes_needed * 8
    all_extracted_bytes = extract_bits_from_image(img, max_bits=total_bits_needed)
    
    if len(all_extracted_bytes) < total_bytes_needed:
        raise HeaderCorruptionError("The hidden message appears to be corrupted or modified.")
        
    header_bytes = bytes(all_extracted_bytes[:HEADER_SIZE])
    payload_bytes = bytes(all_extracted_bytes[HEADER_SIZE:total_bytes_needed])
    
    # Step 3: Verify SHA-256 integrity checksum
    unpacked_header = StegoPayload.unpack_header(header_bytes)
    StegoPayload.verify_and_extract(payload_bytes, unpacked_header["checksum"])
    
    # Step 4: Decrypt or decode
    is_encrypted = unpacked_header["is_encrypted"]
    if is_encrypted:
        if not password:
            raise DecryptionError("Password required to decrypt this message.")
        message = decrypt_message(payload_bytes, password)
    else:
        try:
            message = payload_bytes.decode('utf-8')
        except UnicodeDecodeError:
            raise HeaderCorruptionError("The hidden message appears to be corrupted or modified.")
            
    metadata = {
        "width": width,
        "height": height,
        "is_encrypted": is_encrypted,
        "payload_bytes": payload_len,
        "checksum": unpacked_header["checksum"].hex(),
        "version": unpacked_header["version"]
    }
    
    return message, metadata
