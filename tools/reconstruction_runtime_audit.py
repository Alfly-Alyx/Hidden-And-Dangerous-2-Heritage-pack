#!/usr/bin/env python3
"""Read-only audit of the experimental runtime register, not a game test runner.

Recorded outcomes never activate a prototype or modify the stable release gate.
Passing records need traceable artifacts and exact current recipe fingerprints.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import sys

from build_burgundy_ambient_patch import RECIPES
from build_reconstruction_variant import load_catalog, qualification_mode

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = {'baseline', 'effect', 'interruption', 'save_load', 'objectives', 'rollback'}
STATES = {'pending', 'blocked', 'passed', 'failed'}
SHA = re.compile(r'[0-9a-f]{64}\Z')
EVIDENCE_FIELDS = {'tester', 'date', 'mode', 'game_build_sha256',
                   'baseline_payload_sha256', 'variant_payload_sha256',
                   'test_plan_sha256', 'notes', 'artifacts'}


def fingerprint(value: dict) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
    return hashlib.sha256(encoded.encode('ascii')).hexdigest()


def study_fingerprint(path: Path) -> str:
    # Normalize text line endings so Git's Windows checkout does not stale proofs.
    return fingerprint({'study_text': path.read_text(encoding='utf-8')})


def test_plan_fingerprint(profile: dict, common: dict, study_sha: str | None) -> str:
    return fingerprint({'profile': {k: v for k, v in profile.items() if k != 'results'},
                        'common_scenarios': common, 'study_sha256': study_sha})


def definitions(root: Path) -> dict:
    result = {p['id']: {'kind': 'script', 'mission': p['source'].split('/')[1],
                       'mode': qualification_mode(p),
                       'definition_sha256': fingerprint(p)}
              for p in load_catalog(root / 'experimental/reconstruction-variants.json').values()}
    for identifier, recipe in RECIPES.items():
        if identifier in result:
            raise ValueError('Script and binary recipe IDs collide')
        result[identifier] = {'kind': 'scene_registry', 'mission': recipe['coop'],
                              'definition_sha256': fingerprint(recipe)}
    return result


def local_file(root: Path, value, prefix: tuple[str, ...]) -> Path:
    if (not isinstance(value, str) or not value or '\\' in value or ':' in value
            or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('Expected a safe repository-relative path')
    parts = tuple(value.split('/'))
    if parts[:len(prefix)] != prefix or len(parts) <= len(prefix):
        raise ValueError('File is outside its permitted evidence/study directory')
    candidate = root.joinpath(*parts).resolve()
    allowed = root.joinpath(*prefix).resolve()
    if (not allowed.is_relative_to(root.resolve()) or not candidate.is_relative_to(allowed)
            or not candidate.is_file()):
        raise ValueError('Missing file or symlink outside permitted directory')
    return candidate


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(data)
    return digest.hexdigest()


def strings(value) -> bool:
    return isinstance(value, list) and bool(value) and all(
        isinstance(v, str) and v.strip() for v in value)


def evidence_errors(root: Path, evidence, mode: str, plan_sha: str) -> list[str]:
    errors = []
    if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_FIELDS:
        return ['A recorded pass/failure needs the complete evidence object']
    for field in ('tester', 'notes'):
        if not isinstance(evidence[field], str) or not evidence[field].strip():
            errors.append(f'Missing evidence {field}')
    when = evidence['date']
    try:
        if (not isinstance(when, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', when)
                or date.fromisoformat(when) > date.today()):
            raise ValueError('Invalid date')
    except ValueError:
        errors.append('Evidence date must be a real, nonfuture YYYY-MM-DD date')
    if evidence['mode'] != mode:
        errors.append('Evidence mode does not match the tested profile mode')
    if evidence['test_plan_sha256'] != plan_sha:
        errors.append('Evidence belongs to a different or older test plan')
    for field in ('game_build_sha256', 'baseline_payload_sha256', 'variant_payload_sha256'):
        if not isinstance(evidence[field], str) or not SHA.fullmatch(evidence[field]):
            errors.append(f'Invalid {field}')
    if evidence['baseline_payload_sha256'] == evidence['variant_payload_sha256']:
        errors.append('Baseline and experimental payloads must be distinct')
    artifacts = evidence['artifacts']
    if not isinstance(artifacts, list) or not artifacts:
        return errors + ['A recorded outcome needs at least one local capture or log']
    seen = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != {'path', 'sha256'}:
            errors.append('An artifact needs exactly path and sha256')
            continue
        try:
            path = local_file(root, artifact['path'], ('validation', 'evidence', 'reconstruction'))
            if path in seen:
                errors.append('Duplicate evidence artifact')
            seen.add(path)
            if not isinstance(artifact['sha256'], str) or not SHA.fullmatch(artifact['sha256']):
                errors.append('Invalid artifact SHA-256')
            elif file_hash(path) != artifact['sha256']:
                errors.append('Evidence artifact content has changed')
        except (OSError, ValueError) as error:
            errors.append(str(error))
    return errors


def validate(register, expected: dict, root: Path) -> dict:
    errors, states, identifiers = [], Counter(), []
    common, plan_fingerprints = {}, {}
    profiles = []
    if not isinstance(register, dict):
        errors.append('Register must be an object')
    else:
        if register.get('schema_version') != 1 or register.get('scope') != 'experimental-reconstruction':
            errors.append('Unsupported experimental register schema or scope')
        if register.get('default_profile') != 'commercial':
            errors.append('Commercial must remain the default')
        common = register.get('common_scenarios')
        if (not isinstance(common, dict) or set(common) != SCENARIOS | {'network'}
                or not all(isinstance(v, str) and v.strip() for v in common.values())):
            errors.append('Common executable scenarios are missing or altered in shape')
        profiles = register.get('profiles')
        if not isinstance(profiles, list) or not profiles:
            errors.append('Register needs a nonempty profiles list')
            profiles = []
    recorded_complete = []
    for item in profiles:
        if not isinstance(item, dict):
            errors.append('Profile is not an object')
            continue
        identifier = item.get('id')
        if not isinstance(identifier, str) or identifier not in expected:
            errors.append(f'Unknown profile: {identifier!r}')
            continue
        identifiers.append(identifier)
        proof = expected[identifier]
        for field in ('kind', 'mission', 'definition_sha256'):
            if item.get(field) != proof[field]:
                errors.append(f'{identifier}: stale or incorrect {field}')
        mode = proof.get('mode', 'cooperation' if proof['kind'] == 'scene_registry' else 'solo')
        if item.get('mode') != mode:
            errors.append(f'{identifier}: unsupported qualification mode')
        if not isinstance(item.get('title'), str) or not item['title'].strip():
            errors.append(f'{identifier}: missing title')
        if not strings(item.get('steps')) or len(item.get('steps', [])) < 2:
            errors.append(f'{identifier}: needs profile-specific executable steps')
        if not strings(item.get('prerequisites')):
            errors.append(f'{identifier}: missing isolation/resource prerequisites')
        study_sha = None
        try:
            study = local_file(root, item.get('study'), ('experimental',))
            if study.suffix != '.md':
                raise ValueError('Study must be a Markdown document')
            study_sha = study_fingerprint(study)
        except (OSError, ValueError) as error:
            errors.append(f'{identifier}: {error}')
        plan_fingerprints[identifier] = test_plan_fingerprint(item, common, study_sha)
        required = SCENARIOS | ({'network'} if mode == 'cooperation' else set())
        results = item.get('results')
        if not isinstance(results, dict) or set(results) != required:
            errors.append(f'{identifier}: missing or unexpected result scenarios')
            continue
        all_passed = True
        for name, result in results.items():
            label = f'{identifier}/{name}'
            if not isinstance(result, dict) or set(result) != {'state', 'evidence'}:
                errors.append(f'{label}: malformed result')
                all_passed = False
                continue
            state, evidence = result['state'], result['evidence']
            if not isinstance(state, str) or state not in STATES:
                errors.append(f'{label}: invalid state')
                all_passed = False
                continue
            states[state] += 1
            all_passed &= state == 'passed'
            if state == 'pending' and evidence is not None:
                errors.append(f'{label}: pending cannot contain claimed results')
            elif state == 'blocked':
                if (not isinstance(evidence, dict) or set(evidence) != {'notes'}
                        or not isinstance(evidence['notes'], str) or not evidence['notes'].strip()):
                    errors.append(f'{label}: blocked needs a precise explanation')
            elif state in ('passed', 'failed'):
                errors.extend(f'{label}: {error}' for error in evidence_errors(
                    root, evidence, mode, plan_fingerprints[identifier]))
        if all_passed:
            recorded_complete.append(identifier)
    duplicates = sorted(k for k, n in Counter(identifiers).items() if n > 1)
    if duplicates:
        errors.append('Duplicate profiles: ' + ', '.join(duplicates))
    missing = sorted(set(expected) - set(identifiers))
    if missing:
        errors.append('Missing profiles: ' + ', '.join(missing))
    return {'ok': not errors, 'scope': 'experimental-reconstruction',
            'profiles': len(identifiers), 'expected_profiles': len(expected),
            'scenarios': sum(states.values()), 'states': dict(sorted(states.items())),
            'test_plan_sha256': plan_fingerprints,
            'profiles_with_all_recorded_passes': recorded_complete if not errors else [],
            'all_recorded_passes': bool(expected) and not errors and len(recorded_complete) == len(expected),
            'engine_executed_by_this_audit': False, 'automatic_activation_authorized': False,
            'stable_release_register_modified': False, 'errors': errors}


def audit(root: Path) -> dict:
    path = root / 'validation/reconstruction-runtime.json'
    return validate(json.loads(path.read_text(encoding='utf-8')), definitions(root), root)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', nargs='?', type=Path, default=ROOT)
    parser.add_argument('--require-recorded-passes', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = audit(args.root.resolve())
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report['ok'] and (not args.require_recorded_passes or report['all_recorded_passes']) else 1
    except (OSError, ValueError, KeyError) as error:
        print(f'Experimental validation register refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
