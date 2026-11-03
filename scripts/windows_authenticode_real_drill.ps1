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
$rootA = $null
$rootB = $null
try {
    Write-Output 'AUTHENTICODE_TEST_GENERATING_DISPOSABLE_OPENSSL_PFX'
    & python scripts/windows_ephemeral_pfx.py --directory $tempRoot
    if ($LASTEXITCODE -ne 0) { throw 'Upstream cryptography PFX generation failed' }
    $material = Get-Content -LiteralPath (Join-Path $tempRoot 'private-material.json') -Raw -Encoding utf8 | ConvertFrom-Json
    $certA = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
        [IO.File]::ReadAllBytes($material.a.cer))
    $certB = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
        [IO.File]::ReadAllBytes($material.b.cer))
    $rootA = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
        [IO.File]::ReadAllBytes($material.a.root_cer))
    $rootB = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new(
        [IO.File]::ReadAllBytes($material.b.root_cer))
    if ($certA.Thumbprint -eq $certB.Thumbprint -or $rootA.Thumbprint -eq $rootB.Thumbprint) {
        throw 'Two independent disposable CA and leaf identities required'
    }
    # Trust only throwaway CA public certificates in CurrentUser Root, and
    # only code-signing leaf public certificates in CurrentUser TrustedPublisher.
    # No private key enters Windows cert stores. The runner is disposable.
    $rootStore = [System.Security.Cryptography.X509Certificates.X509Store]::new(
        'Root', [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser)
    $rootStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
    try { $rootStore.Add($rootA); $rootStore.Add($rootB) }
    finally { $rootStore.Close() }
    $publisherStore = [System.Security.Cryptography.X509Certificates.X509Store]::new(
        'TrustedPublisher', [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser)
    $publisherStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
    try { $publisherStore.Add($certA); $publisherStore.Add($certB) }
    finally { $publisherStore.Close() }
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
    foreach ($record in @(@{ name = 'TrustedPublisher'; cert = $certA },
                           @{ name = 'TrustedPublisher'; cert = $certB },
                           @{ name = 'Root'; cert = $rootA },
                           @{ name = 'Root'; cert = $rootB })) {
        $cert = $record.cert
        if ($null -eq $cert) { continue }
        $certPath = 'Cert:\CurrentUser\' + $record.name + '\' + $cert.Thumbprint
        Remove-Item -LiteralPath $certPath -Force -Confirm:$false -ErrorAction SilentlyContinue
        $cert.Dispose()
    }
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue
}
