"""
Encryption utilities for the AI Language Tutor application.
"""

import base64
from cryptography.fernet import Fernet
from typing import Optional


def encrypt_data(data: str, key: Optional[bytes] = None) -> str:
    """Encrypt data using Fernet."""
    if key is None:
        key = Fernet.generate_key()
    
    f = Fernet(key)
    encrypted_data = f.encrypt(data.encode())
    return base64.b64encode(encrypted_data).decode()


def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """Decrypt data using Fernet."""
    f = Fernet(key)
    decoded_data = base64.b64decode(encrypted_data.encode())
    decrypted_data = f.decrypt(decoded_data)
    return decrypted_data.decode()


