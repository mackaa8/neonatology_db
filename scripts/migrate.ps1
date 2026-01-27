<#
PowerShell helper to run Django migrations using the repository virtual environment.
Usage: .\scripts\migrate.ps1
#>
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found at $venvPython. Creating new venv..."
    python -m venv "$repoRoot\.venv"
}
Write-Host "Running migrations using venv Python: $venvPython"
& $venvPython "manage.py" makemigrations
& $venvPython "manage.py" migrate
