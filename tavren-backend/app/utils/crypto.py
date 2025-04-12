import base64
import json
import os
from typing import Any, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def generate_key() -> bytes:
    """
    Generate a new encryption key for Fernet symmetric encryption.
    
    Returns:
        A URL-safe base64-encoded 32-byte key
    """
    return Fernet.generate_key()

def derive_key_from_password(password: str, salt: bytes = None) -> bytes:
    """
    Derive an encryption key from a password using PBKDF2.
    
    Args:
        password: The password to derive the key from
        salt: Optional salt bytes, if not provided a new one will be generated
        
    Returns:
        A tuple of (key, salt), where key is a URL-safe base64-encoded 32-byte key
    """
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

def encrypt_data(data: Union[str, dict, list], key: bytes) -> str:
    """
    Encrypt data using Fernet symmetric encryption.
    
    Args:
        data: String or JSON-serializable data to encrypt
        key: URL-safe base64-encoded 32-byte key
        
    Returns:
        Encrypted data as a string (base64 encoded)
    """
    # Convert non-string data to JSON
    if not isinstance(data, str):
        data = json.dumps(data)
    
    try:
        f = Fernet(key)
        encrypted_data = f.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    except Exception as e:
        raise ValueError(f"Encryption error: {str(e)}")

def decrypt_data(encrypted_data: str, key: bytes) -> Union[str, Any]:
    """
    Decrypt data using Fernet symmetric encryption.
    
    Args:
        encrypted_data: Encrypted data string (base64 encoded)
        key: URL-safe base64-encoded 32-byte key
        
    Returns:
        Decrypted data, as a string or parsed JSON object if valid
    """
    try:
        # Decode from base64
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
        
        # Decrypt
        f = Fernet(key)
        decrypted_data = f.decrypt(encrypted_bytes).decode()
        
        # Try to parse as JSON
        try:
            return json.loads(decrypted_data)
        except json.JSONDecodeError:
            # Return as string if not valid JSON
            return decrypted_data
    except Exception as e:
        raise ValueError(f"Decryption error: {str(e)}")

def hash_identifier(identifier: str, salt: str = None) -> str:
    """
    Create a salted hash of an identifier.
    
    Args:
        identifier: The string to hash
        salt: Optional salt string
        
    Returns:
        Hashed identifier
    """
    if salt is None:
        salt = os.urandom(16).hex()
    
    # Simple hash with salt
    digest = hashes.Hash(hashes.SHA256())
    digest.update(f"{salt}:{identifier}".encode())
    hashed = digest.finalize().hex()
    
    return f"{salt}:{hashed}"

def verify_hashed_identifier(original: str, hashed_value: str) -> bool:
    """
    Verify if an identifier matches a previously hashed value.
    
    Args:
        original: The original identifier to check
        hashed_value: The previously hashed value to compare against
        
    Returns:
        True if the identifier matches the hash
    """
    try:
        salt, hash_hex = hashed_value.split(':', 1)
        
        # Rehash with the same salt
        digest = hashes.Hash(hashes.SHA256())
        digest.update(f"{salt}:{original}".encode())
        computed_hash = digest.finalize().hex()
        
        return computed_hash == hash_hex
    except:
        return False 