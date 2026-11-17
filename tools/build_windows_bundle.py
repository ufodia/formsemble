#!/usr/bin/env python3
"""Build one offline, byte-preserving Windows installer using only the stdlib.

Usage: python tools/build_windows_bundle.py RELEASE_DIR OUTPUT_CMD
The generated CMD uses the installed Windows PowerShell 5.1, with no downloads,
administrator rights, or execution-policy changes. Its readable script precedes
a checksummed data payload; that checksum detects damage, not malicious edits.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import textwrap


DEFAULT_DESTINATION = r"C:\Users\yusuf\Desktop\buy_me_coffee\formsemble"
EXCLUDED_DIRECTORIES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
EXCLUDED_FILES = {".DS_Store", "Thumbs.db"}
INVALID_NAME = re.compile(r'[<>:"\\|?*\x00-\x1f]')
RESERVED_NAME_PATTERN = (
    r"(?i)^(?:CON|PRN|AUX|NUL|CLOCK\$|CONIN\$|CONOUT\$|"
    r"COM[1-9\u00b9\u00b2\u00b3]|LPT[1-9\u00b9\u00b2\u00b3]) *(?:\.|$)"
)
RESERVED_NAME = re.compile(RESERVED_NAME_PATTERN)


def validate_relative_path(name: str) -> None:
    """Accept portable Windows relative paths, with '/' as their only separator."""
    if not isinstance(name, str) or not name:
        raise ValueError("A file path must be a nonempty string")
    for part in name.split("/"):
        if (not part or part in {".", ".."} or part.startswith(" ") or part.endswith((" ", "."))
                or INVALID_NAME.search(part) or RESERVED_NAME.match(part)
                or len(part.encode("utf-16-le")) // 2 > 255):
            raise ValueError(f"Unsafe Windows path: {name!r}")


def validate_destination(destination: str) -> None:
    if not re.match(r"^[A-Za-z]:\\[^\\]", destination):
        raise ValueError("Destination must be an absolute drive-letter Windows folder")
    validate_relative_path(destination[3:].replace("\\", "/"))
    if "/" in destination:
        raise ValueError("Use backslashes in the Windows destination")


def validate_path_set(names: list[str]) -> None:
    """Reject file/directory conflicts and case aliases on Windows."""
    nodes: dict[str, tuple[str, bool]] = {}
    for name in names:
        validate_relative_path(name)
        parts = name.split("/")
        for index in range(len(parts)):
            prefix = "/".join(parts[:index + 1])
            node = (prefix, index == len(parts) - 1)
            key = prefix.casefold()
            if key in nodes and (nodes[key] != node or node[1]):
                raise ValueError(f"Conflicting Windows path: {name!r}")
            nodes[key] = node


def collect_files(release_dir: Path) -> list[dict[str, str]]:
    files: list[dict[str, str]] = []

    def visit(directory: Path) -> None:
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            if path.is_symlink():
                raise ValueError(f"Symlinks are not allowed: {path}")
            mode = path.stat().st_mode
            if stat.S_ISDIR(mode):
                if path.name not in EXCLUDED_DIRECTORIES:
                    validate_relative_path(path.relative_to(release_dir).as_posix())
                    visit(path)
            elif stat.S_ISREG(mode):
                if path.name in EXCLUDED_FILES or path.suffix in {".pyc", ".pyo"}:
                    continue
                name = path.relative_to(release_dir).as_posix()
                validate_relative_path(name)
                contents = path.read_bytes()
                files.append({"path": name, "data": base64.b64encode(contents).decode("ascii"),
                              "sha256": hashlib.sha256(contents).hexdigest()})
            else:
                raise ValueError(f"Only regular files are allowed: {path}")

    visit(release_dir)
    if not files:
        raise ValueError("Release directory contains no files to package")
    validate_path_set([entry["path"] for entry in files])
    return files


# Keep this script plain and readable in the generated installer. It uses .NET
# byte I/O, rather than text cmdlets whose encodings differ across PS versions.
POWERSHELL_BODY = r'''
param([string]$BundleText)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
if ($PSVersionTable.PSVersion -lt [version]'5.1') { throw 'Windows PowerShell 5.1 or newer is required.' }

function Get-Sha256([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $sha.Dispose() }
}
function Assert-SafeRelativePath([string]$Name) {
    if ([string]::IsNullOrEmpty($Name)) { throw 'Empty payload path.' }
    foreach ($part in $Name.Split('/')) {
        if (!$part -or $part -eq '.' -or $part -eq '..' -or $part.StartsWith(' ') -or $part.EndsWith('.') -or $part.EndsWith(' ') -or
            $part -match '[<>:"\|?*\x00-\x1f]' -or $part.Contains('\') -or $part.Length -gt 255 -or
            $part -match '__RESERVED_NAMES__') { throw ('Unsafe payload path: ' + $Name) }
    }
}
function Assert-NoReparseAncestors([string]$Path) {
    $directory = [IO.DirectoryInfo]::new($Path)
    while ($null -ne $directory) {
        if ($directory.Exists -and ($directory.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw ('Destination uses a link or junction: ' + $directory.FullName)
        }
        $directory = $directory.Parent
    }
}
function Test-IdenticalInstallation([string]$Root, $Nodes, $Hashes) {
    $pending = [Collections.Generic.Stack[string]]::new()
    $pending.Push($Root)
    $count = 0
    while ($pending.Count -gt 0) {
        foreach ($path in [IO.Directory]::GetFileSystemEntries($pending.Pop())) {
            $attributes = [IO.File]::GetAttributes($path)
            if ($attributes -band [IO.FileAttributes]::ReparsePoint) { return $false }
            $relative = $path.Substring($Root.Length + 1).Replace('\', '/')
            if (!$Nodes.ContainsKey($relative)) { return $false }
            $count++
            if ($attributes -band [IO.FileAttributes]::Directory) {
                if (!$Nodes[$relative].StartsWith('D:')) { return $false }
                $pending.Push($path)
            } else {
                if (!$Hashes.ContainsKey($relative)) { return $false }
                if ((Get-Sha256 ([IO.File]::ReadAllBytes($path))) -cne $Hashes[$relative]) { return $false }
            }
        }
    }
    return ($count -eq $Nodes.Count)
}

$matches = [regex]::Matches($BundleText, '(?ms)^# BEGIN FORMSEMBLE PAYLOAD ([0-9a-f]{64})\r?\n([A-Za-z0-9+/=\r\n]+)^# END FORMSEMBLE PAYLOAD\r?$')
if ($matches.Count -ne 1) { throw 'Missing or malformed installer payload.' }
[byte[]]$payloadBytes = [Convert]::FromBase64String($matches[0].Groups[2].Value)
if ((Get-Sha256 $payloadBytes) -cne $matches[0].Groups[1].Value) { throw 'Installer payload checksum failed.' }
$manifest = [Text.Encoding]::UTF8.GetString($payloadBytes) | ConvertFrom-Json
if ($manifest.version -ne 1 -or @($manifest.files).Count -eq 0) { throw 'Unsupported or empty installer payload.' }
if ($manifest.destination -isnot [string] -or $manifest.destination -notmatch '^[A-Za-z]:\\[^\\]' -or $manifest.destination.Contains('/')) {
    throw 'Destination must be an absolute drive-letter Windows folder.'
}
$destination = $manifest.destination
Assert-SafeRelativePath ($destination.Substring(3).Replace('\', '/'))
$nodes = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::OrdinalIgnoreCase)
$hashes = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::OrdinalIgnoreCase)
$files = [Collections.Generic.List[object]]::new()
foreach ($entry in @($manifest.files)) {
    if ($entry.path -isnot [string] -or $entry.data -isnot [string] -or $entry.sha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Malformed payload file entry.'
    }
    Assert-SafeRelativePath $entry.path
    $parts = $entry.path.Split('/')
    for ($index = 0; $index -lt $parts.Length; $index++) {
        $prefix = $parts[0..$index] -join '/'
        $kind = if ($index -eq $parts.Length - 1) { 'F:' } else { 'D:' }
        if ($nodes.ContainsKey($prefix) -and ($nodes[$prefix] -cne ($kind + $prefix) -or $kind -eq 'F:')) {
            throw ('Conflicting payload paths: ' + $entry.path)
        }
        $nodes[$prefix] = $kind + $prefix
    }
    [byte[]]$bytes = @([Convert]::FromBase64String($entry.data))
    if ((Get-Sha256 $bytes) -cne $entry.sha256) { throw ('File checksum failed: ' + $entry.path) }
    $hashes.Add($entry.path, $entry.sha256)
    $files.Add([pscustomobject]@{ Path = $entry.path; Bytes = $bytes; Hash = $entry.sha256 })
}

Assert-NoReparseAncestors $destination
if ([IO.Directory]::Exists($destination)) {
    if (Test-IdenticalInstallation $destination $nodes $hashes) {
        Write-Host ('Formsemble is already installed and all files match: ' + $destination) -ForegroundColor Green
        return
    }
    throw ('Destination already exists and differs. Nothing was changed: ' + $destination)
}
if ([IO.File]::Exists($destination)) { throw ('A file already exists at the destination: ' + $destination) }
$parent = [IO.Path]::GetDirectoryName($destination)
$stage = [IO.Path]::Combine($parent, ('.formsemble-stage-' + [Guid]::NewGuid().ToString('N')))
$stageCreated = $false
try {
    if ([IO.Directory]::Exists($stage) -or [IO.File]::Exists($stage)) { throw 'Staging path already exists.' }
    [void][IO.Directory]::CreateDirectory($stage)
    $stageCreated = $true
    foreach ($file in $files) {
        $target = [IO.Path]::GetFullPath([IO.Path]::Combine($stage, $file.Path.Replace('/', '\')))
        if (!$target.StartsWith($stage + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Payload path escaped staging.' }
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
        [IO.File]::WriteAllBytes($target, $file.Bytes)
        if ((Get-Sha256 ([IO.File]::ReadAllBytes($target))) -cne $file.Hash) { throw ('Written file checksum failed: ' + $file.Path) }
    }
    if (!(Test-IdenticalInstallation $stage $nodes $hashes)) { throw 'Staged file inventory did not match the payload.' }
    Assert-NoReparseAncestors $destination
    # A sibling directory rename publishes the complete tree and refuses an
    # existing destination, including one created while files were being written.
    [IO.Directory]::Move($stage, $destination)
    $stageCreated = $false
    Write-Host ('Installed ' + $files.Count + ' verified files to: ' + $destination) -ForegroundColor Green
    Write-Host 'Open README.md in that folder to get started.'
} finally {
    if ($stageCreated -and [IO.Directory]::Exists($stage)) {
        [IO.Directory]::Delete($stage, $true)
    }
}
'''.strip().replace("__RESERVED_NAMES__", RESERVED_NAME_PATTERN)

CMD_HEADER = r'''@echo off
setlocal DisableDelayedExpansion
set "FORMSEMBLE_BUNDLE_PATH=%~f0"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -Command "$ErrorActionPreference='Stop'; try { $text=[IO.File]::ReadAllText($env:FORMSEMBLE_BUNDLE_PATH,[Text.Encoding]::ASCII); $section=[regex]::Match($text,'(?ms)^# BEGIN FORMSEMBLE POWERSHELL\r?\n(.*?)^# END FORMSEMBLE POWERSHELL\r?$'); if(!$section.Success){throw 'Installer script section is missing.'}; & ([scriptblock]::Create($section.Groups[1].Value)) $text } catch { Write-Host ('Installation failed: '+$_.Exception.Message) -ForegroundColor Red; exit 1 }"
set "FORMSEMBLE_EXIT_CODE=%errorlevel%"
echo.
echo Press any key to close this window.
pause >nul
exit /b %FORMSEMBLE_EXIT_CODE%
'''


def build_bundle(release_dir: Path, output_cmd: Path,
                 destination: str = DEFAULT_DESTINATION) -> int:
    release_dir, output_cmd = Path(release_dir), Path(output_cmd)
    if release_dir.is_symlink() or not release_dir.is_dir():
        raise ValueError("Release source must be a real directory, not a symlink")
    release_dir = release_dir.resolve()
    if output_cmd.is_symlink():
        raise ValueError("Output must not be a symlink")
    output_cmd = output_cmd.resolve()
    if output_cmd.is_relative_to(release_dir):
        raise ValueError("Output must be outside the release directory")
    validate_destination(destination)
    files = collect_files(release_dir)
    payload = json.dumps({"version": 1, "destination": destination, "files": files},
                         ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    checksum = hashlib.sha256(payload).hexdigest()
    encoded = "\n".join(textwrap.wrap(base64.b64encode(payload).decode("ascii"), 76))
    text = (CMD_HEADER + "# BEGIN FORMSEMBLE POWERSHELL\n" + POWERSHELL_BODY +
            "\n# END FORMSEMBLE POWERSHELL\n" + f"# BEGIN FORMSEMBLE PAYLOAD {checksum}\n" +
            encoded + "\n# END FORMSEMBLE PAYLOAD\n")
    content = text.replace("\n", "\r\n").encode("ascii")
    if output_cmd.exists():
        if output_cmd.is_file() and output_cmd.read_bytes() == content:
            return len(files)
        raise FileExistsError(f"Output already exists and differs; refusing overwrite: {output_cmd}")
    output_cmd.parent.mkdir(parents=True, exist_ok=True)
    with output_cmd.open("xb") as stream:
        stream.write(content)
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release_dir", type=Path)
    parser.add_argument("output_cmd", type=Path)
    parser.add_argument("--destination", default=DEFAULT_DESTINATION)
    args = parser.parse_args()
    try:
        count = build_bundle(args.release_dir, args.output_cmd, args.destination)
    except (OSError, ValueError) as exc:
        print(f"Bundle not created: {exc}", file=sys.stderr)
        return 1
    print(f"Created {args.output_cmd} with {count} files; destination: {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
