import hashlib
import secrets

import bcrypt

PREFIX_KEY = "cpt_"  # cpt stands for codecarbon project token


def generate_api_key() -> str:
    # Generate a random API key
    api_key = secrets.token_urlsafe(32)
    prefixed_api_key = f"{PREFIX_KEY}{api_key}"
    return prefixed_api_key


def get_api_key_hash(api_key: str) -> str:
    """Get the hash of the api key"""
    return bcrypt.hashpw(
        api_key.encode(),
        bcrypt.gensalt(),
    )


def verify_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Verify the api key
    """
    return bcrypt.checkpw(
        plain_api_key.encode(),
        hashed_api_key.encode(),
    )


def generate_lookup_value(api_key: str) -> str:
    # Generate a SHA-256 hash of the API key
    sha256_hash = hashlib.sha256(api_key.encode()).hexdigest()
    # Use the first 8 characters of the hash as a lookup value
    return sha256_hash[:8]
