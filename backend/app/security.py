"""Security — كلمات السر + JWT-like tokens (standard library فقط)."""
import base64
import hashlib
import hmac
import json
import os
import time

_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    """يرجع salt_hex$digest_hex لتخزينه في الـ env."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def create_token(secret: str, ttl_hours: int) -> str:
    """أوّل JWT بسيط HS256 (header.payload.signature)."""
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": "admin", "role": "admin", "iat": now, "exp": now + ttl_hours * 3600}
    head = _b64(json.dumps(header, separators=(",", ":")).encode("ascii"))
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("ascii"))
    sig = hmac.new(secret.encode("ascii"), f"{head}.{body}".encode("ascii"), hashlib.sha256).digest()
    return f"{head}.{body}.{_b64(sig)}"


def verify_token(secret: str, token: str) -> dict | None:
    try:
        head, body, sig = token.split(".")
        expected = hmac.new(secret.encode("ascii"), f"{head}.{body}".encode("ascii"), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64(expected).encode("ascii"), sig.encode("ascii")):
            return None
        payload = json.loads(_b64d(body))
        if int(payload.get("exp", 0)) < time.time():
            return None
        return payload
    except Exception:
        return None