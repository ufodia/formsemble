"""Installer safety tests using disposable, explicitly synthetic skill fixtures.

No test installs into the real home directory. User scope patches Path.home;
CLI subprocess tests use an explicit temporary project root.
"""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


RELEASE_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = RELEASE_ROOT / "tools" / "install_skill.py"
SPEC = importlib.util.spec_from_file_location("formsemble_install_test_target", INSTALLER_PATH)
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
previous_bytecode_setting = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(installer)
finally:
    sys.dont_write_bytecode = previous_bytecode_setting


def contents(root):
    """Describe bytes and directory names without following links."""
    result = {}
    for directory, directories, files in os.walk(str(root), followlinks=False):
        for name in directories + files:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                result[relative] = ("link", os.readlink(str(path)))
            elif path.is_dir():
                result[relative] = ("directory",)
            elif path.is_file():
                result[relative] = ("file", path.read_bytes())
            else:
                result[relative] = ("special", path.lstat().st_mode)
    return result


def metadata(root):
    return {
        str(path.relative_to(root)): (path.stat().st_ino, path.stat().st_mode, path.stat().st_mtime_ns)
        for path in [root] + list(root.rglob("*"))
    }


class InstallSkillTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="formsemble-installer-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.source = self.base / "release" / "skills" / "formsemble"
        (self.source / "assets" / "empty").mkdir(parents=True)
        (self.source / "scripts").mkdir()
        (self.source / "references").mkdir()
        fixtures = {
            "SKILL.md": b"---\nname: formsemble\ndescription: Synthetic installer test data.\n---\n",
            "assets/review-template.json": b'{"synthetic_test_data": true}\r\n',
            "assets/binary.bin": bytes(range(256)) + b"\x00\xff\r\n",
            "scripts/check_review.py": b'# Synthetic test data, never executed.\nprint("fixture")\n',
            "references/space and unicode-\u00e9.md": "Synthetic test data: \u00e9 \u03bb\n".encode("utf-8"),
            ".fixture": b"Synthetic hidden file: copy the complete folder.\n",
        }
        for relative, data in fixtures.items():
            (self.source / relative).write_bytes(data)
        self.home = self.base / "temporary-home"
        self.project = self.base / "temporary-project"
        self.home.mkdir()
        self.project.mkdir()
        self.source_patch = mock.patch.object(installer, "SKILL_SOURCE", self.source)
        self.home_patch = mock.patch.object(installer.Path, "home", return_value=self.home)
        self.source_patch.start()
        self.home_patch.start()
        self.addCleanup(self.source_patch.stop)
        self.addCleanup(self.home_patch.stop)

    def call(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            result = installer.main(list(arguments))
        return result, output.getvalue(), errors.getvalue()

    def project_call(self, host="both", *extra):
        return self.call("--host", host, "--scope", "project", "--project-root", str(self.project), *extra)

    def destination(self, host, root=None):
        return (root or self.project) / installer.HOST_FOLDERS[host] / "skills" / "formsemble"

    def seed_installation(self, host, root=None):
        destination = self.destination(host, root)
        shutil.copytree(self.source, destination)
        return destination

    def make_link(self, link, target, is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=is_directory)
        except (OSError, NotImplementedError) as exc:
            self.skipTest("Symbolic links are unavailable in this test environment: " + str(exc))

    def test_host_and_scope_matrix_copies_complete_byte_exact_tree(self):
        for host in ("codex", "claude", "both"):
            for scope in ("user", "project"):
                with self.subTest(host=host, scope=scope):
                    root = self.base / (host + "-" + scope)
                    root.mkdir()
                    arguments = ["--host", host, "--scope", scope]
                    if scope == "project":
                        arguments += ["--project-root", str(root)]
                    with mock.patch.object(installer.Path, "home", return_value=root):
                        result, output, errors = self.call(*arguments)
                    self.assertEqual(result, 0, errors)
                    self.assertIn("Installed", output)
                    requested = ("codex", "claude") if host == "both" else (host,)
                    for selected_host in requested:
                        self.assertEqual(contents(self.destination(selected_host, root)), contents(self.source))
                    for other in {"codex", "claude"} - set(requested):
                        self.assertFalse((root / installer.HOST_FOLDERS[other]).exists())

    def test_dry_run_does_not_create_or_modify_any_path(self):
        for scope in ("user", "project"):
            with self.subTest(scope=scope):
                before = contents(self.base)
                arguments = ["--host", "both", "--scope", scope, "--dry-run"]
                if scope == "project":
                    arguments += ["--project-root", str(self.project)]
                result, output, errors = self.call(*arguments)
                self.assertEqual(result, 0, errors)
                self.assertEqual(output.count("Dry run: would install"), 2)
                self.assertEqual(contents(self.base), before)

    def test_identical_installation_is_a_no_op_including_permissions_and_times(self):
        destination = self.seed_installation("codex")
        (destination / "SKILL.md").chmod(stat.S_IRUSR)
        before_bytes, before_metadata = contents(destination), metadata(destination)
        result, output, errors = self.project_call("codex")
        self.assertEqual(result, 0, errors)
        self.assertIn("Already installed", output)
        self.assertEqual(contents(destination), before_bytes)
        self.assertEqual(metadata(destination), before_metadata)

    def test_different_installations_block_all_hosts_before_any_write(self):
        mutations = (
            ("modified", lambda destination: (destination / "SKILL.md").write_bytes(b"User work\n")),
            ("missing", lambda destination: (destination / "assets" / "binary.bin").unlink()),
            ("extra", lambda destination: (destination / "user-note.txt").write_bytes(b"User work\n")),
            ("empty-directory", lambda destination: (destination / "user-empty-directory").mkdir()),
        )
        for name, mutate in mutations:
            with self.subTest(change=name):
                root = self.base / name
                root.mkdir()
                destination = self.seed_installation("claude", root)
                mutate(destination)
                before = contents(root)
                result, _, errors = self.call("--host", "both", "--scope", "project", "--project-root", str(root))
                self.assertEqual(result, 1)
                self.assertIn("left untouched", errors)
                self.assertEqual(contents(root), before)
                self.assertFalse((root / ".agents").exists())

    def test_identical_host_can_coexist_with_a_new_host_installation(self):
        existing = self.seed_installation("codex")
        before = metadata(existing)
        result, output, errors = self.project_call()
        self.assertEqual(result, 0, errors)
        self.assertIn("Already installed", output)
        self.assertIn("Installed", output)
        self.assertEqual(metadata(existing), before)
        self.assertEqual(contents(self.destination("claude")), contents(self.source))

    def test_project_root_is_explicit_and_never_falls_back_to_home(self):
        before = contents(self.base)
        result, _, errors = self.call("--host", "both", "--scope", "project")
        self.assertEqual(result, 1)
        self.assertIn("requires an explicit --project-root", errors)
        self.assertEqual(contents(self.base), before)

    def test_project_root_is_not_silently_ignored_for_user_scope(self):
        before = contents(self.base)
        result, _, errors = self.call("--host", "codex", "--scope", "user", "--project-root", str(self.project))
        self.assertEqual(result, 1)
        self.assertIn("applies only", errors)
        self.assertEqual(contents(self.base), before)

    def test_missing_or_non_directory_project_root_is_rejected_without_writes(self):
        file_root = self.base / "file-root"
        file_root.write_bytes(b"User file\n")
        for root in (self.base / "missing-root", file_root):
            with self.subTest(root=root.name):
                before = contents(self.base)
                result, _, _ = self.call("--host", "both", "--scope", "project", "--project-root", str(root))
                self.assertEqual(result, 1)
                self.assertEqual(contents(self.base), before)

    def test_source_links_are_rejected_including_root_parent_and_dangling_links(self):
        source_link = self.base / "linked-source"
        self.make_link(source_link, self.source, True)
        parent_link = self.base / "linked-skills"
        self.make_link(parent_link, self.source.parent, True)
        for source in (source_link, parent_link / "formsemble"):
            with self.subTest(source=str(source)):
                before = contents(self.base)
                with mock.patch.object(installer, "SKILL_SOURCE", source):
                    result, _, errors = self.project_call()
                self.assertEqual(result, 1)
                self.assertIn("symbolic link", errors)
                self.assertEqual(contents(self.base), before)
        for name, target, directory in (
            ("file-link", self.source / "SKILL.md", False),
            ("directory-link", self.source / "references", True),
            ("dangling-link", self.base / "absent", False),
        ):
            with self.subTest(entry=name):
                link = self.source / name
                self.make_link(link, target, directory)
                before = contents(self.base)
                result, _, errors = self.project_call()
                self.assertEqual(result, 1)
                self.assertIn("symbolic link", errors)
                self.assertEqual(contents(self.base), before)
                link.unlink()

    def test_all_destination_link_components_are_rejected_without_following_them(self):
        outside = self.base / "outside-target"
        outside.mkdir()
        (outside / "sentinel.txt").write_bytes(b"Existing user work\n")
        components = (".agents", ".agents/skills", ".agents/skills/formsemble")
        for index, relative in enumerate(components):
            with self.subTest(component=relative):
                root = self.base / ("link-root-" + str(index))
                root.mkdir()
                link = root / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                self.make_link(link, outside, True)
                before = contents(self.base)
                result, _, errors = self.call("--host", "both", "--scope", "project", "--project-root", str(root))
                self.assertEqual(result, 1)
                self.assertIn("symbolic link", errors)
                self.assertEqual(contents(self.base), before)

    def test_links_inside_an_existing_installation_are_rejected(self):
        destination = self.seed_installation("codex")
        link = destination / "references" / "extra-link"
        self.make_link(link, destination / "SKILL.md")
        before = contents(self.base)
        result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("symbolic link", errors)
        self.assertEqual(contents(self.base), before)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "Named pipes are unavailable")
    def test_nonregular_source_file_is_rejected_without_opening_it(self):
        os.mkfifo(str(self.source / "named-pipe"))
        before = contents(self.base)
        result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("nonregular", errors)
        self.assertEqual(contents(self.base), before)

    def test_file_in_a_parent_path_blocks_both_hosts_before_writes(self):
        (self.project / ".claude").mkdir()
        (self.project / ".claude" / "skills").write_bytes(b"Existing user work\n")
        before = contents(self.project)
        result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("not a directory", errors)
        self.assertEqual(contents(self.project), before)

    def test_preflight_checks_access_for_both_hosts_before_writes(self):
        (self.project / ".claude").mkdir()
        before = contents(self.project)
        real_access = installer.os.access

        def access(path, mode):
            return False if Path(path) == self.project / ".claude" else real_access(path, mode)

        with mock.patch.object(installer.os, "access", side_effect=access):
            result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("not writable/searchable", errors)
        self.assertEqual(contents(self.project), before)

    def test_failure_staging_second_host_removes_all_new_paths(self):
        before = contents(self.project)
        real_copy = installer._copy_snapshot
        count = 0

        def copy(source, stage, snapshot):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("Synthetic second-host copy failure")
            return real_copy(source, stage, snapshot)

        with mock.patch.object(installer, "_copy_snapshot", side_effect=copy):
            result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("Synthetic second-host copy failure", errors)
        self.assertEqual(contents(self.project), before)

    def test_failure_publishing_second_host_rolls_back_first_host(self):
        before = contents(self.project)
        real_rename = installer.os.rename
        count = 0

        def rename(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("Synthetic second-host rename failure")
            return real_rename(source, destination)

        with mock.patch.object(installer.os, "rename", side_effect=rename):
            result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("Synthetic second-host rename failure", errors)
        self.assertEqual(contents(self.project), before)

    def test_failure_does_not_roll_back_a_preexisting_identical_installation(self):
        existing = self.seed_installation("codex")
        before_contents, before_metadata = contents(self.project), metadata(existing)
        with mock.patch.object(installer.os, "rename", side_effect=OSError("Synthetic rename failure")):
            result, _, _ = self.project_call()
        self.assertEqual(result, 1)
        self.assertEqual(contents(self.project), before_contents)
        self.assertEqual(metadata(existing), before_metadata)

    def test_destination_that_appears_after_staging_is_never_overwritten(self):
        real_publish = installer._publish_stage

        def publish(stage, plan):
            if plan.host == "claude":
                plan.destination.mkdir()
                (plan.destination / "user-work.txt").write_bytes(b"Concurrent user work\n")
            return real_publish(stage, plan)

        with mock.patch.object(installer, "_publish_stage", side_effect=publish):
            result, _, _ = self.project_call()
        self.assertEqual(result, 1)
        self.assertFalse(self.destination("codex").exists())
        self.assertEqual(contents(self.destination("claude")), {"user-work.txt": ("file", b"Concurrent user work\n")})
        self.assertFalse(list(self.project.rglob(".formsemble-stage-*")))

    def test_rollback_preserves_concurrent_edits_to_newly_installed_files(self):
        real_rename = installer.os.rename
        count = 0

        def rename(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                (self.destination("codex") / "SKILL.md").write_bytes(b"Concurrent user edit\n")
                raise OSError("Synthetic rename failure after a user edit")
            return real_rename(source, destination)

        with mock.patch.object(installer.os, "rename", side_effect=rename):
            result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("Preserved an installation modified during rollback", errors)
        self.assertEqual((self.destination("codex") / "SKILL.md").read_bytes(), b"Concurrent user edit\n")
        self.assertFalse(self.destination("claude").exists())
        self.assertFalse(list(self.project.rglob(".formsemble-stage-*")))

    def test_source_change_between_stages_prevents_inconsistent_installations(self):
        real_copy = installer._copy_snapshot
        count = 0

        def copy(source, stage, snapshot):
            nonlocal count
            count += 1
            if count == 2:
                (source / "SKILL.md").write_bytes(b"Synthetic source change during install\n")
            return real_copy(source, stage, snapshot)

        with mock.patch.object(installer, "_copy_snapshot", side_effect=copy):
            result, _, errors = self.project_call()
        self.assertEqual(result, 1)
        self.assertIn("changed during installation", errors)
        self.assertEqual(contents(self.project), {})

    def test_host_instructions_and_settings_remain_unchanged(self):
        controls = {
            "AGENTS.md": b"Existing project instructions\n",
            "CLAUDE.md": b"Existing project instructions\r\n",
            ".claude/settings.json": b'{"existing": true}\n',
            ".agents/settings.json": b'{"existing": true}\n',
        }
        for relative, data in controls.items():
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        result, _, errors = self.project_call()
        self.assertEqual(result, 0, errors)
        for relative, data in controls.items():
            self.assertEqual((self.project / relative).read_bytes(), data)

    def test_actual_cli_uses_its_bundled_source_from_an_unrelated_working_directory(self):
        script = self.base / "release" / "tools" / "install_skill.py"
        script.parent.mkdir()
        shutil.copyfile(INSTALLER_PATH, script)
        completed = subprocess.run(
            [sys.executable, str(script), "--host", "both", "--scope", "project", "--project-root", str(self.project)],
            cwd=str(self.base), capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for host in ("codex", "claude"):
            self.assertEqual(contents(self.destination(host)), contents(self.source))

    def test_cli_rejects_an_arbitrary_source_option(self):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            with self.assertRaises(SystemExit) as caught:
                installer.main(["--host", "codex", "--scope", "user", "--source", str(self.source)])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("unrecognized arguments", errors.getvalue())
        self.assertEqual(contents(self.home), {})


if __name__ == "__main__":
    unittest.main()
