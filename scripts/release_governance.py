#!/usr/bin/env python3
"""Fail-closed, PR-review-only release revocation and promotion planning.

The public catalogue is a mirror, never an approval authority. This program
NEVER changes checked-in trust registries, history or app download links. A
caller may write proposed changes to a separate directory and submit a
reviewable, atomic Git commit. No production signer is inferred from receipts.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import publisher_gate
import release_history
import validate_catalog
import integrated_release_review

class GovernanceError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def validate_state(catalog, registry, history):
    publisher_gate.validate_trust_registry(registry)
    release_history.validate_history(history)
    errors = validate_catalog.validate(catalog, registry=registry, history=history)
    if errors:
        raise GovernanceError("existing catalogue is not valid: " + "; ".join(errors))
    return True

def _hide_listing(app):
    app["status"] = "planned"
    app["version"] = None
    app["download_url"] = None
    app.pop("release_proof", None)
    app.pop("changelog", None)

def revoke(catalog, registry, history, *, app_id, platform, version, artifact_sha256):
    """Produce a two-file atomic Git-commit proposal, NEVER commit by itself."""
    validate_state(catalog, registry, history)
    if (not isinstance(app_id, str) or not isinstance(platform, str)
            or not isinstance(version, str) or not isinstance(artifact_sha256, str)
            or platform not in ("android", "windows")
            or not release_history.HEX64.fullmatch(artifact_sha256)):
        raise GovernanceError("exact binary release identity required")
    matching = [r for r in history["releases"] if r["app_id"] == app_id
                and r["platform"] == platform and r["version"] == version
                and r["artifact_sha256"] == artifact_sha256]
    if len(matching) != 1 or matching[0]["status"] != "approved":
        raise GovernanceError("no unique currently approved release to revoke")
    changed_apps, changed_history = copy.deepcopy(catalog), copy.deepcopy(history)
    entry = next(r for r in changed_history["releases"]
                 if (r["app_id"], r["platform"], r["version"], r["artifact_sha256"])
                 == (app_id, platform, version, artifact_sha256))
    entry["status"] = "revoked"
    # If the revoked release was the visible listing, disable its link before publication.
    for app in changed_apps["apps"]:
        if (app["id"] == app_id and app["status"] == "released"
                and app["platforms"] == [platform] and app["version"] == version
                and app["release_proof"]["sha256"] == artifact_sha256):
            _hide_listing(app)
    validate_state(changed_apps, registry, changed_history)
    return {
        "catalog": changed_apps, "history": changed_history,
        "audit": {
            "schema_version": 1, "action": "revoke_release",
            "app_id": app_id, "platform": platform, "version": version,
            "artifact_sha256": artifact_sha256, "base_catalog_sha256": digest(catalog),
            "base_history_sha256": digest(history),
            "proposed_catalog_sha256": digest(changed_apps),
            "proposed_history_sha256": digest(changed_history),
            "github_owner_review_required": True,
            "github_branch_protection_enforced": False,
            "files_committed": False, "site_deployed": False
        }
    }

def revoke_signer(catalog, registry, history, certificate_sha256):
    """Prepare an emergency signer revocation across apps and platforms."""
    validate_state(catalog, registry, history)
    if not isinstance(certificate_sha256, str) or not release_history.HEX64.fullmatch(certificate_sha256):
        raise GovernanceError("exact certificate fingerprint required")
    if certificate_sha256 in history["revoked_signers"]:
        raise GovernanceError("signing identity already revoked")
    matches = [r for r in history["releases"] if r["certificate_sha256"] == certificate_sha256
               and r["status"] == "approved"]
    if not matches:
        raise GovernanceError("no approved releases under this signer")
    changed_apps, changed_history = copy.deepcopy(catalog), copy.deepcopy(history)
    changed_history["revoked_signers"].append(certificate_sha256)
    for r in changed_history["releases"]:
        if r["certificate_sha256"] == certificate_sha256:
            r["status"] = "revoked"
    affected = {(r["app_id"], r["platform"]) for r in matches}
    for app in changed_apps["apps"]:
        if app["status"] == "released" and len(app["platforms"]) == 1:
            if (app["id"], app["platforms"][0]) in affected:
                _hide_listing(app)
    validate_state(changed_apps, registry, changed_history)
    return {
        "catalog": changed_apps, "history": changed_history,
        "audit": {
            "schema_version": 1, "action": "revoke_signer",
            "certificate_sha256": certificate_sha256,
            "affected_release_count": len(matches),
            "base_catalog_sha256": digest(catalog), "base_history_sha256": digest(history),
            "proposed_catalog_sha256": digest(changed_apps),
            "proposed_history_sha256": digest(changed_history),
            "github_owner_review_required": True,
            "github_branch_protection_enforced": False,
            "files_committed": False, "site_deployed": False
        }
    }

def plan_promotion(candidate, registry, history, artifact, trusted_workflow, trusted_source_ref,
                   *, signature_runner=None, gh_runner=None):
    """Run real crypto verification before drafting only; no public promotion."""
    options = {}
    if signature_runner is not None:
        options["signature_runner"] = signature_runner
    if gh_runner is not None:
        options["gh_runner"] = gh_runner
    receipt = integrated_release_review.assess(candidate, registry, history,
                 artifact, trusted_workflow, trusted_source_ref, **options)
    if (not receipt["hash_signature_and_github_source_integrated"]
            or receipt["owner_promotion_approved"]
            or receipt["public_distribution_authorized"]):
        raise GovernanceError("invalid pre-approval assessment")
    # Crucial: these are NOT valid approved registry records or listings.
    return {"schema_version": 1, "action": "propose_release",
            "candidate_release": receipt["release"],
            "verified_artifact_sha256": receipt["verified_provenance"]["artifact_sha256"],
            "review_evidence": receipt,
            "current_history_sha256": digest(history),
            "malware_permission_review_complete": False,
            "signed_repository_and_device_qa_complete": False,
            "github_owner_review_required": True,
            "branch_ruleset_required": True, "public_distribution_authorized": False}

def main():
    parser = argparse.ArgumentParser(description="Prepare review-only release revocation; no repo modifications")
    parser.add_argument("--catalog", type=Path, default=validate_catalog.ROOT / "catalog/apps.json")
    parser.add_argument("--registry", type=Path, default=validate_catalog.ROOT / "catalog/trusted_signers.json")
    parser.add_argument("--history", type=Path, default=validate_catalog.ROOT / "catalog/release_history.json")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--revoke-signer")
    mode.add_argument("--revoke-app")
    parser.add_argument("--platform", choices=("android", "windows"))
    parser.add_argument("--version")
    parser.add_argument("--artifact-sha256")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        source = {
            "catalog": json.loads(args.catalog.read_text(encoding="utf-8")),
            "registry": json.loads(args.registry.read_text(encoding="utf-8")),
            "history": json.loads(args.history.read_text(encoding="utf-8"))
        }
        if args.revoke_signer is not None:
            if any(x is not None for x in (args.platform, args.version, args.artifact_sha256)):
                raise GovernanceError("signer revocation cannot mix release parameters")
            result = revoke_signer(**source, certificate_sha256=args.revoke_signer)
        else:
            if any(x is None for x in (args.platform, args.version, args.artifact_sha256)):
                raise GovernanceError("exact release identity required")
            result = revoke(**source, app_id=args.revoke_app, platform=args.platform,
                            version=args.version, artifact_sha256=args.artifact_sha256)
        output = args.output_dir
        if output.is_symlink() or output.exists() or output.resolve() == validate_catalog.ROOT or validate_catalog.ROOT in output.resolve().parents:
            raise GovernanceError("output must be a new directory outside the source checkout")
        output.mkdir(parents=True, exist_ok=False)
        try:
            for name, payload in (("apps.json", result["catalog"]),
                                  ("release_history.json", result["history"]),
                                  ("review-audit.json", result["audit"])):
                with (output / name).open("x", encoding="utf-8") as stream:
                    json.dump(payload, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
        except Exception:
            import shutil
            shutil.rmtree(output)
            raise
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, "REVIEW_PROPOSAL_REJECTED: " + str(error) + "\n")
    print("REVIEW_ONLY_PROPOSAL; NOT_COMMITTED_NOT_DEPLOYED")

if __name__ == "__main__":
    main()
