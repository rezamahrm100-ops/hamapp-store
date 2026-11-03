#requires -Version 5.1
# Real hosted Windows SignTool + ephemeral OpenSSL PFX. Never owner computer.
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$UnsignedExe)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'Only isolated GitHub-hosted Windows may run disposable signer drill'
}
if (-not (Test-Path -LiteralPath $UnsignedExe -PathType Leaf)) {
    throw 'Missing actual built Windows PyInstaller preview EXE'
}
if (-not $env:RUNNER_TEMP) { throw 'Missing isolated hosted runner temp' }
$tempRoot = Join-Path $env:RUNNER_TEMP 'hamapp-ephemeral-authenticode'
if (Test-Path -LiteralPath $tempRoot) { throw 'Refusing existing key workspace' }
$certA = $null
$certB = $null
try {
    Write-Output 'AUTHENTICODE_TEST_GENERATING_DISPOSABLE_OPENSSL_PFX'
    & python scripts/windows_ephemeral_pfx.py --directory $tempRoot
    if ($LASTEXITCODE -ne 0) { throw 'Upstream cryptography PFX generation failed' }
    $material = Get-Content -LiteralPath (Join-Path $tempRoot 'private-material.json') -Raw -Encoding utf8 | ConvertFrom-Json
    $certA = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
        [IO.File]::ReadAllBytes($material.a.cer))
    $certB = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
        [IO.File]::ReadAllBytes($material.b.cer))
    if ($certA.Thumbprint -eq $certB.Thumbprint) { throw 'Synthetic test certificates unexpectedly identical' }
    # Import PUBLIC cert only; do not provision a Windows CNG private key.
    # Temporary CurrentUser-only trust on this disposable hosted VM.
    foreach ($storeName in @('Root', 'TrustedPublisher')) {
        $store = [System.Security.Cryptography.X509Certificates.X509Store]::new(
            $storeName, [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser)
        $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        try { $store.Add($certA); $store.Add($certB) }
        finally { $store.Close() }
    }
    $kits = Join-Path ${env:ProgramFiles(x86)} 'Windows Kits\10\bin'
    if (-not (Test-Path -LiteralPath $kits)) { throw 'Official Windows SDK SignTool is unavailable' }
    $signer = Get-ChildItem -LiteralPath $kits -Filter 'signtool.exe' -Recurse -File |
       Where-Object { $_.FullName -match '\\x64\\' } |
       Sort-Object FullName -Descending | Select-Object -First 1
    if ($null -eq $signer) { throw 'Real x64 Windows SDK SignTool is unavailable' }
    Write-Output 'AUTHENTICODE_TEST_SIGNING_COPIED_EXE_WITH_OFFICIAL_SDK'
    $signed = Join-Path $tempRoot 'hamapp-signed-test.exe'
    $foreign = Join-Path $tempRoot 'hamapp-foreign-signed-test.exe'
    $tampered = Join-Path $tempRoot 'hamapp-tampered-test.exe'
    Copy-Item -LiteralPath $UnsignedExe -Destination $signed -ErrorAction Stop
    Copy-Item -LiteralPath $UnsignedExe -Destination $foreign -ErrorAction Stop
    & $signer.FullName sign /f $material.a.pfx /p $material.a.password /fd SHA256 $signed
    if ($LASTEXITCODE -ne 0) { throw 'Official Windows SDK signing failed for signer A' }
    & $signer.FullName sign /f $material.b.pfx /p $material.b.password /fd SHA256 $foreign
    if ($LASTEXITCODE -ne 0) { throw 'Official Windows SDK signing failed for signer B' }
    & $signer.FullName verify /pa $signed
    if ($LASTEXITCODE -ne 0) { throw 'Native Windows SDK failed first signed EXE validation' }
    & $signer.FullName verify /pa $foreign
    if ($LASTEXITCODE -ne 0) { throw 'Native Windows SDK failed foreign signed EXE validation' }
    if (-not $env:GITHUB_SHA -or $env:GITHUB_SHA.Length -ne 40) {
        throw 'Immutable producing GitHub source SHA is missing'
    }
    Write-Output 'AUTHENTICODE_TEST_CHECKING_PINNED_PUBLISHER_AND_CORRUPTION_GATES'
    New-Item -ItemType Directory -Path 'dist/windows-authenticode-evidence' -Force | Out-Null
    & python scripts/windows_authenticode_real_drill.py --unsigned $UnsignedExe --signed $signed --foreign $foreign --intended-certificate $material.a.certificate_sha256 --foreign-certificate $material.b.certificate_sha256 --source-sha $env:GITHUB_SHA --tamper-path $tampered --receipt 'dist/windows-authenticode-evidence/receipt.json'
    if ($LASTEXITCODE -ne 0) { throw 'Windows Authenticode exact signer/bytes rejection failed' }
    Write-Output 'ACTUAL_WINDOWS_SIGNTOOL_AND_NATIVE_AUTHENTICODE_SIGNER_NEGATIVES_PASSED'
}
finally {
    Write-Output 'AUTHENTICODE_TEST_REMOVING_DISPOSABLE_CERTIFICATES_AND_PFX'
    foreach ($cert in @($certA, $certB)) {
        if ($null -eq $cert) { continue }
        foreach ($storeName in @('Root', 'TrustedPublisher')) {
            $certPath = 'Cert:\CurrentUser\' + $storeName + '\' + $cert.Thumbprint
            Remove-Item -LiteralPath $certPath -Force -Confirm:$false -ErrorAction SilentlyContinue
        }
        $cert.Dispose()
    }
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue
}
