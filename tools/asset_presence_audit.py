#!/usr/bin/env python3
"""Locate recoverable weapon and vehicle assets without exporting commercial data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from dta_archive import DtaArchive

ARCHIVES = ("models.dta", "others.DTA", "Scripts.dta", "missions.dta", "Patch.dta", "SabreSquadron.dta")
TERMS = {
    "benelli": ("benelli", "beneli", "f_bene", "bene_r"),
    "flamethrower": ("flamethrower", "flammenwerfer", "flame1", "plamenomet"),
    "fg42": ("fg 42", "fg42"),
    "mg34": ("mg 34", "mg34"),
    "vickersk": ("vickers k", "vickersk", "vickerk"),
    "mg15": ("mg 15", "mg15"),
    "mg81": ("mg 81", "mg81"),
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
DISPLAY_NAMES = {
    "benelli": "Benelli M4",
    "flamethrower": "Deux lance-flammes",
    "fg42": "FG 42",
    "mg34": "MG 34 portative",
    "vickersk": "Vickers K",
    "mg15": "MG 15",
    "mg81": "MG 81",
    "garrote": "Garota",
    "zk383": "ZK-383",
    "me323": "Me 323",
    "aichi": "Aichi Val",
    "fa223": "Fa 223",
    "la5": "La-5",
    "ju52": "Ju 52",
    "fw200": "Fw 200",
    "li2": "Li-2",
    "dfs230": "DFS 230",
}
CLASSIFICATIONS = {
    "benelli": "reconstruction additive prioritaire",
    "flamethrower": "effet seul ; armes à reconstruire",
    "fg42": "catalogue incomplet",
    "mg34": "armement de char actif ; portative incomplète",
    "vickersk": "arme montée active sur Jeep SAS",
    "mg15": "armement monté seulement",
    "mg81": "armement monté seulement",
    "garrote": "aucune ressource locale",
    "zk383": "aucune ressource locale",
    "me323": "modèle présent, non placé et non pilotable",
    "aichi": "modèle présent, non placé et non pilotable",
    "fa223": "modèle présent, non placé et non pilotable",
    "la5": "modèle présent, non placé et non pilotable",
    "ju52": "décor scénarisé actif, non pilotable",
    "fw200": "modèle présent, non placé et non pilotable",
    "li2": "modèle présent, non placé et non pilotable",
    "dfs230": "modèle présent, non placé et non pilotable",
}
EXACT_MODEL_NAMES = {
    "flamethrower": {"models/flame1.4ds"},
    "vickersk": {"models/w_vickerkfpv.4ds"},
    "me323": {"models/la_m323.4ds", "models/sla_m323.4ds"},
    "aichi": {"models/la_aici.4ds", "models/sla_aici.4ds"},
    "fa223": {"models/la_fa 223.4ds", "models/sla_fa 223.4ds"},
    "la5": {"models/la_la-5.4ds", "models/sla_la-5.4ds"},
    "ju52": {"models/la_ju52.4ds", "models/sla_ju52.4ds"},
    "fw200": {"models/la_fw 200.4ds", "models/sla_fw 200.4ds"},
    "li2": {"models/la_li2.4ds", "models/sla_li2.4ds"},
    "dfs230": {"models/la_dsf 230.4ds", "models/sla_dsf 230.4ds"},
}
EXPECTED_EXACT_MODEL_COUNTS = {
    "benelli": 18,
    "flamethrower": 1,
    "fg42": 0,
    "mg34": 0,
    "vickersk": 1,
    "mg15": 0,
    "mg81": 0,
    "garrote": 0,
    "zk383": 0,
    "me323": 2,
    "aichi": 2,
    "fa223": 2,
    "la5": 2,
    "ju52": 2,
    "fw200": 2,
    "li2": 2,
    "dfs230": 2,
}
TEXT_SUFFIXES = (".scr", ".txt", ".def", ".tab", ".cfg", ".sav", ".dta", ".bin")


def normalized_name(value: str) -> str:
    return value.replace("\\", "/").lower()


def is_exact_model(category: str, entry: str) -> bool:
    name = normalized_name(entry)
    if category == "benelli":
        return name.startswith("models/#fpvbeneli") and name.endswith((".4ds", ".5ds"))
    return name in EXACT_MODEL_NAMES.get(category, set())


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
            "exact_model_entries": sum(1 for item in items if is_exact_model(category, item["entry"])),
            "script_entries": sum(1 for item in items if item["entry"].lower().endswith(".scr")),
            "table_entries": sum(1 for item in items if item["entry"].lower().endswith((".sav", ".def", ".tab"))),
            "classification": CLASSIFICATIONS[category]}
    evidence_errors = []
    for category, expected in EXPECTED_EXACT_MODEL_COUNTS.items():
        actual = summary[category]["exact_model_entries"]
        if actual != expected:
            evidence_errors.append(
                f"{category}: {actual} exact model resources, expected {expected}"
            )
    for category in ("garrote", "zk383"):
        if summary[category]["matches"] != 0:
            evidence_errors.append(
                f"{category}: unexpected local lexical evidence found"
            )
    if summary["benelli"]["table_entries"] < 2:
        evidence_errors.append("benelli: FPV/table evidence is incomplete")
    if summary["ju52"]["script_entries"] < 1:
        evidence_errors.append("ju52: commercial scripted-scene evidence is missing")
    return {
        "game": str(game),
        "evidence_ok": not evidence_errors,
        "evidence_errors": evidence_errors,
        "summary": summary,
        "matches": matches,
    }


def markdown(report):
    lines = ["# Inventaire des armes et véhicules retirés", "",
        "Premier balayage lexical des archives. Les nombres comptent des noms ou sous-chaînes et ne prouvent ni une liaison exacte à une mission ni une jouabilité complète.", "",
        "| Élément | Correspondances lexicales | Ressources modèle/animation exactes | Scripts | Tables | Classement |",
        "|---|---:|---:|---:|---:|---|"]
    for name, item in report["summary"].items():
        lines.append(
            f"| {DISPLAY_NAMES[name]} | {item['matches']} | "
            f"{item['exact_model_entries']} | {item['script_entries']} | "
            f"{item['table_entries']} | {item['classification']} |"
        )
    lines += ["", "Lecture manuelle recoupée :", "",
        "- le Ju 52 est le seul aéronef retiré dont un usage exact dans une mission soit prouvé : il reste un décor scénarisé dans Africa 1 ;",
        "- les modèles La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DFS/DSF 230 sont réellement présents et articulés, mais aucune chaîne commerciale de placement ou de pilotage ne subsiste ;",
        "- les scripts nommés Li-2 pilotent des sons d’ambiance, pas le modèle d’avion ;",
        "- les correspondances lexicales La-5 dans `posila5`, par exemple, sont des faux positifs distincts : elles ne remettent pas en cause la présence du vrai modèle `la_La-5.4ds` ;",
        "- Garota et ZK-383 n’ont aucune ressource locale identifiable par ces noms.", "",
        "## Armes déjà actives ou faussement présentées comme retirées", "",
        "Le Garand et le fusil juxtaposé Stevens disposent de leurs modèles monde et FPV, animations, entrées Weapon et munitions : ils sont déjà jouables. Le P08 silencieux, le G43, le MAS 36 et le Panzerschreck de Sabre Squadron sont eux aussi complets et actifs. Le Flak 38 et le canon de 17 mm sont déjà employés comme armes fixes.", "",
        "Le Vickers K n’est pas une arme portative oubliée. `w_vickerKFPV.4ds` est l’arme montée de la Jeep SAS : le modèle de Jeep conserve ses sièges, caméras et l’ancrage `BARREL01_00`, et une mission CMP relie encore exactement cet ancrage au modèle FPV. MG 15 et MG 81 n’ont pas de modèles portatifs démontrés ; leurs entrées correspondent à des armements montés.", "",
        "## Benelli M4", "",
        "La Benelli est le candidat expérimental le mieux conservé. Neuf couples d’animation `#FPVBeneli*.4ds/.5DS`, les textures et icônes, les sons de tir et de rechargement, le bloc `FpvAnims.sav` et la munition 179 subsistent. En revanche, l’ancien rang Weapon est occupé par la boussole et aucun modèle extérieur/posé ni paramètres originaux complets n’ont été retrouvés.", "",
        "Une restauration doit donc ajouter une nouvelle entrée sans écraser la boussole, recréer un modèle monde et signaler comme reconstruits la capacité, la cadence, les dégâts et la dispersion. Elle reste hors du lot stable jusqu’à validation en jeu.", "",
        "## Armes incomplètes", "",
        "Les deux lance-flammes conservent icônes, munitions, sons et effet. `flame1.4ds` ne pèse que 471 octets et contient seulement `fire01` : c’est un effet, pas une arme. Modèle, animations et comportement doivent être créés.", "",
        "La MG 34 portative conserve une munition, des icônes et des sons, mais ni modèle portatif, ni animations FPV, ni entrée Weapon autonome. Il ne faut pas la confondre avec la MG 34 de char active. Le FG 42 ne subsiste que comme texte désactivé et munition. Garota et ZK-383 nécessitent des sources nouvelles ou une création moderne explicitement annoncée.", "",
        "## Aéronefs", "",
        "Les modèles exacts La-5, `la_aici`, `LA_M323`, Li-2, `la_Fa 223`, Fw 200 et DFS 230 sont présents avec leurs LOD et plusieurs pièces articulées. Cela permet un banc décoratif et des essais de collision, pas de revendiquer un véhicule jouable : commandes, physique de vol, HUD, dégâts, IA et synchronisation réseau manquent.", "",
        "Le prochain ordre de travail reste : Benelli additive, test du Vickers K monté, banc décoratif Ju 52/La-5/Aichi, puis seulement lance-flammes, FG 42, MG 34 portative, Garota, ZK-383 et pilotage complet.", ""]
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
    if not report["evidence_ok"]:
        for error in report["evidence_errors"]:
            print("ERROR: " + error)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
