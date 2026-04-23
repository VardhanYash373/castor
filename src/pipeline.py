"""Stage 3 - Full sign and verify pipeline."""

import os
from src.crypto.keygen import generate_key_pair, load_private_key, load_public_key
from src.crypto.sign import sign_image
from src.crypto.verify import verify_image, VerifyResult
from src.manifest.builder import build_manifest
from src.manifest.embed import embed_manifest, read_manifest


def sign_and_embed(
    image_path: str,
    private_key_path: str,
    output_path: str = None,
    author: str = "chain-of-trust",
) -> dict:
    """
    Full sign pipeline:
        1. Hash pixels + ECDSA sign
        2. Build manifest
        3. Embed manifest into JPEG XMP metadata

    Returns:
        dict with output_path and manifest
    """
    image_path = os.path.abspath(image_path)
    private_key_path = os.path.abspath(private_key_path)

    print(f"[pipeline] Signing: {image_path}")

    # Stage 1: crypto
    signed = sign_image(image_path, private_key_path)

    # Stage 2: manifest
    manifest = build_manifest(
        pixel_hash=signed["pixel_hash"],
        signature=signed["signature"],
        image_path=image_path,
        author=author,
    )

    # Stage 2: embed
    out = embed_manifest(image_path, manifest, output_path=output_path)

    print(f"[pipeline] Done. Signed image -> {out}")
    return {"output_path": out, "manifest": manifest}


def verify_signed_image(
    image_path: str,
    public_key_path: str,
) -> dict:
    """
    Full verify pipeline:
        1. Extract manifest from XMP metadata
        2. Re-hash pixels and compare
        3. Verify ECDSA signature

    Returns:
        dict with status, message, and manifest details
    """
    image_path = os.path.abspath(image_path)
    public_key_path = os.path.abspath(public_key_path)

    print(f"[pipeline] Verifying: {image_path}")

    # Extract manifest
    try:
        manifest = read_manifest(image_path)
    except ValueError as e:
        return {
            "status": VerifyResult.INVALID_SIGNATURE,
            "message": str(e),
            "manifest": None,
        }

    # Verify
    result = verify_image(
        image_path=image_path,
        pixel_hash=manifest["integrity"]["pixelHash"],
        signature=manifest["signature"]["value"],
        public_key_path=public_key_path,
    )

    result["manifest"] = manifest
    print(f"[pipeline] Result: {result['status']} — {result['message']}")
    return result


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Sign:   python -m src.pipeline sign <image.jpg> <keys/private.pem>")
        print("  Verify: python -m src.pipeline verify <image.jpg> <keys/public.pem>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "sign":
        if len(sys.argv) < 4:
            print("Usage: python -m src.pipeline sign <image.jpg> <keys/private.pem>")
            sys.exit(1)
        result = sign_and_embed(sys.argv[2], sys.argv[3])
        print(json.dumps({"output": result["output_path"]}, indent=2))

    elif cmd == "verify":
        if len(sys.argv) < 4:
            print("Usage: python -m src.pipeline verify <image.jpg> <keys/public.pem>")
            sys.exit(1)
        result = verify_signed_image(sys.argv[2], sys.argv[3])
        print(json.dumps({
            "status": result["status"],
            "message": result["message"],
        }, indent=2))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
