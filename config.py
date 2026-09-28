"""
StegoShield Configuration Module
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'stegoshield-dev-secret-key-change-in-prod-2026')
    
    # Storage paths
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
    
    # File limits
    MAX_CONTENT_LENGTH = 15 * 1024 * 1024  # 15 MB request limit
    MAX_UPLOAD_SIZE_MB = 10  # 10 MB maximum image size
    
    # Allowed input formats (output is strictly PNG)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp', 'webp'}
    
    # Steganography parameters
    MAX_MESSAGE_CHARACTERS = 50000  # Max characters allowed in text area
    MAX_IMAGE_PIXELS = 25_000_000   # Prevent decompression bomb attacks (e.g. 5000x5000)
    
    # Ephemeral storage cleanup & privacy
    CLEANUP_INTERVAL_SECONDS = int(os.environ.get('CLEANUP_INTERVAL_SECONDS', '180'))  # Run cleanup every 3 mins
    FILE_MAX_AGE_SECONDS = int(os.environ.get('FILE_MAX_AGE_SECONDS', '300'))          # Delete temp files older than 5 mins
    
    # Cryptographic settings
    PBKDF2_ITERATIONS = 600000       # OWASP recommendation for PBKDF2-HMAC-SHA256
    SALT_SIZE = 16                   # 128-bit salt
    NONCE_SIZE = 12                  # 96-bit nonce for AES-GCM
    TAG_SIZE = 16                    # 128-bit GCM auth tag

