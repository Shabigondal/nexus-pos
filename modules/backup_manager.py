"""
Backup & Restore Manager
-------------------------
- Local Backup: copies the live SQLite database (.db) to any location chosen
  by the user via a save dialog (works with synced folders too, e.g. Google
  Drive Desktop, OneDrive, Dropbox folders).
- Restore: lets the user pick a previously saved .db file and replaces the
  live database with it (a safety copy of the current DB is kept first).
- Google Drive Upload: uses Google OAuth (Drive API) to upload the backup
  file directly to the user's own Google Drive, inside a folder named
  "Nexus POS Backups".
"""

import os
import io
import shutil
from datetime import datetime
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

from database.db_manager import DB_PATH

# Google Drive optional dependencies. The app must still run if these
# packages are not installed; the Drive button will show a helpful message.
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    import pickle
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False

# --------------------------------------------------------------------------
# Google Drive configuration
# --------------------------------------------------------------------------
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
CREDENTIALS_FILE = "drive_credentials.json"   # OAuth client secret, provided by the app owner
TOKEN_FILE = "drive_token.pickle"             # stores the user's authorized session
DRIVE_BACKUP_FOLDER_NAME = "Nexus POS Backups"
LIVE_SYNC_FILE_NAME = "nexus_live_database.db"  # single file that auto-sync keeps updating


def default_backup_filename():
    """Generates a timestamped backup filename, e.g. nexus_backup_2026-06-14_153000.db"""
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return f"nexus_backup_{stamp}.db"


# --------------------------------------------------------------------------
# LOCAL BACKUP (Save / Download)
# --------------------------------------------------------------------------
def backup_to_local(parent_window=None):
    """
    Opens a 'Save As' dialog so the user can choose any folder
    (including a Google Drive / OneDrive sync folder) and saves
    a full copy of the live database there.

    Returns the saved file path, or None if cancelled / failed.
    """
    if not os.path.exists(DB_PATH):
        messagebox.showerror("Backup Failed", "Database file not found.")
        return None

    suggested_name = default_backup_filename()

    save_path = filedialog.asksaveasfilename(
        parent=parent_window,
        title="Save Backup As",
        initialfile=suggested_name,
        defaultextension=".db",
        filetypes=(("Database Backup", "*.db"), ("All Files", "*.*")),
    )

    if not save_path:
        return None  # user cancelled

    try:
        shutil.copy2(DB_PATH, save_path)
        messagebox.showinfo("Backup Successful", f"Backup saved to:\n{save_path}")
        return save_path
    except Exception as e:
        messagebox.showerror("Backup Failed", f"Could not save backup:\n{e}")
        return None


# --------------------------------------------------------------------------
# RESTORE (Import)
# --------------------------------------------------------------------------
def restore_from_local(parent_window=None, on_restored=None):
    """
    Lets the user pick a .db backup file and restores it as the live
    database. A safety copy of the current database is made first
    (billing_system.db.before_restore).

    on_restored: optional callback called after a successful restore,
    useful to prompt the user to restart the app.
    """
    file_path = filedialog.askopenfilename(
        parent=parent_window,
        title="Select Backup File to Restore",
        filetypes=(("Database Backup", "*.db"), ("All Files", "*.*")),
    )

    if not file_path:
        return False  # user cancelled

    if not os.path.exists(file_path):
        messagebox.showerror("Restore Failed", "Selected file does not exist.")
        return False

    confirm = messagebox.askyesno(
        "Confirm Restore",
        "This will replace ALL current data with the selected backup.\n\n"
        "A safety copy of your current data will be kept.\n\n"
        "Continue?"
    )
    if not confirm:
        return False

    try:
        # Keep a safety copy of the current (live) database first
        if os.path.exists(DB_PATH):
            safety_path = DB_PATH + ".before_restore"
            shutil.copy2(DB_PATH, safety_path)

        # Replace live database with the chosen backup
        shutil.copy2(file_path, DB_PATH)

        messagebox.showinfo(
            "Restore Successful",
            "Backup restored successfully.\n\n"
            "Please restart the application for all changes to take effect."
        )

        if on_restored:
            on_restored()

        return True
    except Exception as e:
        messagebox.showerror("Restore Failed", f"Could not restore backup:\n{e}")
        return False


