# Creates a new repo-scoped runner only. Does not modify existing runners.
param([switch]$StartAfterRegister)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Report = Join-Path $Root 'RUNNER-RESULTS.txt'
try {
  if (-not (Get-Command gh -ErrorAction SilentlyContinue)) { throw 'GitHub CLI is not installed. Run HamApp-SETUP.cmd first.' }
  $repo = (gh repo view --json nameWithOwner -q '.nameWithOwner' 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $repo -or $repo -notmatch '^[A-Za-z0-9-]+/[A-Za-z0-9_.-]+$') {throw 'Cannot identify GitHub repository. Run from the initialized HamApp project folder.'}
  $folder = Join-Path $env:LOCALAPPDATA ('HamAppStore\runner-' + [guid]::NewGuid().ToString('N').Substring(0,8))
  New-Item -ItemType Directory -Path $folder -Force | Out-Null
  $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/actions/runner/releases/latest' -Headers @{ 'User-Agent'='HamApp-Setup'; 'Accept'='application/vnd.github+json' }
  $asset = @($release.assets | Where-Object { $_.name -match '^actions-runner-win-x64-.*\.zip$' } | Select-Object -First 1)
  if ($asset.Count -ne 1) { throw 'Cannot find official win-x64 runner asset.' }
  if (-not $asset[0].digest -or -not $asset[0].digest.StartsWith('sha256:')) {throw 'Runner asset lacks verifiable SHA256 digest; installation blocked.'}
  $downloadPath = Join-Path $folder 'runner-download.zip'
  Invoke-WebRequest -Uri $asset[0].browser_download_url -OutFile $downloadPath -Headers @{ 'User-Agent'='HamApp-Setup' }
  $actual=(Get-FileHash -Path $downloadPath -Algorithm SHA256).Hash.ToLowerInvariant()
  $expected=$asset[0].digest.Substring(7).ToLowerInvariant()
  if ($actual -ne $expected) { throw 'Runner SHA256 mismatch. Installation blocked.' }
  Expand-Archive -Path $downloadPath -DestinationPath $folder -Force
  Remove-Item $downloadPath -Force
  $token = (gh api -X POST "repos/$repo/actions/runners/registration-token" --jq '.token' 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or $token.Length -lt 20) { throw 'Could not obtain short-lived repository runner registration token.' }
  $name = 'hamapp-' + $env:COMPUTERNAME + '-' + [guid]::NewGuid().ToString('N').Substring(0,6)
  Push-Location $folder
  try {
    & .\config.cmd --unattended --url "https://github.com/$repo" --token $token --name $name --labels 'hamapp-windows' --work '_work'
    if ($LASTEXITCODE -ne 0) { throw 'GitHub runner registration failed.' }
  } finally { Pop-Location }
  $launcher = Join-Path $folder 'START-HAMAPP-RUNNER.cmd'
  Set-Content -Path $launcher -Encoding Ascii -Value @('@echo off','cd /d "%~dp0"','call run.cmd','pause')
  $started='NO'
  if ($StartAfterRegister) {
    Start-Process -FilePath $launcher -WorkingDirectory $folder -WindowStyle Minimized
    $started='PROCESS_LAUNCHED'
  }
  "RUNNER_REGISTERED=YES`r`nREPO=$repo`r`nRUNNER_NAME=$name`r`nRUNNER_DIR=$folder`r`nSTART_CMD=$launcher`r`nRUNNER_STARTED=$started`r`n" | Set-Content -Path $Report -Encoding UTF8
  Write-Host "Runner registered. Launcher: $launcher; STARTED=$started" -ForegroundColor Green
  Write-Host 'To run the owner QA workflow: gh workflow run windows-qa.yml'
} catch {
  "RUNNER_REGISTERED=NO`r`nERROR=$($_.Exception.Message)`r`n" | Set-Content -Path $Report -Encoding UTF8
  Write-Error $_
  exit 1
}
