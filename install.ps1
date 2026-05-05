param(
  [string]$Repo = ""
)

$ErrorActionPreference = "Stop"

if ($Repo) {
  $repo = (Resolve-Path -LiteralPath $Repo).Path
} else {
  $repo = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$cli = Join-Path $repo "packages\cli"
$bin = Join-Path $env:USERPROFILE ".remnant\bin"
$cmd = Join-Path $bin "remnant.cmd"

if (-not (Test-Path -LiteralPath (Join-Path $cli "pyproject.toml"))) {
  Write-Error "Cannot find packages\cli\pyproject.toml under $repo. Pass the repo path with -Repo `"C:\path\to\remnant`"."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
  Write-Error "uv is required. Install it first: https://docs.astral.sh/uv/getting-started/installation/"
}

New-Item -ItemType Directory -Force -Path $bin | Out-Null

@"
@echo off
uv run --no-project --with typer --with-editable "$cli" remnant %*
"@ | Set-Content -LiteralPath $cmd -Encoding ASCII

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (($userPath -split ";") -notcontains $bin) {
  [Environment]::SetEnvironmentVariable("Path", "$userPath;$bin", "User")
  Write-Output "Added $bin to your user PATH. Open a new Command Prompt before running remnant."
} else {
  Write-Output "$bin is already in your user PATH."
}

Write-Output "Installed remnant command: $cmd"
Write-Output "Try: remnant --help"
