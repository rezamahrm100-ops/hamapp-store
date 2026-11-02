#!/usr/bin/env python3
"""End-to-end offline candidate verification + rollback review plan.

Never modifies history, signs, installs, downloads or publicly releases artifacts.
"""
import argparse
import json
from pathlib import Path

import publisher_gate
import release_history
import release_integrity


def prepare_review(candidate, registry, history, artifact, runner=None):
    proposed = release_history.check_continuity(candidate, registry, history)
    if runner is None:
        receipt = publisher_gate.verify(candidate, registry, artifact)
    else:
        receipt = publisher_gate.verify(candidate, registry, artifact, runner=runner)
    if (not receipt["signature_verified"]
            or receipt["signer_certificate_sha256"] != proposed["certificate_sha256"]
            or receipt["sha256"] != proposed["artifact_sha256"]):
        raise release_history.HistoryError("signature receipt does not match continuity precheck")
    return {
        "candidate_release": proposed,
        "candidate_verification": receipt,
        "history_changed": False,
        "review_required": True,
        "public_release_authorized": False,
        "source_commit_verified": False,
        "f_droid_index_signed": False,
        "device_install_tested": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Owner review plan (no publication)")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--registry", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/trusted_signers.json")
    parser.add_argument("--history", type=Path, default=Path(__file__).resolve().parents[1] / "catalog/release_history.json")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.receipt.is_symlink() or args.receipt.exists():
            raise release_history.HistoryError("refusing to overwrite a review receipt")
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
        registry = json.loads(args.registry.read_text(encoding="utf-8"))
        history = release_history.load_history(args.history)
        result = prepare_review(candidate, registry, history, args.artifact)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as out:
            out.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    except (OSError, ValueError, UnicodeError, release_integrity.IntegrityError) as e:
        parser.exit(1, "REJECTED: " + str(e) + "\n")
    print("REVIEW_PLAN_ONLY; NOT_PUBLIC_RELEASE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