# --------------------------------------------------------------------------
# GOOGLE DRIVE UPLOAD
# --------------------------------------------------------------------------
def _get_drive_service():
    """
    Handles Google OAuth login and returns an authorized Drive API service.
    On first run, opens a browser window for the user to sign in to their
    own Google account. The session token is saved locally for next time.
    """
    if not GOOGLE_LIBS_AVAILABLE:
        raise RuntimeError(
            "Google Drive support is not installed.\n\n"
            "Please install required packages:\n"
            "pip install google-auth-oauthlib google-api-python-client"
        )

    if not os.path.exists(CREDENTIALS_FILE):
        raise RuntimeError(
            f"'{CREDENTIALS_FILE}' not found.\n\n"
            "This file is needed once to enable Google Drive uploads. "
            "Contact the app developer to provide this file, then place it "
            "in the application folder."
        )

    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("drive", "v3", credentials=creds)


def _get_or_create_backup_folder(service):
    """Finds (or creates) the 'Nexus POS Backups' folder in the user's Drive."""
    query = (
        f"name='{DRIVE_BACKUP_FOLDER_NAME}' and "
        "mimeType='application/vnd.google-apps.folder' and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get("files", [])

    if folders:
        return folders[0]["id"]

    folder_metadata = {
        "name": DRIVE_BACKUP_FOLDER_NAME,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]


def _find_file_in_folder(service, folder_id, filename):
    """Returns the file ID of `filename` inside `folder_id`, or None if not found."""
    query = (
        f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def sync_db_to_drive():
    """
    Keeps a SINGLE live copy of the database ('nexus_live_database.db') inside
    'Nexus POS Backups' on the user's Google Drive, always up to date.

    - If the file already exists on Drive -> its content is overwritten/updated.
    - If it does not exist yet -> it is created.

    Intended to run silently in the background (e.g. every 24 hours) without
    showing popups. Returns True on success, False otherwise (errors are
    swallowed so a failed sync never disrupts the app).
    """
    try:
        if not os.path.exists(DB_PATH):
            return False

        if not GOOGLE_LIBS_AVAILABLE or not os.path.exists(CREDENTIALS_FILE):
            return False

        if not os.path.exists(TOKEN_FILE):
            # No saved session yet -> user must connect manually first
            # (avoid popping up a browser login window in the background)
            return False

        service = _get_drive_service()
        folder_id = _get_or_create_backup_folder(service)

        existing_file_id = _find_file_in_folder(service, folder_id, LIVE_SYNC_FILE_NAME)

        with open(DB_PATH, "rb") as f:
            file_bytes = f.read()
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="application/octet-stream", resumable=False)

        if existing_file_id:
            # Update the existing file's content in place (same file, new data)
            service.files().update(fileId=existing_file_id, media_body=media).execute()
        else:
            # First time -> create the live sync file
            file_metadata = {
                "name": LIVE_SYNC_FILE_NAME,
                "parents": [folder_id],
            }
            service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        return True

    except Exception:
        return False


def upload_to_drive(parent_window=None, local_file_path=None):
    """
    Uploads a backup file to the user's Google Drive, inside a
    'Nexus POS Backups' folder.

    If local_file_path is not provided, a fresh backup of the live
    database is created first.

    Returns True on success, False otherwise.
    """
    try:
        # If no specific file given, create a fresh backup in a temp location
        if not local_file_path:
            if not os.path.exists(DB_PATH):
                messagebox.showerror("Upload Failed", "Database file not found.")
                return False

            local_file_path = default_backup_filename()
            shutil.copy2(DB_PATH, local_file_path)
            cleanup_temp = True
        else:
            cleanup_temp = False

        service = _get_drive_service()
        folder_id = _get_or_create_backup_folder(service)

        file_metadata = {
            "name": os.path.basename(local_file_path),
            "parents": [folder_id],
        }

        # Read the file fully into memory first. On Windows, MediaFileUpload can keep
        # a file handle open even after .execute() returns, which causes
        # "WinError 32: process cannot access the file" when we try to delete the
        # temp backup right afterwards. Using an in-memory buffer avoids that.
        with open(local_file_path, "rb") as f:
            file_bytes = f.read()

        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype="application/octet-stream", resumable=False)

        service.files().create(body=file_metadata, media_body=media, fields="id").execute()

        messagebox.showinfo(
            "Upload Successful",
            f"Backup uploaded to your Google Drive\n"
            f"in folder: '{DRIVE_BACKUP_FOLDER_NAME}'"
        )

        if cleanup_temp and os.path.exists(local_file_path):
            try:
                os.remove(local_file_path)
            except OSError:
                pass  # non-critical: temp file will just remain on disk

        return True

    except RuntimeError as e:
        messagebox.showwarning("Google Drive Setup Required", str(e))
        return False
    except Exception as e:
        messagebox.showerror("Upload Failed", f"Could not upload to Google Drive:\n{e}")
        return False