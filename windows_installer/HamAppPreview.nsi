; HamApp per-user Windows preview installer, unsigned TEST ONLY.
; Free NSIS upstream 3.11.0. No elevation, hidden persistence or remote download.
; This is a real install/upgrade/downgrade-deny/uninstall package on GitHub-hosted Windows.
; Do not distribute publicly or substitute for production Authenticode/WinGet approval.

Unicode True
!include "LogicLib.nsh"

!ifndef INPUT_EXE
  !error "INPUT_EXE must be the exact hosted Windows-built PyInstaller EXE"
!endif
!ifndef OUTPUT_EXE
  !error "OUTPUT_EXE must point to temporary hosted installer artifact"
!endif
!ifndef PACKAGE_CODE
  !error "PACKAGE_CODE must be provided: 1 or 2 for isolated CI lifecycle"
!endif
!if ${PACKAGE_CODE} < 1
  !error "PACKAGE_CODE must be positive"
!endif

!define ROOT_REG "Software\HamAppPreviewSandbox"
!define UNINSTALL_REG "Software\Microsoft\Windows\CurrentVersion\Uninstall\HamAppPreviewSandbox"

Name "HamApp Windows Preview (unsigned test)"
OutFile "${OUTPUT_EXE}"
InstallDir "$LOCALAPPDATA\Programs\HamAppPreviewSandbox"
RequestExecutionLevel user
ShowInstDetails show
ShowUninstDetails show
SetCompressor /SOLID lzma
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Function .onInit
    ; Strictly preserve installed version when an older unsigned installer is run.
    ClearErrors
    ReadRegDWORD $0 HKCU "${ROOT_REG}" "VersionCode"
    IfErrors permitted
    IntCmp $0 ${PACKAGE_CODE} permitted permitted versionTooOld
    versionTooOld:
        SetErrorLevel 14
        Abort "HamApp Preview downgrade was rejected"
    permitted:
FunctionEnd

Section "HamApp Windows Preview"
    SetOutPath "$INSTDIR"
    File /oname=HamApp-Windows-Preview.exe "${INPUT_EXE}"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegDWORD HKCU "${ROOT_REG}" "VersionCode" ${PACKAGE_CODE}
    WriteRegStr HKCU "${ROOT_REG}" "InstallDir" "$INSTDIR"
    WriteRegStr HKCU "${UNINSTALL_REG}" "DisplayName" "HamApp Windows Preview (unsigned test)"
    WriteRegStr HKCU "${UNINSTALL_REG}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
    WriteRegDWORD HKCU "${UNINSTALL_REG}" "NoModify" 1
    WriteRegDWORD HKCU "${UNINSTALL_REG}" "NoRepair" 1
    CreateDirectory "$SMPROGRAMS\HamApp"
    CreateShortCut "$SMPROGRAMS\HamApp\HamApp Preview.lnk" "$INSTDIR\HamApp-Windows-Preview.exe"
SectionEnd

Section "Uninstall"
    ; Never delete a different install root or modify system-wide HKLM state.
    ReadRegStr $0 HKCU "${ROOT_REG}" "InstallDir"
    StrCmp $0 "$INSTDIR" permittedDelete
        SetErrorLevel 18
        Abort "Installed program directory does not match owner-scoped registration"
    permittedDelete:
    Delete "$SMPROGRAMS\HamApp\HamApp Preview.lnk"
    RMDir "$SMPROGRAMS\HamApp"
    Delete "$INSTDIR\HamApp-Windows-Preview.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
    DeleteRegKey HKCU "${UNINSTALL_REG}"
    DeleteRegKey HKCU "${ROOT_REG}"
SectionEnd
