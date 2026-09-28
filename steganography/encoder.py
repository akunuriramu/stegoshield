"""
StegoShield LSB Encoder Module
Embeds structured binary payload into image pixel channels using LSB steganography.
"""

from PIL import Image
from .payload import StegoPayload, HEADER_SIZE
from .crypto import encrypt_message


class CapacityExceededError(Exception):
    """Raised when message payload exceeds the image's embedding capacity."""
    pass


def calculate_image_capacity(width: int, height: int, channels: int = 3) -> dict:
    """
    Calculates the exact embedding capacity of an image given its dimensions.
    StegoShield uses 3 channels (RGB) per pixel, 1 bit per channel.
    
    :param width: Image width in pixels
    :param height: Image height in pixels
    :param channels: Channels used per pixel (default 3 for RGB)
    :return: Dictionary containing capacity metrics in bits, bytes, and KB
    """
    total_pixels = width * height
    total_capacity_bits = total_pixels * 3  # R, G, B channels
    total_capacity_bytes = total_capacity_bits // 8
    
    usable_payload_bytes = max(0, total_capacity_bytes - HEADER_SIZE)
    
    return {
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "total_capacity_bytes": total_capacity_bytes,
        "header_size_bytes": HEADER_SIZE,
        "usable_payload_bytes": usable_payload_bytes,
        "usable_payload_kb": round(usable_payload_bytes / 1024, 2),
    }


def bytes_to_bits(data: bytes):
    """Yields bits (0 or 1) sequentially from bytes (MSB to LSB)."""
    for byte in data:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1


def hide_message_in_image(
    image: Image.Image,
    message: str,
    password: str = None
) -> tuple[Image.Image, dict]:
    """
    Hides a message inside a PIL Image using LSB steganography.
    Saves and returns the modified PIL Image (PNG ready) along with operation metadata.
    
    :param image: Input PIL Image (converted to RGB or RGBA)
    :param message: Secret plaintext message
    :param password: Optional encryption password
    :return: (stego_image: Image.Image, metadata: dict)
    :raises CapacityExceededError: If payload does not fit
    :raises ValueError: If message is empty or image is invalid
    """
    if not message or not message.strip():
        raise ValueError("Secret message cannot be empty.")

    # Ensure image is in RGB or RGBA mode
    if image.mode not in ('RGB', 'RGBA'):
        img = image.convert('RGB')
    else:
        img = image.copy()
        
    width, height = img.size
    is_rgba = (img.mode == 'RGBA')
    channels_per_pixel = 4 if is_rgba else 3
    
    # Check capacity
    capacity_info = calculate_image_capacity(width, height, channels=3)
    usable_bytes = capacity_info["usable_payload_bytes"]
    
    # Prepare payload data (encrypt if password provided)
    is_encrypted = bool(password and len(password) > 0)
    if is_encrypted:
        payload_data = encrypt_message(message, password)
    else:
        payload_data = message.encode('utf-8')
        
    payload_len = len(payload_data)
    
    if payload_len > usable_bytes:
        raise CapacityExceededError(
            f"Message payload ({payload_len} bytes) exceeds the maximum usable image capacity ({usable_bytes} bytes)."
        )
        
    # Pack binary header + payload data
    full_data = StegoPayload.pack(payload_data, is_encrypted=is_encrypted)
    total_bits_to_embed = len(full_data) * 8
    
    # Convert image pixels to mutable bytearray
    raw_bytes = bytearray(img.tobytes())
    bit_generator = bytes_to_bits(full_data)
    
    embedded_bits = 0
    raw_len = len(raw_bytes)
    
    # Embed bits into R, G, B channels, skipping Alpha channel in RGBA
    for i in range(raw_len):
        if is_rgba and (i % 4 == 3):
            # Skip alpha channel
            continue
            
        try:
            bit = next(bit_generator)
            # Clear LSB and write payload bit
            raw_bytes[i] = (raw_bytes[i] & ~1) | bit
            embedded_bits += 1
        except StopIteration:
            # All bits embedded
            break
            
    if embedded_bits < total_bits_to_embed:
        raise RuntimeError("Failed to embed all payload bits into the image.")
        
    # Recreate the image from the modified bytearray
    stego_image = Image.frombytes(img.mode, img.size, bytes(raw_bytes))
    
    metadata = {
        "width": width,
        "height": height,
        "mode": img.mode,
        "is_encrypted": is_encrypted,
        "payload_bytes": payload_len,
        "total_embedded_bytes": len(full_data),
        "capacity_bytes": capacity_info["total_capacity_bytes"],
        "usable_capacity_bytes": usable_bytes,
        "capacity_used_percent": round((len(full_data) / capacity_info["total_capacity_bytes"]) * 100, 2)
    }
    
    return stego_image, metadata
