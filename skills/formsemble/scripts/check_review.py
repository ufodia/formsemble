#!/usr/bin/env python3
"""Check a Formsemble review record or capture explicit file fingerprints.

Read-only, Python standard library only. Exit 0 means the capture succeeded or
the review checks and findings are satisfied. Exit 1 means a valid review has
outstanding checks or findings. Exit 2 means invalid input or stale files.
Review completeness covers the recorded checks and findings. Design quality and
the reviewer's work require separate evidence.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath


DISCLAIMER = (
    "Checks report consistency only; does not evaluate design quality or prove "
    "a review occurred."
)
REQUIRED_CHECKS = {
    "intent", "task", "visual", "accessibility", "responsiveness", "preservation"
}
STATUSES = {"pass", "fail", "not_tested", "not_applicable"}
METHODS = {"source", "runtime", "visual", "automated", "human", "simulation", "none"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
SHA256 = re.compile(r"[0-9a-fA-F]{64}\Z")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("Non-JSON numeric constant: " + value)


class ReviewChecker:
    def __init__(self, root):
        self.root = root
        self.errors = []
        self.blockers = []

    def error(self, location, message):
        self.errors.append(location + ": " + message)

    def fields(self, value, location, required, optional=()):
        if not isinstance(value, dict):
            self.error(location, "must be an object")
            return False
        for key in sorted(set(required) - value.keys()):
            self.error(location, "missing field " + key)
        for key in sorted(value.keys() - set(required) - set(optional)):
            self.error(location, "unknown field " + key)
        return True

    def string(self, value, location, nonempty=False):
        if not isinstance(value, str):
            self.error(location, "must be a string")
            return ""
        if nonempty and not value.strip():
            self.error(location, "must not be blank")
        return value

    def choice(self, value, location, choices):
        if not isinstance(value, str) or value not in choices:
            self.error(location, "must be one of " + ", ".join(sorted(choices)))
            return ""
        return value

    def items(self, value, location):
        if not isinstance(value, list):
            self.error(location, "must be an array")
            return []
        return value

    def file(self, value, location, evidence=False):
        fields = {"path", "sha256"}
        if evidence:
            fields |= {"kind", "description"}
        if not self.fields(value, location, fields):
            return False
        raw = self.string(value.get("path"), location + ".path", True)
        digest = self.string(value.get("sha256"), location + ".sha256", True)
        if not SHA256.fullmatch(digest):
            self.error(location + ".sha256", "must contain exactly 64 hex digits")
        kind = ""
        if evidence:
            kind = self.choice(value.get("kind"), location + ".kind", {"image", "log", "notes"})
            self.string(value.get("description"), location + ".description", True)
        if not raw:
            return False
        actual_digest = self.fingerprint(raw, location + ".path")
        if actual_digest is None:
            return False
        if actual_digest != digest.lower():
            self.error(location + ".sha256", "does not match current file bytes")
        return kind == "image" and PurePosixPath(raw).suffix.lower() in IMAGE_SUFFIXES

    def fingerprint(self, raw, location):
        if not raw.strip():
            self.error(location, "must not be blank")
            return None
        candidate = Path(raw)
        windows = PureWindowsPath(raw)
        if candidate.is_absolute() or windows.drive or windows.root:
            self.error(location, "must be relative to project root")
            return None
        if ".." in candidate.parts or ".." in windows.parts:
            self.error(location, "parent traversal is not allowed")
            return None
        if "\\" in raw:
            self.error(location, "use forward slashes in relative paths")
            return None
        try:
            resolved = (self.root / candidate).resolve(strict=True)
            try:
                resolved.relative_to(self.root)
            except ValueError:
                self.error(location, "resolves outside project root")
                return None
            if not resolved.is_file() or resolved.stat().st_size == 0:
                self.error(location, "must be a nonempty regular file")
                return None
            hasher = hashlib.sha256()
            with resolved.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    hasher.update(block)
            return hasher.hexdigest()
        except (OSError, ValueError, RuntimeError) as exc:
            self.error(location, "cannot read file (" + str(exc) + ")")
            return None

    def capture_files(self, paths):
        files = []
        seen = set()
        for index, raw in enumerate(paths):
            location = f"paths[{index}]"
            path = PurePosixPath(raw).as_posix()
            if path in seen:
                self.error(location, "duplicate selected file: " + path)
                continue
            seen.add(path)
            digest = self.fingerprint(raw, location)
            if digest is not None:
                files.append({"path": path, "sha256": digest})
        return files

    def evidence(self, value, location):
        entries = self.items(value, location)
        has_image = False
        for index, entry in enumerate(entries):
            is_image = self.file(entry, f"{location}[{index}]", evidence=True)
            has_image = has_image or is_image
        return entries, has_image

    def identifier(self, value, location, seen):
        identifier = self.string(value, location, True)
        if identifier != identifier.strip():
            self.error(location, "must not have surrounding whitespace")
        if identifier in seen:
            self.error(location, "duplicate id " + identifier)
        seen.add(identifier)
        return identifier

    def check(self, value, location, seen):
        required = {"id", "status", "method", "expected", "observed", "reason", "evidence"}
        if not self.fields(value, location, required):
            return
        identifier = self.identifier(value.get("id"), location + ".id", seen)
        status = self.choice(value.get("status"), location + ".status", STATUSES)
        method = self.choice(value.get("method"), location + ".method", METHODS)
        self.string(value.get("expected"), location + ".expected", True)
        observed = self.string(value.get("observed"), location + ".observed")
        reason = self.string(value.get("reason"), location + ".reason")
        evidence, has_image = self.evidence(value.get("evidence"), location + ".evidence")
        if status in {"pass", "fail"}:
            if not observed.strip() or not evidence:
                self.error(location, "pass/fail requires an observation and evidence")
            if method == "none":
                self.error(location, "pass/fail requires an actual review method")
        if status in {"fail", "not_tested", "not_applicable"} and not reason.strip():
            self.error(location + ".reason", "required for this status")
        if status == "not_applicable" and identifier in {"intent", "visual"}:
            self.error(location, identifier + " cannot be not_applicable")
        if status == "pass":
            if method == "simulation":
                self.error(location, "simulation cannot establish a pass")
            if identifier == "task" and method not in {"runtime", "human"}:
                self.error(location, "task pass requires runtime or human observation")
            if identifier == "visual":
                if method not in {"visual", "human"} or not has_image:
                    self.error(location, "visual pass requires visual/human review and image evidence")
            if identifier == "responsiveness" and method not in {"runtime", "visual", "human"}:
                self.error(location, "responsiveness pass requires runtime, visual, or human review")
        if status in {"fail", "not_tested"}:
            self.blockers.append("Check " + identifier + ": " + status)

    def finding(self, value, location, seen):
        required = {"id", "severity", "status", "description", "evidence"}
        if not self.fields(value, location, required, {"reason"}):
            return
        identifier = self.identifier(value.get("id"), location + ".id", seen)
        severity = self.choice(value.get("severity"), location + ".severity", {"blocker", "major", "minor"})
        status = self.choice(value.get("status"), location + ".status", {"open", "fixed", "deferred"})
        self.string(value.get("description"), location + ".description", True)
        evidence, _ = self.evidence(value.get("evidence"), location + ".evidence")
        reason = self.string(value.get("reason", ""), location + ".reason")
        if status == "fixed" and not evidence:
            self.error(location, "fixed findings require current evidence")
        if status == "deferred" and not reason.strip():
            self.error(location + ".reason", "deferred findings require a reason")
        if status == "open" or (status == "deferred" and severity in {"blocker", "major"}):
            self.blockers.append("Finding " + identifier + ": " + severity + " / " + status)

    def review(self, report):
        fields = {"schema_version", "scope", "artifact", "checks", "findings"}
        if not self.fields(report, "report", fields):
            return
        if type(report.get("schema_version")) is not int or report["schema_version"] != 1:
            self.error("schema_version", "must be integer 1")
        self.string(report.get("scope"), "scope", True)
        artifact = report.get("artifact")
        if self.fields(artifact, "artifact", {"label", "files"}):
            self.string(artifact.get("label"), "artifact.label", True)
            files = self.items(artifact.get("files"), "artifact.files")
            if not files:
                self.error("artifact.files", "at least one reviewed file is required")
            seen_paths = set()
            for index, entry in enumerate(files):
                self.file(entry, f"artifact.files[{index}]")
                if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                    portable_path = PurePosixPath(entry["path"])
                    if portable_path in seen_paths:
                        self.error(f"artifact.files[{index}].path", "duplicate reviewed file")
                    seen_paths.add(portable_path)
        seen_checks = set()
        for index, entry in enumerate(self.items(report.get("checks"), "checks")):
            self.check(entry, f"checks[{index}]", seen_checks)
        for identifier in sorted(REQUIRED_CHECKS - seen_checks):
            self.error("checks", "missing required check " + identifier)
        seen_findings = set()
        for index, entry in enumerate(self.items(report.get("findings"), "findings")):
            self.finding(entry, f"findings[{index}]", seen_findings)

    def result(self):
        valid = not self.errors
        return {
            "valid": valid,
            "complete": valid and not self.blockers,
            "errors": self.errors,
            "blockers": self.blockers,
            "disclaimer": DISCLAIMER,
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("report", nargs="?", type=Path, help="validate a JSON review report")
    mode.add_argument("--fingerprint", action="append", metavar="PATH",
                      help="capture one project-relative file as JSON (repeat for more files)")
    parser.add_argument("--project-root", required=True, type=Path, help="Root for every recorded file path")
    args = parser.parse_args(argv)
    checker = ReviewChecker(args.project_root)
    files = []
    try:
        checker.root = args.project_root.resolve(strict=True)
        if not checker.root.is_dir():
            raise ValueError("project root must be a directory")
        if args.fingerprint is not None:
            files = checker.capture_files(args.fingerprint)
        else:
            with args.report.open("r", encoding="utf-8-sig") as stream:
                report = json.load(stream, object_pairs_hook=unique_object, parse_constant=reject_constant)
            checker.review(report)
    except (OSError, ValueError, RuntimeError) as exc:
        checker.error("report" if args.fingerprint is None else "project root", str(exc))
    if args.fingerprint is not None:
        valid = not checker.errors
        result = {"valid": valid, "files": files if valid else [], "errors": checker.errors}
        exit_code = 0 if valid else 2
    else:
        result = checker.result()
        exit_code = 2 if not result["valid"] else (0 if result["complete"] else 1)
    # Keep the JSON readable by consumers even on a legacy console encoding.
    print(json.dumps(result, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
