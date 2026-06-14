@echo off
REM ============================================================
REM  Nexus POS - Build Script
REM  Builds the standalone EXE using PyInstaller.
REM  Run this from the project root folder (apafixedfinal).
REM ============================================================

echo.
echo === Step 1: Installing/updating dependencies ===
pip install -r requirements.txt
pip install pyinstaller

echo.
echo === Step 2: Cleaning old build folders ===
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo === Step 3: Building NexusPOS.exe with PyInstaller ===
pyinstaller nexus_pos.spec

echo.
echo ============================================================
echo  BUILD COMPLETE
echo  Output folder: dist\NexusPOS\
echo  Main executable: dist\NexusPOS\NexusPOS.exe
echo.
echo  Next step: run build_installer.bat to create the Setup.exe
echo ============================================================
pause
