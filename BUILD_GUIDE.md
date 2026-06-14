# Nexus POS - Build & Distribution Guide

This guide explains how to turn this project into a professional Windows
installer (`NexusPOS_Setup.exe`) that any user can install with one click -
no Python, no pip, nothing extra required on their PC.

---

## Overview of the process

```
Your code (Python)
        |
        v
  PyInstaller  -->  dist/NexusPOS/  (a folder with NexusPOS.exe + all dependencies)
        |
        v
  Inno Setup   -->  Output/NexusPOS_Setup.exe  (the installer you send to users)
```

You only need to do this on **your** Windows PC. The end user just runs
`NexusPOS_Setup.exe` and clicks Next/Next/Install/Finish.

---

## One-time setup (only the first time)

1. **Install Python** (3.10+) if not already installed - https://python.org
2. **Install Inno Setup** (free) - https://jrsoftware.org/isdl.php
   - Just download and install it normally. You'll use its GUI compiler.

---

## Step 1 - Build the EXE (PyInstaller)

Open a terminal/PowerShell in the project folder (`apafixedfinal`) and run:

```bash
build_exe.bat
```

This will:
- Install all required Python packages from `requirements.txt` + PyInstaller
- Build a standalone app folder at `dist\NexusPOS\`
- The main file inside is `dist\NexusPOS\NexusPOS.exe`

You can test it right now by double-clicking `dist\NexusPOS\NexusPOS.exe` -
it should run exactly like `python main.py`, but without needing Python
installed.

---

## Step 2 - Build the Installer (Inno Setup)

1. Open **Inno Setup Compiler**.
2. File -> Open -> select `installer.iss` (in the project folder).
3. Click the green **Compile** (Run/Play) button.
4. When it finishes, you'll find:

   ```
   Output\NexusPOS_Setup.exe
   ```

This single file is what you send to users / upload to GitHub Releases.

---

## Step 3 - What the user experience looks like

The user double-clicks `NexusPOS_Setup.exe`:
1. Setup wizard opens (modern style, with your app icon)
2. Click Next -> Next -> Install
3. Optional desktop shortcut gets created
4. App launches automatically at the end (optional, can be unchecked)
5. Start Menu entry "Nexus POS" + "Uninstall Nexus POS" are created

No Python, no pip, no extra downloads. Everything (customtkinter, openpyxl,
tkcalendar, xhtml2pdf, Google Drive libs, etc.) is bundled inside the exe.

---

## Step 4 - Pushing updates to GitHub & Releases

Whenever you make code changes:

```bash
git add .
git commit -m "Describe your changes"
git push
```

Then create a new **Release** on GitHub so the in-app "Check for Software
Update" button can detect it:

1. Go to https://github.com/Shabigondal/nexus-pos
2. Click "Releases" (right sidebar) -> "Create a new release" / "Draft a new release"
3. Tag version: e.g. `v1.0.1` (must start with `v` and be higher than the
   `CURRENT_VERSION` in `main.py`)
4. Title: whatever you like, e.g. "Version 1.0.1 - Bug fixes"
5. Re-run Step 1 and Step 2 above to produce a fresh `NexusPOS_Setup.exe`
6. Attach `NexusPOS_Setup.exe` to the release (drag & drop into the
   "Attach binaries" area)
7. Click "Publish release"

Users with the older version will see an update notification when they
click "Check for Software Update" in System Configuration, and can
download the new `NexusPOS_Setup.exe` to upgrade (running it again will
overwrite the app files while keeping their database/backups).

---

## Notes & Tips

- **User data safety**: `billing_system.db`, `database/pos_system.db`,
  `products.xlsx`, and `khata.xlsx` are created automatically on first run,
  inside the install folder. Re-running the installer (to update) will NOT
  delete these files - only the app's program files get replaced.

- **Antivirus warnings**: PyInstaller-built exes are sometimes flagged by
  Windows Defender / antivirus as "unknown publisher" (false positive,
  common for unsigned new exes). This is normal for unsigned software. If
  you want to avoid this long-term, you can purchase a code-signing
  certificate and sign `NexusPOS.exe` and `NexusPOS_Setup.exe` - optional,
  not required for the app to work.

- **First run**: On first run, the app shows the "Initial System Deployment"
  / registration screen (since no admin user exists yet in the fresh
  `billing_system.db`).

- **Updating the version number**: When releasing a new version, also update
  `CURRENT_VERSION = "v1.0.0"` in `main.py` to match your new GitHub release
  tag, then rebuild (Steps 1-2) before publishing.

- **Where things install**: By default, `installer.iss` is configured with
  `PrivilegesRequired=lowest`, so it installs to the user's local app data
  folder without needing Administrator rights. This avoids permission
  issues when the app writes to its own database files.
