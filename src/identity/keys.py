"""
Cryptographic Identity Layer — Phase 7

ALGORITHM: secp256k1 (same curve used by Bitcoin and Ethereum)

KEY PAIR:
  private key  → 32-byte random number, kept secret
  public key   → 64-byte point on the elliptic curve, shared openly

WALLET ADDRESS (Ethereum-compatible):
  1. Take the 64-byte uncompressed public key (strip the 0x04 prefix byte)
  2. Hash with keccak256 → 32 bytes
  3. Take the last 20 bytes → wallet address

SIGNING:
  1. Hash the document with SHA-256 → 32-byte digest
  2. Sign the digest with the private key → DER-encoded signature
  3. Encode signature as hex for embedding in KYA proof field

VERIFICATION:
  1. Hash the document with SHA-256 → same 32-byte digest
  2. Verify the hex signature against the digest using the public key
  3. Returns True if the document is authentic and unmodified
"""

import hashlib
import json
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import utils as ec_utils
from Crypto.Hash import keccak


def load_or_create_private_key_from_file(key_file) -> ec.EllipticCurvePrivateKey:
    """Load private key from a .hex file, or generate and save a new one."""
    from pathlib import Path
    key_file = Path(key_file)
    key_file.parent.mkdir(exist_ok=True)
    if key_file.exists():
        return private_key_from_hex(key_file.read_text().strip())
    private_key = ec.generate_private_key(ec.SECP256K1())
    key_file.write_text(private_key_to_hex(private_key))
    key_file.chmod(0o600)
    return private_key


def generate_keypair() -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    """Generate a fresh secp256k1 key pair."""
    private_key = ec.generate_private_key(ec.SECP256K1())
    return private_key, private_key.public_key()


def private_key_to_hex(private_key: ec.EllipticCurvePrivateKey) -> str:
    """Serialize private key to hex string for storage (via PEM round-trip)."""
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem.hex()


def private_key_from_hex(hex_str: str) -> ec.EllipticCurvePrivateKey:
    """Deserialize private key from hex string."""
    pem = bytes.fromhex(hex_str)
    return serialization.load_pem_private_key(pem, password=None)


def public_key_to_hex(public_key: ec.EllipticCurvePublicKey) -> str:
    """Serialize public key to uncompressed hex (04 || x || y)."""
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return raw.hex()


def public_key_from_hex(hex_str: str) -> ec.EllipticCurvePublicKey:
    """Deserialize public key from uncompressed hex."""
    raw = bytes.fromhex(hex_str)
    return ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), raw)


def derive_wallet_address(public_key: ec.EllipticCurvePublicKey) -> str:
    """
    Derive an Ethereum-compatible wallet address from a public key.

    Steps:
      1. Get uncompressed public key bytes (65 bytes: 04 || x || y)
      2. Strip the 0x04 prefix → 64 bytes
      3. keccak256 hash → 32 bytes
      4. Take last 20 bytes → wallet address
    """
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    pubkey_bytes = raw[1:]  # strip 0x04 prefix

    k = keccak.new(digest_bits=256)
    k.update(pubkey_bytes)
    address_bytes = bytes.fromhex(k.hexdigest())[-20:]
    return "0x" + address_bytes.hex()


def _document_digest(doc: dict) -> bytes:
    """
    Produce a canonical SHA-256 digest of a document.
    Keys are sorted so the hash is deterministic regardless of insertion order.
    The 'proof' field is excluded so the signature covers the content, not itself.
    """
    doc_without_proof = {k: v for k, v in doc.items() if k != "proof"}
    canonical = json.dumps(doc_without_proof, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).digest()


def sign_document(doc: dict, private_key: ec.EllipticCurvePrivateKey) -> str:
    """
    Sign a document with the private key.
    Returns a hex-encoded DER signature.
    The 'proof' field is excluded from the signed content.
    SHA-256 digest is passed directly; the library signs it as a prehashed value.
    """
    digest    = _document_digest(doc)
    signature = private_key.sign(digest, ec.ECDSA(ec_utils.Prehashed(hashes.SHA256())))
    return signature.hex()


def verify_signature(doc: dict, signature_hex: str, public_key_hex: str) -> bool:
    """
    Verify a document signature.
    Returns True if the document is authentic and unmodified.
    Returns False if verification fails for any reason.
    """
    try:
        public_key = public_key_from_hex(public_key_hex)
        digest     = _document_digest(doc)
        signature  = bytes.fromhex(signature_hex)
        public_key.verify(signature, digest, ec.ECDSA(ec_utils.Prehashed(hashes.SHA256())))
        return True
    except (InvalidSignature, Exception):
        return False
