#!/usr/bin/env python3
"""Private unified native attachment/time/pose audit, no scene or renderer."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

from ls3d_tick_oracle import TickOracle
from ls3d_math_oracle import DLL_SHA
from animation_attach_audit import op, invented, check_receipt as check_attachment
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from build_benelli_fpv_lab import read_sources, MANIFEST, STATES
from benelli_fpv_rig_audit import read_hands, HAND_MODELS, HAND_PINS
from benelli_fpv_static import derive
from build_modern_animation_bank import compile_bank, CASES, ROOT


def model_poses(raw):
    nodes=parse_4ds_nodes(raw)['nodes']
    return [node['name'] for node in nodes],[{'position':list(node['position']),
        'rotation':list(struct.unpack_from('<4f',raw,node['position_offset']+12)),
        'scale':list(node['scale'])} for node in nodes]


def boundary_steps(end):
    if type(end) is not int or not 2 <= end <= 250:
        raise ValueError('Unreviewed unified bank duration')
    return [0,0,1,19,20,end*40-41,1,0,20]


def controls():
    seed={'position':[4,5,6],'rotation':[0,0,0,1],'scale':[1,1,1]}
    raw=invented(['Root']);names=['Root','Absent'];initial=[seed,seed]
    for mode in range(4):
        for weight in (0,.25,1,1.5):
            yield names,{'A':{'data':raw,'mode':mode}},[op('A',7,weight)],initial,boundary_steps(10),9
    for kind in (9,0):
        clips={'A':{'data':raw,'mode':2},'B':{'data':invented(['Absent']),'mode':1}}
        yield names,clips,[op('A'),op('B',7,.5)],initial,[0,20,380,0,20],kind
        yield names,clips,[op('A'),op(None)],initial,[0,40,0],kind
        yield names,clips,[op('A'),op('B')],initial,[0,40,360,40],kind


def check_receipt(row,names,clips,operations,initial,deltas,kind):
    true_flags=('native_attached_time_pose_checked','same_native_memory_across_phases',
        'full_original_channels_sampled','initial_pose_is_explicit_seed',
        'inputs_and_descriptors_preserved','poses_before_wrap_or_deactivation',
        'allocator_is_bounded_double','poses_carried_between_ticks')
    false_flags=('events_or_callbacks_called','extra_poses_evaluated','native_loader_executed',
        'skin_or_renderer_called','game_initial_pose_policy_qualified','time_unit_seconds_qualified',
        'scene_loaded','library_loaded','game_started')
    if any(row.get(key) is not True for key in true_flags) or any(row.get(key) is not False for key in false_flags):
        raise ValueError('Incomplete unified native tick receipt')
    check_attachment(row.get('attachment',{}),names,clips,operations,kind)
    if not isinstance(row.get('ticks'),list) or len(row['ticks'])!=len(deltas):
        raise ValueError('Invalid unified tick count receipt')
    errors=[]
    for delta,tick in zip(deltas,row['ticks']):
        if (type(tick.get('delta')) is not int or tick['delta']!=delta
                or type(tick.get('controller_processed')) is not bool
                or any(type(tick.get(key)) is not int or not 0<=tick[key]<=limit for key,limit in
                       (('pose_calls',len(names)),('written_channels',3*len(names)),('active_slots',8)))
                or type(tick.get('max_error')) not in (int,float) or not math.isfinite(tick['max_error'])
                or not 0<=tick['max_error']<=2e-6):
            raise ValueError('Invalid unified tick result receipt')
        errors.append(tick['max_error'])
    if type(row.get('max_error')) not in (int,float) or row['max_error']!=max(errors):
        raise ValueError('Invalid unified tick error receipt')


def audit_cases(machine,cases,progress=None):
    totals=dict(sequences=0,ticks=0,pose_calls=0,written_channels=0,max_error=0)
    for names,clips,operations,initial,deltas,kind in cases:
        row=machine.sequence_with_ticks(names,clips,operations,initial,deltas,kind)
        check_receipt(row,names,clips,operations,initial,deltas,kind)
        totals['sequences']+=1;totals['ticks']+=len(row['ticks'])
        for tick in row['ticks']:
            totals['pose_calls']+=tick['pose_calls'];totals['written_channels']+=tick['written_channels']
        totals['max_error']=max(totals['max_error'],row['max_error'])
        if progress:progress(totals['sequences'])
    return totals


def bank_cases(names,raw_clips,initial):
    if len(set(names))!=len(names) or not raw_clips:raise ValueError('Ambiguous or empty tick bank')
    for key,raw in raw_clips.items():
        parsed=parse_5ds(raw)
        if any(track['name'] not in names for track in parsed['tracks']):raise ValueError('Unbound tick bank target')
        for mode in (1,2):
            yield names,{key:{'data':raw,'mode':mode}},[op(key,7)],initial,boundary_steps(parsed['frame_end']),9
    clips={key:{'data':raw,'mode':2} for key,raw in raw_clips.items()}
    for ordered in (list(clips)[:8],list(reversed(clips))[:8]):
        operations=[op(key,index,(index+1)/8) for index,key in enumerate(ordered)]
        yield names,clips,operations,initial,[0,1,19,20,40,200,400,0,40],9


def audit(game,archives_only=False):
    machine=TickOracle((game/'LS3DF.dll').read_bytes())
    synthetic=audit_cases(machine,controls())
    print('Checked unified synthetic tick controls',file=sys.stderr,flush=True)
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources,excluded=read_sources(game,manifest,archives_only=archives_only)
    hands,hand_excluded=read_hands(game,archives_only=archives_only)
    weapon,_=derive(sources['models/#fpvbeneliaim.4ds']);weapon_names,weapon_poses=model_poses(weapon)
    stock={state:sources['models/#fpvbeneli'+state+'.5ds'] for state in STATES};banks={}
    def run(label,names,clips,poses):
        report=audit_cases(machine,bank_cases(names,clips,poses),
            lambda count:print(f'Checked unified ticks: {label} / {count} sequences',file=sys.stderr,flush=True))
        report['target_count']=len(names)
        report['clips']={key:{'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for key,raw in clips.items()}
        return report
    for name in HAND_MODELS:
        names,poses=model_poses(hands[name]);names+=weapon_names;poses+=weapon_poses
        banks[name]=run(name,names,stock,poses)
        banks[name]['model_sha256']=hashlib.sha256(hands[name]).hexdigest()
        banks[name]['weapon_sha256']=hashlib.sha256(weapon).hexdigest()
    for name,folder in CASES.items():
        directory=ROOT/'experimental'/folder
        recipe=json.loads((directory/'modern-world-model.json').read_text(encoding='utf-8'))
        spec=json.loads((directory/'modern-animation-bank.json').read_text(encoding='utf-8'))
        rig,clips,_,_=compile_bank(recipe,spec);names,poses=model_poses(rig)
        banks[name]=run(name,names,{key:value[1] for key,value in clips.items()},poses)
        banks[name]['provenance']='MODERNE';banks[name]['model_sha256']=hashlib.sha256(rig).hexdigest()
    totals={key:sum(bank[key] for bank in banks.values()) for key in ('sequences','ticks','pose_calls','written_channels')}
    totals['max_error']=max(bank['max_error'] for bank in banks.values())
    return {'schema_version':1,'scope':'unified_native_attachment_time_and_transform_pose_with_explicit_seed',
        'library_sha256':DLL_SHA,'synthetic_controls':synthetic,'bank_totals':totals,'banks':banks,
        'source_pins':manifest['sources'],'hand_pins':HAND_PINS,'excluded_loose_overrides':{**excluded,**hand_excluded},
        'same_native_memory_across_phases':True,'full_original_channels_sampled':True,
        'initial_pose_is_explicit_seed':True,'poses_carried_between_ticks':True,
        'playback_modes_are_explicit_fixtures':True,'allocator_is_bounded_double':True,
        'events_or_callbacks_called':False,'extra_poses_evaluated':False,'native_loader_executed':False,
        'skin_or_renderer_called':False,'game_initial_pose_policy_qualified':False,
        'time_unit_seconds_qualified':False,'loaded_scene_qualified':False,
        'library_loaded':False,'game_started':False,'game_modified':False,'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.game,args.archives_only)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('banks','source_pins','hand_pins','excluded_loose_overrides')},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Unified native tick audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
