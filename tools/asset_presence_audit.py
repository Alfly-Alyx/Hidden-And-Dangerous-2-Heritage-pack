#!/usr/bin/env python3
"""Locate recoverable weapon and vehicle assets without exporting commercial data."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from dta_archive import DtaArchive
from item_editor_table import require_row

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
    "me323": "modèle présent ; pilotage non démontré",
    "aichi": "modèle présent ; pilotage non démontré",
    "fa223": "modèle présent ; pilotage non démontré",
    "la5": "modèle présent ; pilotage non démontré",
    "ju52": "décor scénarisé actif ; pilotage non démontré",
    "fw200": "modèle présent ; pilotage non démontré",
    "li2": "modèle présent ; pilotage non démontré",
    "dfs230": "modèle présent ; pilotage non démontré",
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
TEXT_SUFFIXES = (
    ".scr", ".txt", ".def", ".tab", ".tbl", ".cfg", ".sav", ".dta", ".bin",
)
BENELLI_SHOOT_START = 1551
BENELLI_SHOOT_END = 1686
BENELLI_SHOOT_SHA256 = (
    "CE461707BB7551ABDB45E165222582201DC90C292D2FF781F684540E38E47FEF"
)
BENELLI_COMPASS_START = 1485
BENELLI_COMPASS_END = 1618
BENELLI_COMPASS_SHA256 = (
    "EE8CB099A336049848D8E7C0CE05103E4B77D7EF7C716BE117C1ECA765ABFD5F"
)


def normalized_name(value: str) -> str:
    return value.replace("\\", "/").lower()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def benelli_shoot_evidence(data: bytes) -> dict[str, object]:
    row = require_row(data,9,stride=135,name_column=2,name='Benelli')
    if (row['offset'],row['size'])!=(BENELLI_SHOOT_START,135):
        raise ValueError('Changed Benelli editor row layout')
    record = data[BENELLI_SHOOT_START:BENELLI_SHOOT_END]
    evidence: dict[str, object] = {
        "archive": "others.DTA",
        "entry": "TABLES/item_shoot.tbl",
        "offset_start": BENELLI_SHOOT_START,
        "offset_end": BENELLI_SHOOT_END,
        "size": len(record),
        "sha256": sha256(record),
        "header_ok": False,
        "row_index": 9,
        "boundaries_from_column_schema": True,
        "record_type_header_present": False,
    }
    if len(record) == 135:
        evidence.update({
            "marker": row['fields'][1],
            "name": row['fields'][2],
            "category": row['fields'][3],
            "value_1": row['fields'][4],
            "value_2": row['fields'][6],
        })
        evidence["header_ok"] = (
            evidence["marker"] == 1
            and evidence["name"] == "Benelli"
            and evidence["category"] == 2
            and abs(float(evidence["value_1"]) - 0.3) < 0.000001
            and evidence["value_2"] == 1500.0
        )
    return evidence


def benelli_compass_evidence(data: bytes) -> dict[str, object]:
    row = require_row(data,9,stride=133,name_column=2,name='KOMPAS')
    if (row['offset'],row['size'])!=(BENELLI_COMPASS_START,133):
        raise ValueError('Changed compass editor row layout')
    record = data[BENELLI_COMPASS_START:BENELLI_COMPASS_END]
    fragments = {
        "compass_name": data[1486:1493] == b"KOMPAS\x00",
        "m4": data[1493:1496] == b" M4",
        "fpv_model_tail": data[1511:1523] == b"_benelliFPV\x00",
        "compass_icon": data[1526:1536] == b"ii_compas\x00",
        "world_model_tail": data[1536:1540] == b"lli\x00",
    }
    return {
        "archive": "SabreSquadron.dta",
        "entry": "Tables/item_base_items.tbl",
        "offset_start": BENELLI_COMPASS_START,
        "offset_end": BENELLI_COMPASS_END,
        "size": len(record),
        "sha256": sha256(record),
        "row_index":9,
        "boundaries_from_column_schema":True,
        "fragments": fragments,
        "fragments_ok": all(fragments.values()),
    }


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
    benelli_evidence: dict[str, object] = {}
    for archive_name in ARCHIVES:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                name_data = entry.name.lower().encode("cp1252", errors="replace")
                found = hits(name_data)
                kinds = ["name"] if found else []
                content = None
                if entry.size <= 4 * 1024 * 1024 and entry.name.lower().endswith(TEXT_SUFFIXES):
                    content = archive.read(entry)
                    content_hits = hits(content)
                    if content_hits:
                        found = sorted(set(found) | set(content_hits))
                        kinds.append("content")
                entry_name = normalized_name(entry.name)
                if (
                    archive_name.casefold() == "others.dta"
                    and entry_name == "tables/item_shoot.tbl"
                ):
                    if content is None:
                        content = archive.read(entry)
                    benelli_evidence["item_shoot"] = benelli_shoot_evidence(content)
                if (
                    archive_name.casefold() == "sabresquadron.dta"
                    and entry_name == "tables/item_base_items.tbl"
                ):
                    if content is None:
                        content = archive.read(entry)
                    benelli_evidence["compass_record"] = (
                        benelli_compass_evidence(content)
                    )
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
            "table_entries": sum(
                1 for item in items
                if item["entry"].lower().endswith(
                    (".sav", ".def", ".tab", ".tbl")
                )
            ),
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
    shoot = benelli_evidence.get("item_shoot")
    if (
        not isinstance(shoot, dict)
        or shoot.get("sha256") != BENELLI_SHOOT_SHA256
        or shoot.get("header_ok") is not True
    ):
        evidence_errors.append(
            "benelli: exact official item_shoot record is missing or changed"
        )
    compass = benelli_evidence.get("compass_record")
    if (
        not isinstance(compass, dict)
        or compass.get("sha256") != BENELLI_COMPASS_SHA256
        or compass.get("fragments_ok") is not True
    ):
        evidence_errors.append(
            "benelli: Compass/Benelli mixed record is missing or changed"
        )
    if summary["ju52"]["script_entries"] < 1:
        evidence_errors.append("ju52: commercial scripted-scene evidence is missing")
    return {
        "game": str(game),
        "evidence_ok": not evidence_errors,
        "evidence_errors": evidence_errors,
        "summary": summary,
        "benelli_evidence": benelli_evidence,
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
        if name == "mg81":
            lines += [
                "| Modèle `w_m1gran` | 1 | 1 | 0 | 0 | modèle orphelin, fonction exacte non démontrée |",
                "| Anciennes mines | 5 | 5 | 0 | 0 | variantes techniques sans chaîne d'objet complète |",
            ]
    lines += ["", "Lecture manuelle recoupée :", "",
        "- le Ju 52 est le seul aéronef retiré dont des usages exacts dans des missions soient prouvés : il reste un décor scénarisé actif dans Africa 1 et Africa 2 ;",
        "- les modèles La-5, Aichi, M323, Li-2, Fa 223, Fw 200 et DSF 230 sont réellement présents et articulés, mais aucune liaison par identifiant exact ne subsiste dans les 3 059 scènes, registres et scripts commerciaux examinés ;",
        "- les scripts nommés Li-2 pilotent des sons d’ambiance, pas le modèle d’avion ;",
        "- les correspondances lexicales La-5 dans `posila5`, par exemple, sont des faux positifs distincts : elles ne remettent pas en cause la présence du vrai modèle `la_La-5.4ds` ;",
        "- Garota et ZK-383 n’ont aucune ressource locale identifiable par ces noms.",
        "- aucun des 49 `car_table.dat` commerciaux ni des 105 tables libres actuellement installées ne contient sous forme lisible les identifiants exacts de ces aéronefs ; leur format binaire n’étant pas décodé, ce résultat n’exclut pas une ancienne liaison numérique ou indirecte.", "",
        "## Armes déjà actives ou faussement présentées comme retirées", "",
        "Le Garand et le fusil juxtaposé Stevens disposent de leurs modèles monde et FPV, animations, entrées Weapon et munitions : ils sont déjà jouables. Le P08 silencieux, le G43, le MAS 36 et le Panzerschreck de Sabre Squadron sont eux aussi complets et actifs. Le Flak 38 et le canon de 17 mm sont déjà employés comme armes fixes.", "",
        "Le Vickers K n’est pas une arme portative oubliée. `w_vickerKFPV.4ds` est l’arme montée de la Jeep SAS : le modèle de Jeep conserve ses sièges, caméras et l’ancrage `BARREL01_00`, et une mission CMP relie encore exactement cet ancrage au modèle FPV. MG 15 et MG 81 n’ont pas de modèles portatifs démontrés ; leurs entrées correspondent à des armements montés.", "",
        "## Benelli M4", "",
        "La Benelli est le candidat expérimental le mieux conservé. Neuf couples d’animation `#FPVBeneli*.4ds/.5DS`, les textures et icônes, les sons de tir et de rechargement, le bloc `FpvAnims.sav` et la munition 179 subsistent. La table `others.DTA::TABLES/item_shoot.tbl` conserve la ligne `Benelli` de 135 octets, aux offsets 1551–1686, dont le SHA-256 est `CE461707BB7551ABDB45E165222582201DC90C292D2FF781F684540E38E47FEF`. Les bornes proviennent du schéma TBL ; la sémantique de tir reste à qualifier.", "",
        "La ligne de 133 octets occupée par la boussole dans `SabreSquadron.dta::Tables/item_base_items.tbl` conserve simultanément `M4`, `_benelliFPV` et `lli` après des terminateurs de chaînes. Son empreinte exacte est `EE8CB099A336049848D8E7C0CE05103E4B77D7EF7C716BE117C1ECA765ABFD5F`. Ces fragments sont des vestiges, pas des références vivantes ; les valeurs numériques actuelles appartiennent à la boussole et ne sont pas des réglages d’arme récupérables.", "",
        "Une reconstruction doit créer une nouvelle entrée sans écraser la boussole. Le candidat 359 reste provisoire : l'absence de collision dans des missions ne qualifie pas les sauvegardes. Un modèle monde original moderne et un FPV statique dérivé sont maintenant construits séparément. Les contrôles natifs isolés établissent la liaison objet/groupe FPV et le consommateur de munition ; ils ne valident pas l'animation, le tir ou une sauvegarde complète. Consulter `experimental/BENELLI_M4_ADDITIVE/` pour ces preuves distinctes.", "",
        "`tools/item_id_collision_audit.py` contrôle les catalogues et déclarations de mission ; `tools/benelli_table_audit.py` vérifie les tables commerciales et leurs surcharges. Leurs rapports datés font foi pour les effectifs, pas ce scan de ressources. Une occurrence ambiguë dans une zone non décodée doit faire refuser l'allocation.", "",
        "## Armes incomplètes", "",
        "Le Flammenwerfer conserve un record d'arme complet comme référence, mais ses modèles `w_flmwrFPV` et `w_flmwr` sont absents. Le record britannique a été remplacé par `Flak TMP` et ne conserve que les fragments `_FlameFPV` et `_Flame`. Les deux munitions, vingt ressources d'icônes et l'effet 25 subsistent. `flame1.4ds` ne pèse que 471 octets et contient seulement `fire01`, huit sommets et quatre faces : c'est un effet, pas une arme. Les libellés sonores retrouvés sont deux réactions vocales, pas les sons de tir ou de recharge. Aucune table de tir, animation FPV ou logique de script n'est reliée ; modèles, animations et comportement doivent donc être créés.", "",
        "`tools/flamethrower_evidence_audit.py` vérifie ces preuves et leurs empreintes exactes sans exporter les données commerciales dans le dépôt.", "",
        "Le FG 42 et la MG 34 portative conservent chacun un record de tir complet et une munition. Leurs anciens emplacements d'objet 27 et 32 ont cependant été réemployés par des casques, malgré les fragments résiduels `_42FGfpv` et `_34mgFPV`. Le FG 42 n'a plus de modèle, d'icône de munition ni de son identifiable ; la MG 34 portative conserve icônes et sons, mais ni modèle ni animations FPV. La munition 211 appartient à la MG 34 de char active et ne constitue pas une preuve portative.", "",
        "MG 15 et MG 81 conservent quatre entrées d'armement monté, des icônes et des sons. L'emplacement 55 est incohérent entre la table de tir MG 15 et l'objet MG 81, signe d'un réemploi ; aucun modèle portatif n'est démontré. `tools/orphan_weapon_evidence_audit.py` contrôle ces records et interdit de réutiliser les IDs 27/32. Garota et ZK-383 nécessitent des sources nouvelles ou une création moderne explicitement annoncée.", "",
        "`w_m1gran.4ds` conserve un modèle et une référence de texture `W_GRANATUS.BMP`, mais aucune entrée d'objet, animation FPV, occurrence de mission ou fonction explicitement nommée. Le trou 1065 du catalogue textuel n'est pas une preuve suffisante de son identité. Les cinq modèles `w_mine*`/mine technique n'ont eux non plus ni chaîne d'objet complète ni placement commercial attesté ; ils restent séparés des mines finales actives.", "",
        "## Aéronefs", "",
        "Les modèles exacts La-5, `la_aici`, `LA_M323`, Li-2, `la_Fa 223`, Fw 200 et DSF 230 sont présents avec leurs LOD et plusieurs pièces articulées. Le M323 est le vestige le plus fourni avec six moteurs, plusieurs sièges, caméras et ancrages d’arme ; Fa 223, Li-2 et DSF 230 conservent eux aussi des sièges et caméras, tandis que le Fw 200 est plus proche d’un décor animé. Cela permet un banc décoratif et des essais de collision, pas de revendiquer un véhicule jouable : commandes, physique de vol, HUD, dégâts, IA et synchronisation réseau manquent.", "",
        "`tools/aircraft_scenic_audit.py` vérifie les modèles et empreintes des huit types d’aéronefs, les 49 `car_table.dat` commerciaux, les 105 tables libres, les 3 059 ressources de mission pertinentes et les deux chaînes Ju 52 encore actives. Africa 1 utilise `CUTjunkers` et `CUTjunkersB` dans sa cinématique ; Africa 2 anime `HoriciJunkers` sur `fight_stage01`, tourne ses trois hélices, crée la fumée 16 puis masque et fait exploser l'appareil. La liaison vers `AF2_particle_junkers.scr` subsiste, mais le fichier manque dans Base, Patch et Sabre ; son rôle ne doit pas être inventé dans le paquet stable puisque `AF2_actprelet.scr` assure déjà la fumée et son nettoyage.", "",
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
