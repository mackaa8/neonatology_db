<#
Helper script to create a Django superuser via the venv python.
Usage: .\scripts\createsuperuser.ps1 --username admin --email admin@example.com
This script forwards any args directly to manage.py createsuperuser.
#>
Param(
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)
Set-StrictMode -Version Latest
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found at $venvPython. Creating new venv..."
    python -m venv "$repoRoot\.venv"
}
Write-Host "Running createsuperuser using venv Python: $venvPython"
& $venvPython "manage.py" createsuperuser @Args
