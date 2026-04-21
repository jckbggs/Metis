import hashlib


def verify_password(plain: str, stored_hash: str) -> bool:
    try:
        salt, digest = stored_hash.split(":", 1)
        return hashlib.sha256((salt + plain).encode()).hexdigest() == digest
    except ValueError:
        return False