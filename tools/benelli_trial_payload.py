#!/usr/bin/env python3
"""Strict, memory-only before/after payload plan for a PRIVATE Benelli trial.

Only two new models, two central tables and eight inventory text tables may be
targets. Standalone descriptor/group fragments are audit material, not files
the engine should receive. This tool never applies or launches anything.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

from build_benelli_descriptor_lab import MODEL_PINS,SYNTHETIC_SLOT
from item_table_additive import restore,fingerprint
from texty_additive import ENCODINGS,remove_append
from reconstruction_sandbox import destination

AUDIT_FILES={'PROTOTYPE_Benelli.item.disabled','PROTOTYPE_Benelli.fpvgroup.disabled'}
TABLE_FILES={'Tables/items.sav.disabled':'items','Tables/FpvAnims.sav.disabled':'fpv'}


def target_map(names):
    if not isinstance(names,(dict,set,list,tuple)):raise ValueError('Expected a named disabled payload set')
    mapping={};languages=set();seen=set()
    for name in names:
        if not isinstance(name,str) or name.casefold() in seen:raise ValueError('Duplicate or invalid disabled payload name')
        seen.add(name.casefold())
        if name in AUDIT_FILES:continue
        if name in TABLE_FILES:mapping[name]=name.removesuffix('.disabled');continue
        if name in {stem+'.4ds.disabled' for stem in MODEL_PINS}:
            mapping[name]='Models/'+name.removesuffix('.disabled');continue
        match=re.fullmatch(r'Text/([A-Za-z]+)/TEXTY_DD\.txt\.disabled',name)
        if match and match[1].casefold() in ENCODINGS and match[1].casefold() not in languages:
            languages.add(match[1].casefold());mapping[name]=name.removesuffix('.disabled');continue
        raise ValueError('Unknown or unsafe Benelli trial payload: '+name)
    required=AUDIT_FILES|set(TABLE_FILES)|{stem+'.4ds.disabled' for stem in MODEL_PINS}
    if not required<=set(names) or languages!=set(ENCODINGS):
        raise ValueError('Incomplete two-model, two-table, eight-language trial payload')
    return mapping


def read_targets(game,mapping):
    before={}
    for name in mapping.values():
        path=destination(game,name)
        if path.exists() and not path.is_file():raise ValueError('Trial target is not a regular file')
        before[name]=path.read_bytes() if path.exists() else None
    return before


def prepare(files,manifest,before):
    mapping=target_map(files)
    if (not isinstance(files,dict) or any(not isinstance(raw,bytes) for raw in files.values())
            or not isinstance(before,dict) or set(before)!=set(mapping.values())
            or any(raw is not None and not isinstance(raw,bytes) for raw in before.values())):
        raise ValueError('Expected complete immutable before/after snapshots')
    if (not isinstance(manifest,dict) or manifest.get('scope')!='private_disabled_benelli_full_table_lab'
            or manifest.get('installation_allowed') is not False or manifest.get('game_modified') is not False
            or manifest.get('reverse_verified_in_memory') is not True):
        raise ValueError('Unreviewed or incomplete disabled laboratory manifest')
    expected={name:fingerprint(raw) for name,raw in files.items()}
    if json.dumps(manifest.get('files'),sort_keys=True)!=json.dumps(expected,sort_keys=True):
        raise ValueError('Disabled payload differs from its exact manifest')
    transaction=manifest['transaction']
    if type(transaction.get('slot')) is not int or transaction['slot']!=SYNTHETIC_SLOT:
        raise ValueError('Unexpected Benelli trial slot')
    current={key:files[name] for name,key in TABLE_FILES.items()}
    originals=restore(current,transaction)
    if (fingerprint(files['PROTOTYPE_Benelli.item.disabled'])!=transaction['descriptor']
            or fingerprint(files['PROTOTYPE_Benelli.fpvgroup.disabled'])!=transaction['fragment']):
        raise ValueError('Audit fragments do not describe the table addition')
    for stem,pin in MODEL_PINS.items():
        raw=files[stem+'.4ds.disabled']
        if (len(raw),fingerprint(raw)['sha256'])!=pin:raise ValueError('Changed reviewed modern model')
        if before['Models/'+stem+'.4ds'] is not None:raise ValueError('Modern model target already exists; not overwritten')
    composition=manifest.get('central_table_overlay_composition')
    source_kinds=composition['selected_source'] if composition else {key:'reviewed_archive' for key in ('items','fpv')}
    for name,key in TABLE_FILES.items():
        original=before[mapping[name]]
        if (source_kinds.get(key) not in ('reviewed_archive','installed_snapshot')
                or (original is None and source_kinds[key]!='reviewed_archive')
                or (original is not None and original!=originals[key])):
            raise ValueError('Current central table differs from the prepared source snapshot')
    text_report=manifest['descriptor_lab']['inventory_texts']
    for name,target in mapping.items():
        if not target.startswith('Text/'):continue
        proof=text_report['proofs'].get(target)
        if proof is None or before[target]!=remove_append(files[name],proof):
            raise ValueError('Current inventory text differs from prepared append source')
    after={target:files[name] for name,target in mapping.items()}
    rows=[{'path':name,'before':fingerprint(before[name]) if before[name] is not None else None,
           'after':fingerprint(after[name]),'operation':'create' if before[name] is None else 'replace'}
          for name in sorted(after)]
    return after,{'schema_version':1,'scope':'private_benelli_trial_file_plan','files':rows,
        'audit_only_files':sorted(AUDIT_FILES),'new_model_targets_must_be_absent':True,
        'central_tables_reverse_verified':True,'inventory_text_prefixes_verified':True,
        'source_lab_files':expected,'source_transaction':transaction,
        'pending_requirements':list(manifest['pending_requirements']),
        'isolated_filesystem_transaction_performed':False,'native_resource_search_qualified':False,
        'installation_allowed':False,'game_started':False,'game_modified':False,'playable_weapon':False}


def load_lab(path):
    manifest=json.loads(destination(path,'MANIFEST.json').read_text(encoding='utf-8'))
    names=manifest.get('files');mapping=target_map(names)
    files={name:destination(path,name).read_bytes() for name in names}
    return files,manifest,mapping


def main(argv=None):
    from benelli_asset_preflight import audit
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--lab',type=Path,required=True)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; choose a fresh path')
        files,manifest,mapping=load_lab(args.lab)
        assets=audit(args.game)
        if not assets['no_candidate_collisions']:raise ValueError('Resource preflight has unresolved candidates')
        before=read_targets(args.game,mapping)
        _,report=prepare(files,manifest,before)
        if read_targets(args.game,mapping)!=before:raise ValueError('Targets changed during trial planning')
        report['asset_preflight']=assets
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({'target_count':len(report['files']),
            'create':[row['path'] for row in report['files'] if row['operation']=='create'],
            'replace':[row['path'] for row in report['files'] if row['operation']=='replace'],
            'audit_only_files':report['audit_only_files'],'game_modified':False,
            'isolated_filesystem_transaction_performed':False},ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('Benelli trial file plan refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
