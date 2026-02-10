import hashlib
import hmac


def hmac_sha256_hex(secret: str, raw: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def secure_compare(left: str, right: str) -> bool:
    return hmac.compare_digest(left, right)
