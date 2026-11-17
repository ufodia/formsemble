#!/usr/bin/env python3
"""Verify Formsemble's release inventory and fingerprints without modifying it.

This detects changed/missing/unlisted files, not the authenticity of an untrusted
package. Run from any directory; the default root is this script's release root.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath


IGNORED_DIRS = {"__pycache__", ".git"}
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key: " + key)
        result[key] = value
    return result


def safe_relative(value):
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    posix, windows = PurePosixPath(value), PureWindowsPath(value)
    if posix.is_absolute() or windows.drive or windows.root:
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def verify(root):
    errors = []
    manifest_path = root / "MANIFEST.json"
    if manifest_path.is_symlink():
        raise ValueError("MANIFEST.json must not be a symbolic link")
    with manifest_path.open("r", encoding="utf-8-sig") as stream:
        manifest = json.load(stream, object_pairs_hook=no_duplicate_keys)
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "name", "version", "files"}:
        raise ValueError("Unexpected manifest structure")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ValueError("Unsupported manifest schema")
    if manifest["name"] != "formsemble" or not isinstance(manifest["version"], str) or not manifest["version"].strip():
        raise ValueError("Unexpected package identity")
    entries = manifest["files"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("Manifest files must be a nonempty array")
    expected = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ValueError("Unexpected file entry")
        rel, wanted = entry["path"], entry["sha256"]
        if not safe_relative(rel) or rel == "MANIFEST.json" or rel in expected:
            raise ValueError("Unsafe, duplicate, or self-referential manifest path")
        if not isinstance(wanted, str) or not HASH_RE.fullmatch(wanted):
            raise ValueError("Malformed SHA-256 fingerprint")
        expected.add(rel)
        path = root / rel
        if any(part.is_symlink() for part in [path, *path.parents] if part != root.parent):
            errors.append(rel + ": symbolic link is not permitted")
            continue
        try:
            path.resolve().relative_to(root)
            if not path.is_file():
                errors.append(rel + ": missing regular file")
            elif digest(path) != wanted:
                errors.append(rel + ": fingerprint mismatch")
        except (OSError, ValueError) as exc:
            errors.append(rel + ": " + str(exc))
    actual = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRS for part in relative.parts):
            continue
        if path.is_symlink():
            errors.append(relative.as_posix() + ": symbolic link is not permitted")
        elif path.is_file() and relative.as_posix() != "MANIFEST.json":
            actual.add(relative.as_posix())
    for rel in sorted(actual - expected):
        errors.append(rel + ": unlisted file")
    return {"valid": not errors, "name": "formsemble", "version": manifest["version"], "checked_files": len(expected), "errors": errors}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("Release root is not a directory")
        result = verify(root)
    except (OSError, ValueError, RuntimeError) as exc:
        result = {"valid": False, "errors": [str(exc)]}
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
