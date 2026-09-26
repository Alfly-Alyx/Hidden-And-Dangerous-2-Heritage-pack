#!/usr/bin/env python3
"""Check or build one disabled experimental script from licensed HD2 archives.

No commercial script is bundled, no source archive is changed, and nothing is
installed. The default action is a read-only check. A build requires an explicit
profile and writes exclusively below the repository's ignored .analysis folder.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

from dta_archive import DtaArchive
from menu_gui_audit import parse_4ds_nodes
from script_binding_audit import parse_bindings, scene_frame_names

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "experimental/reconstruction-variants.json"
ARCHIVES = ("missions.dta", "Scripts.dta", "Patch.dta", "SabreSquadron.dta")
ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
SHA_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
ASSET_PATTERN = re.compile(r"(?:sounds/[0-9]{8}\.wav|tables/dabing/[0-9]{8}\.dat)\Z")
ASSET_ARCHIVES = ("LangEnglish.dta", "SabreSquadron.dta")


def asset_specs(profile: dict) -> list[dict]:
    specs = profile.get("asset_evidence", [])
    if not isinstance(specs, list):
        raise ValueError("Asset evidence must be a list")
    seen = set()
    for spec in specs:
        if (not isinstance(spec, dict) or set(spec) != {"path", "archive", "size", "sha256"}
                or not isinstance(spec["path"], str) or not ASSET_PATTERN.fullmatch(spec["path"])
                or spec["archive"] not in ASSET_ARCHIVES
                or type(spec["size"]) is not int or spec["size"] <= 0
                or not isinstance(spec["sha256"], str) or not SHA_PATTERN.fullmatch(spec["sha256"])
                or spec["path"] in seen):
            raise ValueError("Invalid or duplicate pinned dialogue asset")
        seen.add(spec["path"])
    return specs


def normalized(value: str) -> str:
    return value.replace("\\", "/").casefold()


def entry_path(value: str) -> str:
    name = normalized(value)
    parts = name.split("/")
    if (len(parts) != 3 or parts[0] not in ("scripts", "missions")
            or any(part in ("", ".", "..") for part in parts)
            or ":" in name):
        raise ValueError(f"Invalid mission entry path: {value}")
    return name


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def change_specs(profile: dict) -> list[dict]:
    """An atomic profile may have several bound scripts in the same mission."""
    fields = {"source", "actor", "owner_entry", "edits"}
    primary = {key: profile[key] for key in fields if key in profile}
    additional = profile.get("additional_changes", [])
    if not isinstance(additional, list):
        raise ValueError("additional_changes must be a list")
    result = [primary]
    sources, actors = set(), set()
    mission = entry_path(primary["source"]).split("/")[1]
    for change in [primary, *additional]:
        if not isinstance(change, dict) or set(change) - fields:
            raise ValueError("Unexpected additional script fields")
        if not {"source", "actor", "edits"}.issubset(change):
            raise ValueError("Each changed script needs source, actor and edits")
        source = entry_path(change["source"])
        if (source != change["source"] or source.split("/")[1] != mission
                or not source.startswith("scripts/") or not source.endswith(".scr")):
            raise ValueError("A changed script must stay in the source mission")
        if not isinstance(change["actor"], str) or not change["actor"].strip():
            raise ValueError("Each changed script needs a named owner")
        actor = change["actor"].casefold()
        if source in sources or actor in actors:
            raise ValueError("Duplicate script or owner in atomic profile")
        sources.add(source)
        actors.add(actor)
    result.extend(additional)
    return result


def typed_names(raw: bytes, entry: str) -> set[str]:
    if entry.endswith(".4ds"):
        return {node["name"].casefold() for node in parse_4ds_nodes(raw)["nodes"]}
    return scene_frame_names(raw)


def load_catalog(path: Path = CATALOG) -> dict:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if catalog.get("schema_version") != 1:
        raise ValueError("Unsupported reconstruction catalog version")
    profiles = catalog.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("Catalog must contain profiles")
    ids = set()
    for profile in profiles:
        identifier = profile["id"]
        if not ID_PATTERN.fullmatch(identifier) or identifier in ids:
            raise ValueError(f"Invalid or duplicate profile id: {identifier}")
        ids.add(identifier)
        source = entry_path(profile["source"])
        mission = source.split("/")[1]
        if not source.startswith("scripts/") or not source.endswith(".scr"):
            raise ValueError(f"Profile source is not a script: {identifier}")
        if profile.get("runtime_status") != "pending":
            raise ValueError("This generator only accepts pending prototypes")
        if profile.get("default_profile") != "commercial":
            raise ValueError("The commercial profile must remain the default")
        evidence = profile["evidence"]
        asset_specs(profile)
        changes = change_specs(profile)
        required = {f"missions/{mission}/scripts.dta", f"missions/{mission}/actors.bin"}
        for change in changes:
            owner_entry = change.get("owner_entry", f"missions/{mission}/actors.bin")
            if owner_entry not in tuple(f"missions/{mission}/{name}" for name in
                                        ("actors.bin", "scene2.bin", "scene.4ds")):
                raise ValueError("Owner evidence must be the mission actors or typed scene frames")
            required.update((change["source"], owner_entry))
        if not required.issubset(evidence):
            raise ValueError(f"Missing script, registry or actor evidence: {identifier}")
        for name, proof in evidence.items():
            if entry_path(name) != name or name.split("/")[1] != mission:
                raise ValueError(f"Evidence outside the selected mission: {name}")
            if (proof["archive"] not in ARCHIVES or proof["size"] <= 0
                    or not SHA_PATTERN.fullmatch(proof["sha256"])):
                raise ValueError(f"Invalid evidence fingerprint: {name}")
        for check in profile.get("checks", []):
            if check["entry"] not in evidence:
                raise ValueError("A prerequisite must have pinned evidence")
            if check["kind"] not in ("frames", "4ds_frames", "nul_strings") or not check["values"]:
                raise ValueError("Invalid prerequisite check")
            if check["kind"] == "4ds_frames" and not check["entry"].endswith(".4ds"):
                raise ValueError("4DS prerequisites require a 4DS source")
        for change in changes:
            if not change["edits"]:
                raise ValueError("A variant must contain at least one explicit edit")
            for edit in change["edits"]:
                if not edit["before"] or edit["before"] == edit["after"]:
                    raise ValueError("Empty or ineffective edit")
                # Edits use LF; the original local newline style is retained.
                if "\r" in edit["before"] + edit["after"]:
                    raise ValueError("Catalog edits must use LF newlines")
                edit["before"].encode("cp1252")
                edit["after"].encode("cp1252")
    return {profile["id"]: profile for profile in profiles}


class ArchiveSources:
    """Indexed, read-only archive reader with explicit effective-file provenance."""

    def __init__(self, game: Path, archives_only: bool = False):
        self.game = game.resolve()
        self.archives_only = archives_only
        self.excluded_loose_overrides = {}
        self.stack = ExitStack()
        self.index = {}
        self.cache = {}

    def __enter__(self):
        try:
            for name in (*ARCHIVES, "PatchX01.dta"):
                path = self.game / name
                if name == "PatchX01.dta" and not path.exists():
                    continue
                archive = self.stack.enter_context(DtaArchive(path))
                entries = {}
                for entry in archive.entries:
                    key = normalized(entry.name)
                    entries.setdefault(key, []).append(entry)
                self.index[name] = (archive, entries)
        except Exception:
            self.stack.close()
            raise
        return self

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def mission_entries(self, mission: str) -> list[str]:
        if not re.fullmatch(r"[a-z0-9_]+", mission):
            raise ValueError("Invalid source mission name")
        prefixes = (f"missions/{mission}/", f"scripts/{mission}/")
        return sorted({name for archive in (*ARCHIVES, "PatchX01.dta") if archive in self.index
                       for name in self.index[archive][1]
                       if name.startswith(prefixes)})

    def read(self, name: str) -> tuple[str, bytes]:
        name = entry_path(name)
        # Loose overrides are deliberately not used as an unverified baseline.
        loose = self.game.joinpath(*PurePosixPath(name).parts)
        if loose.exists():
            if not self.archives_only:
                raise ValueError(f"Loose override must be reviewed separately: {name}")
            raw = loose.read_bytes()
            self.excluded_loose_overrides[name] = {
                "size": len(raw), "sha256": digest(raw),
            }
        if name in self.cache:
            return self.cache[name]
        if "PatchX01.dta" in self.index and name in self.index["PatchX01.dta"][1]:
            raise ValueError(f"Unreviewed PatchX01 override: {name}")
        found = None
        for archive_name in ARCHIVES:
            archive, entries = self.index[archive_name]
            matches = entries.get(name, [])
            if len(matches) > 1:
                raise ValueError(f"Ambiguous archive entry: {archive_name}::{name}")
            if matches:
                found = (archive_name, archive, matches[0])
        if found is None:
            raise ValueError(f"Missing commercial entry: {name}")
        archive_name, archive, entry = found
        result = (archive_name, archive.read(entry))
        self.cache[name] = result
        return result

    def read_asset(self, name: str, archive_name: str) -> bytes:
        """Read a named audio/lip-sync reference, never export or install it.

        This pins the selected English source, not a claim about all language
        editions or runtime resource precedence.
        """
        if not ASSET_PATTERN.fullmatch(name) or archive_name not in ASSET_ARCHIVES:
            raise ValueError("Unsupported dialogue asset source")
        loose = self.game.joinpath(*name.split('/'))
        if loose.exists():
            if not self.archives_only:
                raise ValueError(f"Loose asset override must be reviewed separately: {name}")
            raw = loose.read_bytes()
            self.excluded_loose_overrides[name] = {"size": len(raw), "sha256": digest(raw)}
        if archive_name not in self.index:
            archive = self.stack.enter_context(DtaArchive(self.game / archive_name))
            entries = {}
            for entry in archive.entries:
                entries.setdefault(normalized(entry.name), []).append(entry)
            self.index[archive_name] = (archive, entries)
        archive, index = self.index[archive_name]
        matches = index.get(name, [])
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous dialogue asset: {name}")
        raw = archive.read(matches[0])
        if loose.exists() and loose.read_bytes() != raw:
            raise ValueError("Conflicting loose dialogue asset: " + name)
        return raw


def apply_edits(source: bytes, edits: list[dict]) -> bytes:
    # Some shipped scripts mix CRLF and LF. Match the local anchor's newline
    # style; never normalize the complete script to make an edit fit.
    variant = source
    for edit in edits:
        before = edit["before"].encode("cp1252")
        after = edit["after"].encode("cp1252")
        if not before or before == after:
            raise ValueError("Each edit must match exactly once and change bytes")
        if b"\n" in before:
            candidates = [(before.replace(b"\n", newline), newline)
                          for newline in (b"\r\n", b"\n", b"\r")]
            if sum(variant.count(anchor) for anchor, _ in candidates) != 1:
                raise ValueError("Each edit must match exactly once and change bytes")
            before, newline = next((a, n) for a, n in candidates if a in variant)
        else:
            if variant.count(before) != 1:
                raise ValueError("Each edit must match exactly once and change bytes")
            position = variant.index(before)
            following = re.search(rb"\r\n|\r|\n", variant[position + len(before):])
            preceding = list(re.finditer(rb"\r\n|\r|\n", variant[:position]))
            newline = (following.group() if following else
                       preceding[-1].group() if preceding else b"\n")
        after = after.replace(b"\n", newline)
        variant = variant.replace(before, after, 1)
    if variant == source:
        raise ValueError("The profile does not change its source")
    return variant


def prepare(profile: dict, sources) -> tuple[bytes, dict]:
    if profile.get("additional_changes"):
        raise ValueError("Atomic multi-script profile requires prepare_changes / a laboratory")
    verified = {}
    for asset in asset_specs(profile):
        raw = sources.read_asset(asset["path"], asset["archive"])
        if len(raw) != asset["size"] or digest(raw) != asset["sha256"]:
            raise ValueError("Pinned dialogue asset changed: " + asset["path"])
    for name, proof in profile["evidence"].items():
        archive, raw = sources.read(name)
        if (archive != proof["archive"] or len(raw) != proof["size"]
                or digest(raw) != proof["sha256"]):
            raise ValueError(f"Commercial source changed: {name} ({archive})")
        verified[name] = raw
    source_name = profile["source"]
    mission = source_name.split("/")[1]
    registry = verified[f"missions/{mission}/scripts.dta"]
    bindings = [script for actor, script in parse_bindings(registry)
                if actor.casefold() == profile["actor"].casefold()]
    if len(bindings) != 1 or normalized(bindings[0]) != source_name.rsplit("/", 1)[1]:
        raise ValueError(f"Missing or conflicting owner binding: {profile['actor']}")
    owner_entry = profile.get("owner_entry", f"missions/{mission}/actors.bin")
    actor_names = typed_names(verified[owner_entry], owner_entry)
    if profile["actor"].casefold() not in actor_names:
        raise ValueError(f"Missing serialized actor: {profile['actor']}")
    for check in profile.get("checks", []):
        raw = verified[check["entry"]]
        names = typed_names(raw, check["entry"]) if check["kind"] in ("frames", "4ds_frames") else set()
        for value in check["values"]:
            present = (value.casefold() in names if check["kind"] in ("frames", "4ds_frames")
                       else value.encode("cp1252") + b"\0" in raw)
            if not present:
                raise ValueError(f"Missing {check['kind']} prerequisite: {value}")
    source = verified[source_name]
    variant = apply_edits(source, profile["edits"])
    report = {
        "profile": profile["id"], "mission": mission, "actor": profile["actor"],
        "owner_entry": owner_entry,
        "source": source_name,
        "source_archive": profile["evidence"][source_name]["archive"],
        "source_sha256": digest(source), "variant_sha256": digest(variant),
        "source_bytes": len(source), "variant_bytes": len(variant),
        "edit_count": len(profile["edits"]),
        "verified_evidence_count": len(verified),
        "default_profile": "commercial", "static_status": "passed",
        "runtime_status": "pending", "installed_into_game": False,
        "source_mode": ("commercial_archives_only" if getattr(sources, "archives_only", False)
                        else "commercial_archives_without_relevant_loose_overrides"),
        "excluded_loose_overrides": {
            name: details for name, details in
            getattr(sources, "excluded_loose_overrides", {}).items() if name in verified
        },
        "installed_game_compatibility": "not_tested",
        "output": None,
    }
    return variant, report


def prepare_changes(profile: dict, sources) -> tuple[dict[str, bytes], dict]:
    """Validate every member before returning any portion of an atomic change."""
    specs = change_specs(profile)
    payload, reports = {}, []
    for spec in specs:
        single = {key: value for key, value in profile.items()
                  if key not in ("additional_changes", "owner_entry")}
        single.update(spec)
        data, report = prepare(single, sources)
        payload[spec["source"]] = data
        reports.append(report)
    report = dict(reports[0])
    report["changed_script_count"] = len(reports)
    report["changes"] = [{key: item[key] for key in (
        "source", "actor", "owner_entry", "source_archive", "source_sha256",
        "variant_sha256", "source_bytes", "variant_bytes", "edit_count")}
        for item in reports]
    report["edit_count"] = sum(item["edit_count"] for item in reports)
    return payload, report


def write_disabled(output: Path, data: bytes, game: Path,
                   root: Path = ROOT) -> Path:
    ignored_root = root.resolve() / ".analysis"
    output = output.resolve()
    if not output.is_relative_to(ignored_root):
        raise ValueError("Output must stay inside the ignored .analysis directory")
    if output.is_relative_to(game.resolve()):
        raise ValueError("Output must never be written into the game installation")
    if not output.name.endswith(".scr.disabled"):
        raise ValueError("Output must end in .scr.disabled")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(data)
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true")
    selection.add_argument("--profile")
    selection.add_argument("--check-all", action="store_true")
    parser.add_argument("--game", type=Path)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--archives-only", action="store_true",
                        help="Explicitly exclude loose mod files; report their fingerprints")
    args = parser.parse_args(argv)
    if args.build and not args.profile:
        parser.error("--build requires one explicit --profile")
    if args.output and not args.build:
        parser.error("--output requires --build")
    if not args.list and not args.game:
        parser.error("--game is required for checks and builds")
    try:
        profiles = load_catalog()
        if args.list:
            print(json.dumps([
                {key: p[key] for key in ("id", "title", "source", "runtime_status")}
                for p in profiles.values()
            ], ensure_ascii=False, indent=2))
            return 0
        if args.profile and args.profile not in profiles:
            raise ValueError(f"Unknown profile: {args.profile}")
        chosen = [profiles[args.profile]] if args.profile else list(profiles.values())
        reports = []
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            for profile in chosen:
                try:
                    changes, report = prepare_changes(profile, sources)
                    if args.build:
                        if len(changes) != 1:
                            raise ValueError("Atomic multi-script profile: build a complete disabled laboratory")
                        output = args.output or (
                            ROOT / ".analysis/generated" / f"{profile['id']}.scr.disabled"
                        )
                        report["output"] = str(write_disabled(output, next(iter(changes.values())), args.game))
                    reports.append(report)
                except (OSError, ValueError) as error:
                    reports.append({"profile": profile["id"], "static_status": "failed",
                                    "error": str(error), "runtime_status": "pending",
                                    "installed_into_game": False, "output": None})
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0 if all(r["static_status"] == "passed" for r in reports) else 1
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Variant not built: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
