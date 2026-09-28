"""
StegoShield Utilities Module
Image format verification, secure path handling, and ephemeral file cleanup.
"""

import os
import time
import uuid
from PIL import Image
from werkzeug.utils import secure_filename

# Decompression bomb mitigation (limit to ~25 megapixels)
Image.MAX_IMAGE_PIXELS = 25_000_000

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}



def is_allowed_file(filename: str) -> bool:
    """Checks if filename has an allowed image extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_open_image(filepath: str) -> Image.Image:
    """
    Safely opens and verifies an image file using Pillow.
    Converts palette/grayscale images to RGB, preserves RGBA if present.
    
    :param filepath: Path to local image file
    :return: PIL Image in RGB or RGBA mode
    :raises ValueError: If image is corrupted or invalid
    """
    try:
        img = Image.open(filepath)
        img.verify()  # Verify integrity of file
    except Exception as e:
        raise ValueError(f"Invalid or corrupted image file: {str(e)}")

    # Re-open after verify() because verify leaves image in unusable state
    try:
        img = Image.open(filepath)
        # Convert image modes safely:
        # If RGBA, retain RGBA; if RGB, retain RGB; otherwise (CMYK, P, L, 1, etc.) convert to RGB
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGB')
        return img
    except Exception as e:
        raise ValueError(f"Failed to process image: {str(e)}")


def generate_unique_filename(extension: str = "png") -> str:
    """Generates a cryptographically random, collision-resistant filename."""
    token = uuid.uuid4().hex
    return f"stego_{token}.{extension.lstrip('.')}"


def cleanup_expired_files(directory: str, max_age_seconds: int = 600) -> int:
    """
    Removes files in directory older than max_age_seconds.
    
    :param directory: Directory path to clean
    :param max_age_seconds: Threshold age in seconds (default 10 mins)
    :return: Number of deleted files
    """
    if not os.path.exists(directory):
        return 0
    
    deleted_count = 0
    now = time.time()
    
    for filename in os.listdir(directory):
        # Do not delete placeholder files like .gitkeep
        if filename.startswith('.'):
            continue
        
        filepath = os.path.join(directory, filename)
        try:
            if os.path.isfile(filepath):
                file_age = now - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    deleted_count += 1
        except OSError:
            pass  # Suppress errors for concurrent file locks
            
    return deleted_count


def safe_join_paths(base_dir: str, filename: str) -> str:
    """
    Safely joins base directory and filename to prevent path traversal.
    """
    clean_name = secure_filename(filename)
    full_path = os.path.abspath(os.path.join(base_dir, clean_name))
    base_abs = os.path.abspath(base_dir)
    
    if not full_path.startswith(base_abs):
        raise ValueError("Invalid path traversal detected.")
    return full_path
