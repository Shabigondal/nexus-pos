"""
dev_tools/keygen.py
---------------------------------------------------------------------------
PRIVATE developer tool. Run this on YOUR OWN PC only.

NEVER:
  - put this file (or private_key.pem) inside the build / installer
  - send this folder to a client
  - commit private_key.pem to a public repo

What it does:
  1. First run: generates a fresh RSA keypair.
       - dev_tools/private_key.pem  -> stays on your PC forever. This is
         the ONLY thing that can create valid activation codes.
       - dev_tools/public_key.pem   -> safe to be public. Also gets
         auto-copied into modules/license_manager.py so the shipped app
         can verify codes (but never create them).
  2. Every run after that: asks for a client's Device ID (they send you
     this from the app's Activation screen) and prints back an
     Activation Code to send them.

Usage:
    python dev_tools/keygen.py
"""

import os
import sys
import base64

try:
    import rsa
except ImportError:
    print("This tool needs the 'rsa' package: pip install rsa")
    sys.exit(1)

DEV_TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DEV_TOOLS_DIR)
PRIVATE_KEY_PATH = os.path.join(DEV_TOOLS_DIR, "private_key.pem")
PUBLIC_KEY_PATH = os.path.join(DEV_TOOLS_DIR, "public_key.pem")
LICENSE_MANAGER_PATH = os.path.join(PROJECT_ROOT, "modules", "license_manager.py")

PLACEHOLDER = (
    "-----BEGIN RSA PUBLIC KEY-----\n"
    "PASTE_PUBLIC_KEY_HERE_RUN_DEV_TOOLS_KEYGEN_PY_FIRST\n"
    "-----END RSA PUBLIC KEY-----"
)


def ensure_keypair():
    """Generates the RSA keypair on first run only; reuses it after that."""
    if os.path.exists(PRIVATE_KEY_PATH) and os.path.exists(PUBLIC_KEY_PATH):
        with open(PUBLIC_KEY_PATH, "rb") as f:
            pubkey = rsa.PublicKey.load_pkcs1(f.read())
        with open(PRIVATE_KEY_PATH, "rb") as f:
            privkey = rsa.PrivateKey.load_pkcs1(f.read())
        return pubkey, privkey

    print("No keypair found - generating a new one (one-time setup)...")
    pubkey, privkey = rsa.newkeys(2048)

    with open(PRIVATE_KEY_PATH, "wb") as f:
        f.write(privkey.save_pkcs1())
    with open(PUBLIC_KEY_PATH, "wb") as f:
        f.write(pubkey.save_pkcs1())

    print(f"  Saved private key -> {PRIVATE_KEY_PATH}  (keep this safe, NEVER share it)")
    print(f"  Saved public key  -> {PUBLIC_KEY_PATH}")

    _sync_public_key_into_app(pubkey)
    return pubkey, privkey


def _sync_public_key_into_app(pubkey):
    """Writes the new public key into modules/license_manager.py automatically,
    so you don't have to copy-paste it by hand."""
    pem_text = pubkey.save_pkcs1().decode("utf-8").strip()

    if not os.path.exists(LICENSE_MANAGER_PATH):
        print(f"  ⚠ Could not find {LICENSE_MANAGER_PATH} to auto-update. "
              f"Paste this public key into PUBLIC_KEY_PEM manually:\n\n{pem_text}\n")
        return

    with open(LICENSE_MANAGER_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    if PLACEHOLDER not in content:
        print("  ⚠ modules/license_manager.py already has a public key set "
              "(placeholder not found) - left untouched.")
        return

    content = content.replace(PLACEHOLDER, pem_text)
    with open(LICENSE_MANAGER_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("  ✓ modules/license_manager.py updated automatically with the new public key.")


def generate_activation_code(privkey, device_id):
    signature = rsa.sign(device_id.encode("utf-8"), privkey, "SHA-256")
    encoded = base64.b32encode(signature).decode("utf-8").rstrip("=")
    # Pretty-print in dash groups of 6 — purely cosmetic, dashes/case are
    # normalized away automatically when the client pastes it into the app.
    return "-".join(encoded[i:i + 6] for i in range(0, len(encoded), 6))


def main():
    print("=" * 60)
    print(" Nexus POS — Activation Code Generator (PRIVATE TOOL)")
    print("=" * 60)

    pubkey, privkey = ensure_keypair()

    print()
    while True:
        device_id = input("Paste the client's Device ID (or 'q' to quit): ").strip()
        if device_id.lower() in ("q", "quit", "exit"):
            break
        if not device_id:
            continue

        code = generate_activation_code(privkey, device_id)
        print()
        print("  Activation Code (send this to the client):")
        print(f"  {code}")
        print()


if __name__ == "__main__":
    main()
