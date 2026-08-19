import hashlib
import secrets

import bcrypt

PREFIX_KEY = "cpt_"  # cpt stands for codecarbon project token


def generate_api_key() -> str:
    # Generate a random API key
    api_key = secrets.token_urlsafe(32)
    prefixed_api_key = f"{PREFIX_KEY}{api_key}"
    return prefixed_api_key


def get_api_key_hash(api_key: str) -> bytes:
    """Get the hash of the api key.

    Returns bcrypt's own ``bytes`` output. It is stored in a ``String`` column and
    comes back from the database as ``str``, which is what ``verify_api_key``
    expects — hence the asymmetric annotations.
    """
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
    """Derive the non-secret database index for an API key.

    This is a lookup shortcut, not a credential. It narrows a token lookup to a
    handful of candidate rows; authentication is always ``verify_api_key``
    (bcrypt) against the stored ``hashed_token``. Collisions are expected and the
    caller iterates over every candidate, so 8 hex characters is deliberate.

    SHA-256 is correct here and must not be swapped for an HMAC or a KDF: static
    analysis flags this line as weak credential hashing (``py/weak-sensitive-data-
    hashing``), but the value authenticates nothing. Changing the derivation would
    also be unrecoverable — it is computed from plaintext tokens that are never
    stored, so existing rows could not be backfilled and every issued API key
    would stop resolving.
    """
    sha256_hash = hashlib.sha256(api_key.encode()).hexdigest()
    return sha256_hash[:8]
