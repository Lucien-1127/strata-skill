#!/usr/bin/env python3
"""Read-only evidence manifest validator for Agent Reliability Audit.

Exit 0: structurally/evidentially consistent completed report.
Exit 2: structurally valid report with an unresolved status.
Exit 1: invalid, inconsistent or missing evidence.

This validates claims and file digests, NOT whether the report or evidence is truthful.
No network, subprocess, environment, deletion, or write operations are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

STATUSES = {
    "completed", "blocked", "regressed", "unverified",
    "budget_exhausted", "no_progress",
}
DIMENSIONS = {"functional", "safety", "regression", "customer"}
RESULTS = {"pass", "fail", "skipped"}
NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,99}$")
SHA = re.compile(r"^[0-9a-fA-F]{64}$")
MAX_REPORT = 256 * 1024
MAX_EVIDENCE = 10 * 1024 * 1024
MAX_CHECKS = 40


class DuplicateKeyError(ValueError):
    pass


def no_duplicate_keys(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise DuplicateKeyError(f"Duplicate JSON key: {key}")
        output[key] = value
    return output


def no_special_number(value):
    raise ValueError(f"Nonfinite JSON number is not allowed: {value}")


def load_report(path: Path):
    raw = path.read_bytes()
    if len(raw) > MAX_REPORT:
        raise ValueError("Report exceeds 256KB")
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=no_duplicate_keys,
        parse_constant=no_special_number,
    )


def valid_evidence_path(root: Path, supplied: str):
    if not isinstance(supplied, str) or not supplied or "\x00" in supplied:
        raise ValueError("Missing or invalid evidence path")
    if "\\" in supplied or ":" in supplied or supplied.startswith("/"):
        raise ValueError("Evidence path must be portable and relative")
    parts = supplied.split("/")
    if any(p in {"", ".", ".."} for p in parts):
        raise ValueError("Evidence traversal or ambiguous path component")
    root = root.resolve()
    candidate = root.joinpath(*parts)
    if any(p.is_symlink() for p in (root.joinpath(*parts[:i]) for i in range(1, len(parts) + 1))):
        raise ValueError("Evidence symlinks are forbidden")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Evidence path escapes approved root")
    if not resolved.is_file():
        raise ValueError("Evidence file does not exist")
    size = resolved.stat().st_size
    if size <= 0 or size > MAX_EVIDENCE:
        raise ValueError("Evidence must be nonempty and at most 10MB")
    return resolved


def validate(report, evidence_root: Path):
    findings = []
    if not isinstance(report, dict):
        return {"verdict": "invalid", "exit_code": 1,
                "findings": ["Report must be a JSON object"]}

    task_id = report.get("task_id")
    if not isinstance(task_id, str) or not NAME.fullmatch(task_id):
        findings.append("task_id must be 1-100 portable characters")
    if report.get("schema_version") != "1.0":
        findings.append("schema_version must equal 1.0")
    goal = report.get("objective")
    if not isinstance(goal, str) or not (1 <= len(goal.strip()) <= 2000):
        findings.append("objective must be a nonempty text under 2001 characters")
    status = report.get("status")
    if not isinstance(status, str) or status not in STATUSES:
        findings.append("Unknown status")
    attempts = report.get("attempts")
    max_attempts = report.get("max_attempts")
    if type(attempts) is not int or attempts < 0:
        findings.append("attempts must be a nonnegative integer")
    if type(max_attempts) is not int or not (1 <= max_attempts <= 50):
        findings.append("max_attempts must be an integer from 1 to 50")
    if type(attempts) is int and type(max_attempts) is int and attempts > max_attempts:
        findings.append("attempts exceeded max_attempts")
    if status == "completed" and attempts == 0:
        findings.append("completed requires at least one actual attempt")

    blockers = report.get("blockers", [])
    if not isinstance(blockers, list) or not all(isinstance(b, str) and b.strip() for b in blockers):
        findings.append("blockers must be a list of nonempty strings")
    elif status == "blocked" and not blockers:
        findings.append("blocked requires an explicit blocker")

    checks = report.get("checks")
    if not isinstance(checks, list) or len(checks) > MAX_CHECKS:
        findings.append("checks must be a list of at most 40 items")
        checks = []
    identifiers = set()
    passes = set()
    for index, item in enumerate(checks):
        label = f"check[{index}]"
        if not isinstance(item, dict):
            findings.append(f"{label}: must be an object")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not NAME.fullmatch(item_id):
            findings.append(f"{label}: invalid id")
        elif item_id in identifiers:
            findings.append(f"{label}: duplicated id")
        else:
            identifiers.add(item_id)
        dimension = item.get("dimension")
        if not isinstance(dimension, str) or dimension not in DIMENSIONS:
            findings.append(f"{label}: invalid dimension")
        result = item.get("result")
        if not isinstance(result, str) or result not in RESULTS:
            findings.append(f"{label}: invalid result")
        executed = item.get("executed")
        if type(executed) is not bool:
            findings.append(f"{label}: executed must be boolean")
        exit_code = item.get("exit_code")
        if exit_code is not None and (type(exit_code) is not int or not 0 <= exit_code <= 255):
            findings.append(f"{label}: invalid exit_code")
        if result == "pass" and executed is not True:
            findings.append(f"{label}: cannot pass when not executed")
        if result == "pass" and exit_code != 0:
            findings.append(f"{label}: passing evidence requires exit_code 0")
        if executed is False and exit_code is not None:
            findings.append(f"{label}: unexecuted check cannot contain exit_code")

        path = item.get("evidence_path")
        digest = item.get("evidence_sha256")
        if result == "pass" and (not path or not digest):
            findings.append(f"{label}: passing checks require evidence path and SHA-256")
        if path is not None or digest is not None:
            if not isinstance(digest, str) or not SHA.fullmatch(digest):
                findings.append(f"{label}: invalid evidence_sha256")
            try:
                file = valid_evidence_path(evidence_root, path)
            except (OSError, ValueError) as exc:
                findings.append(f"{label}: {exc}")
            else:
                if isinstance(digest, str) and SHA.fullmatch(digest):
                    with file.open("rb") as stream:
                        actual = hashlib.file_digest(stream, "sha256").hexdigest()
                    if actual.lower() != digest.lower():
                        findings.append(f"{label}: evidence checksum mismatch")
        if isinstance(dimension, str) and dimension in DIMENSIONS and result == "pass" and executed is True and exit_code == 0:
            passes.add(dimension)

    if status == "completed":
        missing = sorted(DIMENSIONS - passes)
        if missing:
            findings.append("completed missing passing gates: " + ", ".join(missing))
        if any(not isinstance(c, dict) or c.get("result") != "pass" for c in checks):
            findings.append("completed cannot contain failed/skipped checks")
        if blockers:
            findings.append("completed cannot contain unresolved blockers")

    verdict = "invalid" if findings else ("verified_completed" if status == "completed" else "unresolved")
    return {"verdict": verdict, "exit_code": 1 if findings else (0 if status == "completed" else 2),
            "task_id": task_id, "declared_status": status,
            "checked_gates": sorted(passes),
            "findings": findings,
            "limitations": "The checksums and assertions are consistent, not independently proven authentic."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True, help="Existing JSON closeout report")
    parser.add_argument("--evidence-root", type=Path, required=True, help="Approved evidence folder")
    args = parser.parse_args(argv)
    try:
        if not args.evidence_root.is_dir():
            raise ValueError("Evidence root must exist and be a directory")
        outcome = validate(load_report(args.report), args.evidence_root)
    except (OSError, ValueError, UnicodeError) as exc:
        outcome = {"verdict": "invalid", "exit_code": 1, "findings": [str(exc)]}
    print(json.dumps(outcome, ensure_ascii=False, sort_keys=True))
    return outcome["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
