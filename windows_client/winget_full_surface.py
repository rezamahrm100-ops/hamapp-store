"""Native WinGet command-surface adapter for HamApp.

Expose the official installed WinGet engine's *documented* command families
without hand-coding each subcommand into the GUI. This is an explicit
advanced user operation path; the safe exact-package install/upgrade/uninstall
flow in winget_discovery remains the ONLY install channel.

This module never invokes cmd.exe, PowerShell, a shell, or an arbitrary binary.
No secrets, network telemetry or machine-global settings are written by the
adapter. Windows/WinGet is still the source of truth for capabilities.
"""
from dataclasses import dataclass
import re
import shlex
import subprocess
import sys
import unicodedata

# Microsoft Learn's documented top-level commands; avoids treating an
# untrusted, localized help string as permission to execute new verbs.
CATEGORIES = {
    "source": "منابع بسته‌ها",
    "list": "برنامه‌های نصب‌شده",
    "show": "اطلاعات بسته",
    "search": "جست‌وجو",
    "features": "قابلیت‌های موتور",
    "settings": "تنظیمات WinGet",
    "pin": "ثابت‌نگه‌داشتن نسخه",
    "export": "صدور فهرست برنامه‌ها",
    "import": "ورود فهرست برنامه‌ها",
    "hash": "هش نصب‌کننده",
    "validate": "اعتبارسنجی مانیفست",
    "download": "دریافت نصب‌کننده",
    "repair": "تعمیر برنامه",
    "configure": "پیکربندی سامانه",
    "dscv3": "تنظیمات مطلوب DSC",
}
# State-changing packages are already managed by winget_discovery, with exact
# source/package identifiers and independent installed-state verification.
MANAGED_SEPARATELY = frozenset({"install", "upgrade", "uninstall"})
INFO = {"--version": "نسخهٔ موتور", "--info": "اطلاعات موتور", "--help": "راهنمای موتور"}
OPERATIONS = {**INFO, **CATEGORIES}
MAX_ARGS = 24
MAX_OUTPUT = 32000
MAX_LENGTH = 1100
MAX_TOKEN = 512

# Source/options that can bypass user interaction, hash checking or source
# consent are NEVER available on this generic command surface.
FORBIDDEN_FLAGS = frozenset({
    "--silent", "--force", "--override", "--custom",
    "--accept-package-agreements", "--accept-source-agreements",
    "--ignore-security-hash", "--ignore-security-hash", "--ignore-warnings",
    "--disable-interactivity", "--allow-reboot", "--skip-dependencies",
    "--proxy", "--header", "--authentication-mode", "--authentication-account",
    "--ignore-local-archive-malware-scan", "--no-vt", "--wait",
})
CONTROL = frozenset("\x00\r\n&|;<>^")
SENSITIVE_VERBS = frozenset({"configure", "dscv3", "source", "import"})
MUTATING = frozenset({"import", "download", "repair", "configure", "dscv3"})
SAFE_SUBCOMMANDS = {
    "source": frozenset({"list", "export"}),
    "pin": frozenset({"list"}),
    "settings": frozenset({"export"}),
}
KNOWN_SUBCOMMANDS = {
    "source": frozenset({"list", "export", "add", "edit", "update", "remove", "reset"}),
    "pin": frozenset({"list", "add", "remove", "reset"}),
    "settings": frozenset({"export", "open"}),
}

class EngineError(ValueError):
    pass

@dataclass(frozen=True)
class Plan:
    verb: str
    args: tuple
    state_changing: bool
    high_risk: bool

    @property
    def argv(self):
        if self.verb.startswith("--"):
            return ["winget", self.verb]
        return ["winget", self.verb, *self.args]

