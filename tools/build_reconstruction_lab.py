#!/usr/bin/env python3
"""Build an inert A/B mission laboratory, without installing or launching HD2.

Every payload member, including tree.klz, mission.json and scripts, ends with
.disabled. Even accidental extraction cannot create a scannable mission package.
The bundle contains licensed commercial derivatives: keep it local and ignored.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import zipfile

from build_reconstruction_variant import (
    ROOT, ArchiveSources, digest, entry_path, load_catalog, prepare,
)
from mission_closure_audit import INCLUDE_RE, transitive_scripts
from objective_audit import split_comments
from script_binding_audit import normalize_script_name, parse_bindings

REQUIRED_MISSION_FILES = {
    "tree.klz", "scene.4ds", "scene2.bin", "actors.bin", "scripts.dta", "check2.bin",
}
# Empty names explicitly detach a script. They are literals, not dependencies.
# Require the closing parenthesis so "prefix" + variable is not mistaken for
# a complete literal name by the broader discovery regex in the shared audit.
LITERAL_ASSIGN_RE = re.compile(
    r'\bScriptAssign\s*\(\s*[^,\r\n]+\s*,\s*"([^"]*)"\s*\)', re.I)


def lab_names(profile: dict, mode: str) -> tuple[str, str]:
    if mode not in ("baseline", "variant"):
        raise ValueError("Unknown laboratory mode")
    mission = profile["source"].split("/")[1]
    identifier = digest(profile["id"].encode("ascii"))[:12]
    directory = f"H2Lab_{mission}_{identifier}_{'B' if mode == 'baseline' else 'V'}"
    return f"hd2lab.{identifier}.{mode}", directory


def script_closure(files: dict[str, bytes], mission: str) -> dict:
    prefix = f"scripts/{mission}/"
    # Undefined cp1252 bytes occur in commercial comments. Decoding is used
    # only for analysis; the bytes placed into the bundle are never transcoded.
    texts = {name.rsplit("/", 1)[1]: split_comments(raw.decode("cp1252", errors="replace"))[0]
             for name, raw in files.items() if name.startswith(prefix) and name.endswith(".scr")}
    roots = set()
    for _, script in parse_bindings(files[f"missions/{mission}/scripts.dta"]):
        if not script.strip():
            continue
        if "/" in script or "\\" in script:
            raise ValueError(f"Non-local registry script requires manual remapping: {script}")
        roots.add(normalize_script_name(script))
    used, missing = transitive_scripts(roots, texts)
    if missing:
        raise ValueError("Missing script dependencies: " + ", ".join(sorted(missing)))
    for name in sorted(used):
        text = texts[name]
        includes, assignments = INCLUDE_RE.findall(text), LITERAL_ASSIGN_RE.findall(text)
        if (len(assignments) != len(re.findall(r"\bScriptAssign\s*\(", text, re.I))
                or len(includes) != len(re.findall(r"^\s*#include\b", text, re.I | re.M))):
            raise ValueError(f"Non-literal script dependency requires review: {name}")
        for dependency in includes + assignments:
            if "/" in dependency or "\\" in dependency:
                raise ValueError(f"Non-local script dependency requires remapping: {name}: {dependency}")
    return {"root_scripts": len(roots), "reachable_scripts": len(used),
            "available_scripts": len(texts), "missing_scripts": [],
            "runtime_resolution": "pending"}


def plan_lab(profile: dict, sources) -> tuple[dict[str, bytes], dict]:
    variant, variant_report = prepare(profile, sources)
    mission = profile["source"].split("/")[1]
    files, provenance = {}, {}
    for name in sources.mission_entries(mission):
        entry_path(name)  # refuse traversal and unreviewed nested structures
        if not name.startswith((f"missions/{mission}/", f"scripts/{mission}/")):
            raise ValueError(f"Entry outside the selected mission: {name}")
        archive, raw = sources.read(name)
        files[name] = raw
        provenance[name] = {"archive": archive, "size": len(raw), "sha256": digest(raw)}
    required = {f"missions/{mission}/{name}" for name in REQUIRED_MISSION_FILES}
    if not required.issubset(files):
        raise ValueError("Incomplete source mission: " + ", ".join(sorted(required - files.keys())))
    if files.get(profile["source"]) is None:
        raise ValueError("The variant script is outside the copied source set")
    if digest(files[profile["source"]]) != variant_report["source_sha256"]:
        raise ValueError("Source changed between validation and packaging")
    needles = [f"{kind}{sep}{mission}{sep}".encode("ascii")
               for kind in ("missions", "scripts") for sep in ("/", "\\")]
    for name, raw in files.items():
        if any(needle in raw.lower() for needle in needles):
            raise ValueError(f"Hard-coded original mission path requires manual remapping: {name}")
    baseline_closure = script_closure(files, mission)
    changed_files = {**files, profile["source"]: variant}
    variant_closure = script_closure(changed_files, mission)
    if baseline_closure != variant_closure:
        raise ValueError("A single-script profile unexpectedly changes script dependency closure")

    members, packages = {}, []
    for mode, payload in (("baseline", files), ("variant", changed_files)):
        package_id, directory = lab_names(profile, mode)
        manifest = {
            "format": 1, "id": package_id, "category": "user-mission",
            "missionDirectory": directory, "templateMission": mission,
            "preserveTemplateObjectives": True,
            "title": {"default": f"TEST {mode} - {profile['id']}",
                      "french": f"TEST {'temoin' if mode == 'baseline' else 'variante'} - {profile['id']}"},
        }
        manifest_member = f"{mode}/mission.json.disabled"
        members[manifest_member] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        mapping = []
        for name, raw in sorted(payload.items()):
            kind, _, filename = name.split("/")
            relative = f"{'Missions' if kind == 'missions' else 'Scripts'}/{directory}/{filename}"
            member = f"{mode}/payload/{relative}.disabled"
            members[member] = raw
            mapping.append({"member": member, "proposed_relative_path": relative,
                            "source_entry": name, "size": len(raw), "sha256": digest(raw),
                            "changed_from_commercial": mode == "variant" and name == profile["source"]})
        packages.append({"mode": mode, "id": package_id, "mission_directory": directory,
                         "manifest_member": manifest_member, "files": mapping})
    report = {
        "schema_version": 1, "profile": profile["id"], "source_mission": mission,
        "status": "disabled_lab_prepared", "runtime_status": "pending",
        "installed_into_game": False, "commercial_derivative_do_not_distribute": True,
        "template_objectives": "preserve_exactly", "script_closure": baseline_closure,
        "source_files": provenance, "variant": variant_report, "packages": packages,
        "excluded_loose_overrides": {name: proof for name, proof in
                                     getattr(sources, "excluded_loose_overrides", {}).items()
                                     if name in files},
        "remaining_gates": ["isolated_runtime_installation", "menu_and_spawn",
                            "local_script_resolution", "objectives_and_end",
                            "interruption_and_save_load", "baseline_comparison"],
    }
    # No unreviewed active manifest or script is left behind even on extraction.
    members["lab-report.json"] = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return members, report


def verify_bundle(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) > 10000 or sum(info.file_size for info in archive.infolist()) > 512 * 1024 * 1024:
            raise ValueError("Laboratory bundle exceeds inspection limits")
        if len(names) != len(set(names)) or any(
                name.startswith(("/", "\\")) or "\\" in name or ":" in name
                or any(part in ("", ".", "..") for part in name.split("/")) for name in names):
            raise ValueError("Unsafe or duplicate bundle member")
        if "lab-report.json" not in names:
            raise ValueError("Missing laboratory report")
        report = json.loads(archive.read("lab-report.json"))
        if (report["schema_version"] != 1 or report["runtime_status"] != "pending"
                or report["installed_into_game"] is not False):
            raise ValueError("Invalid laboratory state")
        expected = {"lab-report.json"}
        if [p["mode"] for p in report["packages"]] != ["baseline", "variant"]:
            raise ValueError("A laboratory requires one baseline and one variant")
        variant = report["variant"]
        if variant["profile"] != report["profile"]:
            raise ValueError("Profile identity mismatch")
        snapshots = []
        for package in report["packages"]:
            directory = package["mission_directory"]
            expected_id, expected_directory = lab_names(
                {"id": report["profile"], "source": variant["source"]}, package["mode"])
            if (directory != expected_directory or package["id"] != expected_id
                    or not re.fullmatch(r"H2Lab_[a-z0-9_]+_[0-9a-f]{12}_[BV]", directory)):
                raise ValueError("Unexpected laboratory namespace")
            manifest_member = package["manifest_member"]
            expected.add(manifest_member)
            if manifest_member != f"{package['mode']}/mission.json.disabled":
                raise ValueError("An active or misplaced manifest is forbidden")
            manifest = json.loads(archive.read(manifest_member))
            if (manifest.get("format") != 1 or manifest.get("id") != expected_id
                    or manifest.get("category") != "user-mission"
                    or manifest.get("missionDirectory") != directory
                    or manifest.get("preserveTemplateObjectives") is not True
                    or manifest.get("templateMission") != report["source_mission"]
                    or "objectives" in manifest):
                raise ValueError("Laboratory manifest changes the commercial objective contract")
            snapshot = {}
            for record in package["files"]:
                relative = record["proposed_relative_path"]
                entry = entry_path(record["source_entry"])
                kind, mission, filename = entry.split("/")
                prescribed = f"{'Missions' if kind == 'missions' else 'Scripts'}/{directory}/{filename}"
                if mission != report["source_mission"] or relative != prescribed:
                    raise ValueError("Payload escapes its laboratory namespace")
                member = record["member"]
                if member != f"{package['mode']}/payload/{relative}.disabled" or member in expected:
                    raise ValueError("Active, misplaced or duplicate payload member")
                expected.add(member)
                raw = archive.read(member)
                if len(raw) != record["size"] or digest(raw) != record["sha256"]:
                    raise ValueError(f"Corrupt laboratory payload: {member}")
                snapshot[entry] = digest(raw)
            snapshots.append(snapshot)
        if set(names) != expected or set(snapshots[0]) != set(snapshots[1]):
            raise ValueError("Unexpected or asymmetric bundle contents")
        required = {f"missions/{report['source_mission']}/{name}" for name in REQUIRED_MISSION_FILES}
        if not required.issubset(snapshots[0]):
            raise ValueError("Incomplete source mission in bundle")
        source_hashes = {name: p["sha256"] for name, p in report["source_files"].items()}
        if snapshots[0] != source_hashes:
            raise ValueError("The baseline is not an exact commercial copy")
        changed = [name for name in snapshots[0] if snapshots[0][name] != snapshots[1][name]]
        if (changed != [variant["source"]] or snapshots[1][changed[0]] != variant["variant_sha256"]
                or snapshots[0][changed[0]] != variant["source_sha256"]):
            raise ValueError("The variant changes more than the approved script")
        return report


def write_bundle(output: Path, members: dict[str, bytes], game: Path,
                 root: Path = ROOT) -> Path:
    output = output.resolve()
    if not output.is_relative_to(root.resolve() / ".analysis") or output.is_relative_to(game.resolve()):
        raise ValueError("Laboratory output must stay under .analysis and outside the game")
    if not output.name.endswith(".lab.zip.disabled"):
        raise ValueError("Laboratory output must end in .lab.zip.disabled")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream, zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    verify_bundle(output)
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--profile")
    selection.add_argument("--verify", type=Path)
    parser.add_argument("--game", type=Path)
    parser.add_argument("--archives-only", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.verify and (args.build or args.output):
        parser.error("--verify is read-only")
    if args.profile and not args.game:
        parser.error("--game is required with --profile")
    if args.output and not args.build:
        parser.error("--output requires --build")
    try:
        if args.verify:
            report = verify_bundle(args.verify)
            output = args.verify
        else:
            profiles = load_catalog()
            if args.profile not in profiles:
                raise ValueError(f"Unknown profile: {args.profile}")
            with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
                members, report = plan_lab(profiles[args.profile], sources)
            output = None
            if args.build:
                output = write_bundle(args.output or ROOT / ".analysis/laboratories" /
                                      f"{args.profile}.lab.zip.disabled", members, args.game)
        print(json.dumps({
            "profile": report["profile"], "status": report["status"],
            "source_files": len(report["source_files"]),
            "packages": [{k: p[k] for k in ("mode", "mission_directory")} for p in report["packages"]],
            "script_closure": report["script_closure"], "runtime_status": "pending",
            "installed_into_game": False, "output": str(output) if output else None,
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"Laboratory not ready: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
