"""
Per-user secrets at rest (SOLVARY_INTERVIEWER_DESIGN.md §3 decision 2).

A user's Anthropic API key is stored as a Fernet token. The Fernet key is
derived from `settings.secret_key` with HKDF-SHA256, so rotating SECRET_KEY
invalidates every stored key (callers treat `InvalidToken` as "no key" and
log it — never a 500). `cryptography` ships with python-jose[cryptography].
"""

import base64
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from app.config import get_settings

logger = logging.getLogger(__name__)

__all__ = ["InvalidToken", "decrypt_secret", "encrypt_secret", "secret_last4"]

_SALT = b"solvary"
_INFO = b"user-secrets"


def _derive(secret_key: str) -> bytes:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=_SALT, info=_INFO)
    return base64.urlsafe_b64encode(hkdf.derive(secret_key.encode("utf-8")))


@lru_cache(maxsize=4)
def _fernet(secret_key: str) -> Fernet:
    return Fernet(_derive(secret_key))


def encrypt_secret(plain: str, secret_key: str | None = None) -> str:
    settings = get_settings()
    key = secret_key if secret_key is not None else settings.secret_key
    if settings.environment == "production" and key == "change-me":
        # main.create_app already refuses to start like this; belt and braces
        raise RuntimeError("Refusing to encrypt secrets with the default SECRET_KEY")
    return _fernet(key).encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str, secret_key: str | None = None) -> str:
    """Raises `cryptography.fernet.InvalidToken` when the token was written
    under a different SECRET_KEY (or was tampered with)."""
    key = secret_key if secret_key is not None else get_settings().secret_key
    return _fernet(key).decrypt(token.encode("ascii")).decode("utf-8")


def secret_last4(plain: str) -> str:
    return plain[-4:] if len(plain) >= 4 else plain
