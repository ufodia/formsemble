"""Exercise release-integrity boundaries using synthetic temporary packages."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "verify_package.py"
SPEC = importlib.util.spec_from_file_location("formsemble_verify", MODULE_PATH)
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


class VerifyPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / "content.txt").write_bytes(b"Synthetic package fixture\n")
        self.manifest = {
            "schema_version": 1,
            "name": "formsemble",
            "version": "test-fixture",
            "files": [{"path": "content.txt", "sha256": hashlib.sha256((self.root / "content.txt").read_bytes()).hexdigest()}],
        }
        self.write_manifest()

    def write_manifest(self):
        (self.root / "MANIFEST.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def test_current_inventory_passes(self):
        self.assertTrue(VERIFY.verify(self.root)["valid"])

    def test_changed_and_missing_files_fail(self):
        (self.root / "content.txt").write_text("Changed", encoding="utf-8")
        self.assertFalse(VERIFY.verify(self.root)["valid"])
        (self.root / "content.txt").unlink()
        self.assertFalse(VERIFY.verify(self.root)["valid"])

    def test_unlisted_files_fail_but_generated_caches_are_ignored(self):
        cache = self.root / "__pycache__"
        cache.mkdir()
        (cache / "fixture.pyc").write_bytes(b"synthetic cache")
        self.assertTrue(VERIFY.verify(self.root)["valid"])
        (self.root / "unexpected.txt").write_text("Extra", encoding="utf-8")
        self.assertFalse(VERIFY.verify(self.root)["valid"])

    def test_unsafe_duplicate_and_self_paths_are_rejected(self):
        for value in ["../content.txt", "/content.txt", "C:/content.txt", "a/../content.txt", "a\\content.txt", "MANIFEST.json"]:
            with self.subTest(path=value):
                self.manifest["files"][0]["path"] = value
                self.write_manifest()
                with self.assertRaises(ValueError):
                    VERIFY.verify(self.root)
        self.manifest["files"][0]["path"] = "content.txt"
        self.manifest["files"].append(dict(self.manifest["files"][0]))
        self.write_manifest()
        with self.assertRaises(ValueError):
            VERIFY.verify(self.root)

    def test_links_are_not_accepted_as_evidence_of_package_bytes(self):
        (self.root / "content.txt").rename(self.root / "actual.txt")
        try:
            (self.root / "content.txt").symlink_to(self.root / "actual.txt")
        except (OSError, NotImplementedError):
            self.skipTest("Symbolic links are unavailable")
        self.assertFalse(VERIFY.verify(self.root)["valid"])

    def test_duplicate_manifest_keys_are_rejected(self):
        (self.root / "MANIFEST.json").write_text('{"name":"formsemble","name":"other"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            VERIFY.verify(self.root)


if __name__ == "__main__":
    unittest.main()
