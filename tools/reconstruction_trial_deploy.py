#!/usr/bin/env python3
"""Reversible native-mission trials, confined to a verified local sandbox.

One experiment at a time. Payloads stay disabled in the content store until an
explicit apply. No executable, installer, menu manager or game is ever launched.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from build_burgundy_ambient_patch import RECIPES, prepare as prepare_scene
from build_reconstruction_lab import REQUIRED_MISSION_FILES, script_closure
from build_reconstruction_variant import ArchiveSources, digest, entry_path, load_catalog, prepare_changes
from reconstruction_bundle_evidence import payload_manifest
from reconstruction_runtime_audit import audit, definitions, file_hash, fingerprint
from reconstruction_sandbox import (
    ROOT, SHA, SLUG, atomic_json, destination, idle_game, json_data, load_session,
    normal, operation, relative, verify as verify_clone, write_new,
)

AFRICA5_MISSING = 'af4_runway01_detector.scr'
AFRICA5_REGISTRY_SHA = 'c5b32bcc3d74cea53ee9b29675a6154a148ee77998d6174dce5783bb84937db6'
# Same original 1.12 client pinned by MissionPackageCore and the menu tooling.
SUPPORTED_CLIENT_SHA = '1eebde4710f800f712a05b1ecee2ba862c144f478df89b58e54c912e857ee78c'
NATIVE_MISSING = {
    'africa5': ('scripts.dta', AFRICA5_REGISTRY_SHA, [AFRICA5_MISSING]),
    'co_burgundy1': ('mpscripts.dta', RECIPES['co-burgundy1-ambience']['pins'][
        'missions/co_burgundy1/mpscripts.dta'][1], ['bu1_diary.scr', 'bur1_obj_carnage.scr']),
}


def payload_path(value: str) -> str:
    parts = relative(value)
    if len(parts) != 3 or parts[0] not in ('Missions', 'Scripts'):
        raise ValueError('Only mission-local payload paths are allowed')
    return value


def object_path(session: Path, sha: str, *, create=False) -> Path:
    if not SHA.fullmatch(sha):
        raise ValueError('Invalid content-store key')
    folder = session / 'objects'
    if folder.exists():
        normal(folder, independent=True)
    elif create:
        folder.mkdir()
    else:
        raise FileNotFoundError('Content store is missing')
    # Keys are generated lowercase hex, not user paths. Avoid rescanning the
    # entire object directory for every read (quadratic with thousands of blobs).
    path = folder / (sha + '.disabled')
    if path.exists() or path.is_symlink():
        normal(path, independent=True)
    return path


def put_blob(session: Path, raw: bytes) -> dict:
    proof = {'size': len(raw), 'sha256': digest(raw)}
    path = object_path(session, proof['sha256'], create=True)
    if path.exists():
        if path.stat().st_size != len(raw) or file_hash(path) != proof['sha256']:
            raise ValueError('Content-store object changed')
    else:
        write_new(path, raw)
    return proof


def blob(session: Path, proof: dict) -> bytes:
    if (not isinstance(proof, dict) or not isinstance(proof.get('sha256'), str)
            or not SHA.fullmatch(proof['sha256']) or type(proof.get('size')) is not int
            or proof['size'] < 0):
        raise ValueError('Invalid stored-content proof')
    path = object_path(session, proof['sha256'])
    raw = path.read_bytes()
    if len(raw) != proof['size'] or digest(raw) != proof['sha256']:
        raise ValueError('Stored payload/backup is missing or changed')
    return raw


def closure(files: dict[str, bytes], mission: str, registry: str, *, commercial_registry=None) -> dict:
    try:
        result = script_closure(files, mission, registry)
        return {**result, 'commercial_missing_script_preserved': False}
    except ValueError as error:
        # This is NOT an exception in the complete-lab generator. Here the
        # original mission namespace and its exact fossil binding are retained.
        contract = NATIVE_MISSING.get(mission)
        original = files.get(f'missions/{mission}/{registry}') if commercial_registry is None else commercial_registry
        if (contract is None or registry != contract[0]
                or str(error) != 'Missing script dependencies: ' + ', '.join(contract[2])
                or original is None or digest(original) != contract[1]):
            raise
        return {'missing_scripts': contract[2],
                'commercial_missing_script_preserved': True,
                'runtime_resolution': 'original_baseline_must_be_observed',
                'complete_lab': False, 'registry_sha256': contract[1]}


def native_plan(identifier: str, catalog: dict, sources, runtime: dict) -> tuple[dict, dict]:
    if identifier in catalog:
        profile = catalog[identifier]
        changes, proof = prepare_changes(profile, sources)
        mission, registry = profile['source'].split('/')[1], 'scripts.dta'
        definition_sha = fingerprint(profile)
        mode = 'solo'
    else:
        if identifier not in RECIPES:
            raise ValueError('Unknown native trial profile')
        pair, proof = prepare_scene(sources, identifier)
        mission, registry, mode = RECIPES[identifier]['coop'], 'mpscripts.dta', 'cooperation'
        changes = {f'missions/{mission}/{name.split("/")[1].removesuffix(".disabled")}': raw
                   for name, raw in pair.items() if name.startswith('variant/')}
        definition_sha = fingerprint(RECIPES[identifier])
    files, provenance = {}, {}
    for name in sources.mission_entries(mission):
        entry_path(name)
        if not name.startswith((f'missions/{mission}/', f'scripts/{mission}/')):
            raise ValueError('Source outside selected native mission')
        archive, raw = sources.read(name)
        files[name] = raw
        provenance[name] = {'archive': archive, 'size': len(raw), 'sha256': digest(raw)}
    required = (REQUIRED_MISSION_FILES - {'scripts.dta'}) | {registry}
    if not {f'missions/{mission}/{name}' for name in required} <= set(files):
        raise ValueError('Incomplete native mission resources')
    if not set(changes) <= set(files):
        raise ValueError('Variant is outside original mission files')
    variant = {**files, **changes}
    baseline_closure = closure(files, mission, registry)
    variant_closure = closure(variant, mission, registry,
                              commercial_registry=files[f'missions/{mission}/{registry}'])
    if baseline_closure['missing_scripts'] != variant_closure['missing_scripts']:
        raise ValueError('Variant changes the set of missing commercial scripts')
    if identifier in catalog and baseline_closure != variant_closure:
        raise ValueError('Script variant changes the dependency contract')
    missing = baseline_closure['missing_scripts']
    snapshots = {}
    payloads = {}
    for branch, values in (('baseline', files), ('variant', variant)):
        renamed = {('/'.join([name.split('/')[0].title(), *name.split('/')[1:]])): raw
                   for name, raw in values.items()}
        rows, sha = payload_manifest(renamed)
        snapshots[branch] = renamed
        payloads[branch] = {'files': rows, 'sha256': sha}
    if payloads['baseline']['sha256'] == payloads['variant']['sha256']:
        raise ValueError('Empty experimental difference')
    return snapshots, {
        'schema_version': 1, 'kind': 'native_mission_trial', 'profile': identifier,
        'mission': mission, 'mode': mode, 'definition_sha256': definition_sha,
        'test_plan_sha256': runtime['test_plan_sha256'][identifier],
        'payloads': payloads, 'source_files': provenance,
        'changed_entries': sorted(name for name in files if files[name] != variant[name]),
        'closure': {'baseline': baseline_closure, 'variant': variant_closure},
        'required_absent': [f'Scripts/{mission}/{name}' for name in missing],
        'variant_requires_observed_baseline': bool(missing),
        'excluded_loose_overrides': {n: p for n, p in sources.excluded_loose_overrides.items() if n in files},
        'runtime_status': 'pending', 'game_launched': False, 'installed_into_personal_game': False,
        'limits': ['Commercial mission data on an independently copied installed environment',
                   'Native original mission paths, not renamed custom-mission laboratories',
                   'Heritage composition and engine behavior remain runtime tests'],
    }


def save_preset(path: Path, preset: dict, *, resume=False):
    raw = json_data(preset)
    if resume and path.exists():
        normal(path, independent=True)
        if path.read_bytes() != raw:
            raise ValueError('Partial preset differs from freshly verified sources; not overwritten')
    else:
        write_new(path, raw)


def supported_client(session: Path):
    path = destination(session / 'game', 'HD2_SabreSquadron.exe')
    if file_hash(path) != SUPPORTED_CLIENT_SHA:
        raise ValueError('Native trials require the verified original Sabre Squadron 1.12 client')


def prepare_all(session: Path, *, root=ROOT, progress=None, resume=False) -> dict:
    session, ready, manifest = load_session(session, root)
    idle_game()
    supported_client(session)
    if (session / 'active.json').exists() or (session / 'PRESETS.json').exists():
        raise ValueError('Restore active trial or choose a fresh preparation session')
    checked = audit(root)
    if not checked['ok']:
        raise ValueError('Runtime register must be valid before preparation')
    catalog = load_catalog(root / 'experimental/reconstruction-variants.json')
    records = []
    with operation(session), ArchiveSources(session / 'game', archives_only=True) as sources:
        for identifier in sorted(set(catalog) | set(RECIPES)):
            snapshots, preset = native_plan(identifier, catalog, sources, checked)
            for values in snapshots.values():
                for raw in values.values():
                    put_blob(session, raw)
            preset['environment_sha256'] = ready['manifest_sha256']
            path = destination(session, 'presets/' + identifier + '.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            save_preset(path, preset, resume=resume)
            records.append({'profile': identifier, 'sha256': fingerprint(preset)})
            if progress:
                progress('Prepared ' + identifier)
        result = {'schema_version': 1, 'kind': 'native_trial_presets', 'profiles': records,
                  'environment_sha256': ready['manifest_sha256'], 'game_launched': False}
        write_new(session / 'PRESETS.json', json_data(result))
    return {'profiles': len(records), 'status': 'native_trial_presets_prepared',
            'game_launched': False, 'payloads_activated': False}


def load_preset(session: Path, identifier: str, *, expected=None) -> dict:
    if not SLUG.fullmatch(identifier):
        raise ValueError('Invalid preset identifier')
    index = json.loads(destination(session, 'PRESETS.json').read_text(encoding='utf-8'))
    preset = json.loads(destination(session, 'presets/' + identifier + '.json').read_text(encoding='utf-8'))
    matches = [p for p in index['profiles'] if p['profile'] == identifier]
    if (len(matches) != 1 or matches[0]['sha256'] != fingerprint(preset)
            or preset.get('schema_version') != 1 or preset.get('kind') != 'native_mission_trial'
            or preset.get('profile') != identifier):
        raise ValueError('Preset identity/fingerprint mismatch')
    if expected is not None and preset['definition_sha256'] != expected[identifier]['definition_sha256']:
        raise ValueError('Recipe changed since preparation')
    if set(preset['payloads']) != {'baseline', 'variant'}:
        raise ValueError('Both native snapshots are required')
    for snapshot in preset['payloads'].values():
        paths = []
        for item in snapshot['files']:
            payload_path(item['path'])
            if item['path'].split('/')[1] != preset['mission']:
                raise ValueError('Preset escapes its selected mission')
            paths.append(item['path'].casefold())
            blob(session, item)
        if not paths or len(paths) != len(set(paths)) or snapshot['sha256'] != fingerprint({'files': snapshot['files']}):
            raise ValueError('Invalid native payload manifest')
    if {p['path'] for p in preset['payloads']['baseline']['files']} != {
            p['path'] for p in preset['payloads']['variant']['files']}:
        raise ValueError('Asymmetric native snapshots')
    if preset['payloads']['baseline']['sha256'] == preset['payloads']['variant']['sha256']:
        raise ValueError('Indistinguishable baseline and variant')
    present = {row['path'].casefold() for row in preset['payloads']['baseline']['files']}
    absent = []
    for name in preset['required_absent']:
        payload_path(name)
        if name.split('/')[1] != preset['mission'] or name.casefold() in present:
            raise ValueError('A path cannot be both required and absent or outside its mission')
        absent.append(name.casefold())
    if len(absent) != len(set(absent)):
        raise ValueError('Duplicate absent-path requirement')
    return preset


def check_environment(session: Path, ready: dict, manifest: dict):
    # Frozen archives and executable determine the global resolution environment.
    for item in manifest['files']:
        name = item['path']
        if (('/' not in name and (name.lower().endswith(('.dta', '.dll'))
                                  or name.lower() == 'hd2_sabresquadron.exe'))
                or (name.lower().startswith('scripts/') and name.count('/') == 1
                    and name.lower().endswith(('.asi', '.ini')))):
            path = destination(session / 'game', name)
            if not path.is_file() or path.stat().st_size != item['size'] or file_hash(path) != item['sha256']:
                raise ValueError('Frozen game archive/executable changed: ' + name)


def replace_payload(session: Path, name: str, proof: dict):
    raw = blob(session, proof)
    game = session / 'game'
    target = destination(game, payload_path(name))
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / ('.trial-' + uuid.uuid4().hex + '.disabled')
    write_new(temporary, raw)
    destination(game, name)
    os.replace(temporary, target)
    if file_hash(target) != proof['sha256']:
        raise ValueError('Written payload failed its read-back check')


def current_proof(session: Path, name: str) -> dict | None:
    path = destination(session / 'game', payload_path(name))
    if not path.exists():
        return None
    if not path.is_file():
        raise ValueError('A payload target is not a regular file')
    return {'size': path.stat().st_size, 'sha256': file_hash(path)}


def retire(session: Path, name: str, transaction: str, category: str):
    target = destination(session / 'game', payload_path(name))
    saved = destination(session, 'retired/' + transaction + '/' + category + '/' + name + '.disabled')
    saved.parent.mkdir(parents=True, exist_ok=True)
    if saved.exists():
        raise FileExistsError('Retired payload already exists')
    os.rename(target, saved)


def restore_locked(session: Path) -> dict:
    path = destination(session, 'active.json')
    journal = json.loads(path.read_text(encoding='utf-8'))
    if (journal.get('schema_version') != 1 or journal.get('kind') != 'native_trial_transaction'
            or not isinstance(journal.get('transaction'), str)
            or not re_transaction(journal['transaction'])):
        raise ValueError('Invalid restoration journal')
    seen, conflicts = set(), []
    for item in journal['files']:
        name = payload_path(item['path'])
        if name.casefold() in seen:
            raise ValueError('Duplicate restoration target')
        seen.add(name.casefold())
        if item['after'] is not None:
            blob(session, item['after'])
        if item['before'] is not None:
            blob(session, item['before'])
        if current_proof(session, name) not in (item['before'], item['after']):
            conflicts.append(name)
    if conflicts:
        raise ValueError('Later edits preserved; restoration refused for: ' + ', '.join(conflicts))
    journal['phase'] = 'restoring'
    atomic_json(session, 'active.json', journal)
    retired = []
    for item in journal['files']:
        name = item['path']
        current = current_proof(session, name)
        if current == item['before']:
            continue
        if current != item['after']:
            raise ValueError('Target changed during restoration; later edits preserved')
        if item['before'] is None:
            retire(session, name, journal['transaction'], 'created')
            retired.append(name)
        else:
            replace_payload(session, name, item['before'])
    if any(current_proof(session, item['path']) != item['before'] for item in journal['files']):
        raise ValueError('Restoration verification failed')
    remaining_directories = []
    for name in sorted(journal.get('created_directories', []), key=lambda n: (-n.count('/'), n)):
        parts = relative(name)
        if len(parts) > 2 or parts[0] not in ('Missions', 'Scripts'):
            raise ValueError('Invalid generated directory in restoration journal')
        directory = destination(session / 'game', name)
        if directory.is_dir():
            if any(directory.iterdir()):
                remaining_directories.append(name)
            else:
                directory.rmdir()  # Only a verified empty directory created by this transaction.
    journal.update(phase='restored', retired_files=retired,
                   preserved_nonempty_directories=remaining_directories, game_launched=False)
    atomic_json(session, 'active.json', journal)
    history = destination(session, 'history/' + journal['transaction'] + '.json')
    history.parent.mkdir(parents=True, exist_ok=True)
    if history.exists():
        raise FileExistsError('History collision')
    os.rename(session / 'active.json', history)
    return {'status': 'restored', 'files': len(journal['files']),
            'retired_files': len(retired), 'history': str(history), 'game_launched': False}


def re_transaction(value: str) -> bool:
    return len(value) == 32 and all(c in '0123456789abcdef' for c in value)


def apply(session: Path, identifier: str, mode: str, *, root=ROOT, expected=None) -> dict:
    if mode not in ('baseline', 'variant'):
        raise ValueError('Choose baseline or variant')
    session, ready, manifest = load_session(session, root)
    idle_game()
    with operation(session):
        if (session / 'active.json').exists():
            raise ValueError('Restore the current experiment before applying another snapshot')
        preset = load_preset(session, identifier, expected=expected)
        if preset['environment_sha256'] != ready['manifest_sha256']:
            raise ValueError('Preset belongs to another frozen environment')
        if expected is not None:
            checked = audit(root)
            if not checked['ok'] or preset['test_plan_sha256'] != checked['test_plan_sha256'][identifier]:
                raise ValueError('Test protocol changed since preparation')
            supported_client(session)
        if mode == 'variant' and preset['variant_requires_observed_baseline']:
            checked = audit(root)
            register = json.loads((root / 'validation/reconstruction-runtime.json').read_text(encoding='utf-8'))
            items = [p for p in register['profiles'] if p['id'] == identifier]
            result = items[0]['results']['baseline'] if len(items) == 1 else {}
            evidence = result.get('evidence') or {}
            if (not checked['ok'] or result.get('state') != 'passed'
                    or evidence.get('baseline_payload_sha256') != preset['payloads']['baseline']['sha256']
                    or evidence.get('variant_payload_sha256') != preset['payloads']['variant']['sha256']
                    or evidence.get('game_build_sha256') != file_hash(session / 'game/HD2_SabreSquadron.exe')):
                raise ValueError('This variant awaits a real, evidenced native-baseline test')
        check_environment(session, ready, manifest)
        records, created_directories = [], set()
        for item in preset['payloads'][mode]['files']:
            target = destination(session / 'game', item['path'])
            parts = item['path'].split('/')
            for count in (1, 2):
                name = '/'.join(parts[:count])
                if not destination(session / 'game', name).exists():
                    created_directories.add(name)
            before = put_blob(session, target.read_bytes()) if target.is_file() else None
            if target.exists() and not target.is_file():
                raise ValueError('Non-file payload target')
            records.append({'path': item['path'], 'before': before,
                            'after': {'size': item['size'], 'sha256': item['sha256']}})
        for name in preset['required_absent']:
            target = destination(session / 'game', payload_path(name))
            before = put_blob(session, target.read_bytes()) if target.is_file() else None
            if target.exists() and not target.is_file():
                raise ValueError('Non-file target for a required commercial absence')
            records.append({'path': name, 'before': before, 'after': None})
        journal = {'schema_version': 1, 'kind': 'native_trial_transaction',
                   'transaction': uuid.uuid4().hex, 'profile': identifier, 'mode': mode,
                   'phase': 'applying', 'files': records, 'game_launched': False,
                   'created_directories': sorted(created_directories),
                   'payload_sha256': preset['payloads'][mode]['sha256'],
                   'baseline_payload_sha256': preset['payloads']['baseline']['sha256'],
                   'variant_payload_sha256': preset['payloads']['variant']['sha256'],
                   'test_plan_sha256': preset['test_plan_sha256']}
        atomic_json(session, 'active.json', journal)
        try:
            for item in records:
                if current_proof(session, item['path']) != item['before']:
                    raise ValueError('Target changed during preparation')
                if item['after'] is not None:
                    replace_payload(session, item['path'], item['after'])
                elif item['before'] is not None:
                    retire(session, item['path'], journal['transaction'], 'excluded-overrides')
            journal['phase'] = 'applied_not_run'
            atomic_json(session, 'active.json', journal)
        except (OSError, ValueError):
            restore_locked(session)
            raise
        return {'status': 'applied_not_run', 'profile': identifier, 'mode': mode,
                'files': len(records), 'payload_sha256': journal['payload_sha256'],
                'preserved_commercial_absences': preset['required_absent'],
                'game_launched': False, 'personal_installation_modified': False}


def restore(session: Path, *, root=ROOT) -> dict:
    session, _, _ = load_session(session, root)
    idle_game()
    with operation(session):
        return restore_locked(session)


def status(session: Path, *, root=ROOT) -> dict:
    session, ready, _ = load_session(session, root)
    path = destination(session, 'active.json')
    if not path.exists():
        return {'status': 'no_active_experiment', 'game_launched_by_tool': False}
    journal = json.loads(path.read_text(encoding='utf-8'))
    changed = [item['path'] for item in journal['files']
               if current_proof(session, item['path']) != item['after']]
    return {'status': journal['phase'], 'profile': journal['profile'], 'mode': journal['mode'],
            'modified_targets': changed, 'payload_sha256': journal['payload_sha256'],
            'preserved_commercial_absences': [row['path'] for row in journal['files'] if row['after'] is None],
            'game_launched_by_tool': False}


def rehearse(session: Path, *, root=ROOT, progress=None) -> dict:
    """Exercise real file application/rollback, not game behavior or engine tests."""
    session, _, _ = load_session(session, root)
    if destination(session, 'OFFLINE_REHEARSAL.json').exists():
        raise FileExistsError('An existing rehearsal record is never overwritten')
    if not verify_clone(session, root=root)['ok']:
        raise ValueError('Offline rehearsal requires the unmodified initial copy')
    expected = definitions(root)
    index = json.loads(destination(session, 'PRESETS.json').read_text(encoding='utf-8'))
    ids = [row['profile'] for row in index['profiles']]
    if set(ids) != set(expected) or len(ids) != len(expected):
        raise ValueError('Rehearsal needs the complete current preset set')
    records, awaiting = [], []
    for identifier in sorted(ids):
        preset = load_preset(session, identifier, expected=expected)
        modes = ['baseline']
        if preset['variant_requires_observed_baseline']:
            awaiting.append(identifier)
        else:
            modes.append('variant')
        for mode in modes:
            applied = apply(session, identifier, mode, root=root, expected=expected)
            check = status(session, root=root)
            if check['modified_targets']:
                raise ValueError('Rehearsal content check failed; transaction retained for inspection')
            restored = restore(session, root=root)
            records.append({'profile': identifier, 'mode': mode,
                            'payload_sha256': applied['payload_sha256'],
                            'files': applied['files'], 'restoration_history': restored['history']})
            if progress:
                progress('Applied, read back and restored: ' + identifier + '/' + mode)
    final = verify_clone(session, root=root)
    if not final['ok']:
        raise ValueError('Whole-copy comparison failed after rehearsal')
    report = {'kind': 'offline_filesystem_rehearsal', 'profiles': len(ids), 'cycles': records,
              'variant_engine_baseline_gates': awaiting, 'initial_copy_restored': True,
              'game_launched': False, 'runtime_tests_performed': 0, 'runtime_register_modified': False}
    output = destination(session, 'OFFLINE_REHEARSAL.json')
    write_new(output, json_data(report))
    return {'profiles': len(ids), 'filesystem_cycles': len(records),
            'variant_engine_baseline_gates': awaiting, 'initial_copy_restored': True,
            'game_launched': False, 'runtime_tests_performed': 0, 'report': str(output)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'apply', 'restore', 'status', 'rehearse'))
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--profile')
    parser.add_argument('--mode', choices=('baseline', 'variant'))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args(argv)
    if args.action == 'apply' and (not args.profile or not args.mode):
        parser.error('apply requires --profile and --mode')
    if args.action != 'apply' and (args.profile or args.mode):
        parser.error('--profile and --mode are only used by apply')
    if args.resume and args.action != 'prepare':
        parser.error('--resume only rechecks an incomplete preset preparation')
    try:
        if args.action == 'prepare':
            report = prepare_all(args.session, resume=args.resume,
                                 progress=lambda s: print(s, file=sys.stderr, flush=True))
        elif args.action == 'apply':
            report = apply(args.session, args.profile, args.mode, expected=definitions(ROOT))
        elif args.action == 'restore':
            report = restore(args.session)
        elif args.action == 'rehearse':
            report = rehearse(args.session, progress=lambda s: print(s, file=sys.stderr, flush=True))
        else:
            report = status(args.session)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report.get('modified_targets') else 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'Native trial operation refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
