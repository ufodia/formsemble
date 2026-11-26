# Validation scope

## Patch and handoff smoke check, 2026-11-26

A synthetic Turkish appointment form reproduced a clipped submit label at 320 CSS px in local Chrome 158 on Windows. After a CSS-only change, the label fit at 320 and 880 CSS px. Tab reached the existing submit button. Pressing Enter with an invalid appointment code showed feedback and kept the entered text. Clicking submit with the corrected code showed confirmation through the existing handler.

The fingerprint command captured the form, a screenshot, and runtime notes. The resulting handoff validated as incomplete with visual inspection marked `not_tested`. The checker rejected the same handoff after the form file changed. Screen-reader behavior and visual craft were outside this smoke check.

The generated offline Windows installer extracted 30 files, all verified against the package manifest. The installer copied the 13-file skill into an isolated test project's Codex and Claude folders with matching file bytes in both.

## Version 1.2.0 workspace verification

Prepared on 2026-11-17 in the Windows workspace.

The release inventory and fingerprint check was run after the final package files were assembled:

    py -3 -B tools\verify_package.py

The standard-library suite was run with:

    py -3 -B -m unittest discover -s tests -v

This run used Python 3.12.10. The package verifier reported a valid inventory of 29 files with no errors. The test suite ran 70 methods with 58 passing, 12 skipped, and no failures.

The Windows sandbox refused symlink creation with WinError 1314, so symlink-focused cases were skipped rather than treated as passing. A nonregular-file fixture and a Windows-inapplicable filename fixture were also skipped. These environment-dependent checks still need a host that supports the relevant filesystem operations.

The skill-creator quick validator could not run because its PyYAML import is not installed in this Python environment. The simple skill frontmatter and Codex metadata were checked manually against the allowed fields and stated length/name constraints; full YAML parser validation remains untested here.

## Version 1.1.0 baseline evidence

Prepared on 2026-11-17.

## Executed checks

The release tooling was exercised on Linux with Python 3.12.14. The repeatable command is:

```bash
python -B -m unittest discover -s tests -v
```

The run completed with **70 passing test methods**:

| Area | Test methods | What was exercised |
|---|---:|---|
| Evidence-record checker | 29 | Required fields, methods/statuses, observations, missing/stale files, hashes, traversal, links, duplicate keys/IDs, simulation honesty, read-only behavior, CLI exit codes, UTF-8 BOM |
| Local skill installer | 23 | Host/scope selection, exact file copies, dry run, existing-tree protection, link rejection, preflight, staging, ordinary rollback, concurrent-change protection |
| Release inventory verifier | 6 | Current inventory, altered/missing/unlisted files, ignored caches, unsafe paths, links, duplicate manifest keys |
| Windows bundle generator | 12 | Reproducibility, decoded payload byte equality, checksum corruption, Unicode/special names, traversal/reserved names, symlinks, case conflicts, output protection, static wrapper properties |

Some test methods include several input variants. Counts describe test methods, not independent product-quality experiments. Tests use clearly synthetic fixtures; synthetic image bytes are only a test of the checker's declared metadata contract, not visual evidence.

The canonical installed skill also passed its skill-format validator. Relative documentation references and portable metadata were checked during packaging. The release manifest is generated from the final file inventory; `tools/verify_package.py` can verify the resulting package without changing it.

## Workflow exercises

Three fresh task contexts were used during development:

- A narrow-screen button-label defect received a bounded CSS change without unrelated redesign.
- A staff-duty interface was understood from current source despite outdated parent-portal notes; assignment, conflict, removal, and storage behavior were preserved through a redesign.
- A source-only audit respected its no-edit scope and separated source findings from unperformed runtime and visual checks.

The redesigned example's actual script was exercised with a minimal DOM and storage simulation. Local browser launch was unavailable in the environment. These exercises therefore do not establish rendered layout quality, real keyboard behavior, screen-reader behavior, or improvement in real-user outcomes.

## Static review

A separate reviewer inspected the design method, portability, scope boundaries, and optional checker semantics. A focused review also examined the Windows wrapper's quoting, self-read markers, PowerShell syntax, byte handling, staging, idempotence, and cleanup.

The Windows carrier is intended for Windows PowerShell 5.1. The Python helpers target Python 3.9 or later. The release was not run on every supported Python version or operating system.

## Not established by this release

- Actual execution of the generated CMD/PowerShell folder creator on Windows.
- Direct writing to the user's Windows desktop from the preparation environment.
- Native end-to-end execution of the skill inside both Claude Code and Codex.
- A rendered-UI benchmark or controlled comparison of model design quality.
- Human usability research, conversion improvement, or full accessibility conformance.
- Worldwide uniqueness, trademark clearance, or guaranteed design quality.

The host installation conventions were checked against current official documentation. Tooling tests support the tooling guarantees described above; they do not turn the design method into a quality certification.
