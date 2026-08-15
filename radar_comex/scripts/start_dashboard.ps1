$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
}

$Backend = Start-Job -ScriptBlock {
  param($ProjectRoot)
  Set-Location $ProjectRoot
  .\.venv\Scripts\python.exe -m uvicorn src.web.app:app --host 127.0.0.1 --port 8000
} -ArgumentList $Root

Set-Location "$Root\dashboard"
if (-not (Test-Path "node_modules")) {
  npm.cmd install
}
try {
  npm.cmd run dev
} finally {
  Stop-Job $Backend -ErrorAction SilentlyContinue
  Remove-Job $Backend -ErrorAction SilentlyContinue
}
