from __future__ import annotations

import os
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

PRIVATE_KEY_FILENAME = "identity.key"


def generate_keypair() -> tuple[bytes, bytes]:
    """Generate an ed25519 keypair and return (private_bytes, public_bytes)."""
    private_key = Ed25519PrivateKey.generate()
    private_bytes = private_key.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption()
    )
    public_bytes = private_key.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    )
    return private_bytes, public_bytes


def save_private_key(data_dir: Path, key_bytes: bytes) -> Path:
    """Write the raw private key to disk with restricted permissions."""
    path = data_dir / PRIVATE_KEY_FILENAME
    path.write_bytes(key_bytes)
    if os.name != "nt":
        path.chmod(0o600)
    return path


def load_private_key(data_dir: Path) -> Ed25519PrivateKey:
    """Load the raw private key from disk."""
    path = data_dir / PRIVATE_KEY_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"Identity key not found at {path}. "
            "The creature is bound to the machine where it was born."
        )
    raw = path.read_bytes()
    return Ed25519PrivateKey.from_private_bytes(raw)


def verify_binding(data_dir: Path, stored_pub_hex: str) -> bool:
    """Verify that the local private key matches the stored public key."""
    private_key = load_private_key(data_dir)
    derived_pub = private_key.public_key().public_bytes(
        Encoding.Raw, PublicFormat.Raw
    )
    return derived_pub.hex() == stored_pub_hex
