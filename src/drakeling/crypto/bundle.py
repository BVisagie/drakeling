"""Encrypted .drakeling bundle format per Spec Section 17.

Bundle layout:
  [4 bytes magic: 0x4F434C48]  ("OCLH")
  [1 byte version: 0x01]
  [16 bytes salt]
  [12 bytes AES-GCM IV]
  [remaining bytes: AES-256-GCM ciphertext + 16-byte tag]

Plaintext payload is JSON: { "database": base64, "private_key": base64 }
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from drakeling.crypto.identity import PRIVATE_KEY_FILENAME
from drakeling.storage.database import DB_FILENAME

MAGIC = b"OCLH"
VERSION = b"\x01"
SALT_LEN = 16
IV_LEN = 12
PBKDF2_ITERATIONS = 600_000


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(passphrase.encode("utf-8"))


def export_bundle(data_dir: Path, passphrase: str) -> bytes:
    """Create an encrypted .drakeling bundle from the current creature data."""
    db_path = data_dir / DB_FILENAME
    key_path = data_dir / PRIVATE_KEY_FILENAME

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}")
    if not key_path.exists():
        raise FileNotFoundError(f"Identity key not found at {key_path}")

    db_bytes = db_path.read_bytes()
    key_bytes = key_path.read_bytes()

    payload = json.dumps({
        "database": base64.b64encode(db_bytes).decode("ascii"),
        "private_key": base64.b64encode(key_bytes).decode("ascii"),
    }).encode("utf-8")

    salt = os.urandom(SALT_LEN)
    iv = os.urandom(IV_LEN)
    aes_key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(iv, payload, None)

    return MAGIC + VERSION + salt + iv + ciphertext


def import_bundle(bundle: bytes, passphrase: str) -> tuple[bytes, bytes]:
    """Decrypt a .drakeling bundle and return (db_bytes, private_key_bytes)."""
    if len(bundle) < 4 + 1 + SALT_LEN + IV_LEN + 16:
        raise ValueError("Bundle too small to be valid")

    if bundle[:4] != MAGIC:
        raise ValueError("Invalid bundle: bad magic bytes")
    if bundle[4:5] != VERSION:
        raise ValueError(f"Unsupported bundle version: {bundle[4]}")

    offset = 5
    salt = bundle[offset:offset + SALT_LEN]
    offset += SALT_LEN
    iv = bundle[offset:offset + IV_LEN]
    offset += IV_LEN
    ciphertext = bundle[offset:]

    aes_key = _derive_key(passphrase, salt)
    aesgcm = AESGCM(aes_key)

    try:
        plaintext = aesgcm.decrypt(iv, ciphertext, None)
    except Exception as exc:
        raise ValueError("Decryption failed — wrong passphrase or corrupted bundle") from exc

    data = json.loads(plaintext)
    db_bytes = base64.b64decode(data["database"])
    key_bytes = base64.b64decode(data["private_key"])
    return db_bytes, key_bytes
