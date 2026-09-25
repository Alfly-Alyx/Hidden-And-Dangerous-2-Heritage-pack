#!/usr/bin/env python3
"""Read selected WAV resources in memory; report metadata, never export audio."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import wave

from dta_archive import DtaArchive, matches


def pcm_metadata(raw: bytes) -> dict:
    with wave.open(io.BytesIO(raw), 'rb') as wav:
        frames = wav.getnframes()
        width, channels, rate = wav.getsampwidth(), wav.getnchannels(), wav.getframerate()
        if rate <= 0 or channels <= 0 or width <= 0:
            raise ValueError('Invalid PCM format')
        if len(wav.readframes(frames)) != frames * width * channels:
            raise ValueError('Truncated PCM sample data')
        return {'channels': channels, 'sample_width_bytes': width,
                'sample_rate_hz': rate, 'sample_frames': frames,
                'duration_seconds': frames / rate,
                'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'listened': False, 'runtime_validated': False}


def audit(archive_path: Path, patterns: list[str]) -> dict:
    if not patterns:
        raise ValueError('At least one explicit resource pattern is required')
    resources = []
    with DtaArchive(archive_path) as archive:
        entries = [entry for entry in archive.entries if matches(entry.name, patterns)]
        if not entries:
            raise ValueError('No matching archive resource')
        for entry in entries:
            if not entry.name.casefold().endswith('.wav'):
                raise ValueError(f'Not a WAV resource: {entry.name}')
            resources.append({'entry': entry.name, **pcm_metadata(archive.read(entry))})
    return {'status': 'read_only_audio_metadata', 'archive': archive_path.name,
            'resources': resources, 'exported_audio': False, 'installed_into_game': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--match', action='append', required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(audit(args.archive, args.match), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, EOFError, wave.Error) as error:
        print(f'Audio audit refused: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
