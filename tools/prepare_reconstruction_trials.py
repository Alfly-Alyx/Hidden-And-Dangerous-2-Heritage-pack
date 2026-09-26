#!/usr/bin/env python3
"""Prepare local trial cards and exact manifests, without activating any payload.

Read-only by default. --build writes a new ignored documentation directory;
--check-output reconstructs it from current sources and compares every byte.
No game, installer, manager, process launcher or runtime-result writer is used.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import zipfile

from build_reconstruction_lab import plan_lab
from build_reconstruction_variant import (
    ROOT, ID_PATTERN, ArchiveSources, change_specs, load_catalog, prepare_changes,
)
from reconstruction_bundle_evidence import inspect_lab, inspect_scene
from reconstruction_runtime_audit import definitions, file_hash, fingerprint, validate

SCENARIO_ORDER = ('baseline', 'effect', 'interruption', 'save_load', 'objectives',
                  'rollback', 'network')
LIMITS = [
    "Préparation documentaire uniquement : aucun déploiement ni lancement effectué.",
    "Les empreintes couvrent les fichiers listés, pas une installation entière.",
    "Une copie de jeu isolée et un déploiement réversible restent à préparer.",
    "Les surcharges Heritage exclues ne sont pas déclarées compatibles.",
    "Le retour arrière décrit est un protocole à vérifier, pas un résultat acquis.",
]
ROLLBACK = [
    "Avant déploiement, inventorier les fichiers de la copie isolée qui seront touchés; "
    "sauvegarder leurs octets et empreintes ainsi que les sauvegardes de jeu.",
    "Conserver un journal distinguant les fichiers préexistants des fichiers créés. "
    "Inclure les fichiers de menu générés ultérieurement, hors du manifeste du prototype.",
    "Fermer le jeu avant restauration. Ne retirer un fichier créé que si son contenu "
    "correspond encore à celui déployé; conserver et signaler toute modification ultérieure.",
    "Restaurer les fichiers préexistants depuis leurs sauvegardes vérifiées. Comparer "
    "au relevé initial puis recharger le témoin; ne jamais viser l'installation personnelle.",
]


def locate_bundle(directory: Path, identifier: str, suffix: str) -> Path | None:
    if not ID_PATTERN.fullmatch(identifier):
        raise ValueError('Unsafe profile identifier')
    if not directory.is_dir():
        raise ValueError(f'Bundle directory is missing: {directory}')
    matches = sorted(directory.rglob(identifier + suffix))
    if len(matches) > 1:
        raise ValueError(f'Ambiguous bundle selection: {identifier}')
    if not matches:
        return None
    path = matches[0]
    if not path.is_file() or not path.resolve().is_relative_to(directory.resolve()):
        raise ValueError('Bundle link escapes its selected directory')
    return path.resolve()


def conflicts(catalog: dict) -> dict[str, list[str]]:
    changed = {identifier: {s['source'] for s in change_specs(profile)}
               for identifier, profile in catalog.items()}
    return {identifier: sorted(other for other, paths in changed.items()
                               if other != identifier and paths & changed[identifier])
            for identifier in changed}


def collect(root: Path, game: Path, labs: Path, scenes: Path, sources,
            catalog: dict, register: dict, expected: dict) -> dict:
    checked = validate(register, expected, root)
    if not checked['ok']:
        raise ValueError('Invalid runtime register: ' + '; '.join(checked['errors']))
    executable = game / 'HD2_SabreSquadron.exe'
    executable_proof = {'name': executable.name, 'size': executable.stat().st_size,
                        'sha256': file_hash(executable)}
    incompatible = conflicts(catalog)
    rows = []
    for item in sorted(register['profiles'], key=lambda p: p['id']):
        identifier = item['id']
        row = {key: item[key] for key in ('id', 'title', 'kind', 'mission', 'mode', 'study',
                                         'definition_sha256', 'prerequisites', 'steps')}
        if 'comparison_baseline' in item:
            row['comparison_baseline'] = item['comparison_baseline']
        row.update(test_plan_sha256=checked['test_plan_sha256'][identifier],
                   incompatible_profiles=incompatible.get(identifier, []),
                   scenarios=[{'id': name, 'instruction': register['common_scenarios'][name],
                               'recorded_state': item['results'][name]['state']}
                              for name in SCENARIO_ORDER if name in item['results']],
                   deployment_status='not_prepared', runtime_executed=False,
                   bundle=None, payload_evidence=None, preparation_obstacles=[])
        if item['kind'] == 'script':
            profile = catalog[identifier]
            path = locate_bundle(labs, identifier, '.lab.zip.disabled')
            if path is None:
                # A missing bundle is not evidence that a mission is incomplete.
                # Recheck the recipe and closure against the actual archives.
                _, proof = prepare_changes(profile, sources)
                row['script_variant_proof'] = proof
                try:
                    plan_lab(profile, sources)
                except ValueError as error:
                    if str(error).startswith('Native-only qualification mode: '):
                        row['preparation_status'] = 'native_mode_required'
                    elif str(error).startswith('Native-only comparison baseline: '):
                        row['preparation_status'] = 'native_composition_required'
                    elif str(error).startswith('Missing script dependencies: '):
                        row['preparation_status'] = 'missing_script_dependencies'
                    else:
                        raise
                    row['preparation_obstacles'].append(str(error))
                else:
                    row['preparation_status'] = 'complete_lab_bundle_missing'
                    row['preparation_obstacles'].append('Complete mission checked but no stored lab bundle supplied')
            else:
                row['payload_evidence'] = inspect_lab(path, profile, sources)
                row['preparation_status'] = 'source_verified_inert_lab'
        else:
            path = locate_bundle(scenes, identifier, '.scene-patch.zip.disabled')
            if path is None:
                raise ValueError(f'Missing scene comparison: {identifier}')
            row['payload_evidence'] = inspect_scene(path, identifier, sources)
            row['preparation_status'] = 'source_verified_inert_scene_comparison'
            row['preparation_obstacles'].append('Not a complete mission package; isolated cooperative deployment required')
        if path is not None:
            row['bundle'] = {'path': str(path), 'size': path.stat().st_size, 'sha256': file_hash(path)}
        rows.append(row)
    return {
        'schema_version': 1, 'kind': 'offline_reconstruction_trial_preparation',
        'game_source': str(game.resolve()), 'executable': executable_proof,
        'source_mode': 'archives_only' if getattr(sources, 'archives_only', False) else 'strict',
        'profiles': rows, 'preparation_counts': dict(sorted(Counter(
            r['preparation_status'] for r in rows).items())),
        'recorded_result_counts': checked['states'], 'limits': LIMITS, 'rollback_protocol': ROLLBACK,
        'game_launched': False, 'installer_launched': False, 'payloads_activated': False,
        'installed_into_game': False, 'runtime_register_modified': False,
        'automatic_activation_authorized': False,
    }


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def card(row: dict, report: dict) -> bytes:
    lines = [f"# {row['title']}", '', 'Préparation hors moteur — aucun essai effectué.', '',
             f"Profil : `{row['id']}` · mode : `{row['mode']}`.", '',
             f"Étude du dépôt : `{row['study']}`.", '',
             f"État de préparation : `{row['preparation_status']}`.", '',
             f"Empreinte du protocole : `{row['test_plan_sha256']}`.", '',
             f"Exécutable source : `{report['executable']['sha256']}`.", '',
             '## Avant tout déploiement', '']
    lines += ['- ' + text for text in row['prerequisites'] + row['preparation_obstacles']]
    if row.get('comparison_baseline'):
        lines += ['', 'Témoin composé Heritage : `' + row['comparison_baseline']
                  + '`. Ne pas le confondre avec une référence commerciale inchangée.']
    if row['incompatible_profiles']:
        lines += ['', 'Ne pas combiner avec : ' + ', '.join(
            f'`{p}`' for p in row['incompatible_profiles']) + '.']
    if row['bundle']:
        lines += ['', f"ZIP conservé désactivé : `{row['bundle']['path']}`.", '',
                  f"SHA-256 du ZIP : `{row['bundle']['sha256']}`."]
    evidence = row['payload_evidence']
    if evidence:
        lines += ['', '## Fichiers de référence', '',
                  f"Témoin : `{evidence['baseline_payload_sha256']}`.", '',
                  f"Variante : `{evidence['variant_payload_sha256']}`.", '',
                  'Le JSON joint contient chaque chemin, taille et empreinte. Aucun fichier de jeu '
                  'n’est extrait. Les menus ultérieurs devront être relevés séparément.']
        if evidence['excluded_loose_overrides']:
            lines += ['', 'Surcharges locales exclues (compatibilité non testée) :', '']
            lines += ['- `' + name + '`' for name in sorted(evidence['excluded_loose_overrides'])]
    lines += ['', '## Étapes propres au comportement', '']
    lines += [f'{i}. {step}' for i, step in enumerate(row['steps'], 1)]
    lines += ['', '## Contrôles et relevés à effectuer plus tard', '']
    for scenario in row['scenarios']:
        lines += [f"### {scenario['id']}", '', scenario['instruction'], '',
                  f"État déjà consigné au registre : `{scenario['recorded_state']}`.", '',
                  'Observation : à renseigner après essai réel.', '',
                  'Capture ou journal et empreinte : à renseigner après essai réel.', '']
    lines += ['## Retour arrière à vérifier', '']
    lines += [f'{i}. {step}' for i, step in enumerate(ROLLBACK, 1)]
    lines += ['', '## Limites', ''] + ['- ' + text for text in LIMITS]
    return ('\n'.join(lines) + '\n').encode('utf-8')


def documents(report: dict) -> dict[str, bytes]:
    files = {'preparation.json': json_bytes(report)}
    lines = ['# Dossier local de préparation des essais', '',
             'Aucun jeu, installateur ou gestionnaire lancé. Aucun prototype activé.', '',
             'Ce dossier ne contient que des consignes et des empreintes, sans contenu commercial.', '',
             'La copie isolée et le déploiement restent à réaliser avant les essais.', '',
             '## Fiches', '']
    for row in report['profiles']:
        identifier = row['id']
        if not ID_PATTERN.fullmatch(identifier):
            raise ValueError('Unsafe card identifier')
        files[f'{identifier}.md'] = card(row, report)
        files[f'{identifier}.json'] = json_bytes(row)
        lines.append(f"- [{row['title']}]({identifier}.md) — `{row['preparation_status']}`")
    lines += ['', '## Limites', ''] + ['- ' + text for text in LIMITS]
    files['LIRE_AVANT_ESSAI.md'] = ('\n'.join(lines) + '\n').encode('utf-8')
    return files


def safe_output(output: Path, root: Path, game: Path) -> Path:
    # Reject junctions before resolving: otherwise a redirected .analysis could
    # make a path outside the workspace appear to be a legitimate output root.
    root = root.resolve()
    allowed = root / '.analysis' / 'reconstruction-trials'
    for path in (root / '.analysis', allowed, output):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Linked trial output directories are forbidden')
    output = output.resolve()
    if (output.parent != allowed or not ID_PATTERN.fullmatch(output.name)
            or len(output.name) > 64 or output.is_relative_to(game.resolve())):
        raise ValueError('Output must be a named child of .analysis/reconstruction-trials outside the game')
    return output


def persist(output: Path, files: dict[str, bytes], root: Path, game: Path, *, check=False):
    output = safe_output(output, root, game)
    # All documents are flat metadata files, never arbitrary archive paths.
    if any(Path(name).name != name or '/' in name or '\\' in name or ':' in name
           or not name.endswith(('.md', '.json')) for name in files):
        raise ValueError('Unexpected preparation document path')
    if check:
        actual = list(output.iterdir())
        if ({p.name for p in actual} != set(files) or any(
                p.is_symlink() or not p.is_file() or p.read_bytes() != files[p.name] for p in actual)):
            raise ValueError('Trial preparation differs from current sources, bundle or protocol')
        return
    # Existing directories (including partial earlier attempts) are never reused.
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    for name, raw in sorted(files.items()):
        with (output / name).open('xb') as stream:
            stream.write(raw)
    persist(output, files, root, game, check=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--labs', type=Path, required=True)
    parser.add_argument('--scenes', type=Path, required=True)
    parser.add_argument('--archives-only', action='store_true')
    action = parser.add_mutually_exclusive_group()
    action.add_argument('--build', action='store_true')
    action.add_argument('--check-output', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if bool(args.output) != bool(args.build or args.check_output):
        parser.error('--output requires exactly one of --build or --check-output')
    try:
        if args.output:
            output = safe_output(args.output, ROOT, args.game)
            if args.build and output.exists():
                raise FileExistsError('Preparation output already exists; choose a new session name')
            if args.check_output and not output.is_dir():
                raise FileNotFoundError('Preparation output does not exist')
        catalog = load_catalog()
        register = json.loads((ROOT / 'validation/reconstruction-runtime.json').read_text(encoding='utf-8'))
        with ArchiveSources(args.game, archives_only=args.archives_only) as sources:
            report = collect(ROOT, args.game, args.labs, args.scenes, sources,
                             catalog, register, definitions(ROOT))
        if args.output:
            persist(args.output, documents(report), ROOT, args.game, check=args.check_output)
        print(json.dumps({
            'profiles': len(report['profiles']), 'preparation_counts': report['preparation_counts'],
            'recorded_result_counts': report['recorded_result_counts'],
            'preparation_sha256': fingerprint(report),
            'output': str(args.output.resolve()) if args.output else None,
            'action': 'checked' if args.check_output else 'built' if args.build else 'read_only',
            'game_launched': False, 'payloads_activated': False, 'installed_into_game': False,
        }, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f'Trial preparation refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
