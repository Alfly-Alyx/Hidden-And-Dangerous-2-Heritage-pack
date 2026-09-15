#!/usr/bin/env python3
"""Audit the H&D2 single-player menu and mission catalogue layers.

The report is deliberately read-only. It inventories the menu scene controls,
decodes the campaign/mission hierarchy stored in Gamedata*.gdt and records the
corresponding strings embedded in the Sabre Squadron executable. It does not
publish commercial assets or their raw payloads.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

from dta_archive import DtaArchive
from objective_audit import Block, blocks, direct, walk


CATALOGUE_ARCHIVES = ("others.DTA", "Patch.dta", "SabreSquadron.dta")
MENU_ARCHIVES = ("Patch.dta", "SabreSquadron.dta")
MENU_MODELS = (
    "models/main_menu.4ds",
    "models/singleplayer.4ds",
    "models/single mission 2.4ds",
    "models/selection screen.4ds",
)
CATALOGUE_RE = re.compile(r"^gamedata/gamedata\d+\.gdt$", re.I)
PRINTABLE_RE = re.compile(rb"[A-Za-z][A-Za-z0-9_ &.\-]{3,63}")
CONTROL_RE = re.compile(
    r"^(?:b[a-z]|text_|normal|actived|inactive|table|scroll|slider|screen_|panel$|video$)",
    re.I,
)
EXECUTABLE_TERMS = (
    "main_menu.4ds",
    "singleplayer.4ds",
    "single mission 2.4ds",
    "selection screen.4ds",
    "Gamedata00.gdt",
    "Gamedata01.gdt",
)


def normalized(value: str) -> str:
    return value.replace("\\", "/").lower()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def effective_entries(
    game: Path, archive_names: tuple[str, ...], predicate
) -> tuple[dict[str, dict[str, object]], dict[str, list[dict[str, object]]]]:
    effective: dict[str, dict[str, object]] = {}
    layers: dict[str, list[dict[str, object]]] = {}
    for archive_name in archive_names:
        archive_path = game / archive_name
        if not archive_path.is_file():
            continue
        with DtaArchive(archive_path) as archive:
            for entry in archive.entries:
                name = normalized(entry.name)
                if not predicate(name):
                    continue
                data = archive.read(entry)
                item: dict[str, object] = {
                    "archive": archive_name,
                    "entry": entry.name,
                    "size": len(data),
                    "sha256": sha256(data),
                    "data": data,
                }
                layers.setdefault(name, []).append(item)
                effective[name] = item
    return effective, layers


def scalar(block: Block) -> object:
    payload = block.payload
    if not block.children:
        stripped = payload.rstrip(b"\0")
        if stripped and all(32 <= value <= 126 for value in stripped):
            return stripped.decode("cp1252", errors="replace")
        if len(payload) == 1:
            return payload[0]
        if len(payload) == 2:
            return struct.unpack_from("<H", payload)[0]
        if len(payload) == 4:
            return struct.unpack_from("<I", payload)[0]
    return {"bytes": len(payload), "children": [child.kind for child in block.children]}


def fields(block: Block) -> list[dict[str, object]]:
    return [
        {"kind": child.kind, "value": scalar(child)}
        for child in block.children
    ]


def first_string(block: Block, kind: int) -> str | None:
    matches = direct(block, kind)
    if not matches:
        return None
    value = scalar(matches[0])
    return value if isinstance(value, str) else None


def first_integer(block: Block, kind: int) -> int | None:
    matches = direct(block, kind)
    if not matches:
        return None
    value = scalar(matches[0])
    return value if isinstance(value, int) else None


def mission_record(node: Block) -> dict[str, object]:
    objectives = []
    for index, objective in enumerate(direct(node, 0x28), 1):
        objectives.append({
            "index": index,
            "text_id": first_integer(objective, 0x29),
            "fields": fields(objective),
        })
    return {
        "directory": first_string(node, 0x36),
        "name_text_id": first_integer(node, 0x33),
        "loading_screen": first_string(node, 0x35),
        "objectives": objectives,
        "fields": fields(node),
    }


def catalogue(data: bytes, source: str) -> dict[str, object]:
    root = blocks(data, 0, len(data))
    if root is None:
        raise ValueError(f"Invalid GDT block structure: {source}")
    campaigns = []
    assigned_mission_starts: set[int] = set()
    for campaign_index, node in enumerate(
        (item for item in walk(root) if item.kind == 0x3C), 1
    ):
        mission_nodes = [
            item for item in walk(node.children) if item.kind == 0x32
        ]
        assigned_mission_starts.update(item.start for item in mission_nodes)
        campaigns.append({
            "index": campaign_index,
            "header": first_integer(node, 0x3D),
            "mission_count": len(mission_nodes),
            "missions": [mission_record(item) for item in mission_nodes],
            "fields": fields(node),
        })
    unassigned = [
        mission_record(item)
        for item in walk(root)
        if item.kind == 0x32 and item.start not in assigned_mission_starts
    ]
    return {
        "source": source,
        "size": len(data),
        "sha256": sha256(data),
        "campaign_count": len(campaigns),
        "mission_count": sum(item["mission_count"] for item in campaigns) + len(unassigned),
        "campaigns": campaigns,
        "unassigned_missions": unassigned,
        "root_kinds": [item.kind for item in root],
    }


def printable_tokens(data: bytes) -> list[str]:
    seen: set[str] = set()
    result = []
    for match in PRINTABLE_RE.finditer(data):
        value = match.group(0).decode("cp1252", errors="replace").strip()
        folded = value.casefold()
        if value and folded not in seen:
            seen.add(folded)
            result.append(value)
    return result


class FourDsReader:
    def __init__(self, data: bytes):
        self.data = data
        self.position = 0

    def take(self, count: int) -> bytes:
        end = self.position + count
        if count < 0 or end > len(self.data):
            raise ValueError(f"4DS read outside file at 0x{self.position:X}")
        value = self.data[self.position:end]
        self.position = end
        return value

    def u8(self) -> int:
        return self.take(1)[0]

    def u16(self) -> int:
        return struct.unpack("<H", self.take(2))[0]

    def u32(self) -> int:
        return struct.unpack("<I", self.take(4))[0]

    def vector3(self) -> list[float]:
        return list(struct.unpack("<3f", self.take(12)))

    def vector4(self) -> list[float]:
        return list(struct.unpack("<4f", self.take(16)))


def skip_material(reader: FourDsReader) -> None:
    flags = reader.u32()
    reader.take(64 + 4 + 4)
    has_texture = False
    if flags & (1 << 19):
        reader.take(4)
        reader.take(reader.u8())
    if flags & (1 << 18):
        has_texture = True
        reader.take(reader.u8())
    if flags & (1 << 30) and not flags & (1 << 24):
        has_texture = True
        reader.take(reader.u8())
    if not has_texture:
        reader.take(1)
    if flags & (1 << 25) or flags & (1 << 26):
        reader.take(18)


def skip_object(reader: FourDsReader) -> int:
    instance_id = reader.u16()
    if instance_id:
        return 0
    lod_count = reader.u8()
    for _ in range(lod_count):
        reader.take(4)
        extra_length = reader.u32()
        vertex_count = reader.u16()
        reader.take(vertex_count * 32)
        reader.take(extra_length * vertex_count * 4)
        for _ in range(reader.u8()):
            reader.take(reader.u16() * 6)
            reader.take(2)
    return lod_count


def skip_single_mesh(reader: FourDsReader, lod_count: int) -> None:
    bone_count = reader.u8()
    reader.take(32)
    reader.take(bone_count)
    reader.take(bone_count * 96)
    for _ in range(lod_count):
        reader.take(reader.u32() * 2)


def skip_morph(reader: FourDsReader) -> None:
    target_count = reader.u8()
    if not target_count:
        return
    channel_count = reader.u8()
    lod_count = reader.u8()
    for _ in range(lod_count):
        for _ in range(channel_count):
            vertex_count = reader.u16()
            if vertex_count:
                reader.take(vertex_count * target_count * 24)
                if reader.u8():
                    reader.take(vertex_count * 2)
    reader.take(48)


def skip_sector(reader: FourDsReader) -> None:
    reader.take(8)
    vertex_count = reader.u32()
    face_count = reader.u32()
    reader.take(32 + vertex_count * 16 + face_count * 6)
    for _ in range(reader.u8()):
        portal_vertices = reader.u8()
        reader.take(16 + 4 + 4 + 4 + 4 + portal_vertices * 16)


def skip_visual(reader: FourDsReader, visual_type: int) -> None:
    if visual_type in (0, 1):
        skip_object(reader)
    elif visual_type == 2:
        skip_single_mesh(reader, skip_object(reader))
    elif visual_type == 3:
        skip_single_mesh(reader, skip_object(reader))
        skip_morph(reader)
    elif visual_type == 4:
        skip_object(reader)
        reader.take(5)
    elif visual_type == 5:
        skip_object(reader)
        skip_morph(reader)
    elif visual_type == 6:
        reader.take(reader.u8() * 10)
    elif visual_type == 7:
        reader.take(4)
    elif visual_type == 8:
        reader.take(32 + 16 + 64 + 16 + 4)
        vertex_count = reader.u32()
        face_count = reader.u32()
        reader.take(vertex_count * 16 + face_count * 6)
    elif visual_type == 9:
        reader.take(5)
    else:
        raise ValueError(f"Unsupported HD2 visual type {visual_type}")


def parse_4ds_nodes(data: bytes) -> dict[str, object]:
    reader = FourDsReader(data)
    if reader.take(4) != b"4DS\0":
        raise ValueError("Invalid 4DS signature")
    version = reader.u16()
    if version != 41:
        raise ValueError(f"Expected HD2 4DS version 41, got {version}")
    reader.take(8)
    material_count = reader.u16()
    for _ in range(material_count):
        skip_material(reader)
    node_count_offset = reader.position
    node_count = reader.u16()
    nodes = []
    for index in range(1, node_count + 1):
        start = reader.position
        frame_type = reader.u8()
        visual_type = None
        if frame_type == 1:
            visual_type = reader.u8()
            reader.take(2)
        parent_offset = reader.position
        parent_id = reader.u16()
        position_offset = reader.position
        position = reader.vector3()
        reader.take(16)
        scale = reader.vector3()
        reader.take(4)
        reader.take(1)
        name_length_offset = reader.position
        name_length = reader.u8()
        name_offset = reader.position
        name = reader.take(name_length).rstrip(b"\0").decode(
            "cp1252", errors="replace"
        )
        properties = reader.take(reader.u8()).rstrip(b"\0").decode(
            "cp1252", errors="replace"
        )
        if frame_type == 1:
            assert visual_type is not None
            skip_visual(reader, visual_type)
        elif frame_type == 2:
            reader.take(84)
        elif frame_type == 5:
            skip_sector(reader)
        elif frame_type == 6:
            reader.take(32)
        elif frame_type == 7:
            reader.take(2 + reader.u8() * 2)
        elif frame_type == 10:
            reader.take(4)
        elif frame_type == 12:
            vertex_count = reader.u32()
            face_count = reader.u32()
            reader.take(vertex_count * 16 + face_count * 6)
        else:
            raise ValueError(f"Unsupported HD2 frame type {frame_type}")
        nodes.append({
            "index": index,
            "parent_id": parent_id,
            "frame_type": frame_type,
            "visual_type": visual_type,
            "position": position,
            "scale": scale,
            "name": name,
            "properties": properties,
            "start": start,
            "end": reader.position,
            "parent_offset": parent_offset,
            "position_offset": position_offset,
            "name_length_offset": name_length_offset,
            "name_offset": name_offset,
            "name_length": name_length,
        })
    has_animation = reader.u8()
    if reader.position != len(data):
        raise ValueError(
            f"Unparsed 4DS tail: {len(data) - reader.position} bytes"
        )
    return {
        "version": version,
        "material_count": material_count,
        "node_count": node_count,
        "node_count_offset": node_count_offset,
        "has_animation": has_animation,
        "nodes": nodes,
    }


def menu_model(item: dict[str, object]) -> dict[str, object]:
    data = item["data"]
    assert isinstance(data, bytes)
    tokens = printable_tokens(data)
    controls = [token for token in tokens if CONTROL_RE.match(token)]
    textures = [
        token for token in tokens
        if token.lower().endswith((".bmp", ".tga"))
    ]
    parsed = parse_4ds_nodes(data)
    return {
        "archive": item["archive"],
        "entry": item["entry"],
        "size": item["size"],
        "sha256": item["sha256"],
        "controls": controls,
        "textures": textures,
        "structure": parsed,
    }


def executable_references(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    lowered = data.lower()
    found = []
    for term in EXECUTABLE_TERMS:
        ascii_needle = term.lower().encode("cp1252")
        utf16_needle = term.lower().encode("utf-16le")
        encodings = []
        if ascii_needle in lowered:
            encodings.append("ascii")
        if utf16_needle in lowered:
            encodings.append("utf-16le")
        if encodings:
            found.append({"term": term, "encodings": encodings})
    return {
        "file": path.name,
        "size": len(data),
        "sha256": sha256(data),
        "references": found,
    }


def without_data(item: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in item.items() if key != "data"}


def build(game: Path) -> dict[str, object]:
    catalogues, catalogue_layers = effective_entries(
        game, CATALOGUE_ARCHIVES, lambda name: bool(CATALOGUE_RE.match(name))
    )
    menus, menu_layers = effective_entries(
        game, MENU_ARCHIVES, lambda name: name in MENU_MODELS
    )
    decoded_catalogues = [
        catalogue(item["data"], f"{item['archive']}:{item['entry']}")
        for _, item in sorted(catalogues.items())
    ]
    loose_catalogues = []
    loose_root = game / "GameData"
    if loose_root.is_dir():
        for path in sorted(loose_root.glob("Gamedata*.gdt")):
            loose_catalogues.append(catalogue(path.read_bytes(), str(path)))

    executable = game / "HD2_SabreSquadron.exe"
    return {
        "game": str(game),
        "catalogues": decoded_catalogues,
        "loose_catalogues": loose_catalogues,
        "catalogue_layers": {
            name: [without_data(item) for item in items]
            for name, items in sorted(catalogue_layers.items())
        },
        "menu_models": {
            name: menu_model(item) for name, item in sorted(menus.items())
        },
        "menu_model_layers": {
            name: [without_data(item) for item in items]
            for name, items in sorted(menu_layers.items())
        },
        "executable": executable_references(executable) if executable.is_file() else None,
    }


def markdown(report: dict[str, object]) -> str:
    lines = [
        "# Audit du menu et du catalogue solo",
        "",
        "Audit statique en lecture seule de l'installation locale. Les ressources commerciales ne sont pas reproduites.",
        "",
        "## Catalogues effectifs",
        "",
        "| Catalogue | Campagnes | Missions |",
        "|---|---:|---:|",
    ]
    for item in report["catalogues"]:
        lines.append(
            f"| {item['source']} | {item['campaign_count']} | {item['mission_count']} |"
        )
    for item in report["loose_catalogues"]:
        lines.append(
            f"| {item['source']} (fichier libre) | {item['campaign_count']} | {item['mission_count']} |"
        )
    lines += ["", "## Écrans et contrôles", ""]
    for name, item in report["menu_models"].items():
        controls = ", ".join(f"`{value}`" for value in item["controls"]) or "—"
        lines.append(f"- `{name}` ({item['archive']}) : {controls}")
    singleplayer = report["menu_models"].get("models/singleplayer.4ds")
    if singleplayer:
        roots = [
            node["name"]
            for node in singleplayer["structure"]["nodes"]
            if node["parent_id"] == 0 and node["name"].startswith("b")
        ]
        lines += [
            "",
            "## Architecture visée",
            "",
            "```text",
            "Solo",
            "├── Missions du jeu original          (inchangé : Gamedata00.gdt)",
            "├── Missions Sabre Squadron           (inchangé : Gamedata01.gdt)",
            "└── Missions personnalisées           (cible : Gamedata02.gdt)",
            "    ├── Adaptations multijoueur",
            "    ├── Créations originales",
            "    └── Exploration libre",
            "```",
            "",
            "Boutons racine actuellement reconnus dans l’écran Solo : "
            + ", ".join(f"`{name}`" for name in roots) + ".",
        ]
    lines += [
        "",
        "## Conclusion technique",
        "",
        "- Le catalogue solo est piloté par `Gamedata00.gdt` et `Gamedata01.gdt`, qui contiennent une hiérarchie campagnes → missions.",
        "- Les écrans du menu sont des scènes `.4ds` avec des contrôles nommés, mais leur action est prise en charge par l'exécutable.",
        "- La séparation demandée impose de ne modifier ni `Gamedata00.gdt` ni `Gamedata01.gdt` : les contenus personnalisés doivent vivre dans un troisième catalogue.",
        "- La scène peut recevoir visuellement une troisième commande `bcampaign02`, mais l'essai en jeu a confirmé que ce bouton n'est pas enregistré par le moteur.",
        "- La première sonde a aussi provoqué un chevauchement de contrôles ; elle a été retirée et ne doit pas entrer dans l'installateur stable.",
        "- Si le moteur ignore ce troisième suffixe, il faudra alors ajouter le gestionnaire dans l'exécutable ou employer un lanceur/catalogue séparé ; mélanger les missions avec celles d'origine n'est pas retenu comme solution.",
        "- La piste d'un lanceur modifiant la mémoire a été abandonnée après détection antivirus ; aucune exclusion de sécurité ne doit être utilisée.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--json-output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    arguments = parser.parse_args()
    report = build(arguments.game)
    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if arguments.json_output:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(encoded + "\n", encoding="utf-8")
    if arguments.markdown_output:
        arguments.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.markdown_output.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({
        "catalogues": [
            {
                "source": item["source"],
                "campaigns": item["campaign_count"],
                "missions": item["mission_count"],
            }
            for item in report["catalogues"]
        ],
        "menu_models": len(report["menu_models"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
