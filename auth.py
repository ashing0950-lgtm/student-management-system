"""
auth.py
Password hashing helpers (stdlib-only, no external dependencies).

Uses PBKDF2-HMAC-SHA256 with a random per-user salt, in the same spirit
as werkzeug.security but without adding a dependency to this project.
"""

import hashlib
import hmac
import os

_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    """Return a salted hash string: 'pbkdf2_sha256$iterations$salt_hex$hash_hex'."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Check a plaintext password against a hash produced by hash_password()."""
    try:
        algo, iterations, salt_hex, hash_hex = stored_hash.split("$")
        if algo != "pbkdf2_sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(dk, expected)
    except (ValueError, AttributeError):
        return False
