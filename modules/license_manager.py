"""
modules/license_manager.py
---------------------------------------------------------------------------
Locks the app to a single activated device (single-PC activation).

How it works (asymmetric / public-key signing — same idea as software
license keys used by most commercial desktop apps):

  - The developer keeps a PRIVATE key on their own PC only, inside
    dev_tools/ (never shipped to clients, never part of the build).
  - This file only ships with the PUBLIC key, which can verify a code
    but cannot be used to *create* one. Even if a client fully
    decompiles the .exe, they cannot forge a valid activation code.

Flow:
  1. App computes a Device ID fingerprint for the current PC.
  2. Developer runs dev_tools/keygen.py with that Device ID -> gets back
     an Activation Code, and sends it to the client.
  3. Client pastes the Activation Code into the app once. If it's a
     valid signature for THIS device's ID, it's saved locally and the
     app unlocks permanently on this PC.
  4. If the same install is copied to a different PC, the Device ID
     changes, the old code no longer matches, and activation is
     required again.
"""

import os
import sys
import json
import base64
import hashlib

try:
    import winreg
except ImportError:
    winreg = None

try:
    import rsa
    RSA_AVAILABLE = True
except ImportError:
    RSA_AVAILABLE = False

# ---------------------------------------------------------------------------
# PUBLIC KEY — safe to ship. Generated once by dev_tools/keygen.py, which
# automatically writes the matching key here. Do NOT hand-edit.
# ---------------------------------------------------------------------------
PUBLIC_KEY_PEM = """-----BEGIN RSA PUBLIC KEY-----
MIIBCgKCAQEAkG/xnT4Z2N0SQRvRncO6gAUAvkjoUYVRcYwRD566ByFnCEMB/sWN
W7USjuTyeIMKdbU/MHzr1bFNQA7SSNnANmU/JT3hs5GD36UjbzPnIKd5KHdbXJ3x
x+aEJBzcXCjSxg76eVNGDEzA6AHIionpDQu8JqHM29fYjeCTEplPHQh3/EN+nblO
4b3tgoA3yhh8oCvzmJGsnBCXDmlAmrm73w3ndS0Kl+0Telay8fuxNGBDe/e14fwl
kq11NrmVDTuxjqrN3bTa6WX0d0p6LPDMykUXT+pVbW+zSJNOH3iiMHsRp6QL2CZO
/Q7/ITdyA/+jzCYutSJuMPO4vnsV84+hWwIDAQAB
-----END RSA PUBLIC KEY-----"""


def _user_data_dir():
    """Writable per-user folder (same location backup_manager.py uses)."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "NexusPOS")
    os.makedirs(path, exist_ok=True)
    return path


LICENSE_FILE = os.path.join(_user_data_dir(), "license.dat")


# ---------------------------------------------------------------------------
# Device fingerprint
# ---------------------------------------------------------------------------
def get_device_id():
    """
    Returns a stable, human-shareable fingerprint for this PC.
    Primary source: Windows' own per-install MachineGuid (set once by
    Windows itself, survives reboots, doesn't need admin rights to read).
    Falls back to a MAC-address-based ID on non-Windows / if unavailable,
    so the app never crashes even off-target during development.
    """
    raw = None
    if winreg is not None:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography")
            raw, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
        except OSError:
            raw = None

    if not raw:
        import uuid
        raw = str(uuid.getnode())

    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()[:20]
    # Format as readable groups: XXXX-XXXX-XXXX-XXXX-XXXX
    return "-".join(digest[i:i + 4] for i in range(0, len(digest), 4))


# ---------------------------------------------------------------------------
# Verification (client side — only needs the PUBLIC key)
# ---------------------------------------------------------------------------
def _load_public_key():
    return rsa.PublicKey.load_pkcs1(PUBLIC_KEY_PEM.encode("utf-8"))


def _verify_code(device_id, code):
    """True only if `code` is a valid signature of `device_id` for our public key."""
    if not RSA_AVAILABLE:
        return False
    try:
        raw = code.strip().upper().replace("-", "").replace(" ", "")
        padding = "=" * (-len(raw) % 8)
        signature = base64.b32decode(raw + padding)
        pubkey = _load_public_key()
        rsa.verify(device_id.encode("utf-8"), signature, pubkey)
        return True
    except Exception:
        return False


def is_activated():
    """Checks the saved license file against THIS device's current ID."""
    if not os.path.exists(LICENSE_FILE):
        return False
    try:
        with open(LICENSE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("device_id") != get_device_id():
            return False
        return _verify_code(data["device_id"], data["code"])
    except Exception:
        return False


def activate_with_code(code):
    """Validates a user-entered code against this device. Saves it on success."""
    device_id = get_device_id()
    if not _verify_code(device_id, code):
        return False
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump({"device_id": device_id, "code": code.strip()}, f)
    return True
