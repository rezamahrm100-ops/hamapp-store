#requires -Version 5.1
# Real per-user installer lifecycle only on short-lived GitHub-hosted Windows.
# Unsigned NSIS preview; never owner runner or trusted public installer release.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$UnsignedExe,
    [Parameter(Mandatory=$true)][string]$SecondUnsignedExe
)

$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or -not $env:RUNNER_TEMP) {
    throw 'Actual isolated GitHub-hosted Windows runner is mandatory'
}
if (-not (Test-Path -LiteralPath $UnsignedExe -PathType Leaf) -or
        -not (Test-Path -LiteralPath $SecondUnsignedExe -PathType Leaf)) {
    throw 'Both distinct real PyInstaller Windows executables are required'
}
if (-not $env:GITHUB_SHA -or $env:GITHUB_SHA -notmatch '^[a-f0-9]{40}$') {
    throw 'Exact producing GitHub source SHA missing'
}
$origin = (Resolve-Path -LiteralPath $UnsignedExe).Path
$origin2 = (Resolve-Path -LiteralPath $SecondUnsignedExe).Path
$expected = (Get-FileHash -LiteralPath $origin -Algorithm SHA256).Hash.ToLowerInvariant()
$expected2 = (Get-FileHash -LiteralPath $origin2 -Algorithm SHA256).Hash.ToLowerInvariant()
if ($origin -eq $origin2 -or $expected -eq $expected2) {
    throw 'Second Windows native app must have different real executable bytes'
}
$root = Join-Path $env:LOCALAPPDATA 'Programs\HamAppPreviewSandbox'
$reg = 'HKCU:\Software\HamAppPreviewSandbox'
$uninstallReg = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\HamAppPreviewSandbox'
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\HamApp'
if ((Test-Path -LiteralPath $root) -or (Test-Path -LiteralPath $reg) -or (Test-Path -LiteralPath $uninstallReg)) {
    throw 'Refusing to modify pre-existing Windows installation or registry'
}
$tools = @(
    (Join-Path ${env:ProgramFiles(x86)} 'NSIS\makensis.exe'),
    (Join-Path $env:ProgramFiles 'NSIS\makensis.exe')
)
$makensis = $tools | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
if (-not $makensis) { throw 'Pinned actual upstream NSIS compiler was not installed' }
$sourceScript = (Resolve-Path -LiteralPath 'windows_installer/HamAppPreview.nsi').Path
$outdir = Join-Path $env:RUNNER_TEMP 'hamapp-nsis-actual-ci-only'
if (Test-Path -LiteralPath $outdir) { throw 'Refusing to reuse previous installer workspace' }
New-Item -ItemType Directory -Path $outdir | Out-Null
$setup1 = Join-Path $outdir 'HamApp-Preview-Setup-v1-UNSIGNED.exe'
$setup2 = Join-Path $outdir 'HamApp-Preview-Setup-v2-UNSIGNED.exe'
$installed = Join-Path $root 'HamApp-Windows-Preview.exe'
$uninstall = Join-Path $root 'Uninstall.exe'
$createdByTest = $false
try {
    Write-Output 'NSIS_REAL_TWO_TEST_INSTALLERS_BUILDING'
    & $makensis '/V3' "/DPACKAGE_CODE=1" "/DINPUT_EXE=$origin" "/DOUTPUT_EXE=$setup1" $sourceScript
    if ($LASTEXITCODE -ne 0) { throw 'NSIS actual installer v1 compilation failed' }
    & $makensis '/V3' "/DPACKAGE_CODE=2" "/DINPUT_EXE=$origin2" "/DOUTPUT_EXE=$setup2" $sourceScript
    if ($LASTEXITCODE -ne 0) { throw 'NSIS actual installer v2 compilation failed' }
    if (-not (Test-Path -LiteralPath $setup1 -PathType Leaf) -or -not (Test-Path -LiteralPath $setup2 -PathType Leaf)) {
        throw 'Real NSIS output EXEs are missing'
    }
    $installerHash1 = (Get-FileHash -LiteralPath $setup1 -Algorithm SHA256).Hash.ToLowerInvariant()
    $installerHash2 = (Get-FileHash -LiteralPath $setup2 -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($installerHash1 -eq $installerHash2) { throw 'Two installer-version builds are byte-identical' }
    $args = @('/S')
    Write-Output 'NSIS_REAL_SANDBOX_VERSION1_INSTALL'
    $v1 = Start-Process -FilePath $setup1 -ArgumentList $args -Wait -PassThru -NoNewWindow
    $createdByTest = $true
    if ($v1.ExitCode -ne 0 -or -not (Test-Path -LiteralPath $installed -PathType Leaf)) {
        throw 'Real version-one per-user installer execution failed'
    }
    $observed1 = (Get-ItemProperty -LiteralPath $reg -Name VersionCode).VersionCode
    if ($observed1 -ne 1) { throw 'Windows registry did not record actual version 1 installation' }
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw 'Installed Windows EXE is not exact original PyInstaller bytes'
    }
    Write-Output 'NSIS_REAL_SANDBOX_VERSION2_UPGRADE'
    $v2 = Start-Process -FilePath $setup2 -ArgumentList $args -Wait -PassThru -NoNewWindow
    if ($v2.ExitCode -ne 0) { throw 'Real version-two installer failed' }
    $observed2 = (Get-ItemProperty -LiteralPath $reg -Name VersionCode).VersionCode
    if ($observed2 -ne 2) { throw 'Windows registry did not record upgraded installer version 2' }
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected2) {
        throw 'Installer upgrade did not install the second distinct native GUI app bytes'
    }
    Write-Output 'NSIS_REAL_SANDBOX_DOWNGRADE_REJECTION'
    $downgrade = Start-Process -FilePath $setup1 -ArgumentList $args -Wait -PassThru -NoNewWindow
    if ($downgrade.ExitCode -eq 0) { throw 'A lower installer version unexpectedly succeeded' }
    if ((Get-ItemProperty -LiteralPath $reg -Name VersionCode).VersionCode -ne 2) {
        throw 'Denied downgrade corrupted current installed version'
    }
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected2) {
        throw 'Denied downgrade corrupted the installed v2 native app bytes'
    }
    Write-Output 'NSIS_REAL_SANDBOX_UNINSTALL'
    if (-not (Test-Path -LiteralPath $uninstall -PathType Leaf)) { throw 'Real registered uninstaller missing' }
    $remove = Start-Process -FilePath $uninstall -ArgumentList @('/S') -Wait -PassThru -NoNewWindow
    if ($remove.ExitCode -ne 0) { throw 'Real uninstall process returned failure' }
    for ($attempt=0; $attempt -lt 15 -and (Test-Path -LiteralPath $root); $attempt++) {
        Start-Sleep -Milliseconds 300
    }
    if (Test-Path -LiteralPath $root) { throw 'Actual installation directory remained after uninstall' }
    if ((Test-Path -LiteralPath $reg) -or (Test-Path -LiteralPath $uninstallReg)) {
        throw 'Actual per-user installer registry keys remained after uninstall'
    }
    $createdByTest = $false
    $evidencePath = 'dist/windows-installer-evidence/receipt.json'
    New-Item -ItemType Directory -Path 'dist/windows-installer-evidence' -Force | Out-Null
    $receipt = [ordered]@{
        schema_version = 1
        scope = 'real-hosted-windows-per-user-NSIS-installer-lifecycle'
        source_sha = $env:GITHUB_SHA
        source_windows_exe_sha256 = $expected
        actual_distinct_windows_exe_v2_sha256 = $expected2
        installer_v1_sha256 = $installerHash1
        installer_v2_sha256 = $installerHash2
        actual_hosted_windows_v1_install_passed = $true
        actual_hosted_windows_v2_installer_upgrade_passed = $true
        installed_exe_sha256_continuity_passed = $true
        actual_older_installer_downgrade_refused = $true
        actual_uninstaller_and_registry_cleanup_passed = $true
        product_binary_v2_content_change_verified = $true
        native_installer_authenticode_production_verified = $false
        elevation_UAC_or_owner_device_acceptance = $false
        public_release_approved = $false
        production_ready = $false
    }
    $receipt | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $evidencePath -Encoding utf8
    Write-Output 'ACTUAL_WINDOWS_NSIS_DISTINCT_APP_V1_TO_V2_UPGRADE_DENY_DOWNGRADE_UNINSTALL_ACCEPTED; NO_PRODUCTION_RELEASE'
}
finally {
    # Only cleanup files/registry proven to have been created by THIS isolated
    # test; never delete arbitrary existing owner state.
    if ($createdByTest -and (Test-Path -LiteralPath $uninstall -PathType Leaf)) {
        & $uninstall /S | Out-Null
    }
    Remove-Item -LiteralPath $outdir -Recurse -Force -ErrorAction SilentlyContinue
}
