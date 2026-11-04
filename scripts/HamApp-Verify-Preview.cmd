@echo off
setlocal EnableExtensions
pushd "%~dp0" || exit /b 2
echo HamApp Owner Preview - SHA256 integrity verification
powershell.exe -NoLogo -NoProfile -NonInteractive -Command "$ErrorActionPreference='Stop'; $m=Get-Content -LiteralPath 'manifest.json' -Raw | ConvertFrom-Json; if($m.production_signed -ne $false -or $m.public_release_authorized -ne $false){throw 'Unexpected release claims'}; $rows=@($m.build_files); $lines=@(Get-Content -LiteralPath 'SHA256SUMS.txt'); if($rows.Count -lt 1 -or $rows.Count -gt 2 -or $lines.Count -ne $rows.Count){throw 'Unexpected manifest/checksum entries'}; foreach($item in $rows){$n=[string]$item.filename; $digest=[string]$item.sha256; if($n -notmatch '^[A-Za-z0-9.-]+$' -or $digest -notmatch '^[0-9a-f]{64}$'){throw 'Unsafe manifest entry'}; if($lines -notcontains ($digest+'  '+$n)){throw 'Checksum listing differs from manifest'}; $p=Join-Path (Get-Location).Path $n; $file=Get-Item -LiteralPath $p -ErrorAction Stop; if($file.PSIsContainer -or ($file.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'Linked or non-file artifact rejected'}; if([long]$file.Length -ne [long]$item.bytes){throw 'Artifact size mismatch'}; $actual=(Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLowerInvariant(); if($actual -ne $digest){throw 'SHA256 mismatch'}; Write-Host ('PASS: '+$n)}; Write-Host 'ALL_ARTIFACT_SHA256_CHECKS_PASSED';"
set "HAMAPP_VERIFY_EXIT=%ERRORLEVEL%"
popd
if not "%HAMAPP_VERIFY_EXIT%"=="0" (
  echo FAILED: do not open or install these files.
  pause
  exit /b %HAMAPP_VERIFY_EXIT%
)
echo Verified checksums only. This does not prove a trusted publisher signature.
pause
exit /b 0
