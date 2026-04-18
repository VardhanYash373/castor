"""End-to-end tests: sign -> embed -> verify -> tamper -> detect."""

import os
import shutil
import pytest
from PIL import Image

from src.crypto.keygen import generate_key_pair
from src.pipeline import sign_and_embed, verify_signed_image
from src.crypto.verify import VerifyResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def key_pair(tmp_path_factory):
    keys_dir = str(tmp_path_factory.mktemp("keys"))
    priv_path, pub_path = generate_key_pair(keys_dir)
    return priv_path, pub_path


@pytest.fixture
def sample_jpeg(tmp_path):
    img = Image.new("RGB", (100, 100), color=(34, 139, 34))
    path = str(tmp_path / "sample.jpg")
    img.save(path, "JPEG")
    return path


exiftool_available = shutil.which("exiftool") is not None
skip_no_exiftool = pytest.mark.skipif(
    not exiftool_available, reason="exiftool not installed"
)


# ── Pipeline tests ────────────────────────────────────────────────────────────

@skip_no_exiftool
def test_sign_and_embed_creates_output(sample_jpeg, key_pair, tmp_path):
    priv_path, _ = key_pair
    out_path = str(tmp_path / "signed.jpg")
    result = sign_and_embed(sample_jpeg, priv_path, output_path=out_path)
    assert os.path.exists(result["output_path"])
    assert result["manifest"]["schema"] == "chain-of-trust/v1"


@skip_no_exiftool
def test_verify_valid_signed_image(sample_jpeg, key_pair, tmp_path):
    priv_path, pub_path = key_pair
    out_path = str(tmp_path / "signed.jpg")
    sign_and_embed(sample_jpeg, priv_path, output_path=out_path)
    result = verify_signed_image(out_path, pub_path)
    assert result["status"] == VerifyResult.VALID


@skip_no_exiftool
def test_verify_detects_pixel_tamper(sample_jpeg, key_pair, tmp_path):
    priv_path, pub_path = key_pair
    out_path = str(tmp_path / "signed.jpg")
    sign_and_embed(sample_jpeg, priv_path, output_path=out_path)

    # Tamper: flip one pixel in the signed image
    with Image.open(out_path) as img:
        img = img.convert("RGB")
        pixels = img.load()
        pixels[0, 0] = (255, 0, 0)
        tampered_path = str(tmp_path / "tampered.jpg")
        img.save(tampered_path, "JPEG")

    # Copy manifest from signed to tampered so only pixels differ
    shutil.copy2(out_path, tampered_path)
    with Image.open(out_path) as orig:
        orig_px = list(orig.getdata())
    with Image.open(tampered_path) as tamp:
        img2 = tamp.convert("RGB")
        px = list(img2.getdata())
        px[0] = (255, 0, 0)
        tampered = Image.new("RGB", tamp.size)
        tampered.putdata(px)
        tampered.save(tampered_path, "JPEG")

    # Transplant the manifest from the signed image into the tampered one
    import subprocess
    manifest_json = subprocess.run(
        ["exiftool", "-XMP:Description", "-j", out_path],
        capture_output=True, text=True
    )
    import json
    raw = json.loads(manifest_json.stdout)[0].get("Description", "")
    subprocess.run(
        ["exiftool", f"-XMP:Description={raw}", "-overwrite_original", tampered_path],
        capture_output=True
    )

    result = verify_signed_image(tampered_path, pub_path)
    assert result["status"] == VerifyResult.TAMPERED


@skip_no_exiftool
def test_verify_unsigned_image_fails(sample_jpeg, key_pair):
    _, pub_path = key_pair
    result = verify_signed_image(sample_jpeg, pub_path)
    assert result["status"] == VerifyResult.INVALID_SIGNATURE


@skip_no_exiftool
def test_manifest_embedded_contains_correct_hash(sample_jpeg, key_pair, tmp_path):
    priv_path, pub_path = key_pair
    out_path = str(tmp_path / "signed.jpg")
    sign_result = sign_and_embed(sample_jpeg, priv_path, output_path=out_path)
    verify_result = verify_signed_image(out_path, pub_path)
    assert verify_result["manifest"]["integrity"]["pixelHash"] == sign_result["manifest"]["integrity"]["pixelHash"]
