#!/usr/bin/env python3
"""Verify the surviving commercial evidence for both cut flamethrowers."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from dta_archive import DtaArchive
from item_editor_table import require_row
from items_sav import parse as parse_items


GERMAN_WEAPON_START = 6140
BRITISH_REUSED_START = 6273
WEAPON_RECORD_SIZE = 133
GERMAN_WEAPON_SHA256 = (
    "B3D39235D832F9635F03397B3A4863DCF0BA185C59BD1E35D2FCD8CEDC134357"
)
BRITISH_REUSED_SHA256 = (
    "CE59F7B51606351A3BB26261D288552CDEB536DCF64CE2C87504F95A1B4E54C0"
)
FLAME_MODEL_SHA256 = (
    "A9285573B4FCE73631F51C2AF70431600EDC28F9C0C489B8A37511D8C79A5EF8"
)
EFFECT_25_SHA256 = (
    "B4DE1A96006B2C27998496CF649DE7E05AD499762270CB4D1C43856A2DAB5274"
)
AMMO_RECORDS = (
    {
        "key": "german",
        "slot":207,
        "base_start": 101628,
        "sabre_start": 103644,
        "sha256": (
            "7FE33CD9D042BBA4F2D0F831D52D548DC8846837932C585130B939CECB506106"
        ),
        "icon": "ii_ge-flmwr35-m",
        "internal_name": "AMMO Flammewer",
        "text_id": 1207,
    },
    {
        "key": "british",
        "slot":208,
        "base_start": 102136,
        "sabre_start": 104152,
        "sha256": (
            "48D16AA252C8712B9DF3D1405FA8C56D36645F72E4708BBC415E53D223FCC564"
        ),
        "icon": "ii_br-flmthr2-m",
        "internal_name": "AMMO Flamethrow",
        "text_id": 1208,
    },
)
AMMO_RECORD_SIZE = 508
EFFECT_SLICES = {
    "others.DTA": (12604, 13068),
    "SabreSquadron.dta": (13913, 14377),
}
ICON_PREFIXES = (
    "wi_ge-flmwr35",
    "wi_br-flmthr2",
    "ii_ge-flmwr35-m",
    "ii_br-flmthr2-m",
)
ICON_SUFFIXES = (".bmp", "_1.dx1", "_7.dx1", "_1l.dx1", "_6l.dx1")
MISSING_MODEL_REFERENCES = (
    "models/w_flmwrfpv.4ds",
    "models/w_flmwrfpv.5ds",
    "models/w_flmwr.4ds",
    "models/w_flamefpv.4ds",
    "models/w_flamefpv.5ds",
    "models/w_flame.4ds",
)
SEARCH_TERMS = (
    b"flamethrower",
    b"flammenwerfer",
    b"flmwr",
    b"flmthr",
    b"flamefpv",
    b"plamenomet",
)


def normalized_name(value: str) -> str:
    return value.replace("\\", "/").casefold()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def archive_data(game: Path, archive_name: str, entry_name: str) -> bytes:
    expected = normalized_name(entry_name)
    with DtaArchive(game / archive_name) as archive:
        entry = next(
            (
                candidate
                for candidate in archive.entries
                if normalized_name(candidate.name) == expected
            ),
            None,
        )
        if entry is None:
            raise FileNotFoundError(f"{archive_name}::{entry_name}")
        return archive.read(entry)


def c_string(record: bytes, offset: int, size: int) -> str:
    return (
        record[offset : offset + size]
        .split(b"\0", 1)[0]
        .decode("cp1252", errors="replace")
    )


def weapon_table_evidence(data: bytes) -> dict[str, object]:
    german_row=require_row(data,44,stride=133,name_column=2,name='Flammewerfer')
    reused_row=require_row(data,45,stride=133,name_column=2,name='Flak TMP')
    if (german_row['offset'],reused_row['offset'])!=(GERMAN_WEAPON_START,BRITISH_REUSED_START):
        raise ValueError('Changed flamethrower editor row layout')
    german = data[
        GERMAN_WEAPON_START : GERMAN_WEAPON_START + WEAPON_RECORD_SIZE
    ]
    reused = data[
        BRITISH_REUSED_START : BRITISH_REUSED_START + WEAPON_RECORD_SIZE
    ]
    german_fragments = {
        "name": b"Flammewerfer\0" in german,
        "fpv_model": b"w_flmwrFPV\0" in german,
        "icon": b"wi_ge-flmwr35\0" in german,
        "world_model": b"w_flmwr\0" in german,
        "text_id_1044": struct.pack("<I", 1044) in german,
    }
    reused_fragments = {
        "replacement_name": b"Flak TMP\0" in reused,
        "replacement_icon": b"wi_flak38\0" in reused,
        "replacement_text_id_1046": struct.pack("<I", 1046) in reused,
        "old_fpv_tail": b"_FlameFPV\0" in reused,
        "old_world_tail": b"_Flame\0" in reused,
    }
    return {
        "archive": "SabreSquadron.dta",
        "entry": "Tables/item_base_items.tbl",
        "german_record": {
            "row_index":44,"boundaries_from_column_schema":True,
            "presence_flag":german_row['fields'][1],
            "offset_start": GERMAN_WEAPON_START,
            "offset_end": GERMAN_WEAPON_START + WEAPON_RECORD_SIZE,
            "size": len(german),
            "sha256": sha256(german),
            "fragments": german_fragments,
            "complete_reference_record": all(german_fragments.values()),
        },
        "british_reused_record": {
            "row_index":45,"boundaries_from_column_schema":True,
            "presence_flag":reused_row['fields'][1],
            "live_fpv_reference":reused_row['fields'][6],
            "live_world_reference":reused_row['fields'][10],
            "offset_start": BRITISH_REUSED_START,
            "offset_end": BRITISH_REUSED_START + WEAPON_RECORD_SIZE,
            "size": len(reused),
            "sha256": sha256(reused),
            "fragments": reused_fragments,
            "replacement_proven": all(reused_fragments.values()),
        },
    }


def ammo_record_evidence(
    data: bytes,
    start: int,
    definition: dict[str, object],
) -> dict[str, object]:
    parsed=parse_items(data)
    slot=parsed['slots'][definition['slot']]
    if (slot['offset'],slot['size'],slot.get('kind'))!=(start,AMMO_RECORD_SIZE,0):
        raise ValueError('Ammo proof does not coincide with its parsed native item slot')
    record = data[start : start + AMMO_RECORD_SIZE]
    return {
        "offset_start": start,
        "offset_end": start + AMMO_RECORD_SIZE,
        "size": len(record),
        "sha256": sha256(record),
        "slot":slot['slot'],"boundaries_from_presence_parser":True,
        "icon": slot['icon'],
        "world_model": slot['world_model'],
        "internal_name": slot['internal_name'],
        "text_id": slot['text_id'],
        "weight": slot['weight_raw'],
        "category": struct.unpack_from("<I", record, 116)[0],
        "expected": (
            len(record) == AMMO_RECORD_SIZE
            and sha256(record) == definition["sha256"]
            and slot['icon'] == definition["icon"]
            and slot['world_model'] == "w_ammo"
            and slot['internal_name'] == definition["internal_name"]
            and slot['text_id']
            == definition["text_id"]
            and slot['weight_raw'] == 5.0
            and struct.unpack_from("<I", record, 116)[0] == 2
        ),
    }


def icon_evidence(game: Path) -> dict[str, object]:
    expected = {
        f"maps/{prefix}{suffix}".casefold()
        for prefix in ICON_PREFIXES
        for suffix in ICON_SUFFIXES
    }
    found: dict[str, object] = {}
    with DtaArchive(game / "maps.dta") as archive:
        for entry in archive.entries:
            name = normalized_name(entry.name)
            if name not in expected:
                continue
            data = archive.read(entry)
            found[name] = {
                "entry": entry.name,
                "size": entry.size,
                "sha256": sha256(data),
            }
    return {
        "expected_count": len(expected),
        "found_count": len(found),
        "missing": sorted(expected - set(found)),
        "resources": [found[name] for name in sorted(found)],
    }


def model_evidence(game: Path) -> dict[str, object]:
    with DtaArchive(game / "models.dta") as archive:
        names = {normalized_name(entry.name) for entry in archive.entries}
        effect_entry = next(
            entry
            for entry in archive.entries
            if normalized_name(entry.name) == "models/flame1.4ds"
        )
        data = archive.read(effect_entry)
    return {
        "effect_model": {
            "entry": effect_entry.name,
            "size": len(data),
            "sha256": sha256(data),
            "node_fire01": b"\x06fire01" in data,
            "verified_as_small_effect": (
                len(data) == 471
                and sha256(data) == FLAME_MODEL_SHA256
                and b"\x06fire01" in data
            ),
        },
        "missing_weapon_models": [
            name for name in MISSING_MODEL_REFERENCES if name not in names
        ],
        "all_expected_weapon_models_absent": all(
            name not in names for name in MISSING_MODEL_REFERENCES
        ),
    }


def effect_evidence(game: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    for archive_name, (start, end) in EFFECT_SLICES.items():
        data = archive_data(game, archive_name, "Tables/effects.def")
        record = data[start:end]
        result[archive_name] = {
            "offset_start": start,
            "offset_end": end,
            "size": len(record),
            "sha256": sha256(record),
            "label": b"25 - plamenomet\0" in record,
            "texture": b"d_fire.tga\0" in record,
            "expected": (
                len(record) == 464
                and sha256(record) == EFFECT_25_SHA256
                and b"25 - plamenomet\0" in record
                and b"d_fire.tga\0" in record
            ),
        }
    return result


def absent_runtime_links(game: Path) -> dict[str, object]:
    tables = {
        "others_item_shoot": archive_data(
            game, "others.DTA", "TABLES/item_shoot.tbl"
        ),
        "others_fpv_anims": archive_data(
            game, "others.DTA", "TABLES/FpvAnims.sav"
        ),
        "sabre_fpv_anims": archive_data(
            game, "SabreSquadron.dta", "Tables/FpvAnims.sav"
        ),
    }
    table_hits: dict[str, list[str]] = {}
    for name, data in tables.items():
        lowered = data.lower()
        table_hits[name] = [
            term.decode("ascii") for term in SEARCH_TERMS if term in lowered
        ]

    script_hits: list[str] = []
    with DtaArchive(game / "Scripts.dta") as archive:
        for entry in archive.entries:
            name = entry.name.casefold().encode("cp1252", errors="replace")
            data = archive.read(entry).lower()
            if any(term in name or term in data for term in SEARCH_TERMS):
                script_hits.append(entry.name)
    return {
        "table_hits": table_hits,
        "script_hits": script_hits,
        "no_shoot_animation_or_script_link": (
            not any(table_hits.values()) and not script_hits
        ),
    }


def localized_names(game: Path) -> dict[str, object]:
    result: dict[str, object] = {}
    wanted = {1044, 1045, 1207, 1208}
    for language in ("english", "french"):
        path = game / "Text" / language / "TEXTY.txt"
        text = path.read_text(encoding="cp1252")
        values: dict[int, str] = {}
        for line in text.splitlines():
            match = re.match(r'\s*(\d+)\s+"([^"]*)"', line)
            if match and int(match.group(1)) in wanted:
                values[int(match.group(1))] = match.group(2)
        result[language] = {
            "path": str(path),
            "values": {str(key): values.get(key) for key in sorted(wanted)},
            "all_present": set(values) == wanted,
        }
    return result


def reaction_sound_labels(game: Path) -> dict[str, object]:
    data = archive_data(game, "others.DTA", "TABLES/IngameSounds.def")
    labels = {
        "enemy_spotted_flamethrowers": b"Got Flamethrowers" in data,
        "flamethrower_pain": b"GH Aaaa (Flamethrower)" in data,
    }
    return {
        "archive": "others.DTA",
        "entry": "TABLES/IngameSounds.def",
        "labels": labels,
        "all_present": all(labels.values()),
        "interpretation": (
            "Reaction voice labels only; no dedicated firing or reload sound "
            "is demonstrated."
        ),
    }


def audit(game: Path) -> dict[str, object]:
    errors: list[str] = []
    item_base = archive_data(
        game, "SabreSquadron.dta", "Tables/item_base_items.tbl"
    )
    weapons = weapon_table_evidence(item_base)
    german = weapons["german_record"]
    reused = weapons["british_reused_record"]
    if (
        german["sha256"] != GERMAN_WEAPON_SHA256
        or not german["complete_reference_record"]
    ):
        errors.append("German flamethrower weapon reference record changed")
    if (
        reused["sha256"] != BRITISH_REUSED_SHA256
        or not reused["replacement_proven"]
    ):
        errors.append("British flamethrower/Flak TMP reused record changed")

    base_items = archive_data(game, "others.DTA", "TABLES/items.sav")
    sabre_items = archive_data(
        game, "SabreSquadron.dta", "Tables/items.sav"
    )
    ammunition: dict[str, object] = {}
    for definition in AMMO_RECORDS:
        key = str(definition["key"])
        base = ammo_record_evidence(
            base_items, int(definition["base_start"]), definition
        )
        sabre = ammo_record_evidence(
            sabre_items, int(definition["sabre_start"]), definition
        )
        ammunition[key] = {"base": base, "sabre": sabre}
        if not base["expected"] or not sabre["expected"]:
            errors.append(f"{key} ammunition record changed")
        if base["sha256"] != sabre["sha256"]:
            errors.append(f"{key} ammunition differs between Base and Sabre")

    icons = icon_evidence(game)
    if icons["missing"]:
        errors.append("Flamethrower icon resources are missing")
    models = model_evidence(game)
    if not models["effect_model"]["verified_as_small_effect"]:
        errors.append("flame1.4ds changed or no longer contains fire01 evidence")
    if not models["all_expected_weapon_models_absent"]:
        errors.append("A previously absent flamethrower weapon model now exists")
    effects = effect_evidence(game)
    if not all(item["expected"] for item in effects.values()):
        errors.append("Effect 25 differs between the commercial layers")
    runtime = absent_runtime_links(game)
    if not runtime["no_shoot_animation_or_script_link"]:
        errors.append("A flamethrower shooting, animation or script link needs review")
    names = localized_names(game)
    if not all(item["all_present"] for item in names.values()):
        errors.append("Localized flamethrower names or ammunition labels are missing")
    reactions = reaction_sound_labels(game)
    if not reactions["all_present"]:
        errors.append("Flamethrower reaction voice labels are missing")

    return {
        "ok": not errors,
        "game": str(game),
        "classification": "experimental reconstruction required",
        "weapon_table": weapons,
        "ammunition": ammunition,
        "icons": icons,
        "effect_model": models,
        "effect_25": effects,
        "runtime_links": runtime,
        "localized_names": names,
        "sound_evidence": reactions,
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
