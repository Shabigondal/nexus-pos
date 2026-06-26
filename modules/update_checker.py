"""
Update Checker
----------------
Shared logic for checking the latest GitHub release version against the
currently installed version (CURRENT_VERSION). Used both for the silent
startup check (popup if a new version is found) and the manual
"Check for Software Update" button in Settings.
"""

import requests

CURRENT_VERSION = "v1.3.0"
GITHUB_REPO_URL = "https://api.github.com/repos/Shabigondal/nexus-pos/releases/latest"


def check_for_update(timeout=5):
    """
    Checks GitHub for the latest release.

    Returns a dict:
        {
            "status": "update_available" | "up_to_date" | "error",
            "latest_version": str or None,
            "download_url": str or None,   # direct link to the Setup.exe asset, if found
            "release_url": str or None,    # link to the GitHub release page
            "message": str                 # human-readable status message
        }
    """
    try:
        response = requests.get(GITHUB_REPO_URL, timeout=timeout)
        if response.status_code != 200:
            return {
                "status": "error",
                "latest_version": None,
                "download_url": None,
                "release_url": None,
                "message": "Update server unreachable. Running in offline mode.",
            }

        data = response.json()
        latest_version = data.get("tag_name", CURRENT_VERSION)
        release_url = data.get("html_url")

        # Try to find a Setup.exe asset for direct download
        download_url = None
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.lower().endswith(".exe"):
                download_url = asset.get("browser_download_url")
                break

        if latest_version != CURRENT_VERSION:
            return {
                "status": "update_available",
                "latest_version": latest_version,
                "download_url": download_url,
                "release_url": release_url,
                "message": f"New version available: {latest_version} (current: {CURRENT_VERSION})",
            }
        else:
            return {
                "status": "up_to_date",
                "latest_version": latest_version,
                "download_url": download_url,
                "release_url": release_url,
                "message": "You are running the latest version.",
            }

    except Exception:
        return {
            "status": "error",
            "latest_version": None,
            "download_url": None,
            "release_url": None,
            "message": "Could not check for updates. Check your internet connection.",
        }
