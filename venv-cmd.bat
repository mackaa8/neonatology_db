@echo off
REM PowerShell wrapper to activate venv and run a Django command
REM Usage: venv-cmd.bat migrate
REM        venv-cmd.bat runserver

setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found. Creating...
    python -m venv .venv
)

".venv\Scripts\python.exe" manage.py %*
