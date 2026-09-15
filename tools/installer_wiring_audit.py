#!/usr/bin/env python3
"""Check that installer features are wired into validation, install and status paths."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


VALIDATE_RE = re.compile(
    r"Console\.WriteLine\((?P<class>[A-Za-z0-9_]+)\.ValidateOnly\("
)
INSTALL_RE = re.compile(
    r"^\s*(?P<class>[A-Za-z0-9_]+)\.Install\(", re.MULTILINE
)
STATUS_RE = re.compile(
    r"if\s*\(\s*(?P<class>[A-Za-z0-9_]+)\."
    r"Is[A-Za-z0-9_]*Active\(gamePath\)\s*\)\s*ready\+\+;"
)
OPTION_MAP = {
    "ConfigureMasterServer": "master",
    "EnableDirectPlay": "directPlay",
    "InstallCmp": "cmp",
    "FreeExploration": "exploration",
    "FixOptionalObjectives": "objectives",
    "RestoreDormantSequences": "dormant",
    "RestoreOfficialEasterEggs": "officialEasterEggs",
    "UnlockAllMissions": "unlockMissions",
    "AutoConfigureGraphics": "graphics",
}


def between(text: str, start: str, end: str, source: Path) -> str:
    begin = text.find(start)
    finish = text.find(end, begin + len(start))
    if begin < 0 or finish < 0:
        raise ValueError(f"Unable to isolate {start!r} in {source}")
    return text[begin:finish]


def duplicates(values: list[str]) -> list[str]:
    return sorted({value for value in values if values.count(value) > 1})


def audit(root: Path) -> dict[str, object]:
    installer = root / "installer"
    program_path = installer / "Program.cs"
    core_path = installer / "InstallerCore.cs"
    status_path = installer / "FeatureStatusDetector.cs"
    config_path = installer / "Config.cs"
    main_form_path = installer / "MainForm.cs"
    program = program_path.read_text(encoding="utf-8-sig")
    core = core_path.read_text(encoding="utf-8-sig")
    status = status_path.read_text(encoding="utf-8-sig")
    config = config_path.read_text(encoding="utf-8-sig")
    main_form = main_form_path.read_text(encoding="utf-8-sig")
    mutation_sources = []
    unhashed_mutation_sources = []
    for source in sorted(installer.glob("*.cs")):
        if source.name == "InstallerCore.cs":
            continue
        content = source.read_text(encoding="utf-8-sig")
        if "InstallerCore.PrepareTarget(" not in content:
            continue
        mutation_sources.append(source.name)
        if ".RecordHash(" not in content:
            unhashed_mutation_sources.append(source.name)

    local_block = between(
        program,
        'if (command == "--self-test-local")',
        'if (command == "--self-test")',
        program_path,
    )
    full_block = between(
        program,
        'if (command == "--self-test")',
        'if (command == "--install")',
        program_path,
    )
    status_block = between(
        status,
        "private static string DetectDormantGuidance(string gamePath)",
        "private static string DetectEasterEggs(string gamePath)",
        status_path,
    )

    local = VALIDATE_RE.findall(local_block)
    full = VALIDATE_RE.findall(full_block)
    installed = INSTALL_RE.findall(core)
    status_classes = STATUS_RE.findall(status_block)
    status_checks = len(re.findall(r"\bready\+\+;", status_block))
    total_match = re.search(
        r"return\s+CountStatus\(ready,\s*(?P<total>\d+)\s*\);",
        status_block,
    )
    if total_match is None:
        raise ValueError("DetectDormantGuidance has no CountStatus total")
    declared_total = int(total_match.group("total"))

    errors: list[str] = []
    for label, values in (
        ("local self-test", local),
        ("full self-test", full),
        ("install", installed),
    ):
        repeated = duplicates(values)
        if repeated:
            errors.append(f"Duplicate classes in {label}: {', '.join(repeated)}")

    full_without_cmp = [name for name in full if name != "CmpInstaller"]
    if full_without_cmp != local:
        errors.append("Local and full self-tests differ beyond CmpInstaller")
    if full.count("CmpInstaller") != 1:
        errors.append("Full self-test must contain CmpInstaller exactly once")
    if "CmpInstaller" in local:
        errors.append("Local self-test must not require the external CMP archive")

    expected_full = set(installed) | {
        "DiagnosticStatusMatcher",
        "GraphicsConfigurator",
    }
    if set(full) != expected_full:
        missing = sorted(set(installed) - set(full))
        extra = sorted(set(full) - expected_full)
        if missing:
            errors.append("Installed without full self-test: " + ", ".join(missing))
        if extra:
            errors.append("Full self-test without install path: " + ", ".join(extra))

    missing_status_tests = sorted(set(status_classes) - set(local))
    missing_status_install = sorted(set(status_classes) - set(installed))
    if missing_status_tests:
        errors.append(
            "Status checks without local self-test: " + ", ".join(missing_status_tests)
        )
    if missing_status_install:
        errors.append(
            "Status checks without install path: " + ", ".join(missing_status_install)
        )
    if declared_total != status_checks:
        errors.append(
            f"Dormant status total is {declared_total}, but {status_checks} checks increment ready"
        )
    if unhashed_mutation_sources:
        errors.append(
            "Mutation sources without RecordHash: "
            + ", ".join(unhashed_mutation_sources)
        )
    if "journal.SealMissingHashes(options.GamePath)" not in core:
        errors.append("InstallerCore does not seal legacy missing hashes")

    declared_options = set(re.findall(r"public bool ([A-Za-z0-9_]+)\s*=", config))
    expected_options = set(OPTION_MAP)
    if declared_options != expected_options:
        missing = sorted(expected_options - declared_options)
        extra = sorted(declared_options - expected_options)
        if missing:
            errors.append("Expected InstallOptions missing: " + ", ".join(missing))
        if extra:
            errors.append("Unmapped InstallOptions: " + ", ".join(extra))
    detected_block = between(
        main_form,
        "private void ApplyDetectedState(string diagnostic)",
        "private void AppendLog(string message)",
        main_form_path,
    )
    busy_block = main_form[main_form.find("private void SetBusy(bool busy)") :]
    for option, checkbox in OPTION_MAP.items():
        if not re.search(
            rf"\b{re.escape(option)}\s*=\s*{re.escape(checkbox)}\.Checked\b",
            main_form,
        ):
            errors.append(f"{option} is not assigned from {checkbox}.Checked")
        if not re.search(rf"\boptions\.{re.escape(option)}\b", core):
            errors.append(f"{option} is not consumed by InstallerCore")
        if not re.search(rf"\b{re.escape(checkbox)}\.Checked\s*=", detected_block):
            errors.append(f"{checkbox} is not refreshed by detected state")
        if not re.search(rf"\b{re.escape(checkbox)}\.Checked\s*=\s*true\s*;", main_form):
            errors.append(f"{checkbox} has no enabled default")
        if not re.search(rf"\b{re.escape(checkbox)}\.Enabled\s*=\s*!busy\s*;", busy_block):
            errors.append(f"{checkbox} is not locked while the installer is busy")
    browse_block = between(
        main_form,
        "private void BrowseClick(object sender, EventArgs e)",
        "private async void InstallClick(object sender, EventArgs e)",
        main_form_path,
    )
    if "RunDiagnostic();" not in browse_block:
        errors.append("Choosing another game folder does not refresh detected state")

    return {
        "ok": not errors,
        "local_self_tests": len(local),
        "full_self_tests": len(full),
        "install_calls": len(installed),
        "dormant_status_checks": status_checks,
        "dormant_status_total": declared_total,
        "status_installer_classes": len(set(status_classes)),
        "mutation_sources": len(mutation_sources),
        "unhashed_mutation_sources": unhashed_mutation_sources,
        "interface_options": len(OPTION_MAP),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root (defaults to the parent of tools)",
    )
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.root.resolve())
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
