#!/usr/bin/env python3
"""Build a derived audit of all commercial H&D2 mission scripts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

from dta_archive import DtaArchive
from objective_audit import blocks, direct, split_comments, walk
from script_binding_audit import audit as binding_audit

SCRIPT_ARCHIVES = ("Scripts.dta", "Patch.dta", "SabreSquadron.dta")
GAMEDATA_ARCHIVES = ("others.DTA", "Patch.dta", "SabreSquadron.dta")
OBJECTIVE_RE = re.compile(r"\bSetObjectiveStatus\s*\(\s*(\d+)\s*,\s*([^\),]+)", re.I)
DORMANT_WORD_RE = re.compile(r"\b(TODO|FIXME|UNUSED|DISABLED|NOT\s+USED|OLD|TEST|DOPLNIT|POZDEJI)\b", re.I)
CANDIDATE_NAME_RE = re.compile(r"(obj|route|path|door|gate|bridge|tunnel|open|detector|counter|gary|easter|(?:^|_)ee(?:_|\.)|weapon|flame|garot|zk[-_ ]?383)", re.I)
TEXT_LINE_RE = re.compile(r'^\s*(\d+)\s+"(.*)"\s*$')
INITIAL_BLOCK_RE = re.compile(r"\bblock\s*\{(.*?)^\s*\}", re.I | re.S | re.M)
SAVE_GAME_RE = re.compile(r"\bSaveGameValue\s*\(\s*(\d+)\s*,", re.I)


def normalized(name: str) -> str:
    return name.replace("\\", "/").lower()


def archive_layers(game: Path, archive_names: tuple[str, ...], predicate):
    layers = defaultdict(list)
    effective = {}
    for archive_name in archive_names:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                name = normalized(entry.name)
                if not predicate(name):
                    continue
                data = archive.read(entry)
                item = {"archive": archive_name, "name": name, "size": len(data),
                        "sha256": hashlib.sha256(data).hexdigest().upper(), "data": data}
                layers[name].append(item)
                effective[name] = item
    return effective, layers


def catalogue_data(data: bytes, source: str):
    root = blocks(data, 0, len(data))
    if root is None:
        raise ValueError(f"Invalid GDT block structure: {source}")
    missions = []
    for node in walk(root):
        if node.kind != 0x32:
            continue
        names = direct(node, 0x36)
        if not names:
            continue
        name = names[0].payload.rstrip(b"\0").decode("cp1252", errors="replace")
        objectives = []
        for index, objective in enumerate(direct(node, 0x28), 1):
            ids = direct(objective, 0x29)
            text_id = struct.unpack_from("<I", ids[0].payload)[0] if ids and len(ids[0].payload) >= 4 else None
            objectives.append({"index": index, "text_id": text_id})
        missions.append({"name": name, "objectives": objectives, "source": source,
                         "kind": "singleplayer"})
    return missions


def multiplayer_catalogue_data(data: bytes, source: str):
    text = data.decode("cp1252", errors="replace")
    missions = []
    for map_match in re.finditer(r"<MAP\b[\s\S]*?</MAP>", text, re.I):
        block = map_match.group(0)
        directory = re.search(r'\bdir\s*=\s*"([^"]+)"', block, re.I)
        if not directory:
            continue
        objectives = [
            {"index": index, "text_id": int(match.group(1))}
            for index, match in enumerate(re.finditer(
                r'<OBJECTIVE\b[^>]*\ballied_text\s*=\s*"(\d+)"', block, re.I), 1)
        ]
        if objectives:
            missions.append({"name": directory.group(1), "objectives": objectives,
                             "source": source, "kind": "multiplayer"})
    return missions

def objective_text_index(game: Path):
    result = {}
    for relative in (Path("Text/english/TEXTY.txt"),
                     Path("Text/EnglishUS/TEXTY.txt"),
                     Path("Text/english/TEXTY_DD.txt"),
                     Path("Text/EnglishUS/TEXTY_DD.txt")):
        path = game / relative
        if not path.is_file():
            continue
        for line in path.read_text(encoding="cp1252", errors="replace").splitlines():
            match = TEXT_LINE_RE.match(line)
            if match:
                result[int(match.group(1))] = " ".join(
                    match.group(2).lower().split())
    return result

def analyse_script(name: str, data: bytes):
    text = data.decode("cp1252", errors="replace")
    active, comments = split_comments(text)
    active_objectives = Counter(int(m.group(1)) for m in OBJECTIVE_RE.finditer(active))
    commented_objectives = Counter(int(m.group(1)) for m in OBJECTIVE_RE.finditer(comments))
    preamble = re.split(r"\b(?:On[A-Z]\w*|Whenever|Label)\b", active,
                        maxsplit=1, flags=re.I)[0]
    initial = INITIAL_BLOCK_RE.search(preamble)
    initialized = Counter(int(m.group(1)) for m in SAVE_GAME_RE.finditer(
        initial.group(1) if initial else ""))
    return {"name": name, "active_objectives": dict(sorted(active_objectives.items())),
            "commented_objectives": dict(sorted(commented_objectives.items())),
            "duplicate_initial_state_slots": sorted(
                slot for slot, count in initialized.items() if count > 1),
            "dormant_words": sorted({m.group(1).upper() for m in DORMANT_WORD_RE.finditer(text)})}


def build(game: Path):
    scripts, script_layers = archive_layers(game, SCRIPT_ARCHIVES,
        lambda name: name.startswith("scripts/") and name.endswith(".scr"))
    gamedata, _ = archive_layers(game, GAMEDATA_ARCHIVES,
        lambda name: name.startswith("gamedata/")
        and (name.endswith(".gdt") or name.endswith("/mpmaplist.txt")))
    catalogues = []
    for name, item in sorted(gamedata.items()):
        source = f"{item['archive']}:{name}"
        if name.endswith(".gdt"):
            catalogues.extend(catalogue_data(item["data"], source))
        elif name.endswith("/mpmaplist.txt"):
            catalogues.extend(multiplayer_catalogue_data(item["data"], source))
    objective_texts = objective_text_index(game)

    by_directory = defaultdict(list)
    for name, item in sorted(scripts.items()):
        analysis = analyse_script(name, item["data"])
        parts = name.split("/")
        if len(parts) >= 3:
            by_directory[parts[1]].append(analysis)

    bindings = binding_audit(game, set())
    binding_by_mission = {item["mission"]: item for item in bindings["missions"]}
    catalogue_by_name = {}
    for item in catalogues:
        key = item["name"].lower()
        current = catalogue_by_name.get(key)
        if current is None or len(item["objectives"]) > len(current["objectives"]):
            catalogue_by_name[key] = item
    mission_rows = []
    for mission in sorted(set(by_directory) | set(binding_by_mission)):
        files = by_directory.get(mission, [])
        active, supported_active, commented = Counter(), Counter(), Counter()
        dormant_files = []
        duplicate_initializations = []
        binding = binding_by_mission.get(mission, {})
        unbound = set(binding.get("unbound_scripts", []))
        free_owners = set(binding.get(
            "unbound_scripts_with_free_matching_actor", []))
        for item in files:
            active.update({int(k): v for k, v in item["active_objectives"].items()})
            script_name = item["name"].split("/")[-1]
            if script_name not in unbound or script_name in free_owners:
                supported_active.update(
                    {int(k): v for k, v in item["active_objectives"].items()})
            commented.update({int(k): v for k, v in item["commented_objectives"].items()})
            if item["dormant_words"]:
                dormant_files.append(item["name"].split("/")[-1])
            if item["duplicate_initial_state_slots"]:
                duplicate_initializations.append({
                    "script": item["name"].split("/")[-1],
                    "slots": item["duplicate_initial_state_slots"]})
        orphan_active = sorted(set(active) - set(supported_active))
        unbound = sorted(unbound)
        named = sorted(name for name in unbound if CANDIDATE_NAME_RE.search(name))
        catalogue = catalogue_by_name.get(mission)
        declared = catalogue.get("objectives", []) if catalogue else []
        declared_indices = {item["index"] for item in declared}
        script_only = sorted(set(supported_active) - declared_indices) if catalogue else []
        declared_indices = [item["index"] for item in declared]
        inactive_declared = [
            index for index in declared_indices if index not in supported_active]
        text_to_indices = defaultdict(list)
        for item in declared:
            if item["text_id"] is not None:
                text_to_indices[item["text_id"]].append(item["index"])
        duplicate_declared = sorted(index for indices in text_to_indices.values()
            if len(indices) > 1 for index in indices)
        inactive_duplicates = sorted(set(inactive_declared) & set(duplicate_declared))
        active_texts = {
            objective_texts[item["text_id"]]
            for item in declared
            if item["index"] in supported_active and item["text_id"] in objective_texts
        }
        inactive_semantic_duplicates = sorted(
            item["index"] for item in declared
            if item["index"] in inactive_declared
            and item["index"] not in inactive_duplicates
            and item["text_id"] in objective_texts
            and objective_texts[item["text_id"]] in active_texts
        )
        inactive_unique = sorted(set(inactive_declared)
            - set(inactive_duplicates) - set(inactive_semantic_duplicates))
        reasons = []
        if inactive_unique: reasons.append("declared_objectives_without_script_update")
        if inactive_duplicates: reasons.append("inactive_duplicate_catalogue_entries")
        if inactive_semantic_duplicates:
            reasons.append("inactive_semantic_duplicate_catalogue_entries")
        if commented: reasons.append("objective_updates_in_comments")
        if script_only: reasons.append("script_objectives_not_declared")
        if orphan_active: reasons.append("orphan_script_objectives_without_owner")
        if named: reasons.append("unbound_named_scripts")
        if binding.get("unbound_scripts_with_free_matching_actor"):
            reasons.append("unbound_script_free_owner_present")
        if binding.get("missing_attached_scripts"): reasons.append("missing_bound_scripts")
        if dormant_files: reasons.append("dormant_markers")
        if duplicate_initializations:
            reasons.append("duplicate_initial_state_initialization")
        mission_rows.append({"mission": mission, "declared_objectives": len(declared),
            "catalogue_kind": catalogue.get("kind") if catalogue else None,
            "declared_text_ids": [item["text_id"] for item in declared], "script_count": len(files),
            "active_objective_indices": sorted(active),
            "supported_active_objective_indices": sorted(supported_active),
            "orphan_active_objective_indices": orphan_active,
            "inactive_declared_indices": inactive_declared,
            "inactive_unique_declared_indices": inactive_unique,
            "inactive_duplicate_declared_indices": inactive_duplicates,
            "inactive_semantic_duplicate_declared_indices": inactive_semantic_duplicates,
            "commented_objective_indices": sorted(commented),
            "script_only_objective_indices": script_only,
            "unbound_script_count": len(unbound), "unbound_named_candidates": named,
            "unbound_scripts_with_matching_actor": binding.get(
                "unbound_scripts_with_matching_actor", []),
            "unbound_scripts_with_free_matching_actor": binding.get(
                "unbound_scripts_with_free_matching_actor", []),
            "unbound_scripts_with_conflicting_matching_actor": binding.get(
                "unbound_scripts_with_conflicting_matching_actor", []),
            "missing_attached_scripts": binding.get("missing_attached_scripts", []),
            "missing_attached_bindings": binding.get("missing_attached_bindings", []),
            "duplicate_initial_state_initializations": duplicate_initializations,
            "dormant_marker_files": sorted(set(dormant_files)), "candidate_reasons": reasons})

    overridden = []
    for name, versions in sorted(script_layers.items()):
        if len(versions) > 1 and len({item["sha256"] for item in versions}) > 1:
            overridden.append({"name": name, "versions": [
                {key: item[key] for key in ("archive", "size", "sha256")} for item in versions]})
    return {"game": str(game), "scope": {"registry_missions": bindings["mission_count"],
        "registry_files": bindings["registry_count"],
        "script_directories": len(by_directory), "effective_scripts": len(scripts),
        "catalogue_missions": len(catalogue_by_name),
        "singleplayer_catalogue_missions": sum(1 for item in catalogue_by_name.values()
            if item.get("kind") == "singleplayer"),
        "multiplayer_catalogue_missions": sum(1 for item in catalogue_by_name.values()
            if item.get("kind") == "multiplayer"),
        "overridden_scripts": len(overridden)},
        "missions": mission_rows, "overrides": overridden}


def markdown(report):
    scope = report["scope"]
    candidates = [m for m in report["missions"] if m["candidate_reasons"]]
    lines = ["# Audit complet des missions et scripts", "",
        "Ce registre est produit automatiquement à partir des archives commerciales, sans publier leur contenu brut. Un candidat n'est pas encore une restauration sûre.", "",
        "Un objectif hors catalogue n'est retenu que si son script est effectivement raccordé, inclus par un script raccordé, ou possède encore un acteur homonyme libre. Un numéro trouvé uniquement dans un script orphelin reste signalé comme vestige sans propriétaire, mais n'est plus compté comme objectif activable.", "",
        "## Couverture initiale", "", f"- {scope['registry_missions']} missions ou variantes analysées dans {scope['registry_files']} registres solo et multijoueurs ;",
        f"- {scope['script_directories']} dossiers de scripts ;", f"- {scope['effective_scripts']} scripts effectifs ;",
        f"- {scope['catalogue_missions']} entrées de catalogue : "
        f"{scope['singleplayer_catalogue_missions']} solo et "
        f"{scope['multiplayer_catalogue_missions']} coopératives ;",
        f"- {scope['overridden_scripts']} scripts remplacés entre base, Patch et Sabre Squadron ;",
        f"- {len(candidates)} missions ou variantes avec au moins un indice à examiner.", "",
        "## Registre des candidats", "",
        "Les registres `mpscripts.dta` sont inclus : leurs scripts ne sont plus classés à tort comme orphelins. Brest, son conseil contextuel coopératif, le second poste radio et le compteur des cinq charges d'Arctic 2, le journal Burgundy 1 coop, la porte 35 de Czech 4 Zone, la commande du second garde de Czech 2, la réaction du groupe Wood d'Arctic 3, le second détecteur de patrouille de Czech 3, la seconde approche de la place dans Czech 4, le second détecteur du civil 03 d'Alps 1, le détecteur d'alarme d'Alps 2, les dix alertes du commandement d'Africa 1, les deux réactions de garde d'Africa 2, les deux identifiants de voix erronés de la conversation 05 d'Africa 3, la zone de découverte du véhicule d'Africa 3, la conséquence radio d'Africa 4, le compteur des cinq avions d'Africa 5, l'objectif du parc automobile de Libye 2 coopératif, l'objectif des générateurs de Brest coopératif, les deux objectifs de discrétion de Burgundy 1 coopératif, la chaîne des prisonniers de Burgundy 3 coopératif, l'objectif de sortie de Czech 2 ainsi que la paire de détecteurs Norway ont franchi la validation manuelle et sont intégrés aux sources du paquet ; leurs lignes décrivent les archives commerciales originales, pas l'état après installation.", "",
        "| Mission | Obj. déclarés | Obj. de script hors catalogue | Obj. uniques jamais pilotés | Doublons d'identifiant | Doublons de texte | Scripts non reliés | Acteur homonyme libre | Candidats nommés | Références manquantes | États initialisés en double | Indices |",
        "|---|---:|---|---|---|---|---:|---|---|---|---|---|"]
    for mission in candidates:
        named = ", ".join(mission["unbound_named_candidates"]) or "—"
        owners = ", ".join(mission["unbound_scripts_with_free_matching_actor"]) or "—"
        missing = ", ".join(mission["missing_attached_scripts"]) or "—"
        script_only = ", ".join(str(index) for index in mission[
            "script_only_objective_indices"]) or "—"
        inactive = ", ".join(str(index) for index in mission["inactive_unique_declared_indices"]) or "—"
        duplicates = ", ".join(str(index) for index in mission["inactive_duplicate_declared_indices"]) or "—"
        semantic_duplicates = ", ".join(str(index) for index in mission[
            "inactive_semantic_duplicate_declared_indices"]) or "—"
        duplicate_states = ", ".join(
            f"{item['script']}:{'/'.join(str(slot) for slot in item['slots'])}"
            for item in mission["duplicate_initial_state_initializations"]) or "—"
        reasons = ", ".join(mission["candidate_reasons"])
        lines.append(f"| {mission['mission']} | {mission['declared_objectives']} | {script_only} | {inactive} | {duplicates} | {semantic_duplicates} | {mission['unbound_script_count']} | {owners} | {named} | {missing} | {duplicate_states} | {reasons} |")
    lines += ["", "## Règle de validation", "",
        "Chaque candidat doit être relié à un acteur ou déclencheur encore présent, comparé entre les couches d'archives, puis testé en jeu. Aucun script n'est activé automatiquement sur la seule base de son nom.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    report = build(args.game)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["scope"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())