#!/usr/bin/env python3
"""Private native selection/descriptor audit for Benelli and modern banks."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from ls3d_binding_oracle import BindingOracle,select_name
from ls3d_math_oracle import DLL_SHA
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from build_benelli_fpv_lab import read_sources,MANIFEST,STATES
from benelli_fpv_rig_audit import read_hands,HAND_MODELS
from benelli_fpv_static import derive
from build_modern_animation_bank import compile_bank,CASES,ROOT


def digest(raw):return hashlib.sha256(raw).hexdigest()


def audit_name_controls(machine):
    long_names=['A'*60+f'{i:03d}' for i in range(128)]
    cases=[([], 'A'),(['A'],'A'),(['A'],'a'),(['A','AB'],'AB'),(['AB','A'],'A'),
           (['Dup','Dup'],'Dup'),(['é','É'],'É'),(['A'*63],'A'*63),
           (long_names,long_names[-1]),(long_names,'A'*60+'128'),(['abc'],'ab')]
    count=0
    for names,query in cases:
        for kind in (9,0):
            row=machine.select(names,query,kind)
            expected=select_name(names,query)
            if (row.get('native_name_selection_match') is not True or row.get('inputs_preserved') is not True
                    or row.get('selected_index')!=expected or row.get('exact_case_sensitive') is not True
                    or (expected is not None and type(row.get('selected_index')) is not int)
                    or row.get('model_kind')!=kind
                    or any(row.get(k) is not False for k in ('allocation_or_binding_called','scene_loaded','game_started','library_loaded'))):
                raise ValueError('Invalid synthetic name-selection receipt')
            count+=1
    return {'cases':count,'maximum_target_count':128,'maximum_name_bytes_excluding_nul':63,
            'duplicates_select_first':True,'empty_list_and_missing_names_checked':True,
            'case_sensitive_ascii_and_cp1252_checked':True}


def audit_bank(machine,names,clips,progress=None):
    if not isinstance(names,list) or len(set(names))!=len(names):raise ValueError('Ambiguous bank target names')
    if not isinstance(clips,dict) or not clips:raise ValueError('No animation clips')
    reports={}
    for label,raw in clips.items():
        parsed=parse_5ds(raw);selections=0;descriptors=0
        for index,track in enumerate(parsed['tracks']):
            if track['name'] not in names:raise ValueError('Unbound exact animation target')
            for kind in (9,0):
                result=machine.select(names,track['name'],kind)
                if (result.get('native_name_selection_match') is not True or result.get('inputs_preserved') is not True
                        or result.get('exact_case_sensitive') is not True or result.get('model_kind')!=kind
                        or type(result.get('selected_index')) is not int or result['selected_index']!=names.index(track['name'])
                        or any(result.get(key) is not False for key in ('allocation_or_binding_called','scene_loaded','game_started','library_loaded'))):
                    raise ValueError('Incomplete native name-selection receipt')
                selections+=1
            expected={kind:len(channel['frames']) for kind,channel in track['channels'].items()}
            for slot in range(8):
                result=machine.describe(raw,index,slot)
                if (result.get('native_transform_descriptor_match') is not True or result.get('inputs_preserved') is not True
                        or type(result.get('slot')) is not int or result['slot']!=slot or result.get('channels')!=expected
                        or any(type(value) is not int for value in result['channels'].values())
                        or any(result.get(key) is not False for key in ('event_channels_evaluated','allocation_or_binding_called',
                            'scene_loaded','game_started','library_loaded'))):raise ValueError('Incomplete native descriptor receipt')
                descriptors+=1
        reports[label]={'size':len(raw),'sha256':digest(raw),'tracks':parsed['track_count'],
                        'native_name_selections':selections,'native_channel_descriptors':descriptors}
        if progress:progress(label)
    return {'target_count':len(names),'target_names_sha256':digest(json.dumps(names,ensure_ascii=True).encode('ascii')),
            'clips':reports,'tracks':sum(r['tracks'] for r in reports.values()),
            'native_name_selections':sum(r['native_name_selections'] for r in reports.values()),
            'native_channel_descriptors':sum(r['native_channel_descriptors'] for r in reports.values()),
            'actual_model_attachment_qualified':False,'game_started':False,'commercial_geometry_or_keys_exported':False}


def audit(game,archives_only=False):
    machine=BindingOracle((game/'LS3DF.dll').read_bytes())
    controls=audit_name_controls(machine)
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources,excluded=read_sources(game,manifest,archives_only=archives_only)
    hands,hand_excluded=read_hands(game,archives_only=archives_only)
    weapon,_=derive(sources['models/#fpvbeneliaim.4ds'])
    weapon_names=[node['name'] for node in parse_4ds_nodes(weapon)['nodes']]
    clips={state:sources['models/#fpvbeneli'+state+'.5ds'] for state in STATES}
    banks={}
    for name in HAND_MODELS:
        names=[node['name'] for node in parse_4ds_nodes(hands[name])['nodes']]+weapon_names
        banks[name]=audit_bank(machine,names,clips,lambda label:print('Checked '+name+': '+label,file=sys.stderr,flush=True))
        banks[name]['model_sha256']=digest(hands[name]);banks[name]['weapon_sha256']=digest(weapon)
    for name,folder in CASES.items():
        directory=ROOT/'experimental'/folder
        recipe=json.loads((directory/'modern-world-model.json').read_text(encoding='utf-8'))
        spec=json.loads((directory/'modern-animation-bank.json').read_text(encoding='utf-8'))
        rig,modern_clips,_,report=compile_bank(recipe,spec)
        names=[node['name'] for node in parse_4ds_nodes(rig)['nodes']]
        banks[name]=audit_bank(machine,names,{state:row[1] for state,row in modern_clips.items()},
                              lambda label:print('Checked modern '+name+': '+label,file=sys.stderr,flush=True))
        banks[name]['provenance']='MODERNE';banks[name]['model_sha256']=digest(rig)
    return {'schema_version':1,'scope':'native_exact_name_selection_and_transform_descriptor_preparation',
            'library_sha256':DLL_SHA,'banks':banks,'synthetic_name_controls':controls,'source_pins':manifest['sources'],
            'excluded_loose_overrides':{**excluded,**hand_excluded},
            'native_name_selections':sum(b['native_name_selections'] for b in banks.values()),
            'native_channel_descriptors':sum(b['native_channel_descriptors'] for b in banks.values()),
            'actual_model_attachment_qualified':False,'allocation_or_binding_called':False,'skin_evaluated':False,
            'scene_loaded':False,'library_loaded':False,'game_started':False,'game_modified':False,
            'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.game,args.archives_only)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('source_pins','excluded_loose_overrides','banks')},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native animation binding audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
