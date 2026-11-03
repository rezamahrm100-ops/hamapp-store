#requires -Version 5.1
# Real hosted Windows SignTool + ephemeral OpenSSL PFX. Never owner computer.
[CmdletBinding()]
param([Parameter(Mandatory = $true)][string]$UnsignedExe)
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or $env:RUNNER_OS -ne 'Windows' -or $env:RUNNER_ENVIRONMENT -ne 'github-hosted' -or $env:GITHUB_REPOSITORY -ne 'rezamahrm100-ops/hamapp-store') {
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
    # Hosted Windows certificate-store mutation stalled for eight minutes in
    # real CI #41642192393. Never import disposable roots into Windows.
    # This test proves native Windows REJECTION of untrusted test signers,
    # not acceptance of a trusted production signature.
    Write-Output 'AUTHENTICODE_NO_WINDOWS_CERTIFICATE_STORE_MUTATIONS'
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
    if (-not $env:GITHUB_SHA -or $env:GITHUB_SHA -notmatch '^[a-f0-9]{40}$') {
        throw 'Immutable producing GitHub source SHA is missing'
    }
    Write-Output 'AUTHENTICODE_TEST_CHECKING_REAL_NATIVE_UNTRUSTED_SIGNER_REJECTIONS'
    function Observe-NativeSignature([string]$Path) {
        $info = Get-AuthenticodeSignature -LiteralPath $Path
        $digest = $null
        if ($null -ne $info.SignerCertificate) {
            $sha = [Security.Cryptography.SHA256]::Create()
            try { $digest = [BitConverter]::ToString($sha.ComputeHash($info.SignerCertificate.RawData)).Replace('-', '').ToLowerInvariant() }
            finally { $sha.Dispose() }
        }
        return @{ status = [string]$info.Status; signer = $digest }
    }
    # This is a host-native .NET X509Chain test with an explicit in-memory
    # isolated trust root, NOT an OS WinVerifyTrust positive signature verdict.
    # No CurrentUser/LocalMachine certificate store is modified or imported.
    function Test-DisposableCustomRoot(
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Leaf,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$Root
    ) {
        $chain = [System.Security.Cryptography.X509Certificates.X509Chain]::new()
        try {
            $policy = $chain.ChainPolicy
            $policy.TrustMode = [System.Security.Cryptography.X509Certificates.X509ChainTrustMode]::CustomRootTrust
            $policy.CustomTrustStore.Add($Root) | Out-Null
            $policy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::NoCheck
            $policy.VerificationFlags = [System.Security.Cryptography.X509Certificates.X509VerificationFlags]::NoFlag
            $policy.DisableCertificateDownloads = $true
            $policy.ApplicationPolicy.Add([System.Security.Cryptography.Oid]::new(
                '1.3.6.1.5.5.7.3.3')) | Out-Null
            if (-not $chain.Build($Leaf)) { return $false }
            $elements = $chain.ChainElements
            if ($elements.Count -ne 2) { return $false }
            return ($elements[0].Certificate.Thumbprint -eq $Leaf.Thumbprint -and
                    $elements[1].Certificate.Thumbprint -eq $Root.Thumbprint)
        }
        finally { $chain.Dispose() }
    }
    Write-Output 'AUTHENTICODE_NATIVE_DOTNET_CUSTOM_ROOT_CHAIN_IN_MEMORY_ONLY'
    if (-not (Test-DisposableCustomRoot $certA $rootA) -or
        -not (Test-DisposableCustomRoot $certB $rootB)) {
        throw 'Native .NET in-memory disposable CA-to-CodeSigning leaf chain failed'
    }
    if ((Test-DisposableCustomRoot $certA $rootB) -or
        (Test-DisposableCustomRoot $certB $rootA)) {
        throw 'Disposable wrong-root CA was accepted by in-memory native X509Chain'
    }
    $nativeA = Observe-NativeSignature $signed
    $nativeB = Observe-NativeSignature $foreign
    if ($nativeA.signer -ne $material.a.certificate_sha256 -or $nativeB.signer -ne $material.b.certificate_sha256) {
        throw 'Windows native OS returned unexpected signer fingerprints'
    }
    # Actual hosted Windows returned UnknownError for each correctly embedded
    # signer in #41644214183. That is NOT proof of the precise trust-chain
    # failure; it is only proof that Windows did not mark either as Valid.
    # For this pinned disposable test require the exact observed failure.
    if ($nativeA.status -ne 'UnknownError' -or $nativeB.status -ne 'UnknownError') {
        throw ('Unexpected native Windows status for isolated disposable PFX; statuses=' + $nativeA.status + ',' + $nativeB.status)
    }
    $nativeUnsigned = Observe-NativeSignature $UnsignedExe
    if ($nativeUnsigned.status -ne 'NotSigned' -or $null -ne $nativeUnsigned.signer) {
        throw 'Unsigned original unexpectedly has Windows native Authenticode signer'
    }
    $originalHash = (Get-FileHash -LiteralPath $UnsignedExe -Algorithm SHA256).Hash
    $signedHash = (Get-FileHash -LiteralPath $signed -Algorithm SHA256).Hash
    $foreignHash = (Get-FileHash -LiteralPath $foreign -Algorithm SHA256).Hash
    if ($signedHash -eq $originalHash -or $foreignHash -eq $originalHash -or $foreignHash -eq $signedHash) {
        throw 'Two independently signed real PE copies required'
    }
    Copy-Item -LiteralPath $signed -Destination $tampered -ErrorAction Stop
    $stream = [IO.File]::Open($tampered, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite)
    try {
        if ($stream.Length -lt 65537) { throw 'Signed Windows PE too short to tamper in signed section' }
        $stream.Seek(65536, [IO.SeekOrigin]::Begin) | Out-Null
        $before = $stream.ReadByte()
        $stream.Seek(65536, [IO.SeekOrigin]::Begin) | Out-Null
        $stream.WriteByte([byte]($before -bxor 0x01))
        $stream.Flush($true)
    } finally { $stream.Dispose() }
    $nativeTamper = Observe-NativeSignature $tampered
    if ($nativeTamper.status -notin @('HashMismatch', 'NotSigned') -or (Get-FileHash -LiteralPath $tampered -Algorithm SHA256).Hash -eq $signedHash) {
        throw ('Real modified signed PE was not rejected by native Windows: ' + $nativeTamper.status)
    }
    New-Item -ItemType Directory -Path 'dist/windows-authenticode-evidence' -Force | Out-Null
    $receipt = @{
        schema_version = 1
        scope = 'actual-hosted-Windows-OS-untrusted-Authenticode-negative-tests'
        source_sha = $env:GITHUB_SHA
        actual_windows_native_unsigned_exe_provided = $true
        actual_official_windows_sdk_signer_produced_two_distinct_signed_exes = $true
        native_windows_os_observed_two_exact_disposable_leaf_certificates = $true
        native_windows_in_memory_custom_root_code_signing_chains_verified = $true
        native_windows_wrong_disposable_root_chain_rejected = $true
        native_windows_os_positive_authenticode_status_proven = $false
        native_windows_os_did_not_accept_disposable_test_signers = $true
        native_windows_os_disposable_signer_statuses = @('UnknownError', 'UnknownError')
        precise_native_os_trust_failure_cause_verified = $false
        native_windows_os_rejected_unsigned_exe = $true
        native_windows_os_rejected_modified_signed_exe = $true
        production_authenticode_certificate_verified = $false
        native_windows_os_trusted_authenticode_verified = $false
        owner_windows_device_tested = $false
        public_release_authorized = $false
    }
    $receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath 'dist/windows-authenticode-evidence/receipt.json' -Encoding utf8
    Write-Output 'ACTUAL_NATIVE_WINDOWS_INMEMORY_CODE_SIGNING_CHAINS_ACCEPTED_WRONG_ROOT_REJECTED_AND_NATIVE_AUTHENTICODE_UNKNOWN_ERROR_UNCHANGED'
}
finally {
    Write-Output 'AUTHENTICODE_TEST_DISPOSING_CERTIFICATE_OBJECTS_AND_PRIVATE_TEMP_ONLY'
    foreach ($cert in @($certA, $certB, $rootA, $rootB)) {
        if ($null -ne $cert) { $cert.Dispose() }
    }
    Remove-Item -LiteralPath $tempRoot -Recurse -Force -Confirm:$false -ErrorAction SilentlyContinue
}
