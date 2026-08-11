import base64
import hashlib
import os

from cryptography.fernet import Fernet


def get_fernet():
    secret = os.environ.get("MODEL_CONFIG_SECRET") or os.environ.get("SECRET_KEY")

    if not secret:
        raise RuntimeError("MODEL_CONFIG_SECRET or SECRET_KEY is required")

    key = base64.urlsafe_b64encode(
        hashlib.sha256(secret.encode("utf-8")).digest()
    )

    return Fernet(key)


def encrypt_text(value: str) -> str:
    return get_fernet().encrypt(
        value.encode("utf-8")
    ).decode("utf-8")


def decrypt_text(value: str) -> str:
    return get_fernet().decrypt(
        value.encode("utf-8")
    ).decode("utf-8")


def mask_key(value: str) -> str:
    if len(value) <= 8:
        return "****"

    return f"{value[:4]}****{value[-4:]}"
