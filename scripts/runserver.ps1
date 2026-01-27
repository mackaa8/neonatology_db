<#
Helper script to run the Django development server using repo venv.
Usage: .\scripts\runserver.ps1
#>
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found at $venvPython. Creating new venv..."
    python -m venv "$repoRoot\.venv"
}
Write-Host "Starting development server using venv Python: $venvPython"
& $venvPython "manage.py" runserver
