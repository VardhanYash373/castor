"""Stage 1 — Sign a JPEG: hash pixels, sign with private key."""

import os
import hashlib
import base64
from PIL import Image
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from .keygen import load_private_key


def hash_pixels(image_path: str) -> str:
    """
    Extract raw pixel bytes from a JPEG and return a SHA-256 hex digest.
    Uses raw pixel data only — ignores all metadata so the hash is
    purely a function of visual content.
    """
    with Image.open(image_path) as img:
        img = img.convert("RGB")  # normalise mode
        pixel_bytes = img.tobytes()
    return hashlib.sha256(pixel_bytes).hexdigest()


def sign_hash(pixel_hash: str, private_key_path: str) -> str:
    """
    Sign a hex pixel hash with the ECDSA private key.

    Returns:
        Base64-encoded DER signature string.
    """
    private_key = load_private_key(private_key_path)
    signature_bytes = private_key.sign(
        pixel_hash.encode(),
        ec.ECDSA(hashes.SHA256()),
    )
    return base64.b64encode(signature_bytes).decode()


def sign_image(image_path: str, private_key_path: str) -> dict:
    """
    Hash the pixel data of a JPEG and sign it.

    Returns a dict with:
        pixel_hash  — SHA-256 hex digest of raw pixel bytes
        signature   — base64 ECDSA signature over the hash
    """
    pixel_hash = hash_pixels(image_path)
    signature = sign_hash(pixel_hash, private_key_path)

    print(f"[sign] Image      : {image_path}")
    print(f"[sign] Pixel hash : {pixel_hash}")
    print(f"[sign] Signature  : {signature[:40]}...")

    return {"pixel_hash": pixel_hash, "signature": signature}


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python -m src.crypto.sign <image.jpg> <keys/private.pem>")
        sys.exit(1)

    # Resolve to absolute paths so relative paths work from any cwd
    image_path = os.path.abspath(sys.argv[1])
    key_path = os.path.abspath(sys.argv[2])

    result = sign_image(image_path, key_path)
    print(result)
