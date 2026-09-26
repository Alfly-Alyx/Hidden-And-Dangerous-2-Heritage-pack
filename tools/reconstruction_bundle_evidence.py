#!/usr/bin/env python3
"""Verify an inert bundle against current licensed sources and hash its payload.

Read-only: nothing is extracted, installed, launched or marked runtime-passed.
Prints a canonical file manifest suitable for recording later test provenance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import zipfile

from build_burgundy_ambient_patch import MEMBERS, RECIPES, prepare as prepare_scene
from build_reconstruction_lab import plan_lab, verify_bundle
from build_reconstruction_variant import ArchiveSources, digest, load_catalog
from reconstruction_runtime_audit import fingerprint


def payload_manifest(files: dict[str, bytes]) -> tuple[list[dict], str]:
    if not files:
        raise ValueError('An empty payload cannot identify a test build')
    seen, rows = set(), []
    for name, raw in sorted(files.items()):
        parts = name.split('/')
        if ('\\' in name or ':' in name or len(parts) != 3
                or parts[0] not in ('Missions', 'Scripts')
                or any(part in ('', '.', '..') for part in parts)
                or name.casefold() in seen or not isinstance(raw, bytes)):
            raise ValueError('Unsafe, duplicate or unsupported payload path')
        seen.add(name.casefold())
        rows.append({'path': name, 'size': len(raw), 'sha256': digest(raw)})
    return rows, fingerprint({'files': rows})


def check_members(archive, expected: set[str]):
    infos = archive.infolist()
    names = archive.namelist()
    if (len(names) != len(set(names)) or set(names) != expected
            or sum(i.file_size for i in infos) > 512 * 1024 * 1024):
        raise ValueError('Unexpected, duplicate or oversized bundle members')


def inspect_lab(path: Path, profile: dict, sources) -> dict:
    if not path.name.endswith('.lab.zip.disabled'):
        raise ValueError('Expected a disabled laboratory bundle')
    checked = verify_bundle(path)
    if checked['profile'] != profile['id']:
        raise ValueError('Bundle belongs to another profile')
    expected, fresh = plan_lab(profile, sources)
    snapshots = {}
    with zipfile.ZipFile(path) as archive:
        check_members(archive, set(expected))
        # Metadata layout may evolve; every manifest and payload byte must match.
        for name, raw in expected.items():
            if name != 'lab-report.json' and archive.read(name) != raw:
                raise ValueError(f'Bundle differs from current reconstruction: {name}')
        for package in fresh['packages']:
            snapshots[package['mode']] = {
                item['proposed_relative_path']: archive.read(item['member'])
                for item in package['files']}
    return summarize(profile['id'], 'script', fresh['source_mission'], fingerprint(profile),
                     snapshots, fresh['excluded_loose_overrides'])


def inspect_scene(path: Path, identifier: str, sources) -> dict:
    if identifier not in RECIPES or not path.name.endswith('.scene-patch.zip.disabled'):
        raise ValueError('Expected a reviewed disabled scene comparison')
    expected, fresh = prepare_scene(sources, identifier)
    mission = RECIPES[identifier]['coop']
    snapshots = {'baseline': {}, 'variant': {}}
    with zipfile.ZipFile(path) as archive:
        check_members(archive, MEMBERS | {'report.json.disabled'})
        recorded = json.loads(archive.read('report.json.disabled'))
        if (recorded.get('kind') != 'inert_scene_registry_comparison'
                or recorded.get('runtime_status') != 'pending'
                or recorded.get('installed_into_game') is not False
                or recorded.get('playable_mission') is not False):
            raise ValueError('Comparison metadata claims an unreviewed active state')
        # The original Burgundy3 bundle predates the profile field. Its identity
        # is established by all four freshly reconstructed payloads, not its name.
        if recorded.get('profile', identifier) != identifier:
            raise ValueError('Scene comparison belongs to another profile')
        for name, raw in expected.items():
            if archive.read(name) != raw:
                raise ValueError(f'Scene payload differs from current reconstruction: {name}')
            mode, filename = name.split('/')
            snapshots[mode][f'Missions/{mission}/{filename.removesuffix(".disabled")}'] = raw
    return summarize(identifier, 'scene_registry', mission, fingerprint(RECIPES[identifier]),
                     snapshots, {n: p for n, p in fresh['excluded_loose_overrides'].items()
                                 if n in fresh['source_evidence']})


def summarize(identifier: str, kind: str, mission: str, definition_sha: str,
              snapshots: dict[str, dict[str, bytes]], excluded: dict) -> dict:
    if set(snapshots) != {'baseline', 'variant'}:
        raise ValueError('Both baseline and variant are required')
    payloads = {}
    for mode, files in snapshots.items():
        rows, sha = payload_manifest(files)
        payloads[mode] = {'files': rows, 'sha256': sha}
    if payloads['baseline']['sha256'] == payloads['variant']['sha256']:
        raise ValueError('The comparison has no distinct payloads')
    return {
        'status': 'source_verified_inert_bundle', 'profile': identifier, 'kind': kind,
        'mission': mission, 'definition_sha256': definition_sha,
        'baseline_payload_sha256': payloads['baseline']['sha256'],
        'variant_payload_sha256': payloads['variant']['sha256'], 'payloads': payloads,
        'excluded_loose_overrides': excluded, 'runtime_status': 'pending',
        'installed_into_game': False, 'engine_executed': False,
        'automatic_activation_authorized': False,
        'limits': ['Fingerprints cover the listed bundle payload, not a complete game installation',
                   'Menu/runtime files created by a later deployment need separate evidence',
                   'A source-verified inert bundle is not a successful in-game test'],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--profile', required=True)
    parser.add_argument('--game', required=True, type=Path)
    parser.add_argument('--archives-only', action='store_true')
    args = parser.parse_args(argv)
    try:
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            if args.profile in RECIPES:
                report = inspect_scene(args.bundle, args.profile, sources)
            else:
                profiles = load_catalog()
                if args.profile not in profiles:
                    raise ValueError('Unknown reconstruction profile')
                report = inspect_lab(args.bundle, profiles[args.profile], sources)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f'Bundle evidence refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
