import secrets


def generate_api_key():
    return secrets.token_urlsafe(16)
