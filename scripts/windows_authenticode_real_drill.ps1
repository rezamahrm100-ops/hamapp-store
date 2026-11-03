#requires -Version 5.1
# REAL Windows-hosted CodeSigningCert proof on disposable self-signed certificates.
# Never use on owner workstation. Signs only temporary copies; unsigned artifact stays untouched.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$UnsignedExe
)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'Hosted GitHub Windows job required; never owner signing machine'
}
if (-not (Test-Path -LiteralPath $UnsignedExe -PathType Leaf)) {
    throw 'Actual built Windows preview EXE is missing'
}
if (-not $env:RUNNER_TEMP) { throw 'Missing GitHub temporary directory' }
$tempRoot = Join-Path $env:RUNNER_TEMP 'hamapp-ephemeral-authenticode'
if (Test-Path -LiteralPath $tempRoot) { throw 'Refuse to overwrite temporary signer workspace' }
New-Item -ItemType Directory -Path $tempRoot | Out-Null
$certA = $null
$certB = $null
try {
    $opts = @{
        Type = 'CodeSigningCert'
        CertStoreLocation = 'Cert:\CurrentUser\My'
        HashAlgorithm = 'SHA256'
        KeyAlgorithm = 'RSA'
        KeyLength = 2048
        KeyExportPolicy = 'NonExportable'
        NotAfter = (Get-Date).AddDays(1)
    }
    Write-Output 'AUTHENTICODE_TEST_CREATING_DISPOSABLE_CERTIFICATES'
    $certA = New-SelfSignedCertificate @opts -Subject 'CN=HamApp Ephemeral Test Signer A - NEVER PRODUCTION'
    $certB = New-SelfSignedCertificate @opts -Subject 'CN=HamApp Ephemeral Test Signer B - WRONG PUBLISHER'
    # Trust only CurrentUser on short-lived GitHub-hosted Windows, never public CA.
    foreach ($storeName in @('Root', 'TrustedPublisher')) {
        $store = [System.Security.Cryptography.X509Certificates.X509Store]::new(
            $storeName, [System.Security.Cryptography.X509Certificates.StoreLocation]::CurrentUser)
        $store.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        try { $store.Add($certA); $store.Add($certB) }
        finally { $store.Close() }
    }
    $signed = Join-Path $tempRoot 'hamapp-signed-test.exe'
    $foreign = Join-Path $tempRoot 'hamapp-foreign-signed-test.exe'
    $tampered = Join-Path $tempRoot 'hamapp-tampered-test.exe'
    Copy-Item -LiteralPath $UnsignedExe -Destination $signed -ErrorAction Stop
    Copy-Item -LiteralPath $UnsignedExe -Destination $foreign -ErrorAction Stop
    Write-Output 'AUTHENTICODE_TEST_SIGNING_TWO_REAL_COPIES'
    $resultA = Set-AuthenticodeSignature -FilePath $signed -Certificate $certA -HashAlgorithm SHA256 -Confirm:$false
    $resultB = Set-AuthenticodeSignature -FilePath $foreign -Certificate $certB -HashAlgorithm SHA256 -Confirm:$false
    if ($resultA.Status -ne 'Valid' -or $resultB.Status -ne 'Valid') {
        throw 'Actual Authenticode signing failed before real OS validation'
    }
    $sha256 = [Security.Cryptography.SHA256]::Create()
    try {
        $fingerprintA = [BitConverter]::ToString($sha256.ComputeHash($certA.RawData)).Replace('-', '').ToLowerInvariant()
        $fingerprintB = [BitConverter]::ToString($sha256.ComputeHash($certB.RawData)).Replace('-', '').ToLowerInvariant()
    }
    finally { $sha256.Dispose() }
    if (-not $env:GITHUB_SHA -or $env:GITHUB_SHA.Length -ne 40) {
        throw 'Exact GitHub source SHA required'
    }
    New-Item -ItemType Directory -Path 'dist/windows-authenticode-evidence' -Force | Out-Null
    Write-Output 'AUTHENTICODE_TEST_VERIFYING_NATIVE_WINDOWS_SIGNATURES'
    & python scripts/windows_authenticode_real_drill.py --unsigned $UnsignedExe --signed $signed --foreign $foreign --intended-certificate $fingerprintA --foreign-certificate $fingerprintB --source-sha $env:GITHUB_SHA --tamper-path $tampered --receipt 'dist/windows-authenticode-evidence/receipt.json'
    if ($LASTEXITCODE -ne 0) { throw 'Native Windows OS and pinned publisher checks failed' }
    Write-Output 'REAL_WINDOWS_EPHEMERAL_AUTHENTICODE_AND_NEGATIVE_GATES_ACCEPTED'
}
finally {
    Write-Output 'AUTHENTICODE_TEST_DESTROYING_TEMPORARY_SIGNERS'
    foreach ($cert in @($certA, $certB)) {
        if ($null -eq $cert) { continue }
        foreach ($storeName in @('My','Root','TrustedPublisher')) {
            $certPath = 'Cert:\CurrentUser\' + $storeName + '\' + $cert.Thumbprint
            Remove-Item -LiteralPath $certPath -Force -Confirm:$false -ErrorAction SilentlyContinue
        }
    }
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue
}
