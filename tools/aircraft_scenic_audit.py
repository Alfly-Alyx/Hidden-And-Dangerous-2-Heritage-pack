#!/usr/bin/env python3
"""Verify surviving aircraft models, named mission links and scenic Ju 52 use."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from dta_archive import DtaArchive


MODEL_FILES = (
    ("models.dta", "MODELS/la_Ju52.4ds", 142338,
     "8232BB493A0FF0BBDCAE07B1C98A07239627E6AE2E4E90A048F7895F0C1FAD02"),
    ("models.dta", "MODELS/sla_Ju52.4ds", 24456,
     "C08C034D44A4FB2AC1EA58DC8D74E5D95D2271D8760F0E4A12073EA0917F89D4"),
    ("models.dta", "MODELS/la_Ju52Af.4ds", 145323,
     "CC35DD87C03DC928BA1E419FDB0AEAA422AA1906BD26804A12F7826CC3A915FE"),
    ("models.dta", "MODELS/#la_Ju52Af.4ds", 145975,
     "EB0F419BEBD6388D0FC3C0480A368C67C417CC23470329262CCA1727F0BBA218"),
    ("models.dta", "MODELS/#la_Ju52Af.5DS", 21955,
     "9624B5FB5CC28DED234E186ECCF0FE755001B607298363551E49FC9657A93D78"),
    ("models.dta", "MODELS/la_La-5.4ds", 162990,
     "9A1C15AC946084B813214489E828E8266D0C0A283F915FA127FAB55D1AC023A8"),
    ("models.dta", "MODELS/sla_La-5.4ds", 20716,
     "BA12F3D1AD239A01BDC5CC395C289413B32D72F5FE2B0954B22AE1DD2D1FC953"),
    ("models.dta", "MODELS/la_aici.4ds", 150223,
     "0F1075747E382E56EF7C493E75E408255D9614523BF9FB62D7065929E1AB1EA5"),
    ("models.dta", "MODELS/sla_aici.4ds", 22419,
     "53E6196EFC445A3473BACC893248F08B5820ED25CEC54EB6D664713071B93B51"),
    ("models.dta", "MODELS/la_DSF 230.4ds", 143402,
     "2684D387CACDE2C09C131D7B37671E7A68F0DC42BFEF4ED9B85B5DB9DCC246DC"),
    ("models.dta", "MODELS/sla_DSF 230.4ds", 16704,
     "2D2D1AA308406D57F4CB096F21939EF88E36D21A003FCE6118F50AF5AE0D1492"),
    ("models.dta", "MODELS/la_Fa 223.4ds", 175680,
     "F1CD7AD72A822ED3EAE76BB46856065EE9E1F1ED08611771A337F72DD8487B07"),
    ("models.dta", "MODELS/sla_Fa 223.4ds", 26283,
     "E0D96BE29351D4D232F85DFE37651F663CF7EAA52A66D1BA3DAE1631BC1E795E"),
    ("models.dta", "MODELS/la_Fw 200.4ds", 60102,
     "F56A70ED4A68D3E86EF1272304BAE3CBD8CDF5ADEFF31DE0B7FC7B22A7EF6251"),
    ("models.dta", "MODELS/sla_Fw 200.4ds", 58306,
     "0E07FC696CA1C5E9A00D660A50D86B0354CC269E0EB2D3DCDCD45E6242352ED8"),
    ("models.dta", "MODELS/la_Li2.4ds", 323240,
     "557B3C90840F1CBFAF438F72803ACB1BF75F5D3AA9D2F336F3DDEDFEF129EBD3"),
    ("models.dta", "MODELS/sla_Li2.4ds", 23680,
     "112EB9EFD450002CC2CAA1C5DA0C47EE3872587C6BB714571FACECF2AD4FCDC4"),
    ("models.dta", "MODELS/LA_M323.4ds", 257929,
     "3DF44CE22BC2C31BEAD7EDA71A8B370CB5888060B809157BD6235C03204BDB7D"),
    ("models.dta", "MODELS/sla_m323.4ds", 30794,
     "E4329640FBF786F66CA54A5C51EBAA8AE75947957FFBC8C918B874217ED3E209"),
    ("models.dta", "MODELS/la_Ju52trup.4ds", 89238,
     "A7894EC3DFFEC9A182E4D369EBB003180F803F22B4D1D08C28FCD51020479643"),
    ("Patch.dta", "MODELS/la_Ju52trup.4ds", 89462,
     "5FF20D2C26C952E5E970D1207F5C1EE527EE5D9E1BE15B717E0BE215E1422E3D"),
    ("models.dta", "MODELS/#AF1_junkrcut.4ds", 71606,
     "48A5A28FD47A1994B11A082E37931DBF58DEFD96EA07395F751F540198F52070"),
    ("models.dta", "MODELS/#AF1_junkrcut.5DS", 76240,
     "90BDF45C3C8A3ED8D0492DB42C0E99DA57022A418D8213BDBD1065B54676806D"),
)
CHAIN_FILES = (
    ("missions.dta", "MISSIONS/AFRICA1/scene2.bin", 5389638,
     "E0B92D3F2AD10504717E49BB3AB2ADCEC32372A0AC9FBD9E132B04C904B4F007",
     ("CUTjunkers", "CUTjunkersB", "la_Ju52Af")),
    ("missions.dta", "MISSIONS/AFRICA1/scripts.dta", 4622,
     "D37BD79E7D779407884D9CC3329432C0E01F80ABB6CF3C1BAA6FB8F8293A1D39",
     ("CUTjunkers", "CUT_af1Ju52.scr", "CUTit7", "CUT_af1velit.scr")),
    ("Patch.dta", "SCRIPTS/AFRICA1/CUT_af1Ju52.scr", 1135,
     "A9488471746A056EEAEC6E0AFBC07F48184AFCBCFB8384ADAB8DE1212157EB35",
     ("Delay(64100)", "#AF1_junkrcut.i3d", "FRM_CreateIndexedParticle(108")),
    ("Patch.dta", "SCRIPTS/AFRICA1/CUT_af1velit.scr", 1300,
     "106021CBC745FDD7505D8203C8644598F599624BB203AE2CF8284F5B0ED7413C",
     ("CUTjunkersB", "FRM_SetOn(JU52_parkuje,true)")),
    ("missions.dta", "MISSIONS/AFRICA2/scene2.bin", 4905695,
     "803FC3B327FF08B5B37CF6E206F9634A9C3E866E5327C0767715A97FEFECA58C",
     ("HoriciJunkers", "la_Ju52")),
    ("missions.dta", "MISSIONS/AFRICA2/tracks.dat", 2305,
     "CD6F5AA959C903C2499EBA33F222628B7EAD3E85297924FB4A0675EE073E9E8C",
     ("fight_stage01",)),
    ("missions.dta", "MISSIONS/AFRICA2/scripts.dta", 2993,
     "25B04862DCD9D7C1D0485B913E67579B3F91DC1F7C47BF731FA394DFC279AF9D",
     ("dummy_turnat", "AF2_actprelet.scr", "AF2_particle_junkers.scr",
      "AF2_vrtule.scr", "AF2_hidejunkers.scr")),
    ("Patch.dta", "SCRIPTS/AFRICA2/AF2_actprelet.scr", 3480,
     "6DB45B95DF33D8FE1557A69A01949D1C4A709A41EB6841A0A82393C64BA0033B",
     ("FRM_CreateIndexedParticle(16", "fight_stage01", "MakeExplosion")),
    ("Patch.dta", "SCRIPTS/AFRICA2/AF2_vrtule.scr", 133,
     "305B12B18601BC030D40E50D1471A339311EAEA7D81D7DDF1AD944C29042256F",
     ("FRM_RotateZ",)),
    ("Patch.dta", "SCRIPTS/AFRICA2/AF2_hidejunkers.scr", 824,
     "F5EE092DA1ED16E377250FF87C1164F249B50C186875CECE4C4ECEA2D2F62EB5",
     ("HoriciJunkers", "FRM_FinishIndexedParticle", "FRM_SetOn(junk, false)")),
)
COMMERCIAL_ARCHIVES = {
    "missions.dta": 33,
    "Patch.dta": 2,
    "SabreSquadron.dta": 14,
}
AIRCRAFT_TABLE_TERMS = (
    b"la_ju52",
    b"la_ju52af",
    b"la_la-5",
    b"la_aici",
    b"la_dsf 230",
    b"la_fa 223",
    b"la_fw 200",
    b"la_li2",
    b"la_m323",
)
ORPHAN_AIRCRAFT_TERMS = {
    "la5": "la_La-5",
    "aichi": "la_aici",
    "dsf230": "la_DSF 230",
    "fa223": "la_Fa 223",
    "fw200": "la_Fw 200",
    "li2": "la_Li2",
    "m323": "LA_M323",
}
REFERENCE_SUFFIXES = ("scene2.bin", "scripts.dta", "mpscripts.dta", ".scr")
MISSING_AFRICA2_SCRIPT = "scripts/africa2/af2_particle_junkers.scr"


def normalized_name(value: str) -> str:
    return value.replace("\\", "/").casefold()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def archive_index(game: Path, archive_name: str) -> dict[str, object]:
    wanted = {
        normalized_name(str(definition[1]))
        for definition in (*MODEL_FILES, *CHAIN_FILES)
        if definition[0] == archive_name
    }
    wanted.add(MISSING_AFRICA2_SCRIPT)
    with DtaArchive(game / archive_name) as archive:
        return {
            normalized_name(entry.name): (entry, archive.read(entry))
            for entry in archive.entries
            if (
                normalized_name(entry.name) in wanted
                or normalized_name(entry.name).endswith("/car_table.dat")
            )
        }


def cached_archive(
    game: Path,
    cache: dict[str, dict[str, object]],
    archive_name: str,
) -> dict[str, object]:
    if archive_name not in cache:
        cache[archive_name] = archive_index(game, archive_name)
    return cache[archive_name]


def exact_file_evidence(
    game: Path,
    definitions: tuple[tuple[object, ...], ...],
    cache: dict[str, dict[str, object]],
) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for archive_name, entry_name, expected_size, expected_hash, *rest in definitions:
        index = cached_archive(game, cache, str(archive_name))
        record = index.get(normalized_name(str(entry_name)))
        if record is None:
            result.append({
                "archive": archive_name,
                "entry": entry_name,
                "present": False,
                "expected": False,
            })
            continue
        entry, data = record
        required = tuple(rest[0]) if rest else ()
        fragments = {
            value: value.casefold().encode("cp1252") in data.lower()
            for value in required
        }
        result.append({
            "archive": archive_name,
            "entry": entry.name,
            "present": True,
            "size": len(data),
            "sha256": sha256(data),
            "fragments": fragments,
            "expected": (
                len(data) == expected_size
                and sha256(data) == expected_hash
                and all(fragments.values())
            ),
        })
    return result


def commercial_car_tables(
    game: Path,
    cache: dict[str, dict[str, object]],
) -> dict[str, object]:
    layers: dict[str, object] = {}
    all_hits: list[str] = []
    for archive_name, expected_count in COMMERCIAL_ARCHIVES.items():
        index = cached_archive(game, cache, archive_name)
        tables = [
            (name, data)
            for name, (_, data) in index.items()
            if name.endswith("/car_table.dat")
        ]
        hits = [
            f"{archive_name}::{name}"
            for name, data in tables
            if any(term in data.lower() for term in AIRCRAFT_TABLE_TERMS)
        ]
        all_hits.extend(hits)
        layers[archive_name] = {
            "count": len(tables),
            "expected_count": expected_count,
            "count_ok": len(tables) == expected_count,
            "aircraft_hits": hits,
        }
    return {
        "layers": layers,
        "total": sum(item["count"] for item in layers.values()),
        "expected_total": sum(COMMERCIAL_ARCHIVES.values()),
        "aircraft_hits": all_hits,
        "none_reference_aircraft": not all_hits,
        "interpretation": (
            "Only exact readable model identifiers are tested. The binary "
            "car_table.dat format is not decoded, so absence of a string is "
            "not proof that no numeric or indirect definition ever existed."
        ),
    }


def loose_car_tables(game: Path) -> dict[str, object]:
    paths = [
        path
        for path in game.rglob("*")
        if path.is_file() and path.name.casefold() == "car_table.dat"
    ]
    hits = [
        str(path)
        for path in paths
        if any(term in path.read_bytes().lower() for term in AIRCRAFT_TABLE_TERMS)
    ]
    return {
        "count": len(paths),
        "aircraft_hits": hits,
        "none_reference_aircraft": not hits,
        "informational": True,
        "interpretation": (
            "Only exact readable model identifiers are tested. The binary "
            "car_table.dat format is not decoded, so absence of a string is "
            "not proof that no numeric or indirect definition ever existed."
        ),
    }


def encoded_needles(value: str) -> tuple[bytes, bytes]:
    lowered = value.casefold()
    return lowered.encode("cp1252"), lowered.encode("utf-16le")


def commercial_named_references(game: Path) -> dict[str, object]:
    needles = {
        label: encoded_needles(value)
        for label, value in ORPHAN_AIRCRAFT_TERMS.items()
    }
    hits: dict[str, list[str]] = {label: [] for label in needles}
    scanned = 0
    for archive_name in COMMERCIAL_ARCHIVES:
        with DtaArchive(game / archive_name) as archive:
            for entry in archive.entries:
                name = normalized_name(entry.name)
                if not name.endswith(REFERENCE_SUFFIXES):
                    continue
                data = archive.read(entry).lower()
                scanned += 1
                for label, variants in needles.items():
                    if any(needle in data for needle in variants):
                        hits[label].append(f"{archive_name}::{entry.name}")
    return {
        "scanned_resources": scanned,
        "terms": ORPHAN_AIRCRAFT_TERMS,
        "hits": hits,
        "none_found": not any(hits.values()),
        "interpretation": (
            "No exact ASCII or UTF-16 model identifier survives in commercial "
            "scene2.bin, script registries or scripts for these seven orphan "
            "aircraft. This proves no named link, not the absence of every "
            "possible numeric or indirect link."
        ),
    }


def missing_script_evidence(
    game: Path,
    cache: dict[str, dict[str, object]],
) -> dict[str, object]:
    layers: dict[str, bool] = {}
    for archive_name in COMMERCIAL_ARCHIVES:
        index = cached_archive(game, cache, archive_name)
        layers[archive_name] = MISSING_AFRICA2_SCRIPT not in index
    return {
        "entry": MISSING_AFRICA2_SCRIPT,
        "absent_by_layer": layers,
        "absent_everywhere": all(layers.values()),
        "interpretation": (
            "The binding survives, but AF2_actprelet already creates and "
            "finishes particle 16; the missing script cannot be recreated "
            "faithfully from its name alone."
        ),
    }


def audit(game: Path) -> dict[str, object]:
    cache: dict[str, dict[str, object]] = {}
    models = exact_file_evidence(game, MODEL_FILES, cache)
    chains = exact_file_evidence(game, CHAIN_FILES, cache)
    car_tables = commercial_car_tables(game, cache)
    loose_tables = loose_car_tables(game)
    named_references = commercial_named_references(game)
    missing_script = missing_script_evidence(game, cache)
    errors: list[str] = []
    if not all(item["expected"] for item in models):
        errors.append("One or more official aircraft model resources changed")
    if not all(item["expected"] for item in chains):
        errors.append("One or more official Ju 52 scene resources changed")
    if not all(
        item["count_ok"] for item in car_tables["layers"].values()
    ):
        errors.append("Commercial car_table.dat layer counts changed")
    if not car_tables["none_reference_aircraft"]:
        errors.append(
            "A commercial car_table.dat contains an exact aircraft model "
            "identifier and needs review"
        )
    if not named_references["none_found"]:
        errors.append("An orphan aircraft has an exact commercial named link")
    if not missing_script["absent_everywhere"]:
        errors.append("AF2_particle_junkers.scr now exists and needs review")
    return {
        "ok": not errors,
        "game": str(game),
        "verdict": {
            "ju52": (
                "Two active official scenic chains, Africa 1 and Africa 2; "
                "no complete pilotable vehicle chain is demonstrated."
            ),
            "la5": "Official articulated model and LOD only; static decor first.",
            "aichi": "Official articulated model and LOD only; static decor first.",
            "other_orphans": (
                "DSF 230, Fa 223, Fw 200, Li-2 and Me 323 retain exact model "
                "and LOD resources but no exact named commercial mission link."
            ),
            "pilotable_demonstrated": False,
        },
        "models": models,
        "active_ju52_chains": {
            "count": 2,
            "resources": chains,
        },
        "commercial_car_tables": car_tables,
        "installed_loose_car_tables": loose_tables,
        "commercial_named_references": named_references,
        "africa2_missing_particle_script": missing_script,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path)
    arguments = parser.parse_args()
    report = audit(arguments.game.resolve())
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
