"""Stage 2 — Embed / extract manifest via JPEG XMP metadata (PyExifTool)."""

import os
import shutil
import subprocess
import json

from .builder import manifest_to_json, manifest_from_json


def _exiftool(*args) -> subprocess.CompletedProcess:
    cmd = ["exiftool", *args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode not in (0, 1):
        raise RuntimeError(f"exiftool error: {result.stderr.strip()}")
    return result


def embed_manifest(image_path: str, manifest: dict, output_path: str = None) -> str:
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_signed{ext}"

    shutil.copy2(image_path, output_path)
    manifest_json = manifest_to_json(manifest)

    _exiftool(
        f"-XMP:Description={manifest_json}",
        "-overwrite_original",
        output_path,
    )

    print(f"[embed] Manifest embedded -> {output_path}")
    return output_path


def read_manifest(image_path: str) -> dict:
    result = _exiftool("-XMP:Description", "-j", image_path)

    try:
        data = json.loads(result.stdout)
        raw = data[0].get("Description", "")
    except (json.JSONDecodeError, IndexError, KeyError):
        raise ValueError(f"No manifest found in {image_path}")

    if not raw:
        raise ValueError(f"No manifest found in {image_path}")

    try:
        return manifest_from_json(raw)
    except json.JSONDecodeError:
        raise ValueError(f"Manifest in {image_path} is not valid JSON")


def has_manifest(image_path: str) -> bool:
    try:
        read_manifest(image_path)
        return True
    except ValueError:
        return False
