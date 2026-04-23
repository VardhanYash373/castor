"""Tests for Stage 1 — key gen, sign, verify."""

import os
import tempfile
import pytest
from PIL import Image

from src.crypto.keygen import generate_key_pair, load_private_key, load_public_key
from src.crypto.sign import hash_pixels, sign_image
from src.crypto.verify import verify_image, VerifyResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def key_pair(tmp_path_factory):
    """Generate a real ECDSA key pair in a temp dir."""
    keys_dir = str(tmp_path_factory.mktemp("keys"))
    priv_path, pub_path = generate_key_pair(keys_dir)
    return priv_path, pub_path


@pytest.fixture
def sample_jpeg(tmp_path):
    """Create a small synthetic JPEG for testing."""
    img = Image.new("RGB", (64, 64), color=(100, 149, 237))
    path = str(tmp_path / "sample.jpg")
    img.save(path, "JPEG")
    return path


@pytest.fixture
def tampered_jpeg(tmp_path):
    """Create a JPEG then save a pixel-modified copy."""
    img = Image.new("RGB", (64, 64), color=(100, 149, 237))
    path = str(tmp_path / "tampered.jpg")
    # Flip one pixel
    img.putpixel((0, 0), (255, 0, 0))
    img.save(path, "JPEG")
    return path


# ── Keygen tests ──────────────────────────────────────────────────────────────

def test_generate_key_pair_creates_files(key_pair):
    priv_path, pub_path = key_pair
    assert os.path.exists(priv_path)
    assert os.path.exists(pub_path)


def test_load_private_key(key_pair):
    priv_path, _ = key_pair
    key = load_private_key(priv_path)
    assert key is not None


def test_load_public_key(key_pair):
    _, pub_path = key_pair
    key = load_public_key(pub_path)
    assert key is not None


# ── Sign tests ────────────────────────────────────────────────────────────────

def test_hash_pixels_returns_hex_string(sample_jpeg):
    h = hash_pixels(sample_jpeg)
    assert isinstance(h, str)
    assert len(h) == 64  # SHA-256 hex = 64 chars


def test_hash_pixels_is_deterministic(sample_jpeg):
    assert hash_pixels(sample_jpeg) == hash_pixels(sample_jpeg)


def test_sign_image_returns_hash_and_signature(sample_jpeg, key_pair):
    priv_path, _ = key_pair
    result = sign_image(sample_jpeg, priv_path)
    assert "pixel_hash" in result
    assert "signature" in result
    assert len(result["pixel_hash"]) == 64
    assert len(result["signature"]) > 0


# ── Verify tests ──────────────────────────────────────────────────────────────

def test_verify_valid_image(sample_jpeg, key_pair):
    priv_path, pub_path = key_pair
    signed = sign_image(sample_jpeg, priv_path)
    result = verify_image(
        sample_jpeg,
        signed["pixel_hash"],
        signed["signature"],
        pub_path,
    )
    assert result["status"] == VerifyResult.VALID


def test_verify_detects_tampered_pixels(sample_jpeg, tampered_jpeg, key_pair):
    priv_path, pub_path = key_pair
    # Sign the clean image, then verify against the tampered one
    signed = sign_image(sample_jpeg, priv_path)
    result = verify_image(
        tampered_jpeg,
        signed["pixel_hash"],
        signed["signature"],
        pub_path,
    )
    assert result["status"] == VerifyResult.TAMPERED


def test_verify_detects_forged_signature(sample_jpeg, key_pair):
    priv_path, pub_path = key_pair
    signed = sign_image(sample_jpeg, priv_path)
    result = verify_image(
        sample_jpeg,
        signed["pixel_hash"],
        "aW52YWxpZHNpZ25hdHVyZQ==",  # garbage base64
        pub_path,
    )
    assert result["status"] == VerifyResult.INVALID_SIGNATURE
