#!/usr/bin/env python3
"""Build an inert, indivisible Co_Burgundy3 scene/registry comparison.

This is not a mission package or installer. Licensed files stay in ignored local
storage. Default: read-only checks. No script, sound or objective is modified.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import re
import struct
import zipfile

from build_reconstruction_variant import ArchiveSources, ROOT, digest, typed_names
from objective_audit import blocks, direct, split_comments
from script_binding_audit import parse_bindings, registry_string

OWNERS = {f'snd_vrabec{i:02}': script for i, script in enumerate([
    'bur3_snd_bird1.scr', 'bur3_snd_bird2.scr', 'bur3_snd_bird3.scr',
    'bur3_snd_sisky.scr', 'bur3_snd_stromy.scr', 'bur3_snd_bunkr.scr',
    'bur3_snd_door1.scr', 'bur3_snd_door2.scr', 'bur3_snd_door3.scr',
    'bur3_snd_vrzik.scr',
], 1)}
PINS = {
    'missions/burgundy3/scene2.bin': (5008185, '7bcbed955744bd5b5646cbc6ce68dfd8d8d02b786677b378698d6c643cedb94c'),
    'missions/burgundy3/scripts.dta': (3421, '606d7a312b600d9e3b15060d3faa32c27ef6ebe73c1ca38c0f78f899b4b98ac5'),
    'missions/burgundy3/sounds.bin': (14614, 'd7991998f0e4e2988ce28d7b902cb19bb8e76cd5e6d481fd6cc234291a406e15'),
    'missions/co_burgundy3/scene2.bin': (5006340, '4e0b3b14f4d6e14d331585a869f254b1a07c57a29a45c3330eca4c39b10ddf25'),
    'missions/co_burgundy3/mpscripts.dta': (2029, '78e1ae06d70ee4e587d633c196f07d1b9942314cb7fe5d136376b4c79207fe82'),
    'missions/co_burgundy3/sounds.bin': (14614, 'd7991998f0e4e2988ce28d7b902cb19bb8e76cd5e6d481fd6cc234291a406e15'),
    'missions/co_burgundy3/actors.bin': (20767, 'b5a16eac58352fb9cce5fd614fb53d5046dfcfe5e651d191de11457d66487751'),
    'missions/co_burgundy3/scene.4ds': (2699031, '2493ebbb26c31fcf9497cd8d0d0988ae541b83ae8775f526067388561c6ea798'),
}
SCRIPT_SET_SHA = 'e80815747750416426d7f0f9d4514189c64e94f3a99acc58ad177166e4ba05ba'
MEMBERS = {'baseline/scene2.bin.disabled', 'baseline/mpscripts.dta.disabled',
           'variant/scene2.bin.disabled', 'variant/mpscripts.dta.disabled'}


def scene_group(raw: bytes):
    roots = blocks(raw, 0, len(raw))
    if roots is None or len(roots) != 1 or roots[0].kind != 0x4C53:
        raise ValueError('Expected one complete LS scene container')
    groups = direct(roots[0], 0x4000)
    if len(groups) != 1 or not groups[0].children:
        raise ValueError('Expected one nonempty frame group')
    return groups[0]


def record_name(record):
    fields = direct(record, 0x10)
    if len(fields) != 1 or not fields[0].payload.endswith(b'\0'):
        raise ValueError('Expected one terminated frame name')
    value = fields[0].payload[:-1]
    if not value or b'\0' in value:
        raise ValueError('Invalid frame name')
    return value.decode('cp1252').casefold()


def dummy_record(record):
    expected = [0x4011, 0x10, 0x20, 0x22, 0x2D, 0x2C, 0x4020, 0x4050]
    if record.kind != 0x4010 or [c.kind for c in record.children] != expected:
        raise ValueError('Unreviewed dummy record shape')
    children = record.children
    if children[0].payload != struct.pack('<I', 6):
        raise ValueError('Imported owner is not a dummy')
    if [len(children[i].payload) for i in (2, 3, 4, 5, 7)] != [12, 16, 12, 12, 24]:
        raise ValueError('Invalid transform or bounds')
    for index in (2, 3, 4, 5, 7):
        if not all(math.isfinite(value) for value, in struct.iter_unpack('<f', children[index].payload)):
            raise ValueError('Nonfinite transform or bounds')
    if children[2].payload != children[5].payload:
        raise ValueError('Nontrivial parent transform needs separate review')
    parent = children[6]
    if len(parent.children) != 1 or record_name(parent) != 'primary sector':
        raise ValueError('Unreviewed parent sector')


def append_owners(solo: bytes, coop: bytes, owners: dict = OWNERS):
    src, dst = scene_group(solo), scene_group(coop)
    wanted = set(owners)
    found = {}
    for record in src.children:
        if record.kind != 0x4010:
            continue
        name = record_name(record)
        if name not in wanted:
            continue
        if name in found:
            raise ValueError('Duplicate source owner')
        dummy_record(record)
        found[name] = solo[record.start:record.end]
    if set(found) != wanted:
        raise ValueError('Missing source owner')
    if wanted & typed_names(coop, 'scene2.bin'):
        raise ValueError('Target owner already exists')
    # Copy complete records in their original scene order, never rounded floats.
    addition = b''.join(found.values())
    variant = bytearray(coop[:dst.end] + addition + coop[dst.end:])
    struct.pack_into('<I', variant, 2, len(variant))
    struct.pack_into('<I', variant, dst.start + 2, dst.end - dst.start + len(addition))
    variant = bytes(variant)
    updated = scene_group(variant)
    if len(updated.children) != len(dst.children) + len(wanted):
        raise ValueError('Unexpected frame count after import')
    # Removing only appended records and undoing the two lengths recovers every byte.
    restored = bytearray(variant[:dst.end] + variant[dst.end + len(addition):])
    struct.pack_into('<I', restored, 2, len(coop))
    struct.pack_into('<I', restored, dst.start + 2, dst.end - dst.start)
    if bytes(restored) != coop:
        raise ValueError('Existing scene bytes changed')
    return variant, {name: digest(raw) for name, raw in found.items()}


def registry_pairs(raw: bytes):
    if len(raw) < 6 or struct.unpack_from('<HI', raw) != (0, len(raw)):
        raise ValueError('Invalid registry header or length')
    pairs, offset = [], 6
    while offset < len(raw):
        start = offset
        owner, offset = registry_string(raw, offset)
        script, offset = registry_string(raw, offset)
        if '\0' in owner or '\0' in script:
            raise ValueError('Embedded zero in registry field')
        pairs.append((owner.casefold(), script.casefold(), raw[start:offset]))
    return pairs


def append_bindings(solo: bytes, coop: bytes, owners: dict = OWNERS):
    source, target = registry_pairs(solo), registry_pairs(coop)
    if any(owner in owners or script in owners.values() for owner, script, _ in target):
        raise ValueError('Target owner or ambient script is already bound')
    additions = []
    for owner, script in owners.items():
        matches = [raw for name, file, raw in source if name == owner and file == script]
        if len(matches) != 1 or sum(name == owner for name, _, _ in source) != 1:
            raise ValueError('Missing or duplicate source binding')
        additions.append(matches[0])
    payload = coop[6:] + b''.join(additions)
    variant = struct.pack('<HI', 0, len(payload) + 6) + payload
    if len(registry_pairs(variant)) != len(target) + len(owners):
        raise ValueError('Unexpected binding count')
    return variant


def prepare(sources):
    evidence, raw = {}, {}

    def read(name):
        archive, data = sources.read(name)
        evidence[name] = {'archive': archive, 'size': len(data), 'sha256': digest(data)}
        return data

    for name, (size, sha) in PINS.items():
        raw[name] = read(name)
        if evidence[name] != {'archive': 'SabreSquadron.dta', 'size': size, 'sha256': sha}:
            raise ValueError(f'Commercial source changed: {name}')
    scripts = {name: read(name) for name in sources.mission_entries('co_burgundy3')
               if name.startswith('scripts/')}
    hashes = {name: digest(data) for name, data in scripts.items()}
    if digest(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode('ascii')) != SCRIPT_SET_SHA:
        raise ValueError('Coop script set changed')
    if raw['missions/burgundy3/sounds.bin'] != raw['missions/co_burgundy3/sounds.bin']:
        raise ValueError('Solo and coop sound frames differ')
    sound_names = typed_names(raw['missions/co_burgundy3/sounds.bin'], 'sounds.bin')
    target_names = set().union(*(typed_names(raw[f'missions/co_burgundy3/{file}'], file)
                                for file in ('scene2.bin', 'scene.4ds', 'actors.bin')))
    if set(OWNERS) & (target_names | sound_names):
        raise ValueError('Imported owner collides with a target name')
    ambient_targets = set()
    for script in OWNERS.values():
        data = scripts['scripts/co_burgundy3/' + script]
        if read('scripts/burgundy3/' + script) != data:
            raise ValueError('Solo and coop ambient scripts differ')
        active = split_comments(data.decode('cp1252', errors='replace'))[0]
        targets = {name.casefold() for name in re.findall(
            r'FRM_FindFrame\s*\(\s*\w+\s*,\s*"([^"]+)"', active, re.I)}
        if not targets or not targets.issubset(sound_names | target_names):
            raise ValueError('Missing ambient sound or door')
        ambient_targets.update(targets & sound_names)
    if len(ambient_targets) != 24:
        raise ValueError('Unexpected number of ambient sound targets')
    for name, data in scripts.items():
        if name.rsplit('/', 1)[1] in OWNERS.values():
            continue
        active = split_comments(data.decode('cp1252', errors='replace'))[0].casefold()
        if any('"' + target + '"' in active for target in ambient_targets):
            raise ValueError(f'Another script references an ambient sound: {name}')
    scene, records = append_owners(raw['missions/burgundy3/scene2.bin'], raw['missions/co_burgundy3/scene2.bin'])
    registry = append_bindings(raw['missions/burgundy3/scripts.dta'], raw['missions/co_burgundy3/mpscripts.dta'])
    payload = {
        'baseline/scene2.bin.disabled': raw['missions/co_burgundy3/scene2.bin'],
        'baseline/mpscripts.dta.disabled': raw['missions/co_burgundy3/mpscripts.dta'],
        'variant/scene2.bin.disabled': scene, 'variant/mpscripts.dta.disabled': registry,
    }
    report = {'kind': 'inert_scene_registry_comparison', 'runtime_status': 'pending',
              'installed_into_game': False, 'playable_mission': False,
              'installed_game_compatibility': 'not_tested',
              'source_mode': 'archives_only' if sources.archives_only else 'strict',
              'excluded_loose_overrides': sources.excluded_loose_overrides,
              'source_evidence': evidence, 'copied_record_sha256': records,
              'bindings_before': len(parse_bindings(payload['baseline/mpscripts.dta.disabled'])),
              'bindings_after': len(parse_bindings(registry)),
              'unchanged_ambient_scripts': 10, 'verified_sound_targets': 24,
              'payloads': {name: {'size': len(data), 'sha256': digest(data)} for name, data in payload.items()}}
    return payload, report


def write_comparison(output: Path, payload: dict, report: dict, game: Path, root: Path = ROOT):
    output = output.resolve()
    if (not output.is_relative_to(root.resolve() / '.analysis')
            or output.is_relative_to(game.resolve())
            or not output.name.endswith('.scene-patch.zip.disabled')):
        raise ValueError('Comparison must be disabled, ignored and outside the game')
    if (set(payload) != MEMBERS or report.get('runtime_status') != 'pending'
            or report.get('kind') != 'inert_scene_registry_comparison'
            or report.get('installed_into_game') is not False
            or report.get('playable_mission') is not False):
        raise ValueError('Both baseline and variant scene/registry pairs are required')
    expected = {name: {'size': len(data), 'sha256': digest(data)} for name, data in payload.items()}
    if report.get('payloads') != expected:
        raise ValueError('Payload fingerprints do not match')
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in payload.items():
            archive.writestr(name, data)
        archive.writestr('report.json.disabled', json.dumps(report, ensure_ascii=False, indent=2).encode('utf8'))
    with zipfile.ZipFile(output) as archive:
        if len(archive.infolist()) != 5 or set(archive.namelist()) != MEMBERS | {'report.json.disabled'}:
            raise ValueError('Unexpected comparison contents')
        for name, data in payload.items():
            if archive.read(name) != data:
                raise ValueError('Written payload differs')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--archives-only', action='store_true')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and not args.build:
        parser.error('--output requires --build')
    try:
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            payload, report = prepare(sources)
        if args.build:
            output = args.output or ROOT / '.analysis/scene-patches/co-burgundy3-ambience.scene-patch.zip.disabled'
            print('Built:', write_comparison(output, payload, report, args.game))
        print(json.dumps({key: value for key, value in report.items()
                          if key not in ('source_evidence', 'copied_record_sha256')}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print('Comparison not ready:', error)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