def _args(text):
    if not isinstance(text, str) or len(text) > MAX_LENGTH:
        raise EngineError("argument text must be bounded")
    if any(ch in CONTROL or unicodedata.category(ch) in ("Cc", "Cs") for ch in text):
        raise EngineError("no shell operators, control characters or multiline input")
    try:
        # posix=False retains Windows backslashes, while supporting quoted
        # paths. Since shell=False, user arguments are never interpreted as
        # Windows shell language.
        tokens = shlex.split(text, posix=False)
    except ValueError as exc:
        raise EngineError("invalid quoted argument") from exc
    if len(tokens) > MAX_ARGS:
        raise EngineError("too many WinGet arguments")
    normalized = []
    for token in tokens:
        if len(token) > MAX_TOKEN:
            raise EngineError("argument exceeds limit")
        if token.startswith('"') and token.endswith('"') and len(token) >= 2:
            token = token[1:-1]
        if not token or any(ch in CONTROL or ch in "\x00\r\n" for ch in token):
            raise EngineError("invalid argument")
        if token.casefold().split("=")[0] in FORBIDDEN_FLAGS:
            raise EngineError("this bypass/credential flag is unavailable in HamApp")
        normalized.append(token)
    return tuple(normalized)

def plan(verb, text=""):
    if verb in MANAGED_SEPARATELY:
        raise EngineError("select the package in the normal HamApp WinGet explorer")
    if verb not in OPERATIONS:
        raise EngineError("only documented WinGet command families are permitted")
    args = _args(text)
    if verb in INFO:
        if args:
            raise EngineError("engine information verb does not accept extra parameters")
        return Plan(verb, (), False, False)
    if any(x in ("--help", "-?", "/?") for x in args):
        # WinGet help always stays read-only.
        return Plan(verb, args, False, False)
    sub = args[0].lower() if args else ""
    if verb in ("source", "pin", "settings") and sub:
        if sub.startswith("-"):
            raise EngineError("specify the WinGet subcommand explicitly")
        if sub not in KNOWN_SUBCOMMANDS[verb]:
            raise EngineError("unknown subcommand for this engine")
    if verb == "source" and not args:
        raise EngineError("choose source list/export or explicitly confirm a source change")
    if verb == "pin" and not args:
        raise EngineError("choose pin list/add/remove/reset")
    if verb == "settings" and not args:
        raise EngineError("choose settings export or open")
    # WinGet's import, configure and repair commands can perform broad state
    # changes. They are exposed only in the advanced console, with per-run
    # double confirmation; never at program startup or on runner hosts.
    state_change = verb in MUTATING or (
        verb in SAFE_SUBCOMMANDS and sub not in SAFE_SUBCOMMANDS[verb]
    )
    high_risk = state_change and (verb in SENSITIVE_VERBS or verb == "repair")
    return Plan(verb, args, state_change, high_risk)

def execute(spec, *, runner=subprocess.run, allow_mutation=False, timeout=1500):
    if not isinstance(spec, Plan):
        raise EngineError("invalid typed WinGet operation")
    if spec.state_changing and not allow_mutation:
        raise EngineError("explicit user confirmation is required")
    if sys.platform != "win32":
        raise EngineError("native WinGet requires Windows and App Installer")
    if not 5 <= timeout <= 1800:
        raise EngineError("operation timeout must be bounded")
    # Validate the plan again, since callers must not be able to construct an
    # unchecked mutable Plan and use it as an arbitrary command runner.
    confirmed = plan(spec.verb, " ".join(
        ('"' + arg + '"' if ' ' in arg else arg) for arg in spec.args))
    if confirmed != spec:
        raise EngineError("WinGet command integrity changed before execution")
    try:
        result = runner(
            spec.argv, shell=False, text=True, capture_output=True,
            errors="replace", timeout=timeout, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EngineError("WinGet command unavailable or did not finish") from exc
    if result.returncode != 0:
        # Do not show unfiltered output from a failed security-sensitive
        # configuration command; stderr may contain connection tokens.
        raise EngineError("WinGet reported failure; no operation was accepted as successful")
    output = (result.stdout or "")[:MAX_OUTPUT]
    return {
        "verb": spec.verb, "output": output,
        "official_cli_exit_success": True,
        "state_change_requested": spec.state_changing,
        "installed_version_independently_verified": False,
        "owner_publisher_verified": False,
    }
