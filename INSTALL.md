# Install Formsemble

## Choose a scope

| Host | Personal installation | Project installation |
|---|---|---|
| Codex CLI / IDE | `~/.agents/skills/formsemble/` | `<project>/.agents/skills/formsemble/` |
| Claude Code | `~/.claude/skills/formsemble/` | `<project>/.claude/skills/formsemble/` |

Copy the complete `skills/formsemble` folder. Its destination must contain `LICENSE`, `SKILL.md`, `references`, `assets`, `scripts`, and the optional `agents` metadata folder. Copying only `SKILL.md` leaves the license and required references missing.

These are local-host locations. A local installation is separate from a ChatGPT-managed skill or a Claude account/cloud installation. Check the current host documentation if a cloud session uses a different discovery mechanism.

## Automatic file-copy installation

Use Python 3.9 or later. The tools use the standard library and require no package installation.

### Windows

Open a terminal in the extracted Formsemble release directory:

```powershell
py -3 tools\install_skill.py --host both --scope user --dry-run
py -3 tools\install_skill.py --host both --scope user
```

If your Python command is `python`, use that instead of `py -3`.

### macOS or Linux

```bash
python3 tools/install_skill.py --host both --scope user --dry-run
python3 tools/install_skill.py --host both --scope user
```

### A single host

Replace `both` with `codex` or `claude`.

### A specific project

```bash
python3 tools/install_skill.py --host both --scope project --project-root "/absolute/path/to/project" --dry-run
python3 tools/install_skill.py --host both --scope project --project-root "/absolute/path/to/project"
```

Use a real project path. The installer requires it explicitly for project scope and does not guess from the current working directory.

## Existing installations

If the destination has exactly the same files and bytes, the installer reports that it is already installed. If it differs, installation stops before replacing it. Preserve your edits, review the new version, and manually move or back up the old directory before installing again.

The installer preflights both requested hosts before writing, stages files, and attempts to roll back only its own new changes on an ordinary failure. It does not provide a transaction across a machine crash or concurrent edits. It does not overwrite project instructions or change settings, permissions, models, or experimental agent features.

## Manual installation without Python

Create the chosen host's `skills` directory if necessary, then copy this release's complete `skills/formsemble` folder into it. Keep existing files safe if the destination already exists.

Python is needed only for the optional installer, evidence checker, package verifier, bundle builder, and tests. The design workflow is expressed in Markdown.

## Confirm discovery

Invoke `$formsemble` in Codex or `/formsemble` in Claude Code. If the skill is not listed, check the actual folder location, filename capitalization, the active account/environment, and the host's current skill-discovery documentation. Reopen or refresh the skill list where supported.

Ask for a small bounded change first. Confirm that the skill inspects the relevant product evidence, stays within scope, and distinguishes performed checks from unavailable ones.

## Windows offline folder creator

A generated `Formsemble-Setup.cmd` is a self-contained copy of the release. Running it creates the destination embedded when it was built. It requires Windows PowerShell and .NET functionality normally supplied with Windows; it does not require Python or an internet download to extract the files.

The folder creator preserves bytes, verifies checksums, and stages files beside the destination before the final move. An exact existing copy is a no-op; a different existing destination is left untouched. Creating the release folder does not install the skill globally into either coding host. Use the steps above if you also want local host discovery.

The source of the folder creator is included in `tools/build_windows_bundle.py`. The package's validation notes distinguish payload/static tests from actual Windows execution. If an organizational policy blocks command files or PowerShell, use your approved manual file-transfer process; do not change that policy for this package.

## Official host references

- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
