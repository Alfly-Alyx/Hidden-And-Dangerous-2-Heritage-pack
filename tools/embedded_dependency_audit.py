#!/usr/bin/env python3
"""Verify the exact embedded widescreen dependency, wiring and MIT notice."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


ARCHIVE_SIZE = 1_306_660
ARCHIVE_SHA256 = (
    "8B8315B88420FCFED9891F2D39886F6384BDA1B32CDD299AC27D728391E65A9F"
)
EXPECTED_FILES = {
    "d3d8.dll": "A07F2B90B0EA9CFFB568218E500EA3280B750C195E83D82A6BB7A252642708E3",
    "Maps/2e_camra.tga": "43B609F80497959D1127B2A7F3F0FCAAEA1322A8BD9F770ECEEEC4146D2D1EF0",
    "Maps/2e_scope.tga": "8E6E892F11B710F395853EA97CA4D09337FF4842AF543986941A59ADF90738E1",
    "Maps/e_zamer.tga": "0D86A937580805EBFE1F932F218E6407ACB4D7DC365A34C0C50385A7522F6FD7",
    "scripts/HiddenandDangerous2.WidescreenFix.asi": (
        "8375F31A2A1F6C6B401AF40BB4F8C741FD3BA90B36B14603176FB71465D62768"
    ),
    "scripts/HiddenandDangerous2.WidescreenFix.ini": (
        "337A157743D015644EA7DB069C5BDE05D4084C511730F480237B96146D96E701"
    ),
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def audit(root: Path) -> dict[str, object]:
    archive_path = (
        root / "installer" / "assets" / "HiddenandDangerous2.WidescreenFix.zip"
    )
    installer_path = root / "installer" / "WidescreenInstaller.cs"
    build_path = root / "build.ps1"
    notice_path = root / "docs" / "DEPENDANCES_EMBARQUEES.md"
    errors: list[str] = []

    if not archive_path.is_file():
        errors.append("Embedded widescreen archive is missing")
        archive_bytes = b""
        actual_size = 0
        actual_archive_hash = None
        actual_files: dict[str, str] = {}
    else:
        archive_bytes = archive_path.read_bytes()
        actual_size = len(archive_bytes)
        actual_archive_hash = sha256(archive_bytes)
        actual_files = {}
        try:
            with zipfile.ZipFile(archive_path) as archive:
                for entry in archive.infolist():
                    if entry.is_dir():
                        continue
                    if entry.filename in actual_files:
                        errors.append(
                            "Duplicate widescreen entry: " + entry.filename
                        )
                        continue
                    actual_files[entry.filename] = sha256(archive.read(entry))
        except (OSError, zipfile.BadZipFile) as error:
            errors.append(f"Unreadable widescreen archive: {error}")

    if actual_size != ARCHIVE_SIZE:
        errors.append(
            f"Widescreen archive size is {actual_size}, expected {ARCHIVE_SIZE}"
        )
    if actual_archive_hash != ARCHIVE_SHA256:
        errors.append("Widescreen archive SHA-256 changed")
    if set(actual_files) != set(EXPECTED_FILES):
        missing = sorted(set(EXPECTED_FILES) - set(actual_files))
        extra = sorted(set(actual_files) - set(EXPECTED_FILES))
        if missing:
            errors.append("Missing widescreen entries: " + ", ".join(missing))
        if extra:
            errors.append("Unexpected widescreen entries: " + ", ".join(extra))
    for name, expected in EXPECTED_FILES.items():
        if name in actual_files and actual_files[name] != expected:
            errors.append(f"Widescreen entry SHA-256 changed: {name}")

    installer = installer_path.read_text(encoding="utf-8-sig")
    build = build_path.read_text(encoding="utf-8-sig")
    notice = (
        notice_path.read_text(encoding="utf-8-sig")
        if notice_path.is_file() else ""
    )
    code_markers = [
        f'private const string ArchiveSha256 = "{ARCHIVE_SHA256}";',
        "if (!Expected.TryGetValue(relative, out expected))",
        "if (files != Expected.Count)",
        "InstallerCore.SafeGameTarget(gamePath, relative)",
        "InstallerCore.PrepareTarget(gamePath, relative, target, journal, prepared)",
        "HiddenandDangerous2.WidescreenFix.LICENSE.txt",
        "MIT License",
        "Copyright (c) 2018 ThirteenAG",
        "journal.RecordHash(relative, CmpInstaller.ComputeSha256(target))",
    ]
    missing_markers = [marker for marker in code_markers if marker not in installer]
    if missing_markers:
        errors.append(
            "Widescreen validation/license wiring changed: "
            + ", ".join(missing_markers)
        )
    for name, expected in EXPECTED_FILES.items():
        if f'{{ "{name}", "{expected}" }}' not in installer:
            errors.append(f"Widescreen code no longer pins {name}")

    build_markers = [
        r"installer\assets\HiddenandDangerous2.WidescreenFix.zip",
        "/resource:$widescreen,HD2CommunityInstaller.WidescreenFix.zip",
    ]
    missing_markers = [marker for marker in build_markers if marker not in build]
    if missing_markers:
        errors.append(
            "Widescreen resource is not embedded as expected: "
            + ", ".join(missing_markers)
        )

    notice_markers = [
        str(ARCHIVE_SIZE).replace("1306660", "1 306 660"),
        ARCHIVE_SHA256,
        "licence MIT",
        "ThirteenAG",
        "issues/450",
        "issues/467",
        "postérieur à",
    ]
    missing_markers = [marker for marker in notice_markers if marker not in notice]
    if missing_markers:
        errors.append(
            "Embedded dependency notice incomplete: "
            + ", ".join(missing_markers)
        )

    return {
        "ok": not errors,
        "dependency": "HiddenandDangerous2.WidescreenFix",
        "archive_size": actual_size,
        "archive_sha256": actual_archive_hash,
        "expected_files": len(EXPECTED_FILES),
        "verified_files": sum(
            1 for name, expected in EXPECTED_FILES.items()
            if actual_files.get(name) == expected
        ),
        "mit_notice_installed": "MIT License" in installer,
        "official_asset_match_verified_on": "2026-09-15",
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
    report = audit(arguments.root.resolve())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
