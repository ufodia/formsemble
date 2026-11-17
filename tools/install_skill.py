#!/usr/bin/env python3
"""Install the bundled Formsemble skill without replacing an existing skill.

Python 3.9+ and the standard library are sufficient. This program copies local
files only: it never downloads content, runs a host, or edits host settings.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


SKILL_NAME = "formsemble"
RELEASE_ROOT = Path(__file__).resolve().parent.parent
SKILL_SOURCE = RELEASE_ROOT / "skills" / SKILL_NAME
HOST_FOLDERS = {"codex": ".agents", "claude": ".claude"}
HOST_LABELS = {"codex": "Codex", "claude": "Claude Code"}


class InstallError(Exception):
    """An installation cannot proceed without risking existing work."""


@dataclass(frozen=True)
class TreeSnapshot:
    directories: Tuple[str, ...]
    files: Dict[str, str]


@dataclass(frozen=True)
class Plan:
    host: str
    root: Path
    destination: Path
    already_installed: bool


@dataclass(frozen=True)
class OwnedDirectory:
    path: Path
    identity: Tuple[int, int]


def _is_link(info) -> bool:
    # Windows junctions and other reparse points also redirect filesystem
    # access, even when an older Python does not label them as symlinks.
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & reparse_flag)


def _identity(path: Path) -> Tuple[int, int]:
    info = path.lstat()
    if _is_link(info) or not stat.S_ISDIR(info.st_mode):
        raise InstallError("Expected an ordinary directory: " + str(path))
    return info.st_dev, info.st_ino


def _entry(path: Path):
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _ordinary_directory(path: Path, label: str) -> None:
    info = _entry(path)
    if info is None:
        raise InstallError(label + " does not exist: " + str(path))
    if _is_link(info):
        raise InstallError(label + " must not be a symbolic link: " + str(path))
    if not stat.S_ISDIR(info.st_mode):
        raise InstallError(label + " must be a directory: " + str(path))


def _safe_chain(root: Path, target: Path) -> None:
    """Check every existing directory between a selected root and target."""
    _ordinary_directory(root, "Selected root")
    try:
        parts = target.relative_to(root).parts
    except ValueError as exc:
        raise InstallError("Destination is outside the selected root") from exc
    current = root
    missing = False
    for part in parts:
        current = current / part
        if missing:
            continue
        info = _entry(current)
        if info is None:
            missing = True
        elif _is_link(info):
            raise InstallError("Refusing a symbolic link in the installation path: " + str(current))
        elif not stat.S_ISDIR(info.st_mode):
            raise InstallError("Installation path is not a directory: " + str(current))


def _read_regular(path: Path):
    """Open a regular file, refusing a final-component link where supported."""
    before = path.lstat()
    if _is_link(before) or not stat.S_ISREG(before.st_mode):
        raise InstallError("Refusing a symbolic link or nonregular file: " + str(path))
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(str(path), flags)
    try:
        after = os.fstat(descriptor)
        if not stat.S_ISREG(after.st_mode) or (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise InstallError("File changed while it was being opened: " + str(path))
        return os.fdopen(descriptor, "rb")
    except BaseException:
        os.close(descriptor)
        raise


def snapshot_tree(root: Path) -> TreeSnapshot:
    """Return directory names and byte hashes; reject all links/special files."""
    _ordinary_directory(root, "Skill directory")
    directories = []
    files = {}

    def visit(directory: Path) -> None:
        _ordinary_directory(directory, "Skill directory")
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            info = path.lstat()
            relative = path.relative_to(root).as_posix()
            if _is_link(info):
                raise InstallError("Refusing a symbolic link in a skill: " + str(path))
            if stat.S_ISDIR(info.st_mode):
                directories.append(relative)
                visit(path)
            elif stat.S_ISREG(info.st_mode):
                hasher = hashlib.sha256()
                with _read_regular(path) as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        hasher.update(block)
                files[relative] = hasher.hexdigest()
            else:
                raise InstallError("Refusing a nonregular file in a skill: " + str(path))

    visit(root)
    return TreeSnapshot(tuple(sorted(directories)), files)


def _source_snapshot() -> Tuple[Path, TreeSnapshot]:
    # The CLI deliberately has no source/download option. The package is the
    # trust boundary; links within its skills directory are not followed.
    source = SKILL_SOURCE
    _ordinary_directory(source.parent, "Bundled skills directory")
    snapshot = snapshot_tree(source)
    if "SKILL.md" not in snapshot.files:
        raise InstallError("Bundled Formsemble skill is missing SKILL.md: " + str(source))
    return source, snapshot


def plan_installation(host: str, scope: str, project_root: Optional[Path], snapshot: TreeSnapshot) -> List[Plan]:
    if scope == "project":
        if project_root is None:
            raise InstallError("--scope project requires an explicit --project-root PATH")
        selected_root = project_root.expanduser()
    else:
        if project_root is not None:
            raise InstallError("--project-root applies only to --scope project")
        selected_root = Path.home()
    # Resolve the explicitly selected root once. Beneath that root, no
    # installation component may be a link, even a link back into the root.
    root = selected_root.resolve(strict=True)
    _ordinary_directory(root, "Selected root")
    hosts = ("codex", "claude") if host == "both" else (host,)
    plans = []
    for selected_host in hosts:
        destination = root / HOST_FOLDERS[selected_host] / "skills" / SKILL_NAME
        _safe_chain(root, destination)
        exists = _entry(destination) is not None
        if exists and snapshot_tree(destination) != snapshot:
            raise InstallError(
                "Existing installation differs from the bundled skill; left untouched: "
                + str(destination)
                + ". Move or review it yourself before installing."
            )
        if not exists:
            accessible_parent = destination.parent
            while _entry(accessible_parent) is None:
                accessible_parent = accessible_parent.parent
            if not os.access(str(accessible_parent), os.W_OK | os.X_OK):
                raise InstallError("Installation parent is not writable/searchable: " + str(accessible_parent))
        plans.append(Plan(selected_host, root, destination, exists))
    return plans


def _ensure_parents(plan: Plan, created: List[OwnedDirectory]) -> None:
    _safe_chain(plan.root, plan.destination.parent)
    current = plan.root
    for part in plan.destination.parent.relative_to(plan.root).parts:
        current = current / part
        try:
            current.mkdir()
        except FileExistsError:
            _ordinary_directory(current, "Installation parent")
        else:
            created.append(OwnedDirectory(current, _identity(current)))


def _copy_snapshot(source: Path, stage: Path, snapshot: TreeSnapshot) -> None:
    if snapshot_tree(source) != snapshot:
        raise InstallError("Bundled skill changed during installation; retry after reviewing it")
    for relative in sorted(snapshot.directories, key=lambda value: (value.count("/"), value)):
        (stage / relative).mkdir()
    for relative, expected_digest in sorted(snapshot.files.items()):
        hasher = hashlib.sha256()
        with _read_regular(source / relative) as incoming, (stage / relative).open("xb") as outgoing:
            for block in iter(lambda: incoming.read(1024 * 1024), b""):
                outgoing.write(block)
                hasher.update(block)
        if hasher.hexdigest() != expected_digest:
            raise InstallError("Bundled file changed while copying: " + relative)
    if snapshot_tree(source) != snapshot or snapshot_tree(stage) != snapshot:
        raise InstallError("Bundled or staged files changed during installation")


def _remove_empty_owned(directory: OwnedDirectory) -> None:
    if _entry(directory.path) is None:
        return
    if _identity(directory.path) != directory.identity:
        raise InstallError("Preserved a directory that was replaced during installation: " + str(directory.path))
    directory.path.rmdir()


def _publish_stage(stage: OwnedDirectory, plan: Plan) -> OwnedDirectory:
    _safe_chain(plan.root, plan.destination.parent)
    if _identity(stage.path) != stage.identity:
        raise InstallError("Staging directory was replaced during installation: " + str(stage.path))
    if os.name == "nt":
        # Windows rename already refuses every existing destination; replacing
        # even our own empty reservation would fail on that platform.
        os.rename(str(stage.path), str(plan.destination))
        return OwnedDirectory(plan.destination, stage.identity)
    # An exclusive mkdir reserves a previously absent name. A destination that
    # appears after preflight is never adopted or removed. Rename replaces only
    # our own empty reservation, and fails if somebody has added files to it.
    plan.destination.mkdir()
    reservation = OwnedDirectory(plan.destination, _identity(plan.destination))
    try:
        if _identity(plan.destination) != reservation.identity:
            raise InstallError("Installation reservation was replaced: " + str(plan.destination))
        os.rename(str(stage.path), str(plan.destination))
    except BaseException:
        try:
            _remove_empty_owned(reservation)
        except (OSError, InstallError):
            # A nonempty or replaced reservation may contain someone else's
            # work. Preserve it, then report the original installation failure.
            pass
        raise
    return OwnedDirectory(plan.destination, stage.identity)


def _remove_stage(stage: OwnedDirectory) -> None:
    if _entry(stage.path) is None:
        return
    if _identity(stage.path) != stage.identity:
        raise InstallError("Preserved a replaced staging directory: " + str(stage.path))
    shutil.rmtree(stage.path)


def install_plans(source: Path, snapshot: TreeSnapshot, plans: List[Plan]) -> None:
    """Stage every new installation, then publish; undo ordinary failures."""
    parents = []
    stages = []
    published = []
    try:
        # Recheck all destinations before the first mutation. Plans for an
        # identical installation remain read-only throughout the operation.
        for plan in plans:
            _safe_chain(plan.root, plan.destination)
            exists = _entry(plan.destination) is not None
            if exists != plan.already_installed:
                raise InstallError("Installation path changed after preflight: " + str(plan.destination))
            if exists and snapshot_tree(plan.destination) != snapshot:
                raise InstallError("Existing installation changed after preflight: " + str(plan.destination))
        for plan in plans:
            if plan.already_installed:
                continue
            _ensure_parents(plan, parents)
            path = Path(tempfile.mkdtemp(prefix=".formsemble-stage-", dir=str(plan.destination.parent)))
            stage = OwnedDirectory(path, _identity(path))
            stages.append((stage, plan))
            _copy_snapshot(source, path, snapshot)
        for stage, plan in stages:
            published.append(_publish_stage(stage, plan))
    except BaseException as exc:
        cleanup_errors = []
        for directory in reversed(published):
            try:
                if _identity(directory.path) != directory.identity or snapshot_tree(directory.path) != snapshot:
                    raise InstallError("Preserved an installation modified during rollback: " + str(directory.path))
                shutil.rmtree(directory.path)
            except (OSError, InstallError) as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        for stage, _ in reversed(stages):
            try:
                _remove_stage(stage)
            except (OSError, InstallError) as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        for directory in reversed(parents):
            try:
                _remove_empty_owned(directory)
            except OSError:
                # Nonempty directories, including concurrent user additions,
                # must remain. Empty directories are best-effort cleanup only.
                pass
            except InstallError as cleanup_exc:
                cleanup_errors.append(str(cleanup_exc))
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        message = str(exc)
        if cleanup_errors:
            message += "\nCleanup preserved paths that need review:\n  " + "\n  ".join(cleanup_errors)
        raise InstallError(message) from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, choices=("codex", "claude", "both"), help="Host(s) to install for")
    parser.add_argument("--scope", required=True, choices=("user", "project"), help="User or explicit project installation")
    parser.add_argument("--project-root", type=Path, help="Existing project directory; required for project scope")
    parser.add_argument("--dry-run", action="store_true", help="Validate and describe the operation without writing files")
    args = parser.parse_args(argv)
    try:
        source, snapshot = _source_snapshot()
        plans = plan_installation(args.host, args.scope, args.project_root, snapshot)
        if not args.dry_run:
            install_plans(source, snapshot, plans)
        for plan in plans:
            if plan.already_installed:
                action = "Already installed (identical tree)"
            elif args.dry_run:
                action = "Dry run: would install"
            else:
                action = "Installed"
            print(action + " Formsemble for " + HOST_LABELS[plan.host] + ": " + str(plan.destination))
        return 0
    except (InstallError, OSError, ValueError, RuntimeError) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
