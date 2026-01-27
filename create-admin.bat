@echo off
REM Batch wrapper to run create_superuser.py non-interactively
REM Usage: create-admin.bat --username myadmin --email admin@example.com --password mypass

setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating...
    python -m venv .venv
)

".venv\Scripts\python.exe" scripts\create_superuser.py %*
