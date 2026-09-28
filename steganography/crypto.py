"""
StegoShield Cryptography Module
Provides AES-256-GCM authenticated encryption and PBKDF2-HMAC-SHA256 key derivation.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag


class CryptoError(Exception):
    """Base exception for cryptographic operations."""
    pass


class DecryptionError(CryptoError):
    """Raised when decryption fails due to wrong password or corrupted ciphertext."""
    pass


# Default cryptographic constants
SALT_SIZE = 16          # 128-bit salt
NONCE_SIZE = 12         # 96-bit nonce for AES-GCM
KEY_SIZE = 32           # 256-bit AES key
PBKDF2_ITERATIONS = 600000  # OWASP standard for PBKDF2-HMAC-SHA256


def derive_key(password: str, salt: bytes, iterations: int = PBKDF2_ITERATIONS) -> bytes:
    """
    Derives a 256-bit encryption key from a user password using PBKDF2-HMAC-SHA256.
    
    :param password: User-provided plaintext password string
    :param salt: 16-byte cryptographically secure random salt
    :param iterations: Number of PBKDF2 iterations
    :return: 32-byte derived key
    """
    if not isinstance(password, str) or not password:
        raise ValueError("A non-empty string password is required for key derivation.")
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode('utf-8'))


def encrypt_message(message: str, password: str) -> bytes:
    """
    Encrypts a UTF-8 message string using AES-256-GCM.
    
    The resulting envelope is structured as:
    [16 bytes Salt] + [12 bytes Nonce] + [Ciphertext + 16 bytes Auth Tag]
    
    :param message: Secret plaintext message
    :param password: User-chosen encryption password
    :return: Serialized encrypted binary envelope
    """
    if not message:
        raise ValueError("Message to encrypt cannot be empty.")
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    
    aesgcm = AESGCM(key)
    plaintext_bytes = message.encode('utf-8')
    
    # AESGCM automatically appends the 16-byte authentication tag
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_bytes, associated_data=None)
    
    # Envelope: Salt + Nonce + CiphertextWithTag
    return salt + nonce + ciphertext_with_tag


def decrypt_message(envelope: bytes, password: str) -> str:
    """
    Decrypts an AES-256-GCM binary envelope using the user password.
    
    :param envelope: The encrypted byte stream (Salt + Nonce + Ciphertext + Tag)
    :param password: User-provided decryption password
    :return: Original decrypted plaintext string
    :raises DecryptionError: If the password is wrong or ciphertext is tampered
    """
    min_length = SALT_SIZE + NONCE_SIZE + 16  # Tag is at least 16 bytes
    if len(envelope) < min_length:
        raise DecryptionError("Encrypted payload is too short or malformed.")

    salt = envelope[:SALT_SIZE]
    nonce = envelope[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext_with_tag = envelope[SALT_SIZE + NONCE_SIZE:]
    
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    
    try:
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data=None)
        return decrypted_bytes.decode('utf-8')
    except (InvalidTag, UnicodeDecodeError):
        raise DecryptionError("Unable to decrypt message. Check the password.")
    except Exception as e:
        raise DecryptionError("Unable to decrypt message. Check the password.")
