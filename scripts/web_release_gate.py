#!/usr/bin/env python3
"""Fail-closed STATIC owner-reviewed web-deployment catalogue policy.

This checks metadata only, not TLS redirects, live deployment bytes, GitHub build
attestations, owner identity or effective browser integrity. Never auto-approve.
"""
import re
from urllib.parse import urlsplit

import release_history
import release_integrity

SHA40 = re.compile(r"[0-9a-f]{40}\\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\\Z")
HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?\\Z")
PATH = re.compile(r"/[A-Za-z0-9_./-]*\\Z")
ORIGIN_KEYS = {"app_id", "source_repo", "origin"}
RELEASE_KEYS = {"app_id", "source_repo", "source_sha", "artifact_sha256",
                "version", "deployment_url", "status"}


class WebReleaseError(ValueError):
    """Web deployment lacks trusted, immutable owner-reviewed metadata."""


def parse_https(value, origin_only=False):
    if not isinstance(value, str) or len(value) > 2048 or any(c.isspace() for c in value):
        raise WebReleaseError("invalid web URL")
    try:
        url = urlsplit(value)
        host = url.hostname
        valid = (url.scheme == "https" and host is not None and HOST.fullmatch(host)
                 and url.netloc == host and url.port is None and not url.username
                 and not url.password and not url.query and not url.fragment
                 and not url.path.startswith("//"))
    except ValueError as exc:
        raise WebReleaseError("malformed web URL") from exc
    if not valid or not PATH.fullmatch(url.path or "/"):
        raise WebReleaseError("web URL must use canonical HTTPS host and simple path")
    if any(segment in (".", "..") for segment in url.path.split("/")):
        raise WebReleaseError("web URL contains path traversal")
    if origin_only and url.path:
        raise WebReleaseError("trusted origin cannot contain a path")
    return "https://" + host


def validate_origins(data):
    if (not isinstance(data, dict) or set(data) != {"schema_version", "origins"}
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or not isinstance(data["origins"], list) or len(data["origins"]) > 1000):
        raise WebReleaseError("invalid trusted web origin registry")
    seen = set()
    for row in data["origins"]:
        if not isinstance(row, dict) or set(row) != ORIGIN_KEYS:
            raise WebReleaseError("invalid trusted origin record")
        for name in ("app_id", "source_repo"):
            if not isinstance(row[name], str) or not release_integrity.ID.fullmatch(row[name]):
                raise WebReleaseError("invalid trusted web " + name)
        if parse_https(row["origin"], origin_only=True) != row["origin"]:
            raise WebReleaseError("noncanonical trusted origin")
        if row["app_id"] in seen:
            raise WebReleaseError("duplicate web origin registration")
        seen.add(row["app_id"])
    return data


def validate_releases(data):
    if (not isinstance(data, dict) or set(data) != {"schema_version", "releases"}
            or type(data["schema_version"]) is not int or data["schema_version"] != 1
            or not isinstance(data["releases"], list) or len(data["releases"]) > 10000):
        raise WebReleaseError("invalid web release history")
    seen = set()
    for row in data["releases"]:
        if not isinstance(row, dict) or set(row) != RELEASE_KEYS:
            raise WebReleaseError("invalid web release record")
        for name in ("app_id", "source_repo"):
            if not isinstance(row[name], str) or not release_integrity.ID.fullmatch(row[name]):
                raise WebReleaseError("invalid web release " + name)
        release_history.semver_key(row["version"])
        if not isinstance(row["source_sha"], str) or not SHA40.fullmatch(row["source_sha"]):
            raise WebReleaseError("invalid web source commit SHA")
        if not isinstance(row["artifact_sha256"], str) or not SHA64.fullmatch(row["artifact_sha256"]):
            raise WebReleaseError("invalid web artifact digest")
        parse_https(row["deployment_url"])
        if "/releases/" + row["source_sha"] + "/" not in urlsplit(row["deployment_url"]).path:
            raise WebReleaseError("web deployment URL is not source-SHA-versioned")
        if row["status"] not in {"approved", "revoked"}:
            raise WebReleaseError("invalid web review status")
        key = (row["app_id"], row["version"])
        if key in seen:
            raise WebReleaseError("duplicate web app/version approval")
        seen.add(key)
    return data


def check_web_release(app, origins, releases):
    validate_origins(origins)
    validate_releases(releases)
    if app["platforms"] != ["web"]:
        raise WebReleaseError("web release must identify only web platform")
    proof = app.get("release_proof")
    if not isinstance(proof, dict) or set(proof) != {
        "source_repo", "source_sha", "artifact_sha256"
    }:
        raise WebReleaseError("web release proof must include source and artifact digest")
    registered = [x for x in origins["origins"] if x["app_id"] == app["id"]]
    if len(registered) != 1:
        raise WebReleaseError("web origin has no independent owner registration")
    origin = registered[0]
    url = app.get("download_url")
    if parse_https(url) != origin["origin"]:
        raise WebReleaseError("web launch URL differs from registered HTTPS origin")
    history = [x for x in releases["releases"] if x["app_id"] == app["id"]]
    if not history:
        raise WebReleaseError("no independently approved web deployment")
    latest = max(history, key=lambda x: release_history.semver_key(x["version"]))
    if latest["status"] != "approved":
        raise WebReleaseError("latest web release revoked")
    if (latest["version"] != app["version"] or latest["deployment_url"] != url
            or latest["source_repo"] != origin["source_repo"]
            or any(latest[key] != proof[key] for key in (
                "source_repo", "source_sha", "artifact_sha256"))):
        raise WebReleaseError("web launch does not match latest owner-reviewed deployment")
    return True
