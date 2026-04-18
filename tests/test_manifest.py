"""Tests for Stage 2 - manifest build and XMP embed/read."""

import pytest
import shutil
from PIL import Image

from src.manifest.builder import (
    build_manifest,
    manifest_to_json,
    manifest_from_json,
    update_ledger_info,
    DigitalSourceType,
)

DUMMY_HASH = "a" * 64
DUMMY_SIG = "c2lnbmF0dXJl"


@pytest.fixture
def manifest():
    return build_manifest(
        pixel_hash=DUMMY_HASH,
        signature=DUMMY_SIG,
        image_path="samples/test.jpg",
    )


@pytest.fixture
def sample_jpeg(tmp_path):
    img = Image.new("RGB", (64, 64), color=(100, 149, 237))
    path = str(tmp_path / "sample.jpg")
    img.save(path, "JPEG")
    return path


def test_manifest_has_required_fields(manifest):
    assert manifest["schema"] == "chain-of-trust/v1"
    assert "id" in manifest
    assert "timestamp" in manifest
    assert manifest["integrity"]["pixelHash"] == DUMMY_HASH
    assert manifest["signature"]["value"] == DUMMY_SIG


def test_manifest_default_source_type(manifest):
    assert manifest["image"]["digitalSourceType"] == DigitalSourceType.CAMERA_CAPTURE


def test_manifest_ledger_initially_unanchored(manifest):
    assert manifest["ledger"]["anchored"] is False
    assert manifest["ledger"]["txHash"] is None


def test_manifest_serialise_roundtrip(manifest):
    json_str = manifest_to_json(manifest)
    restored = manifest_from_json(json_str)
    assert restored["integrity"]["pixelHash"] == DUMMY_HASH
    assert restored["signature"]["value"] == DUMMY_SIG


def test_update_ledger_info(manifest):
    updated = update_ledger_info(manifest, tx_hash="0xabc123", provider="mock")
    assert updated["ledger"]["anchored"] is True
    assert updated["ledger"]["txHash"] == "0xabc123"
    assert manifest["ledger"]["anchored"] is False


def test_manifest_unique_ids():
    m1 = build_manifest(DUMMY_HASH, DUMMY_SIG, "a.jpg")
    m2 = build_manifest(DUMMY_HASH, DUMMY_SIG, "a.jpg")
    assert m1["id"] != m2["id"]


exiftool_available = shutil.which("exiftool") is not None
skip_no_exiftool = pytest.mark.skipif(not exiftool_available, reason="exiftool not installed")


@skip_no_exiftool
def test_embed_and_read_manifest(sample_jpeg, manifest, tmp_path):
    from src.manifest.embed import embed_manifest, read_manifest
    out_path = str(tmp_path / "signed.jpg")
    embed_manifest(sample_jpeg, manifest, output_path=out_path)
    recovered = read_manifest(out_path)
    assert recovered["integrity"]["pixelHash"] == DUMMY_HASH
    assert recovered["signature"]["value"] == DUMMY_SIG
    assert recovered["schema"] == "chain-of-trust/v1"


@skip_no_exiftool
def test_has_manifest_true(sample_jpeg, manifest, tmp_path):
    from src.manifest.embed import embed_manifest, has_manifest
    out_path = str(tmp_path / "signed.jpg")
    embed_manifest(sample_jpeg, manifest, output_path=out_path)
    assert has_manifest(out_path) is True


@skip_no_exiftool
def test_has_manifest_false_on_unsigned(sample_jpeg):
    from src.manifest.embed import has_manifest
    assert has_manifest(sample_jpeg) is False


@skip_no_exiftool
def test_read_manifest_raises_on_unsigned(sample_jpeg):
    from src.manifest.embed import read_manifest
    with pytest.raises(ValueError, match="No manifest found"):
        read_manifest(sample_jpeg)
