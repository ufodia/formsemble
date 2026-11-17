"""Reproducible contract tests for Formsemble's read-only review checker.

Every report and observation in this file is synthetic test data. Passing these
tests establishes parser/consistency behavior, not visual quality, an actual
review, human research, or accessibility conformance.

Set FORMSEMBLE_SKILL_DIR to test a canonical skill checkout before packaging.
Without that override the checker is imported from skills/formsemble.
"""

import base64
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RELEASE_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path(os.environ.get("FORMSEMBLE_SKILL_DIR", str(RELEASE_ROOT / "skills" / "formsemble"))).expanduser().resolve()
CHECKER_PATH = SKILL_DIR / "scripts" / "check_review.py"
if not CHECKER_PATH.is_file():
    raise RuntimeError(
        "Checker not found at " + str(CHECKER_PATH)
        + "; export skills/formsemble or set FORMSEMBLE_SKILL_DIR to the canonical skill directory."
    )
SPEC = importlib.util.spec_from_file_location("formsemble_review_test_target", CHECKER_PATH)
review_checker = importlib.util.module_from_spec(SPEC)
previous_bytecode_setting = sys.dont_write_bytecode
try:
    # Importing a canonical skill must not add caches to its installed folder.
    sys.dont_write_bytecode = True
    SPEC.loader.exec_module(review_checker)
finally:
    sys.dont_write_bytecode = previous_bytecode_setting


class CheckReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="formsemble-review-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / "project"
        self.root.mkdir()
        (self.root / "ui.html").write_bytes(b"<!-- SYNTHETIC TEST DATA; no application has been reviewed. -->\n")
        (self.root / "notes.txt").write_bytes(
            b"SYNTHETIC TEST DATA: placeholder observations; no human study or visual audit occurred.\n"
        )
        # A tiny fixture image is evidence-shaped data only; its pixels are not
        # inspected by this checker and establish no UI or quality claim.
        (self.root / "fixture.png").write_bytes(base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l1sAAAAASUVORK5CYII="
        ))
        self.report_path = self.base / "synthetic-review.json"

    def reference(self, relative, kind=None):
        value = {"path": relative, "sha256": hashlib.sha256((self.root / relative).read_bytes()).hexdigest()}
        if kind:
            value.update(kind=kind, description="Synthetic fixture for validator behavior only.")
        return value

    def report(self):
        methods = {
            "intent": "source", "task": "runtime", "visual": "visual",
            "accessibility": "automated", "responsiveness": "runtime", "preservation": "source",
        }
        checks = []
        for identifier, method in methods.items():
            evidence = self.reference("fixture.png", "image") if identifier == "visual" else self.reference("notes.txt", "notes")
            checks.append({
                "id": identifier, "status": "pass", "method": method,
                "expected": "Synthetic expected outcome for " + identifier + ".",
                "observed": "Synthetic fixture observation; no actual review is asserted.",
                "reason": "", "evidence": [evidence],
            })
        return {
            "schema_version": 1,
            "scope": "Synthetic validator contract exercise only; no UI is being audited.",
            "artifact": {"label": "synthetic-test-fixture", "files": [self.reference("ui.html")]},
            "checks": checks,
            "findings": [],
        }

    def checked(self, report):
        checker = review_checker.ReviewChecker(self.root)
        checker.review(report)
        return checker.result()

    def check_by_id(self, report, identifier):
        return next(entry for entry in report["checks"] if entry["id"] == identifier)

    def run_cli(self, report=None, raw=None, root=None, bom=False):
        if raw is not None:
            self.report_path.write_bytes(raw)
        elif report is not None:
            text = json.dumps(report, ensure_ascii=False)
            self.report_path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = review_checker.main([str(self.report_path), "--project-root", str(root or self.root)])
        return code, json.loads(output.getvalue())

    def assert_invalid(self, report, message=None):
        result = self.checked(report)
        self.assertFalse(result["valid"])
        self.assertFalse(result["complete"])
        if message:
            self.assertIn(message, "\n".join(result["errors"]))
        return result

    def make_link(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError) as exc:
            self.skipTest("Symbolic links are unavailable in this test environment: " + str(exc))

    def test_complete_synthetic_record_has_stable_output_contract_and_disclaimer(self):
        code, result = self.run_cli(self.report())
        self.assertEqual(code, 0)
        self.assertEqual(set(result), {"valid", "complete", "errors", "blockers", "disclaimer"})
        self.assertTrue(result["valid"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["blockers"], [])
        self.assertIn("consistency only", result["disclaimer"])
        self.assertIn("does not evaluate design quality", result["disclaimer"])
        self.assertIn("prove a review occurred", result["disclaimer"])

    def test_fail_and_not_tested_are_valid_but_incomplete_with_exit_one(self):
        for status in ("fail", "not_tested"):
            with self.subTest(status=status):
                report = self.report()
                check = self.check_by_id(report, "task")
                check.update(status=status, reason="Synthetic outstanding check.")
                if status == "not_tested":
                    check.update(method="none", observed="", evidence=[])
                code, result = self.run_cli(report)
                self.assertEqual(code, 1)
                self.assertTrue(result["valid"])
                self.assertFalse(result["complete"])
                self.assertEqual(result["blockers"], ["Check task: " + status])

    def test_every_required_check_must_be_present(self):
        for identifier in sorted(review_checker.REQUIRED_CHECKS):
            with self.subTest(identifier=identifier):
                report = self.report()
                report["checks"] = [check for check in report["checks"] if check["id"] != identifier]
                self.assert_invalid(report, "missing required check " + identifier)

    def test_additional_checks_are_allowed_and_can_block_completeness(self):
        report = self.report()
        extra = copy.deepcopy(report["checks"][0])
        extra.update(id="custom-localization", status="not_tested", method="none", observed="", evidence=[],
                     reason="Synthetic locale exercise has not run.")
        report["checks"].append(extra)
        result = self.checked(report)
        self.assertTrue(result["valid"])
        self.assertFalse(result["complete"])
        self.assertIn("Check custom-localization: not_tested", result["blockers"])

    def test_pass_and_fail_require_observation_evidence_and_actual_method(self):
        for status in ("pass", "fail"):
            for field, value, message in (
                ("observed", " ", "observation and evidence"),
                ("evidence", [], "observation and evidence"),
                ("method", "none", "actual review method"),
            ):
                with self.subTest(status=status, field=field):
                    report = self.report()
                    check = self.check_by_id(report, "intent")
                    check.update(status=status, reason="Synthetic failure explanation.")
                    check[field] = value
                    self.assert_invalid(report, message)

    def test_nonpass_statuses_require_reasons(self):
        for status in ("fail", "not_tested", "not_applicable"):
            with self.subTest(status=status):
                report = self.report()
                self.check_by_id(report, "task").update(status=status, reason=" \t")
                self.assert_invalid(report, "required for this status")

    def test_not_applicable_is_allowed_only_for_eligible_checks_with_reason(self):
        for identifier in sorted(review_checker.REQUIRED_CHECKS):
            with self.subTest(identifier=identifier):
                report = self.report()
                self.check_by_id(report, identifier).update(
                    status="not_applicable", method="none", observed="", evidence=[],
                    reason="Synthetic example of a scoped inapplicable criterion.",
                )
                if identifier in {"intent", "visual"}:
                    self.assert_invalid(report, "cannot be not_applicable")
                else:
                    result = self.checked(report)
                    self.assertTrue(result["valid"])
                    self.assertTrue(result["complete"])

    def test_simulation_cannot_establish_any_pass(self):
        for identifier in sorted(review_checker.REQUIRED_CHECKS):
            with self.subTest(identifier=identifier):
                report = self.report()
                self.check_by_id(report, identifier)["method"] = "simulation"
                self.assert_invalid(report, "simulation cannot establish a pass")

    def test_simulated_fail_or_not_tested_remains_honest_incomplete_metadata(self):
        for status in ("fail", "not_tested"):
            with self.subTest(status=status):
                report = self.report()
                self.check_by_id(report, "task").update(
                    method="simulation", status=status,
                    reason="Synthetic simulation concern; no human observation claimed.",
                )
                result = self.checked(report)
                self.assertTrue(result["valid"])
                self.assertFalse(result["complete"])

    def test_task_pass_requires_runtime_or_declared_human_observation(self):
        for method in sorted(review_checker.METHODS):
            with self.subTest(method=method):
                report = self.report()
                self.check_by_id(report, "task")["method"] = method
                result = self.checked(report)
                self.assertEqual(result["valid"], method in {"runtime", "human"})
                self.assertEqual(result["complete"], method in {"runtime", "human"})

    def test_human_is_a_declaration_not_machine_verified_identity(self):
        report = self.report()
        for check in report["checks"]:
            check["method"] = "human"
        result = self.checked(report)
        self.assertTrue(result["valid"])
        self.assertIn("prove a review occurred", result["disclaimer"])
        # This acceptance does not mean the synthetic fixtures were reviewed
        # by a person. AI-assisted inspection must use its actual method; an
        # invented AI/human alias is not silently treated as a human study.
        for undeclared_method in ("AI", "ai-human", "assistant", "user-study"):
            with self.subTest(method=undeclared_method):
                invalid = self.report()
                self.check_by_id(invalid, "task")["method"] = undeclared_method
                self.assert_invalid(invalid, "must be one of")

    def test_visual_and_responsiveness_methods_have_distinct_contracts(self):
        for identifier, allowed in (
            ("visual", {"visual", "human"}),
            ("responsiveness", {"runtime", "visual", "human"}),
        ):
            for method in sorted(review_checker.METHODS):
                with self.subTest(identifier=identifier, method=method):
                    report = self.report()
                    self.check_by_id(report, identifier)["method"] = method
                    self.assertEqual(self.checked(report)["valid"], method in allowed)

    def test_visual_pass_requires_declared_image_with_supported_suffix(self):
        for kind, relative in (("notes", "fixture.png"), ("image", "notes.txt"), ("log", "notes.txt")):
            with self.subTest(kind=kind, path=relative):
                report = self.report()
                self.check_by_id(report, "visual")["evidence"] = [self.reference(relative, kind)]
                self.assert_invalid(report, "visual pass requires")
        (self.root / "fixture.PNG").write_bytes((self.root / "fixture.png").read_bytes())
        report = self.report()
        self.check_by_id(report, "visual")["evidence"] = [self.reference("fixture.PNG", "image")]
        self.assertTrue(self.checked(report)["valid"])

    def test_image_metadata_validation_does_not_decode_or_judge_pixels(self):
        (self.root / "synthetic-placeholder.png").write_bytes(
            b"SYNTHETIC TEST DATA, deliberately not a decoded image.\n"
        )
        report = self.report()
        self.check_by_id(report, "visual")["evidence"] = [self.reference("synthetic-placeholder.png", "image")]
        result = self.checked(report)
        self.assertTrue(result["valid"])
        self.assertIn("does not evaluate design quality", result["disclaimer"])

    def test_stale_artifact_and_evidence_bytes_are_rejected(self):
        for relative in ("ui.html", "notes.txt", "fixture.png"):
            with self.subTest(file=relative):
                report = self.report()
                original = (self.root / relative).read_bytes()
                (self.root / relative).write_bytes(original + b"Synthetic changed bytes\n")
                code, result = self.run_cli(report)
                self.assertEqual(code, 2)
                self.assertFalse(result["valid"])
                self.assertIn("does not match current file bytes", "\n".join(result["errors"]))
                (self.root / relative).write_bytes(original)

    def test_hashes_require_64_hex_digits_and_accept_uppercase(self):
        for digest in (None, 12, "", "0" * 63, "0" * 65, "x" * 64):
            with self.subTest(digest=digest):
                report = self.report()
                report["artifact"]["files"][0]["sha256"] = digest
                self.assert_invalid(report, "64 hex digits")
        report = self.report()
        report["artifact"]["files"][0]["sha256"] = report["artifact"]["files"][0]["sha256"].upper()
        self.assertTrue(self.checked(report)["valid"])

    def test_missing_empty_and_directory_references_are_invalid(self):
        (self.root / "empty.txt").write_bytes(b"")
        (self.root / "directory").mkdir()
        for relative in ("missing.txt", "empty.txt", "directory"):
            with self.subTest(path=relative):
                report = self.report()
                report["artifact"]["files"][0]["path"] = relative
                self.assert_invalid(report)

    def test_absolute_and_parent_traversal_paths_are_rejected_in_all_reference_types(self):
        paths = (
            str(self.root / "ui.html"), "../project/ui.html", "nested/../ui.html",
            "..\\project\\ui.html", "nested\\..\\ui.html", "C:\\ui.html",
            "C:ui.html", "\\\\server\\share\\ui.html", "\\ui.html",
        )
        for relative in paths:
            for reference_type in ("artifact", "evidence"):
                with self.subTest(path=relative, reference_type=reference_type):
                    report = self.report()
                    entry = report["artifact"]["files"][0] if reference_type == "artifact" else report["checks"][0]["evidence"][0]
                    entry["path"] = relative
                    self.assert_invalid(report)

    def test_escaping_and_dangling_symlinks_are_rejected(self):
        outside = self.base / "outside.txt"
        outside.write_bytes(b"Synthetic external bytes\n")
        self.make_link(self.root / "outside-link", outside)
        self.make_link(self.root / "outside-directory", self.base, True)
        self.make_link(self.root / "dangling-link", self.base / "absent")
        for relative in ("outside-link", "outside-directory/outside.txt", "dangling-link"):
            with self.subTest(path=relative):
                report = self.report()
                report["artifact"]["files"][0]["path"] = relative
                self.assert_invalid(report)

    def test_in_root_symlink_is_resolved_and_still_hash_checked(self):
        self.make_link(self.root / "inside-link", self.root / "ui.html")
        report = self.report()
        report["artifact"]["files"][0]["path"] = "inside-link"
        self.assertTrue(self.checked(report)["valid"])
        (self.root / "ui.html").write_bytes(b"Synthetic stale link target\n")
        self.assert_invalid(report, "does not match current file bytes")

    def test_duplicate_check_finding_ids_and_artifact_paths_are_rejected(self):
        report = self.report()
        report["checks"].append(copy.deepcopy(report["checks"][0]))
        self.assert_invalid(report, "duplicate id")
        report = self.report()
        finding = {"id": "synthetic-finding", "severity": "minor", "status": "fixed",
                   "description": "Synthetic resolved finding.", "evidence": [self.reference("notes.txt", "notes")]}
        report["findings"] = [finding, copy.deepcopy(finding)]
        self.assert_invalid(report, "duplicate id")
        report = self.report()
        report["artifact"]["files"].append(copy.deepcopy(report["artifact"]["files"][0]))
        self.assert_invalid(report, "duplicate reviewed file")

    def test_required_fields_unknown_fields_and_types_are_strict(self):
        mutations = (
            ("missing scope", lambda report: report.pop("scope")),
            ("unknown top-level", lambda report: report.update(typo=True)),
            ("boolean version", lambda report: report.update(schema_version=True)),
            ("float version", lambda report: report.update(schema_version=1.0)),
            ("wrong version", lambda report: report.update(schema_version=2)),
            ("blank scope", lambda report: report.update(scope=" \t")),
            ("blank artifact label", lambda report: report["artifact"].update(label="")),
            ("empty artifact list", lambda report: report["artifact"].update(files=[])),
            ("wrong checks type", lambda report: report.update(checks={})),
            ("wrong findings type", lambda report: report.update(findings=None)),
            ("missing method", lambda report: report["checks"][0].pop("method")),
            ("unknown check field", lambda report: report["checks"][0].update(typo=True)),
            ("blank expected", lambda report: report["checks"][0].update(expected="")),
            ("surrounded ID", lambda report: report["checks"][0].update(id=" intent ")),
            ("nonstring ID", lambda report: report["checks"][0].update(id=7)),
            ("wrong evidence type", lambda report: report["checks"][0].update(evidence={})),
            ("blank evidence description", lambda report: report["checks"][0]["evidence"][0].update(description="")),
            ("unknown evidence kind", lambda report: report["checks"][0]["evidence"][0].update(kind="url")),
            ("unknown artifact field", lambda report: report["artifact"]["files"][0].update(typo=True)),
        )
        for name, mutate in mutations:
            with self.subTest(case=name):
                report = self.report()
                mutate(report)
                self.assert_invalid(report)
        for invalid_top_level in (None, [], "synthetic invalid root", 1):
            with self.subTest(top_level=invalid_top_level):
                self.assert_invalid(invalid_top_level, "must be an object")

    def test_malformed_json_duplicate_keys_and_non_json_constants_exit_two(self):
        ordinary = json.dumps(self.report())
        payloads = (
            b"{", b"\xff", b'{"schema_version": 1, "schema_version": 1}',
            ordinary.replace('"schema_version": 1', '"schema_version": NaN').encode(),
            ordinary.replace('"schema_version": 1', '"schema_version": Infinity').encode(),
            ordinary.replace('"schema_version": 1', '"schema_version": -Infinity').encode(),
            ordinary.replace('"label": "synthetic-test-fixture"', '"label": "first", "label": "second"').encode(),
        )
        for payload in payloads:
            with self.subTest(payload=payload[:60]):
                code, result = self.run_cli(raw=payload)
                self.assertEqual(code, 2)
                self.assertFalse(result["valid"])
                self.assertFalse(result["complete"])
                self.assertTrue(result["errors"])

    def test_utf8_bom_report_is_accepted_by_cli(self):
        code, result = self.run_cli(self.report(), bom=True)
        self.assertEqual(code, 0)
        self.assertTrue(result["valid"])
        self.assertTrue(result["complete"])

    def test_missing_report_and_invalid_project_roots_return_structured_errors(self):
        code, result = self.run_cli()
        self.assertEqual(code, 2)
        self.assertFalse(result["valid"])
        for root in (self.base / "absent-root", self.root / "ui.html"):
            with self.subTest(root=root.name):
                code, result = self.run_cli(self.report(), root=root)
                self.assertEqual(code, 2)
                self.assertFalse(result["valid"])

    def test_finding_severity_and_status_control_completeness(self):
        for severity in ("blocker", "major", "minor"):
            for status in ("open", "fixed", "deferred"):
                with self.subTest(severity=severity, status=status):
                    report = self.report()
                    report["findings"] = [{
                        "id": "synthetic-finding", "severity": severity, "status": status,
                        "description": "Synthetic finding for consistency testing.",
                        "reason": "Synthetic deferral explanation.",
                        "evidence": [self.reference("notes.txt", "notes")],
                    }]
                    result = self.checked(report)
                    self.assertTrue(result["valid"])
                    expected_complete = status == "fixed" or (status == "deferred" and severity == "minor")
                    self.assertEqual(result["complete"], expected_complete)

    def test_fixed_findings_require_evidence_and_deferred_findings_require_reason(self):
        for status, evidence, reason, message in (
            ("fixed", [], "", "fixed findings require current evidence"),
            ("deferred", [], "", "deferred findings require a reason"),
        ):
            with self.subTest(status=status):
                report = self.report()
                report["findings"] = [{
                    "id": "synthetic-finding", "severity": "minor", "status": status,
                    "description": "Synthetic finding.", "evidence": evidence, "reason": reason,
                }]
                self.assert_invalid(report, message)

    def test_checker_is_read_only_for_project_and_report(self):
        self.report_path.write_text(json.dumps(self.report()), encoding="utf-8")
        before = {str(path.relative_to(self.base)): path.read_bytes() for path in self.base.rglob("*") if path.is_file()}
        code, _ = self.run_cli()
        self.assertEqual(code, 0)
        after = {str(path.relative_to(self.base)): path.read_bytes() for path in self.base.rglob("*") if path.is_file()}
        self.assertEqual(after, before)

    def test_actual_cli_exit_code_and_json_are_consistent(self):
        self.report_path.write_text(json.dumps(self.report()), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(CHECKER_PATH), str(self.report_path), "--project-root", str(self.root)],
            cwd=str(self.base), capture_output=True, text=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertTrue(json.loads(completed.stdout)["complete"])


if __name__ == "__main__":
    unittest.main()
