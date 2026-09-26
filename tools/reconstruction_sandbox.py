#!/usr/bin/env python3
"""Create and verify a real, local HD2 copy. Never start a game or installer."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import uuid

from reconstruction_runtime_audit import file_hash, fingerprint

ROOT = Path(__file__).resolve().parents[1]
SHA = re.compile(r'[0-9a-f]{64}\Z')
SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
GAME_PROCESSES = {'hd2.exe', 'hd2_sabresquadron.exe', 'hd2ds.exe', 'hd2ds_sabresquadron.exe'}


def normal(path: Path, *, independent=False):
    info = path.lstat()
    if (stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400
            or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))):
        raise ValueError(f'Linked or special filesystem object refused: {path}')
    if independent and stat.S_ISREG(info.st_mode) and info.st_nlink != 1:
        raise ValueError(f'Shared hard-linked destination refused: {path}')
    return info


def relative(value: str) -> tuple[str, ...]:
    if (not isinstance(value, str) or not value or '\\' in value
            or any(c in value for c in '<>:"|?*') or any(ord(c) < 32 for c in value)):
        raise ValueError('Unsafe relative path')
    parts = tuple(value.split('/'))
    if any(p in ('', '.', '..') or p.endswith((' ', '.')) for p in parts):
        raise ValueError('Unsafe relative path component')
    if any(p.split('.')[0].casefold() in {'con', 'prn', 'aux', 'nul',
            *('com' + str(n) for n in range(1, 10)), *('lpt' + str(n) for n in range(1, 10))}
           for p in parts):
        raise ValueError('Windows device path refused')
    return parts


def destination(base: Path, name: str) -> Path:
    """Resolve Windows case semantics without following links, also in tests on Unix."""
    current = base
    normal(current, independent=True)
    for part in relative(name):
        if current.is_dir():
            candidates = [p for p in current.iterdir() if p.name.casefold() == part.casefold()]
            if len(candidates) > 1:
                raise ValueError('Case-ambiguous destination')
            current = candidates[0] if candidates else current / part
        else:
            current = current / part
        if current.exists() or current.is_symlink():
            normal(current, independent=True)
    return current


def session_path(path: Path, root: Path = ROOT) -> Path:
    root = root.resolve()
    absolute = Path(os.path.abspath(path))
    allowed = root / '.analysis' / 'reconstruction-sandboxes'
    if (absolute.parent != allowed or len(absolute.name) > 64
            or not SLUG.fullmatch(absolute.name)):
        raise ValueError('Session must be a named child of .analysis/reconstruction-sandboxes')
    for item in (root, root / '.analysis', allowed, absolute):
        if item.exists() or item.is_symlink():
            normal(item, independent=True)
    if absolute.resolve() != absolute:
        raise ValueError('Redirected session path refused')
    return absolute


def tree(root: Path, *, independent=False) -> dict[str, dict]:
    normal(root, independent=independent)
    result, seen = {}, set()
    for folder, directories, filenames in os.walk(root, followlinks=False):
        for name in sorted(directories + filenames):
            path = Path(folder) / name
            info = normal(path, independent=independent)
            rel = path.relative_to(root).as_posix()
            relative(rel)
            if rel.casefold() in seen:
                raise ValueError('Case-colliding source files or directories')
            seen.add(rel.casefold())
            if path.is_file():
                result[rel] = {'size': info.st_size, 'mtime_ns': info.st_mtime_ns}
    return dict(sorted(result.items()))


def json_data(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def write_new(path: Path, raw: bytes):
    with path.open('xb') as output:
        output.write(raw)


def atomic_json(session: Path, name: str, value: dict):
    target = destination(session, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.parent / ('.metadata-' + uuid.uuid4().hex)
    write_new(temporary, json_data(value))
    destination(session, name)  # Recheck links before replacing an existing control file.
    os.replace(temporary, target)


def idle_game():
    if os.name != 'nt':
        raise ValueError('Real game-copy operations require the Windows host')
    # Read through .NET rather than tasklist/WMI, which can be unavailable in a
    # restricted Windows session. No user-supplied shell text is interpolated.
    result = subprocess.run([
        'powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
        '[Diagnostics.Process]::GetProcesses() | ForEach-Object { $_.ProcessName }',
    ], capture_output=True, check=True, timeout=20, creationflags=0x08000000)
    names = {line.strip().casefold() + '.exe' for line in
             result.stdout.decode('utf-8', errors='replace').splitlines() if line.strip()}
    if not names:
        raise ValueError('Cannot establish a trustworthy process inventory')
    if names & GAME_PROCESSES:
        raise ValueError('Close all HD2 clients/servers before modifying a test copy')


@contextmanager
def operation(session: Path):
    lock = destination(session, '.operation.lock')
    write_new(lock, str(os.getpid()).encode('ascii'))
    try:
        yield
    finally:
        # Only this operation's ephemeral lock, never a user/game file.
        lock.unlink()


def clone(source: Path, session: Path, *, root=ROOT, build=False, progress=None) -> dict:
    session = session_path(session, root)
    source = source.resolve()
    if source == root.resolve() or session.is_relative_to(source) or source.is_relative_to(session):
        raise ValueError('Source and isolated session must be separate')
    if session.exists():
        raise FileExistsError('An existing session is never overwritten or silently resumed')
    idle_game()
    initial = tree(source)
    lower = {p.casefold() for p in initial}
    if not {'hd2_sabresquadron.exe', 'sabresquadron.dta', 'missions.dta', 'scripts.dta'} <= lower:
        raise ValueError('Source is not a complete Sabre Squadron installation')
    total = sum(p['size'] for p in initial.values())
    plan = {'files': len(initial), 'bytes': total, 'source': str(source), 'session': str(session),
            'copy_strategy': 'independent_bytes_no_links', 'game_launched': False,
            'installer_launched': False}
    if not build:
        return {**plan, 'status': 'read_only_plan'}
    if shutil.disk_usage(root).free < total + 512 * 1024 * 1024:
        raise ValueError('Insufficient space for an independent copy and preparation reserve')
    session.parent.mkdir(parents=True, exist_ok=True)
    session.mkdir()
    game = session / 'game'
    game.mkdir()
    files = []
    for index, (name, stamp) in enumerate(initial.items(), 1):
        origin = source.joinpath(*relative(name))
        if {'size': origin.stat().st_size, 'mtime_ns': origin.stat().st_mtime_ns} != stamp:
            raise ValueError('Source changed before copy; incomplete session retained')
        normal(origin)
        target = game.joinpath(*relative(name))
        target.parent.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha256()
        with origin.open('rb') as incoming, target.open('xb') as outgoing:
            for block in iter(lambda: incoming.read(1024 * 1024), b''):
                sha.update(block)
                outgoing.write(block)
        normal(target, independent=True)
        if (target.samefile(origin) or target.stat().st_size != stamp['size']
                or file_hash(target) != sha.hexdigest()):
            raise ValueError('Copy verification failed; incomplete session retained')
        files.append({'path': name, 'size': stamp['size'], 'sha256': sha.hexdigest()})
        if progress and (index % 1000 == 0 or index == len(initial)):
            progress(f'Copied and verified {index}/{len(initial)} files')
    if tree(source) != initial:
        raise ValueError('Source changed during copy; incomplete session retained')
    manifest = {'files': files}
    write_new(session / 'clone-manifest.json', json_data(manifest))
    ready = {**plan, 'schema_version': 1, 'kind': 'isolated_reconstruction_copy',
             'status': 'independent_copy_verified', 'manifest_sha256': fingerprint(manifest)}
    write_new(session / 'READY.json', json_data(ready))  # Written only after successful checks.
    return ready


def load_session(session: Path, root=ROOT) -> tuple[Path, dict, dict]:
    session = session_path(session, root)
    for name in ('READY.json', 'clone-manifest.json', 'game'):
        normal(session / name, independent=True)
    ready = json.loads((session / 'READY.json').read_text(encoding='utf-8'))
    manifest = json.loads((session / 'clone-manifest.json').read_text(encoding='utf-8'))
    if (ready.get('schema_version') != 1 or ready.get('kind') != 'isolated_reconstruction_copy'
            or ready.get('status') != 'independent_copy_verified'
            or ready.get('session') != str(session)
            or ready.get('copy_strategy') != 'independent_bytes_no_links'
            or ready.get('manifest_sha256') != fingerprint(manifest)
            or session.is_relative_to(Path(ready['source']).resolve())):
        raise ValueError('Invalid isolated-copy identity or manifest')
    seen = set()
    for item in manifest['files']:
        relative(item['path'])
        if (item['path'].casefold() in seen or not SHA.fullmatch(item['sha256'])
                or type(item['size']) is not int or item['size'] < 0):
            raise ValueError('Invalid clone file manifest')
        seen.add(item['path'].casefold())
    return session, ready, manifest


def verify(session: Path, *, root=ROOT) -> dict:
    session, ready, manifest = load_session(session, root)
    if (session / 'active.json').exists():
        raise ValueError('Restore the active experiment before full clone verification')
    game = session / 'game'
    actual = tree(game, independent=True)
    changed = []
    for item in manifest['files']:
        name = item['path']
        if (name not in actual or actual[name]['size'] != item['size']
                or file_hash(game.joinpath(*relative(name))) != item['sha256']):
            changed.append(name)
    extra = sorted(set(actual) - {r['path'] for r in manifest['files']})
    return {'ok': not changed and not extra, 'files': len(actual), 'changed': changed,
            'extra': extra, 'source': ready['source'], 'game_launched_by_tool': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('clone', 'verify'))
    parser.add_argument('--source', type=Path)
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--build', action='store_true')
    args = parser.parse_args(argv)
    if args.action == 'clone' and not args.source:
        parser.error('clone requires --source')
    if args.action == 'verify' and (args.source or args.build):
        parser.error('verify never copies or writes')
    try:
        report = (clone(args.source, args.session, build=args.build,
                        progress=lambda s: print(s, file=sys.stderr, flush=True))
                  if args.action == 'clone' else verify(args.session))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get('ok', True) else 1
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'Isolated copy refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
