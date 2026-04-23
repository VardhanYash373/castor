"""Stage 1 — Verify a signed JPEG: re-hash pixels, check signature."""

import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from .keygen import load_public_key
from .sign import hash_pixels


class VerifyResult:
    VALID = "VALID"
    TAMPERED = "TAMPERED"
    INVALID_SIGNATURE = "INVALID_SIGNATURE"


def verify_image(
    image_path: str,
    pixel_hash: str,
    signature: str,
    public_key_path: str,
) -> dict:
    """
    Verify a signed JPEG against its stored manifest values.

    Steps:
        1. Re-hash the current pixel bytes
        2. Compare against the stored pixel_hash  → detects tampering
        3. Verify the ECDSA signature over the stored hash → detects forgery

    Returns a dict with:
        status   — VALID | TAMPERED | INVALID_SIGNATURE
        message  — human-readable explanation
        details  — dict of hashes for debugging
    """
    # Step 1: re-hash current pixels
    current_hash = hash_pixels(image_path)

    # Step 2: pixel integrity check
    if current_hash != pixel_hash:
        return {
            "status": VerifyResult.TAMPERED,
            "message": "Pixel data has been modified since signing.",
            "details": {
                "stored_hash": pixel_hash,
                "current_hash": current_hash,
            },
        }

    # Step 3: cryptographic signature check
    try:
        public_key = load_public_key(public_key_path)
        sig_bytes = base64.b64decode(signature)
        public_key.verify(
            sig_bytes,
            pixel_hash.encode(),
            ec.ECDSA(hashes.SHA256()),
        )
    except InvalidSignature:
        return {
            "status": VerifyResult.INVALID_SIGNATURE,
            "message": "Signature is invalid — manifest may have been forged.",
            "details": {"stored_hash": pixel_hash},
        }

    return {
        "status": VerifyResult.VALID,
        "message": "Image is authentic. Pixels and signature both verified.",
        "details": {"pixel_hash": pixel_hash},
    }


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 5:
        print(
            "Usage: python -m src.crypto.verify "
            "<image.jpg> <pixel_hash> <signature> <keys/public.pem>"
        )
        sys.exit(1)

    # Resolve to absolute paths so relative paths work from any cwd
    image_path = os.path.abspath(sys.argv[1])
    key_path = os.path.abspath(sys.argv[4])

    result = verify_image(image_path, sys.argv[2], sys.argv[3], key_path)
    print(json.dumps(result, indent=2))
