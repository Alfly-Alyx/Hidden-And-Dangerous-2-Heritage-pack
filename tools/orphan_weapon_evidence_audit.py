#!/usr/bin/env python3
"""Verify cut-weapon records without presenting them as ready to activate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from dta_archive import DtaArchive
from item_editor_table import parse as parse_editor_table
from items_sav import parse as parse_items


TABLE_HASHES = {
    ("others.DTA", "TABLES/item_shoot.tbl"):
        "9A0CAD7B898549E2A3F61A78C9F5B9B1D937ED3B91DC6F659DE1D62518B97F0A",
    ("SabreSquadron.dta", "Tables/item_base_items.tbl"):
        "96E0A379DCC249E7C9D58B08529987E1BACF8D543B99C702BF3011B5AEB3E8E3",
    ("others.DTA", "TABLES/IngameSounds.def"):
        "3FC663A1EEB87B9F6A7FB94297EB59ACEF20123DC589170DDBDEF5AA6F0A26EB",
}
RECORDS = (
    ("fg42_shoot", "others.DTA", "TABLES/item_shoot.tbl", 3981, 4116,
     "3C1C1186DBEE311E4239297A3D1B460165FC59300C706D6B1F3492E21A3BDFB5",
     (b"FG 42\x00", b"FG42_F\x00", b"FG42_R\x00")),
    ("mg34_shoot", "others.DTA", "TABLES/item_shoot.tbl", 4656, 4791,
     "D577C7866FA84D9DEB9F69765657D87F51278852E3D4FBFB9C09F0F9869ABBB2",
     (b"MG 34\x00",)),
    ("mg15_2_shoot", "others.DTA", "TABLES/item_shoot.tbl", 5331, 5466,
     "B968CBE06617F3573BA5E1F715DCB29186F1AB4B96B84E93E098FEE63D823D04",
     (b"MG 15_2\x00",)),
    ("mg15_1_shoot", "others.DTA", "TABLES/item_shoot.tbl", 6006, 6141,
     "353A0E335DF1BD9619B365EA6E41B2A42BAD0F7CBFB6D116917CCF0B8C5D7DE6",
     (b"MG 15 ",)),
    ("mg81_2_shoot", "others.DTA", "TABLES/item_shoot.tbl", 6141, 6276,
     "1C4AF111ED4FA97DB897836E2F7F0A34DAA93EC9399A92242389A8A5E7571D74",
     (b"MG 81\x00",)),
    ("slot55_shoot_named_mg15", "others.DTA", "TABLES/item_shoot.tbl", 7761, 7896,
     "FF5FC19189FCA14B99F8263F52D3682BF2A40262AECC152AF4B5FC67C35E78D7",
     (b"MG 15\x00",)),
    ("slot27_reused_helmet", "SabreSquadron.dta", "Tables/item_base_items.tbl",
     3879, 4012,
     "2C6269948623C2613F16576912A701D5A47C5573897E0EFECEB8E4EE3DD6FC06",
     (b"G HELM SS\x00", b"_42FGfpv\x00")),
    ("slot32_reused_helmet", "SabreSquadron.dta", "Tables/item_base_items.tbl",
     4544, 4677,
     "C5AF54FE53BA566FC4745D28929C93358AAEF91B52AFFA13275CA60CB4E806CD",
     (b"G HELM NO\x00", b"_34mgFPV\x00")),
    ("mg15_2_item", "SabreSquadron.dta", "Tables/item_base_items.tbl",
     5209, 5342,
     "44EADF3E09B11241C26DE6E99FAE6567BC53504430EC75EEC8086231045D8973",
     (b"MG 15_2\x00", b"wi_ge-mg15\x00")),
    ("mg15_1_item", "SabreSquadron.dta", "Tables/item_base_items.tbl",
     5874, 6007,
     "B03653BA9AC252C6F6A2A1F149FF2FA60A3E93A5BD0EBBA752454362623C677E",
     (b"MG 15_1\x00", b"wi_ge-mg15\x00")),
    ("mg81_2_item", "SabreSquadron.dta", "Tables/item_base_items.tbl",
     6007, 6140,
     "9DE0046E894162DADC7EBB240AC9E79FE7AD4FA7DC6DD8B6C2BCA4E5986E69D7",
     (b"MG 81_2\x00", b"wi_ge-mg81\x00")),
    ("slot55_item_named_mg81", "SabreSquadron.dta", "Tables/item_base_items.tbl",
     7603, 7736,
     "7A3CBA1274C6E3EC5061ABC614ED876EA36DF2A376463A6109189F66FA6FEB82",
     (b"MG 81_1\x00", b"wi_ge-mg81\x00")),
    ("fg42_ammo_base", "others.DTA", "TABLES/items.sav", 96544, 97052,
     "1D2139CFA5AAB689D90C9F976C0C9459C7882959B35F92BB913BB865FFE8A259",
     (b"ii_ge-fg42-m\x00", b"AMMO FG 42\x00")),
    ("fg42_ammo_sabre", "SabreSquadron.dta", "Tables/items.sav", 98056, 98564,
     "5B7E3B38EB13AE12DE1D49207E0C926368C8307A99A0BDB859D10001F476C263",
     (b"ii_ge-fg42-m\x00", b"AMMO FG 42\x00")),
    ("mg34_ammo_base", "others.DTA", "TABLES/items.sav", 99084, 99592,
     "367F6CE2B30C555BA9D3EBCC4FDD017AE82AF602B74A2810E1D71D7883D06EF6",
     (b"ii_ge-mg34-m\x00", b"AMMO MG 34\x00")),
    ("mg34_ammo_sabre", "SabreSquadron.dta", "Tables/items.sav", 100596, 101104,
     "F6B928615353623A430AD1EF678759238E950FAC9C79C0593A096AB3DD42849B",
     (b"ii_ge-mg34-m\x00", b"AMMO MG 34\x00")),
    ("tank_mg34_ammo_base", "others.DTA", "TABLES/items.sav", 103660, 104168,
     "15C165F0B7933BE7D07292C8E691F34D830E57F14314E326B99DA13D965ECFFF",
     (b"AMMO Tank MG 34\x00",)),
    ("tank_mg34_ammo_sabre", "SabreSquadron.dta", "Tables/items.sav",
     105676, 106184,
     "15C165F0B7933BE7D07292C8E691F34D830E57F14314E326B99DA13D965ECFFF",
     (b"AMMO Tank MG 34\x00",)),
)
MODEL_RESOURCES = (
    ("MODELS/w_vickerKFPV.4ds", 26098,
     "2522A705B05D8794F6005A1B87DD97B88480B5F8559B05AD512C901033907D19"),
    ("MODELS/la_Jeepsas.4ds", 328870,
     "8138CD577AE288D3252F3D96130FE59F03062D4041230F7DAEC649BD1D1CCE2A"),
)
MODEL_ARCHIVES = {"models.dta": 7230, "Patch.dta": 97, "SabreSquadron.dta": 1152}
ABSENT_MODEL_TOKENS = (
    "fg42", "42fg", "mg34", "34mg", "mg15", "mg81", "type92", "type89",
    "garot", "zk383", "zk-383", "zk_383",
)
ICON_RESOURCES = (
    ("MAPS/wi_ge-mg15.bmp", 3128,
     "E6702F2C0BF34B8F7429DF4C059F4CF72645B59035C4837F56E49E40E0267C42"),
    ("MAPS/wi_ge-mg34.bmp", 3128,
     "9D101281F23E575EABD0A903812DCED69BF20ED1CC46A1575BB1B38BEF7276EF"),
    ("MAPS/ii_ge-mg34-m.bmp", 3128,
     "E8006B14231F68D65D3A7367D42236D0774A5B8ED230030A59BB981C5D7D3825"),
    ("MAPS/wi_ge-mg81.bmp", 3128,
     "6CE538FAD61792DE5AF7BF0193BAA24048763173B4F858BFBC3091190BB73A2F"),
)
SOUND_MARKERS = (
    b"G MG34", b"f_mg34_a.wav", b"G MG34 Reload", b"mg34_r.wav",
    b"G MG15 A", b"f_mg15_a.wav", b"G MG15 B", b"f_mg15_b.wav",
    b"G MG81 A", b"f_mg81_a.wav", b"G MG81 B", b"f_mg81_b.wav",
)


def normalized_name(value: str) -> str:
    return value.replace("\\", "/").casefold()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def archive_data(game: Path, archive_name: str, entry_name: str) -> bytes:
    wanted = normalized_name(entry_name)
    with DtaArchive(game / archive_name) as archive:
        for entry in archive.entries:
            if normalized_name(entry.name) == wanted:
                return archive.read(entry)
    raise FileNotFoundError(f"{archive_name}::{entry_name}")


def table_boundaries(data,entry_name):
    if entry_name.casefold().endswith('.tbl'):
        entries=parse_editor_table(data)['rows']
    elif entry_name.casefold().endswith('items.sav'):
        entries=[slot for slot in parse_items(data)['slots'] if slot['present']]
    else:raise ValueError('Unreviewed evidence table format')
    return {(row['offset'],row['offset']+row['size']):row.get('index',row.get('slot')) for row in entries}


def audit(game: Path) -> dict[str, object]:
    errors: list[str] = []
    cache: dict[tuple[str, str], bytes] = {}
    for key, expected_hash in TABLE_HASHES.items():
        data = archive_data(game, *key)
        cache[key] = data
        if sha256(data) != expected_hash:
            errors.append(f"{key[0]}::{key[1]} changed")

    records: dict[str, object] = {}
    boundaries = {}
    for label, archive_name, entry_name, start, end, expected_hash, fragments in RECORDS:
        key = (archive_name, entry_name)
        data = cache.get(key)
        if data is None:
            data = archive_data(game, archive_name, entry_name)
            cache[key] = data
        if key not in boundaries:
            boundaries[key]=table_boundaries(data,entry_name)
        if (start,end) not in boundaries[key]:
            raise ValueError(f'{label} proof does not coincide with a parsed table row/slot')
        record = data[start:end]
        fragment_checks = {
            fragment.decode("cp1252", errors="replace").rstrip("\0"):
                fragment in record
            for fragment in fragments
        }
        expected = (
            len(record) == end - start
            and sha256(record) == expected_hash
            and all(fragment_checks.values())
        )
        records[label] = {
            "archive": archive_name,
            "entry": entry_name,
            "offset_start": start,
            "offset_end": end,
            "size": len(record),
            "sha256": sha256(record),
            "fragments": fragment_checks,
            "expected": expected,
            "parsed_row_or_slot": boundaries[key][start,end],
            "boundaries_from_table_parser": True,
        }
        if not expected:
            errors.append(f"{label} record changed")

    exact_models: dict[str, object] = {}
    for entry_name, size, expected_hash in MODEL_RESOURCES:
        data = archive_data(game, "models.dta", entry_name)
        expected = len(data) == size and sha256(data) == expected_hash
        exact_models[entry_name] = {
            "size": len(data), "sha256": sha256(data), "expected": expected
        }
        if not expected:
            errors.append(f"{entry_name} changed")

    model_layers: dict[str, object] = {}
    named_weapon_models: list[str] = []
    for archive_name, expected_count in MODEL_ARCHIVES.items():
        with DtaArchive(game / archive_name) as archive:
            names = [
                entry.name for entry in archive.entries
                if entry.name.casefold().endswith((".4ds", ".5ds"))
            ]
        suspicious = [
            name for name in names
            if any(token in normalized_name(name) for token in ABSENT_MODEL_TOKENS)
        ]
        named_weapon_models.extend(
            f"{archive_name}::{name}" for name in suspicious
        )
        model_layers[archive_name] = {
            "count": len(names),
            "expected_count": expected_count,
            "count_ok": len(names) == expected_count,
            "targeted_name_hits": suspicious,
        }
        if len(names) != expected_count:
            errors.append(f"{archive_name} model count changed")
    if named_weapon_models:
        errors.append("A formerly absent targeted weapon model name now exists")

    icons: dict[str, object] = {}
    with DtaArchive(game / "Maps.dta") as archive:
        index = {normalized_name(entry.name): entry for entry in archive.entries}
        fg42_icon_hits = [
            entry.name for entry in archive.entries
            if "ii_ge-fg42-m" in normalized_name(entry.name)
        ]
        for entry_name, size, expected_hash in ICON_RESOURCES:
            entry = index.get(normalized_name(entry_name))
            if entry is None:
                icons[entry_name] = {"present": False, "expected": False}
                errors.append(f"{entry_name} is missing")
                continue
            data = archive.read(entry)
            expected = len(data) == size and sha256(data) == expected_hash
            icons[entry_name] = {
                "present": True, "size": len(data),
                "sha256": sha256(data), "expected": expected,
            }
            if not expected:
                errors.append(f"{entry_name} changed")
    if fg42_icon_hits:
        errors.append("The formerly missing FG 42 ammunition icon now exists")

    sounds = cache[("others.DTA", "TABLES/IngameSounds.def")]
    sound_checks = {
        marker.decode("ascii"): marker in sounds for marker in SOUND_MARKERS
    }
    if not all(sound_checks.values()):
        errors.append("One or more MG 34/MG 15/MG 81 sound labels changed")

    return {
        "ok": not errors,
        "game": str(game),
        "verdict": {
            "vickers_k": "already mounted on the Jeep SAS; runtime test only",
            "fg42": "complete shoot record, but reused Item 27 and missing assets",
            "portable_mg34": "complete shoot record, but reused Item 32 and missing assets",
            "mg15_mg81": "unplaced mount records with a conflicting reused slot 55",
            "garota_zk383": "no local named resources; modern creation required",
            "stable_activation_available": False,
        },
        "records": records,
        "exact_existing_models": exact_models,
        "model_inventory": {
            "layers": model_layers,
            "total": sum(item["count"] for item in model_layers.values()),
            "targeted_name_hits": named_weapon_models,
        },
        "icons": {
            "present_resources": icons,
            "fg42_ammunition_icon_hits": fg42_icon_hits,
        },
        "sound_definition": {
            "sha256": sha256(sounds),
            "markers": sound_checks,
        },
        "guardrails": {
            "never_reuse_item_27": True,
            "never_reuse_item_32": True,
            "never_treat_tank_ammo_211_as_portable_weapon_proof": True,
            "never_expose_mg15_mg81_as_inventory_items_without_new_assets": True,
        },
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
