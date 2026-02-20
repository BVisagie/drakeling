"""Tests for crypto modules: identity, token, bundle."""
import tempfile
from pathlib import Path

from drakeling.crypto.bundle import export_bundle, import_bundle, MAGIC, VERSION
from drakeling.crypto.identity import (
    generate_keypair,
    load_private_key,
    save_private_key,
    verify_binding,
)
from drakeling.crypto.token import ensure_api_token, generate_api_token


class TestIdentity:
    def test_keypair_lengths(self):
        priv, pub = generate_keypair()
        assert len(priv) == 32
        assert len(pub) == 32

    def test_save_and_load(self, tmp_path):
        priv, pub = generate_keypair()
        save_private_key(tmp_path, priv)
        loaded = load_private_key(tmp_path)
        assert loaded is not None

    def test_verify_binding_passes(self, tmp_path):
        priv, pub = generate_keypair()
        save_private_key(tmp_path, priv)
        assert verify_binding(tmp_path, pub.hex()) is True

    def test_verify_binding_fails_wrong_key(self, tmp_path):
        priv1, pub1 = generate_keypair()
        _priv2, pub2 = generate_keypair()
        save_private_key(tmp_path, priv1)
        assert verify_binding(tmp_path, pub2.hex()) is False


class TestToken:
    def test_generate_token_is_url_safe(self):
        token = generate_api_token()
        assert len(token) > 20
        # URL-safe base64 chars only
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
        assert set(token).issubset(allowed)

    def test_ensure_creates_and_returns(self, tmp_path):
        token = ensure_api_token(tmp_path)
        assert len(token) > 0
        # Second call returns same token
        assert ensure_api_token(tmp_path) == token

    def test_ensure_file_exists(self, tmp_path):
        ensure_api_token(tmp_path)
        assert (tmp_path / "api_token").exists()


class TestBundle:
    def _make_data_dir(self, tmp_path: Path) -> Path:
        (tmp_path / "drakeling.db").write_bytes(b"sqlite-database-bytes")
        (tmp_path / "identity.key").write_bytes(b"x" * 32)
        return tmp_path

    def test_round_trip(self, tmp_path):
        data_dir = self._make_data_dir(tmp_path)
        bundle = export_bundle(data_dir, "secret")
        db, key = import_bundle(bundle, "secret")
        assert db == b"sqlite-database-bytes"
        assert key == b"x" * 32

    def test_magic_and_version(self, tmp_path):
        data_dir = self._make_data_dir(tmp_path)
        bundle = export_bundle(data_dir, "pass")
        assert bundle[:4] == MAGIC
        assert bundle[4:5] == VERSION

    def test_wrong_passphrase_fails(self, tmp_path):
        data_dir = self._make_data_dir(tmp_path)
        bundle = export_bundle(data_dir, "correct")
        import pytest
        with pytest.raises(ValueError, match="wrong passphrase"):
            import_bundle(bundle, "wrong")

    def test_truncated_bundle_fails(self):
        import pytest
        with pytest.raises(ValueError, match="too small"):
            import_bundle(b"OCL", "pass")

    def test_bad_magic_fails(self):
        import pytest
        with pytest.raises(ValueError, match="bad magic"):
            import_bundle(b"XXXX\x01" + b"\x00" * 100, "pass")
