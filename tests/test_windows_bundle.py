"""Payload and static contract tests; these do not execute CMD or PowerShell.

Run from the release root: python -m unittest discover -s tests -p 'test_windows_bundle.py'
An actual Windows double-click installation still needs a Windows host.
"""

import base64
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "tools" / "build_windows_bundle.py"
SPEC = importlib.util.spec_from_file_location("build_windows_bundle", SOURCE)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


def unpack_payload(path: Path) -> dict:
    """Read the documented envelope independently of the generator functions."""
    content = path.read_bytes().decode("ascii")
    match = re.search(
        r"(?ms)^# BEGIN FORMSEMBLE PAYLOAD ([0-9a-f]{64})\r?\n"
        r"([A-Za-z0-9+/=\r\n]+)^# END FORMSEMBLE PAYLOAD\r?$", content)
    if not match:
        raise ValueError("Missing payload")
    payload = base64.b64decode("".join(match.group(2).split()), validate=True)
    if hashlib.sha256(payload).hexdigest() != match.group(1):
        raise ValueError("Payload checksum mismatch")
    result = json.loads(payload)
    for entry in result["files"]:
        data = base64.b64decode(entry["data"], validate=True)
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("File checksum mismatch")
    return result


class WindowsBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = self.root / "release"
        self.release.mkdir()
        self.output = self.root / "Formsemble-Setup.cmd"
        self.fixture = {
            "README.md": b"# Formsemble\r\nOffline.\n",
            "docs/T\u00fcrk\u00e7e + spaces/notes.md": "\u0130yi tasar\u0131m. \U0001f3b2\n".encode("utf-8"),
            "tools/example.py": b"print('example')\n",
            "tests/test_example.py": b"# Tests belong in the release.\n",
            "assets/raw.bin": bytes(range(256)),
            "assets/empty.txt": b"",
            "docs/it's $fine & %safe%! [v1].md": b"Literal filename, not shell code.\n",
        }
        for relative, data in self.fixture.items():
            path = self.release / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def make_symlink(self, link, target, *, is_directory=False):
        try:
            link.symlink_to(target, target_is_directory=is_directory)
        except OSError as exc:
            windows_symlink_privilege_missing = os.name == "nt" and getattr(exc, "winerror", None) == 1314
            if exc.errno in {errno.EPERM, errno.EACCES, errno.ENOTSUP} or windows_symlink_privilege_missing:
                self.skipTest("This host does not permit symlink creation")
            raise

    def test_reproducible_exact_payload_roundtrip(self):
        count = bundle.build_bundle(self.release, self.output)
        second = self.root / "second.cmd"
        bundle.build_bundle(self.release, second)
        self.assertEqual(self.output.read_bytes(), second.read_bytes())
        payload = unpack_payload(self.output)
        self.assertEqual(payload["version"], 1)
        self.assertEqual(payload["destination"], r"C:\Users\yusuf\Desktop\buy_me_coffee\formsemble")
        self.assertEqual(count, len(self.fixture))
        actual = {item["path"]: base64.b64decode(item["data"]) for item in payload["files"]}
        self.assertEqual(actual, self.fixture)
        self.assertNotIn(b"\n", self.output.read_bytes().replace(b"\r\n", b""))

    def test_cache_exclusion_preserves_source_and_tests(self):
        for relative in ["__pycache__/x.pyc", ".pytest_cache/results", ".git/config",
                         "tools/x.pyc", "docs/.DS_Store", "Thumbs.db"]:
            path = self.release / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"excluded")
        bundle.build_bundle(self.release, self.output)
        self.assertEqual({item["path"] for item in unpack_payload(self.output)["files"]}, set(self.fixture))

    def test_payload_corruption_is_detected(self):
        bundle.build_bundle(self.release, self.output)
        data = self.output.read_bytes()
        marker = data.index(b"\r\n# BEGIN FORMSEMBLE PAYLOAD ") + 2
        start = data.index(b"\r\n", marker) + 2
        damaged = data[:start] + (b"A" if data[start:start + 1] != b"A" else b"B") + data[start + 1:]
        self.output.write_bytes(damaged)
        with self.assertRaisesRegex(ValueError, "checksum mismatch"):
            unpack_payload(self.output)

    def test_rejects_unsafe_relative_paths(self):
        names = ["", "/root", "../escape", "a/../../b", "./a", "a//b", "a/", r"a\b",
                 r"C:\escape", "file:stream", "a\x00b", "a\nb", "a?b", "a*b", "a|b",
                 'a"b', "a<b", "a>b", "trailing.", "trailing ", " leading", "NUL", "nul.txt", "CON",
                 "AUX/report", "COM1.txt", "LPT9.log", "COM\u00b9.txt", "LPT\u00b2", "x/PRN.tar.gz",
                 "CLOCK$", "CONIN$", "CONOUT$", "NUL .txt", "aux  .foo", "x" * 256]
        for name in names:
            with self.subTest(name=name), self.assertRaises(ValueError):
                bundle.validate_relative_path(name)

    def test_rejects_case_aliases_and_file_directory_conflicts(self):
        for paths in [["A.md", "a.md"], ["Docs/a", "docs/b"], ["x", "x/y"],
                      ["x/y", "x"], ["same", "same"]]:
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                bundle.validate_path_set(paths)

    @unittest.skipIf(os.name == "nt", "Windows itself rejects this fixture filename")
    def test_generator_rejects_real_invalid_names(self):
        invalid = self.release / "NUL.txt"
        invalid.write_text("invalid on Windows", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Unsafe Windows path"):
            bundle.build_bundle(self.release, self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_external_file_and_directory_symlinks(self):
        external = self.root / "private.txt"
        external.write_text("must not be bundled", encoding="utf-8")
        for target in [external, self.root, self.root / "absent"]:
            link = self.release / "external"
            self.make_symlink(link, target, is_directory=target.is_dir())
            try:
                with self.assertRaisesRegex(ValueError, "Symlinks are not allowed"):
                    bundle.build_bundle(self.release, self.output)
            finally:
                link.unlink()
        source_link = self.root / "source-link"
        self.make_symlink(source_link, self.release, is_directory=True)
        with self.assertRaisesRegex(ValueError, "not a symlink"):
            bundle.build_bundle(source_link, self.output)

    def test_refuses_output_inside_source(self):
        with self.assertRaisesRegex(ValueError, "outside the release"):
            bundle.build_bundle(self.release, self.release / "nested" / "Setup.cmd")
        self.assertFalse((self.release / "nested").exists())

    def test_existing_output_is_idempotent_or_refused_without_changes(self):
        bundle.build_bundle(self.release, self.output)
        original = self.output.read_bytes()
        self.assertEqual(bundle.build_bundle(self.release, self.output), len(self.fixture))
        self.assertEqual(self.output.read_bytes(), original)
        (self.release / "README.md").write_bytes(b"different")
        with self.assertRaises(FileExistsError):
            bundle.build_bundle(self.release, self.output)
        self.assertEqual(self.output.read_bytes(), original)

    def test_refuses_symlink_output_without_touching_target(self):
        target = self.root / "existing.txt"
        target.write_bytes(b"keep")
        self.make_symlink(self.output, target)
        with self.assertRaisesRegex(ValueError, "Output must not be a symlink"):
            bundle.build_bundle(self.release, self.output)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_custom_unicode_destination_is_data(self):
        destination = "D:\\Yusuf's %folder% & !notes!\\T\u00fcrk\u00e7e folder\\formsemble"
        bundle.build_bundle(self.release, self.output, destination)
        self.assertEqual(unpack_payload(self.output)["destination"], destination)
        self.assertNotIn(destination, self.output.read_bytes().decode("ascii"))
        for invalid in [r"relative\folder", r"C:folder", "C:\\", r"\\server\share\folder",
                        r"C:\a\..\b", r"C:\NUL\folder", "C:\\a\\", "C:/folder"]:
            with self.subTest(destination=invalid), self.assertRaises(ValueError):
                bundle.validate_destination(invalid)

    def test_static_windows_safety_contract(self):
        bundle.build_bundle(self.release, self.output)
        text = self.output.read_bytes().decode("ascii")
        header, rest = text.split("# BEGIN FORMSEMBLE POWERSHELL\r\n", 1)
        script, _ = rest.split("# END FORMSEMBLE POWERSHELL\r\n", 1)
        self.assertIn('setlocal DisableDelayedExpansion', header)
        self.assertIn('set "FORMSEMBLE_BUNDLE_PATH=%~f0"', header)
        self.assertIn(r'"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -Command', header)
        self.assertIn('$env:FORMSEMBLE_BUNDLE_PATH', header)
        self.assertIn('exit /b %FORMSEMBLE_EXIT_CODE%', header)
        for forbidden in ["-ExecutionPolicy", "Set-ExecutionPolicy", "-EncodedCommand", "Invoke-WebRequest", "DownloadFile", "-Verb RunAs"]:
            self.assertNotIn(forbidden, text)
        self.assertIn('[IO.File]::WriteAllBytes($target, $file.Bytes)', script)
        self.assertIn('[IO.Directory]::Move($stage, $destination)', script)
        self.assertIn('[IO.Directory]::Delete($stage, $true)', script)
        self.assertNotIn('Delete($destination', script)
        self.assertLess(script.index('Installer payload checksum failed'), script.index('CreateDirectory($stage)'))
        self.assertLess(script.index('Written file checksum failed'), script.index('::Move($stage, $destination)'))
        self.assertLess(script.index('Test-IdenticalInstallation $stage'), script.index('::Move($stage, $destination)'))


if __name__ == "__main__":
    unittest.main()
