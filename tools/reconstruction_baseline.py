"""Explicit, pinned Heritage baseline for one reviewed native comparison.

This is not a generic installer or a merger of arbitrary local modifications.
Only the Africa 4 radio consequence on its original organizer is supported.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import re

from objective_audit import split_comments
from script_binding_audit import parse_bindings, scene_frame_names

ROOT = Path(__file__).resolve().parents[1]
IDENTIFIER = 'heritage-africa4-radio-v1'
SOURCE = 'scripts/africa4/af3b_organizer.scr'
MODULE = 'installer/Africa4RadioConsequenceInstaller.cs'
MODULE_SHA = '2736e5f7f928bc4d451f74d1a045bbaabc6af295ceb64a08d2dd91cbf612a1e6'
EXTERNAL = {'scripts/africa3/af3a_19.scr', 'missions/africa3/scripts.dta',
            'missions/africa3/actors.bin'}
EDIT = {'before': '   odvysilali = 1;\n', 'after': ''}
SHA = re.compile(r'[0-9a-f]{64}\Z')
DRIVERS = ('af3b_01', 'af3b_06')
SOLDIERS = tuple('af3b_' + str(i) for i in (*range(11,26), 31,32,33))
TANKERS = ('af3b_tankista01', 'af3b_tankista04')
RESERVES = tuple('af3b_' + str(i) for i in range(26,31))
CAMPAIGN = ('af3b_dummy_diary', *DRIVERS, *SOLDIERS, *TANKERS, *RESERVES)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def baseline_spec(profile, *, root=ROOT):
    spec = profile.get('comparison_baseline')
    if spec is None:
        return None
    if (not isinstance(spec, dict) or set(spec) != {
            'id', 'source', 'edits', 'module', 'external_evidence', 'size', 'sha256'}
            or spec['id'] != IDENTIFIER or spec['source'] != SOURCE
            or profile.get('source') != SOURCE or profile.get('additional_changes')
            or profile.get('qualification_mode', 'solo') != 'solo'
            or spec['edits'] != [EDIT]
            or spec['module'] != {'path': MODULE, 'text_sha256': MODULE_SHA}
            or type(spec['size']) is not int or spec['size'] <= 0
            or not isinstance(spec['sha256'], str) or not SHA.fullmatch(spec['sha256'])):
        raise ValueError('Unsupported or malformed comparison baseline')
    references = spec['external_evidence']
    if not isinstance(references, dict) or set(references) != EXTERNAL:
        raise ValueError('Heritage baseline needs the exact external campaign evidence')
    if not {f'scripts/africa4/{name}.scr' for name in CAMPAIGN} <= set(profile.get('evidence', {})):
        raise ValueError('Heritage baseline needs pinned diary and reinforcement receivers')
    for proof in references.values():
        if (not isinstance(proof, dict) or set(proof) != {'archive', 'size', 'sha256'}
                or proof['archive'] not in ('missions.dta','Scripts.dta','Patch.dta','SabreSquadron.dta')
                or type(proof['size']) is not int or proof['size'] <= 0
                or not isinstance(proof['sha256'], str) or not SHA.fullmatch(proof['sha256'])):
            raise ValueError('Invalid external campaign evidence')
    # Text normalization avoids changing the reference merely through Git CRLF.
    if digest((root / MODULE).read_text(encoding='utf-8').encode('utf-8')) != MODULE_SHA:
        raise ValueError('Heritage module changed; baseline must be reviewed again')
    return spec


def require(text, pattern):
    if not re.search(pattern, text, re.I | re.M):
        raise ValueError('Missing Heritage radio campaign contract: ' + pattern)


def prepare_baseline(profile, source, sources, apply_edits):
    spec = baseline_spec(profile)
    if spec is None:
        return source, None
    verified = {}
    for name, proof in spec['external_evidence'].items():
        archive, raw = sources.read(name)
        if archive != proof['archive'] or len(raw) != proof['size'] or digest(raw) != proof['sha256']:
            raise ValueError('External campaign source changed: ' + name)
        verified[name] = raw
    bindings = [script for actor, script in parse_bindings(verified['missions/africa3/scripts.dta'])
                if actor.casefold() == 'af3a_19']
    if ([s.casefold() for s in bindings] != ['af3a_19.scr']
            or 'af3a_19' not in scene_frame_names(verified['missions/africa3/actors.bin'])):
        raise ValueError('Missing or ambiguous original radio-operator ownership')
    operator = split_comments(verified['scripts/africa3/af3a_19.scr'].decode('cp1252'))[0]
    for value in (0, 1):
        require(operator, rf'\bSaveGameValue\s*\(\s*20\s*,\s*{value}\s*\)')
    recipients = {}
    for name in CAMPAIGN:
        path = f'scripts/africa4/{name}.scr'
        pin = profile['evidence'][path]
        archive, raw = sources.read(path)
        if archive != pin['archive'] or len(raw) != pin['size'] or digest(raw) != pin['sha256']:
            raise ValueError('Campaign receiver changed: ' + path)
        recipients[name] = split_comments(raw.decode('cp1252'))[0]
    diary = recipients['af3b_dummy_diary']
    require(diary, r'_LoadGameValue\s*\(\s*20\s*\)')
    require(diary, r'if\s*\(\s*odvisilali\s*\)[\s\S]{0,120}AddDiaryText\s*\(\s*4153\s*\)[\s\S]{0,120}else[\s\S]{0,120}AddDiaryText\s*\(\s*4154\s*\)')
    for actors, signals in ((DRIVERS,(20,21)), ((*SOLDIERS,*TANKERS),(1,2)), (RESERVES,(1,))):
        for actor in actors:
            for signal in signals:
                require(recipients[actor], rf'\bOnSignal\s*\(\s*{signal}\s*\)')
    for actor in RESERVES:
        require(recipients[actor], r'_LoadGameValue\s*\(\s*20\s*\)[\s\S]{0,300}if\s*\(\s*!\s*odvysilali\s*\)')
    baseline = apply_edits(source, spec['edits'])
    if len(baseline) != spec['size'] or digest(baseline) != spec['sha256']:
        raise ValueError('Composed baseline fingerprint differs from the reviewed result')
    text = split_comments(baseline.decode('cp1252'))[0]
    require(text, r'INTEGER\s+odvysilali\s*=\s*_LoadGameValue\s*\(\s*20\s*\)\s*;')
    if re.search(r'\bodvysilali\s*=\s*1\s*;', text, re.I):
        raise ValueError('Composed baseline still forces the radio state')
    require(text, r'if\s*\(\s*odvysilali\s*\)[\s\S]{0,120}signal1\s*=\s*20\s*;[\s\S]{0,80}signal2\s*=\s*1\s*;')
    require(text, r'else\s*\{[\s\S]{0,120}signal1\s*=\s*21\s*;[\s\S]{0,80}signal2\s*=\s*2\s*;')
    require(text, r'if\s*\(\s*odvysilali\s*\)[\s\S]{0,100}zpozdeni\s*=\s*30000\s*;[\s\S]{0,100}else[\s\S]{0,80}zpozdeni\s*=\s*20000\s*;')
    return baseline, {'id': spec['id'], 'scope': 'africa4_organizer_radio_only',
                      'source': SOURCE, 'commercial_sha256': digest(source),
                      'sha256': digest(baseline), 'size': len(baseline),
                      'module': spec['module'], 'external_evidence': spec['external_evidence'],
                      'excluded_external_loose_overrides': {
                          name: proof for name, proof in getattr(sources, 'excluded_loose_overrides', {}).items()
                          if name in EXTERNAL},
                      'complete_heritage_installation_qualified': False}
