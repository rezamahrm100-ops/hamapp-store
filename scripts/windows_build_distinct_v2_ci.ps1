#requires -Version 5.1
# Build real GUI preview v2 from different source on an isolated hosted runner.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'Hosted Windows CI required'
}
& python scripts/build_windows_client_catalog.py
if ($LASTEXITCODE -ne 0) { throw 'Invalid Windows embedded catalogue' }
& python -m pip install --disable-pip-version-check pyinstaller==6.22.3
if ($LASTEXITCODE -ne 0) { throw 'Pinned PyInstaller unavailable' }
$entry = Join-Path $env:RUNNER_TEMP 'hamapp-v2-ci-entry.py'
& python scripts/windows_v2_native_ci_entry.py --entry $entry
if ($LASTEXITCODE -ne 0) { throw 'Could not create second source entry' }
$root = Join-Path $env:RUNNER_TEMP 'hamapp-distinct-exe-v2'
if (Test-Path -LiteralPath $root) { throw 'Refuse pre-existing second version work folder' }
New-Item -ItemType Directory -Path $root | Out-Null
$catalog = (Resolve-Path -LiteralPath 'dist/windows-client/windows-client-catalog.json').Path
& python -m PyInstaller --noconfirm --clean --onefile --windowed --name HamApp-Windows-V2-CI-ONLY --paths . --distpath (Join-Path $root 'dist') --workpath (Join-Path $root 'work') --specpath (Join-Path $root 'spec') --add-data "${catalog}:." $entry
if ($LASTEXITCODE -ne 0) { throw 'Second real Windows GUI executable build failed' }
$v2 = Join-Path $root 'dist/HamApp-Windows-V2-CI-ONLY.exe'
if (-not (Test-Path -LiteralPath $v2 -PathType Leaf)) { throw 'Second actual Windows EXE is missing' }
$sha1 = (Get-FileHash 'dist/HamApp-Windows-Preview.exe' -Algorithm SHA256).Hash
$sha2 = (Get-FileHash $v2 -Algorithm SHA256).Hash
if ($sha1 -eq $sha2) { throw 'Second EXE unexpectedly has original code bytes' }
Write-Output 'ACTUAL_DISTINCT_WINDOWS_PREVIEW_V2_COMPILED; NOT_PUBLIC_PRODUCTION'
