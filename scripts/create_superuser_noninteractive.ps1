<#
Wrapper to call `scripts/create_superuser.py` using the repo venv python.
Usage: .\scripts\create_superuser_noninteractive.ps1 --username <user> --email <email> --password <pass>
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
Write-Host "Running create_superuser script using venv Python: $venvPython"
& $venvPython (Join-Path $repoRoot 'scripts\create_superuser.py') @Args
