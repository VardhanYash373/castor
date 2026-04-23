"""Stage 1 — Key pair generation (ECDSA P-256)."""

import os
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


def _default_keys_dir() -> str:
    """Resolve keys/ relative to cwd (i.e. the project root)."""
    return os.path.join(os.getcwd(), "keys")


def generate_key_pair(keys_dir: str = None) -> tuple[str, str]:
    """
    Generate an ECDSA P-256 key pair and save to disk.

    Returns:
        (private_key_path, public_key_path)
    """
    if keys_dir is None:
        keys_dir = _default_keys_dir()

    os.makedirs(keys_dir, exist_ok=True)

    private_key = ec.generate_private_key(ec.SECP256R1())

    # Serialize private key (PEM, unencrypted)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    # Serialize public key (PEM)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path = os.path.join(keys_dir, "private.pem")
    pub_path = os.path.join(keys_dir, "public.pem")

    with open(priv_path, "wb") as f:
        f.write(private_pem)
    with open(pub_path, "wb") as f:
        f.write(public_pem)

    print(f"[keygen] Private key → {priv_path}")
    print(f"[keygen] Public key  → {pub_path}")

    return priv_path, pub_path


def load_private_key(path: str):
    """Load a PEM private key from disk."""
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


def load_public_key(path: str):
    """Load a PEM public key from disk."""
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


if __name__ == "__main__":
    generate_key_pair()
