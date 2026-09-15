#!/usr/bin/env python3
"""Audit the pinned, opt-in and non-embedded CMP integration policy."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


EXPECTED = {
    "version": "2.6.5",
    "commit": "793d979748b27a9924fccc30fa0fba6edb7cd70f",
    "sha256": "DD0CA6FED1FB056DCB064813C223E0423F1FD9B13E291D106D8B983C467ABC33",
    "archive_bytes": "1084146265L",
    "expanded_bytes": "3118285955L",
    "entries": "23600",
}

IGNORED_DIRECTORIES = {
    ".git",
    ".analysis",
    ".research",
    "__pycache__",
    "build",
    "dist",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def missing_markers(text: str, markers: list[str]) -> list[str]:
    return [marker for marker in markers if marker not in text]


def audit(root: Path) -> dict[str, object]:
    config = read(root / "installer" / "Config.cs")
    installer = read(root / "installer" / "CmpInstaller.cs")
    main_form = read(root / "installer" / "MainForm.cs")
    core = read(root / "installer" / "InstallerCore.cs")
    build = read(root / "build.ps1")
    readme = read(root / "README.md")
    policy_path = root / "docs" / "CONTENU_COMMUNAUTAIRE.md"
    policy = read(policy_path) if policy_path.is_file() else ""
    errors: list[str] = []

    config_markers = [
        f'public const string CmpVersion = "{EXPECTED["version"]}";',
        f'public const string CmpCommit = "{EXPECTED["commit"]}";',
        'public const string CmpUrl = '
        '"https://codeload.github.com/ehylla93/had2-cmp/zip/" + CmpCommit;',
        f'public const string CmpSha256 = "{EXPECTED["sha256"]}";',
        f'public const long CmpArchiveBytes = {EXPECTED["archive_bytes"]};',
        f'public const long CmpExpandedBytes = {EXPECTED["expanded_bytes"]};',
    ]
    missing = missing_markers(config, config_markers)
    if missing:
        errors.append("Pinned CMP configuration changed: " + ", ".join(missing))

    integrity_markers = [
        "new FileInfo(path).Length",
        "actualBytes != AppConfig.CmpArchiveBytes",
        "ComputeSha256(path)",
        f"archive.Entries.Count != {EXPECTED['entries']}",
        "CmpRoots.Contains(top)",
        'piece == "." || piece == ".."',
        "relative.IndexOf(':') >= 0",
        "duplicates.Add(relative)",
        "InstallerCore.SafeGameTarget(gamePath, relative)",
        'String.Equals(top, "cmp_optional"',
        "foundMapList",
        "mapCount < 100",
    ]
    missing = missing_markers(installer, integrity_markers)
    if missing:
        errors.append("CMP integrity/structure guard missing: " + ", ".join(missing))

    option_markers = [
        'cmp.Text = "Installer CMP 2.6.5',
        "cmp.Checked = true;",
        "InstallCmp = cmp.Checked",
        '"CMP 2.6.5 :", "deja installee"',
    ]
    missing = missing_markers(main_form, option_markers)
    if missing:
        errors.append("CMP user option/detection incomplete: " + ", ".join(missing))
    if "if (options.InstallCmp)" not in core or "CmpInstaller.Install(" not in core:
        errors.append("CMP option is not connected to installation")

    build_lower = build.lower()
    if "cmpinstaller.cs" in build_lower or re.search(
        r"/resource:[^\r\n]*(had2-cmp|cmp_v\d)", build_lower
    ):
        errors.append("Build script appears to embed CMP content")

    embedded_archives: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        lowered = relative.as_posix().lower()
        if path.suffix.lower() in {".zip", ".7z", ".rar"} and (
            "had2-cmp" in lowered or re.search(r"(^|/)cmp(?:_|-|\d)", lowered)
        ):
            embedded_archives.append(relative.as_posix())
    if embedded_archives:
        errors.append("CMP archives found in repository: " + ", ".join(embedded_archives))

    policy_markers = [
        EXPECTED["commit"],
        EXPECTED["sha256"],
        "aucune licence",
        "aucune donnée CMP n'est incorporée",
        "=RpR=",
        "leurs auteurs respectifs",
        "https://github.com/ehylla93/had2-cmp",
    ]
    missing = missing_markers(policy, policy_markers)
    if missing:
        errors.append("Community-content notice incomplete: " + ", ".join(missing))
    if "CONTENU_COMMUNAUTAIRE.md" not in readme:
        errors.append("README does not link the community-content notice")

    return {
        "ok": not errors,
        "cmp_version": EXPECTED["version"],
        "cmp_commit": EXPECTED["commit"],
        "download_on_demand": "client.DownloadFile(new Uri(AppConfig.CmpUrl)" in installer,
        "exact_size_required": "actualBytes != AppConfig.CmpArchiveBytes" in installer,
        "sha256_required": "VerifySha256(package, AppConfig.CmpSha256)" in installer,
        "archive_entries_required": int(EXPECTED["entries"]),
        "opt_in_checkbox": "InstallCmp = cmp.Checked" in main_form,
        "embedded_cmp_archives": embedded_archives,
        "license_declared_by_source": False,
        "policy_notice": policy_path.relative_to(root).as_posix(),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    arguments = parser.parse_args()
    result = audit(arguments.root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
