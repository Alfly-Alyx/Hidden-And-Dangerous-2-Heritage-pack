#!/usr/bin/env python3
"""Build an inert, indivisible coop Burgundy scene/registry comparison.

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
OWNERS_B2 = {'zwukprase': 'br2_snd_prase.scr', 'zwukkun': 'br2_snd_kun.scr'}
PINS_B2 = {
    'missions/burgundy2/scene2.bin': (13083442, 'a874b1cc7d52967b6291dde817c7ec46fdead1ae8802a62998695e6fc2320d9a'),
    'missions/burgundy2/scripts.dta': (4160, '1f44546fbf2eb36dba10785f92f5762c4358e4312356926279dd3711e37b818a'),
    'missions/burgundy2/sounds.bin': (15940, '762b47feb25f918320ba315e22aa48b0e6df74403846fb5c2dbf93bc866c4bb4'),
    'missions/co_burgundy2/scene2.bin': (13278244, '2f3c004fc66ad2c58c177a748108e22c2f48074eb3601b59326b4ccef6ef4fba'),
    'missions/co_burgundy2/mpscripts.dta': (5265, 'b507c7b0f384f9a4cfa6068f6e487d23ad596ee4b14555c7775918858f525ef1'),
    'missions/co_burgundy2/sounds.bin': (14995, '45189fe0987bad88b4cd89a2134aa554dcafbfdd033058bd535555ea29534cae'),
    'missions/co_burgundy2/actors.bin': (41758, '209be5a6d6403fe482b5f22ff6960e57a09291ba826d23342e6cef86267ddfb6'),
    'missions/co_burgundy2/scene.4ds': (3670973, '0b79e4157e944a713a96e53e80b19753e800dfab853e1f07a558b250e03476d5'),
}
OWNERS_B1 = {f'dummy_snd{i}': script for i, script in enumerate([
    'bur1_snd_bird1.scr', 'bur1_snd_bird2.scr', 'bur1_snd_bird3.scr',
    'bur1_snd_bird4.scr', 'bur1_snd_bird6.scr',
    *[f'bur1_snd_door{i}.scr' for i in range(1, 8)],
], 1)}
PINS_B1 = {
    'missions/burgundy1/scene2.bin': (8053475, 'ef50a34d146a2f7f38d197002aa7c6b6c530e1c9b3b27b9647205f726f3c2eb6'),
    'missions/burgundy1/scripts.dta': (3965, '26286ef163f3dc7c7c041847d7b7ac6bf1285816ae12aab0cbbd97df2d470e9c'),
    'missions/burgundy1/sounds.bin': (19504, 'e0a9a110c2921abc0f754dc5252b3322e710e8a57578b59dd995211b4ef25e8b'),
    'missions/co_burgundy1/scene2.bin': (7551923, '20b520c6570cfacaf137cd15b10890a36cc390e75f598a40bbe91782b6837180'),
    'missions/co_burgundy1/mpscripts.dta': (3376, '1714d8b87f29be8755cb50fb3b2b77a802d357aa28ab3b62bcc24ddd937b315c'),
    'missions/co_burgundy1/sounds.bin': (18239, 'e6fd7c62477032890827ec591684151f4dcc9fc5d606c786a02315b747dfbbe5'),
    'missions/co_burgundy1/actors.bin': (29363, 'c9b3893f4abcd1545ce69d66d2192ac45dfec814fbdde2abe84d5f523a30c5d0'),
    'missions/co_burgundy1/scene.4ds': (2111807, 'faf222ee18380accf71ef7c6cdc173351576afd412d8dc035027f3a98a12f54e'),
}
RECIPES = {
    'co-burgundy1-ambience': {
        'solo': 'burgundy1', 'coop': 'co_burgundy1', 'owners': OWNERS_B1, 'pins': PINS_B1,
        'scripts_sha': 'd5fa37363dd7517b17efc84bfbeafc913f5868f0f6960b7c01ca71f3738a4648',
        'sounds_identical': False, 'sound_count': 21, 'reviewed_script_differences': {},
    },
    'co-burgundy3-ambience': {
        'solo': 'burgundy3', 'coop': 'co_burgundy3', 'owners': OWNERS, 'pins': PINS,
        'scripts_sha': SCRIPT_SET_SHA, 'sounds_identical': True, 'sound_count': 24,
        'reviewed_script_differences': {},
    },
    'co-burgundy2-animal-ambience': {
        'solo': 'burgundy2', 'coop': 'co_burgundy2', 'owners': OWNERS_B2, 'pins': PINS_B2,
        'scripts_sha': '6ef21bdcb4d3a74e3e1e69c4d5bcad4ecba7fefcef827e977d05f03762c2710f',
        'sounds_identical': False, 'sound_count': 3,
        # Coop deliberately lacks the solo stop-on-signal handler. Keep coop bytes.
        'reviewed_script_differences': {'br2_snd_kun.scr': (
            'cc1cdc83b2057cc9a3f5ed053422340b6405f61f6ab17c6b1cab0f4d4a7ef6e3',
            'a1418cb289f131aa8d9c0c41334b2a61ad355188e8a34764350c89782d4ea9a8')},
    },
}
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


def check_script_pair(solo: bytes, coop: bytes, script: str, exceptions: dict):
    if solo == coop:
        return 'identical'
    if exceptions.get(script) != (digest(solo), digest(coop)):
        raise ValueError('Unreviewed solo/coop ambient script difference')
    return 'reviewed_difference_coop_preserved'


def prepare(sources, profile='co-burgundy3-ambience'):
    if profile not in RECIPES:
        raise ValueError('Unknown ambient recipe')
    recipe = RECIPES[profile]
    solo, coop, owners = recipe['solo'], recipe['coop'], recipe['owners']
    src, dst = f'missions/{solo}/', f'missions/{coop}/'
    evidence, raw = {}, {}

    def read(name):
        archive, data = sources.read(name)
        evidence[name] = {'archive': archive, 'size': len(data), 'sha256': digest(data)}
        return data

    for name, (size, sha) in recipe['pins'].items():
        raw[name] = read(name)
        if evidence[name] != {'archive': 'SabreSquadron.dta', 'size': size, 'sha256': sha}:
            raise ValueError(f'Commercial source changed: {name}')
    scripts = {name: read(name) for name in sources.mission_entries(coop)
               if name.startswith('scripts/')}
    hashes = {name: digest(data) for name, data in scripts.items()}
    if digest(json.dumps(hashes, sort_keys=True, separators=(',', ':')).encode('ascii')) != recipe['scripts_sha']:
        raise ValueError('Coop script set changed')
    if recipe['sounds_identical'] and raw[src + 'sounds.bin'] != raw[dst + 'sounds.bin']:
        raise ValueError('Solo and coop sound frames differ')
    sound_names = typed_names(raw[dst + 'sounds.bin'], 'sounds.bin')
    target_names = set().union(*(typed_names(raw[dst + file], file)
                                for file in ('scene2.bin', 'scene.4ds', 'actors.bin')))
    if set(owners) & (target_names | sound_names):
        raise ValueError('Imported owner collides with a target name')
    ambient_targets, script_comparisons = set(), {}
    for script in owners.values():
        data = scripts[f'scripts/{coop}/' + script]
        script_comparisons[script] = check_script_pair(
            read(f'scripts/{solo}/' + script), data, script, recipe['reviewed_script_differences'])
        active = split_comments(data.decode('cp1252', errors='replace'))[0]
        targets = {name.casefold() for name in re.findall(
            r'FRM_FindFrame\s*\(\s*\w+\s*,\s*"([^"]+)"', active, re.I)}
        if not targets or not targets.issubset(sound_names | target_names):
            raise ValueError('Missing ambient sound or door')
        ambient_targets.update(targets & sound_names)
    if len(ambient_targets) != recipe['sound_count']:
        raise ValueError('Unexpected number of ambient sound targets')
    for name, data in scripts.items():
        if name.rsplit('/', 1)[1] in owners.values():
            continue
        active = split_comments(data.decode('cp1252', errors='replace'))[0].casefold()
        if any('"' + target + '"' in active for target in ambient_targets):
            raise ValueError(f'Another script references an ambient sound: {name}')
    scene, records = append_owners(raw[src + 'scene2.bin'], raw[dst + 'scene2.bin'], owners)
    registry = append_bindings(raw[src + 'scripts.dta'], raw[dst + 'mpscripts.dta'], owners)
    payload = {
        'baseline/scene2.bin.disabled': raw[dst + 'scene2.bin'],
        'baseline/mpscripts.dta.disabled': raw[dst + 'mpscripts.dta'],
        'variant/scene2.bin.disabled': scene, 'variant/mpscripts.dta.disabled': registry,
    }
    report = {'kind': 'inert_scene_registry_comparison', 'profile': profile, 'runtime_status': 'pending',
              'installed_into_game': False, 'playable_mission': False,
              'installed_game_compatibility': 'not_tested',
              'source_mode': 'archives_only' if sources.archives_only else 'strict',
              'excluded_loose_overrides': sources.excluded_loose_overrides,
              'source_evidence': evidence, 'copied_record_sha256': records,
              'bindings_before': len(parse_bindings(payload['baseline/mpscripts.dta.disabled'])),
              'bindings_after': len(parse_bindings(registry)),
              'unchanged_ambient_scripts': len(owners), 'verified_sound_targets': len(ambient_targets),
              'script_comparisons': script_comparisons,
              'source_sound_files_identical': raw[src + 'sounds.bin'] == raw[dst + 'sounds.bin'],
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
    parser.add_argument('--profile', choices=sorted(RECIPES), default='co-burgundy3-ambience')
    parser.add_argument('--archives-only', action='store_true')
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and not args.build:
        parser.error('--output requires --build')
    try:
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            payload, report = prepare(sources, args.profile)
        if args.build:
            output = args.output or ROOT / '.analysis/scene-patches' / (args.profile + '.scene-patch.zip.disabled')
            print('Built:', write_comparison(output, payload, report, args.game))
        print(json.dumps({key: value for key, value in report.items()
                          if key not in ('source_evidence', 'copied_record_sha256')}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print('Comparison not ready:', error)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
