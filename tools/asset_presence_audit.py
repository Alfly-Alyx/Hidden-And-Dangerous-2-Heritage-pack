#!/usr/bin/env python3
"""Locate recoverable weapon and vehicle assets without exporting commercial data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dta_archive import DtaArchive

ARCHIVES = ("models.dta", "others.DTA", "Scripts.dta", "missions.dta", "Patch.dta", "SabreSquadron.dta")
TERMS = {
    "flamethrower": ("flamethrower", "flammenwerfer", "flame1", "plamenomet"),
    "garrote": ("garot", "garrota"),
    "zk383": ("zk-383", "zk383", "zk_383"),
    "me323": ("me 323", "me323", "m323"),
    "aichi": ("aichi", "aici"),
    "fa223": ("fa 223", "fa223"),
    "la5": ("la-5", "la5"),
    "ju52": ("ju 52", "ju52", "junkers 52"),
    "fw200": ("fw 200", "fw200"),
    "li2": ("li-2", "li2"),
    "dfs230": ("dfs 230", "dfs230", "dsf 230", "dsf230"),
}
TEXT_SUFFIXES = (".scr", ".txt", ".def", ".tab", ".cfg", ".sav", ".dta", ".bin")


def hits(data: bytes):
    lower = data.lower()
    result = []
    for category, variants in TERMS.items():
        if any(value.encode("cp1252") in lower for value in variants):
            result.append(category)
    return result


def audit(game: Path):
    matches = []
    for archive_name in ARCHIVES:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                name_data = entry.name.lower().encode("cp1252", errors="replace")
                found = hits(name_data)
                kinds = ["name"] if found else []
                if entry.size <= 4 * 1024 * 1024 and entry.name.lower().endswith(TEXT_SUFFIXES):
                    content_hits = hits(archive.read(entry))
                    if content_hits:
                        found = sorted(set(found) | set(content_hits))
                        kinds.append("content")
                if found:
                    matches.append({"archive": archive_name, "entry": entry.name,
                                    "size": entry.size, "terms": found, "match_kinds": kinds})
    for relative in (Path("Tables/items.sav"), Path("Tables/FpvAnims.sav")):
        path = game / relative
        if path.exists():
            found = hits(path.read_bytes())
            if found:
                matches.append({"archive": "loose", "entry": relative.as_posix(),
                                "size": path.stat().st_size, "terms": found,
                                "match_kinds": ["content"]})
    summary = {}
    for category in TERMS:
        items = [item for item in matches if category in item["terms"]]
        summary[category] = {"matches": len(items),
            "model_entries": sum(1 for item in items if item["entry"].lower().endswith(".4ds")),
            "script_entries": sum(1 for item in items if item["entry"].lower().endswith(".scr")),
            "table_entries": sum(1 for item in items if item["entry"].lower().endswith((".sav", ".def", ".tab")))}
    return {"game": str(game), "summary": summary, "matches": matches}


def markdown(report):
    lines = ["# Inventaire des armes et véhicules retirés", "",
        "Premier balayage lexical des archives. Les nombres comptent des noms ou sous-chaînes et ne prouvent ni une liaison exacte à une mission ni une jouabilité complète.", "",
        "| Élément | Correspondances lexicales | Modèles 4DS | Fichiers sous Scripts | Tables |",
        "|---|---:|---:|---:|---:|"]
    for name, item in report["summary"].items():
        lines.append(f"| {name} | {item['matches']} | {item['model_entries']} | {item['script_entries']} | {item['table_entries']} |")
    lines += ["", "Lecture manuelle recoupée :", "",
        "- usage exact dans une mission prouvé : Ju 52 uniquement, comme décor scénarisé dans Africa 1 ;",
        "- modèles présents sans chaîne de mission exacte démontrée : La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DFS/DSF 230 ;",
        "- les scripts nommés Li-2 pilotent des sons d’ambiance, pas le modèle d’avion ;",
        "- les deux lance-flammes conservent icônes, munitions, sons et effet, mais pas une chaîne d’arme fonctionnelle ;",
        "- Garota et ZK-383 n’ont aucune ressource locale identifiable par ces noms.", "",
        "Les faux positifs La-5, Aichi, M323 et Li-2 proviennent de sous-chaînes ou de coïncidences binaires ; consulter l’étude expérimentale détaillée avant toute restauration.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.game)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
