#!/usr/bin/env python3
"""Private Benelli channels -> native pose -> native palette -> native skin.

Every sample starts from the stock hands' rest pose, an explicit diagnostic
seed, NOT a claim about the game's chosen previous pose. Root motion is
evaluated but not applied by a renderer. No events, audio or game are run.
"""
import argparse
from bisect import bisect_right
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

from build_benelli_fpv_lab import read_sources,MANIFEST,STATES,REQUIRED
from benelli_fpv_rig_audit import read_hands,HAND_PINS,HAND_MODELS
from benelli_fpv_static import derive
from menu_gui_audit import parse_4ds_nodes
from five_ds import parse_5ds
from four_ds_skin import read_reviewed
from ls3d_math_oracle import DLL_SHA,validate_channel
from ls3d_pose_oracle import PoseOracle
from ls3d_palette_oracle import PaletteOracle
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_oracle import SkinOracle
from ls3d_skin_audit import check_receipt as check_skin


def key_window(channel,time):
    """Keep exact original bracketing keys/frames, never resample new values."""
    frames,values=channel['frames'],channel['values'];validate_channel(frames,values,time)
    after=bisect_right(frames,time//40)
    indices=[0] if after==0 else [len(frames)-1] if after==len(frames) else [after-1,after]
    return {'frames':[frames[i] for i in indices],'values':[list(values[i]) for i in indices]}


def times(frame_end,sampling):
    if type(frame_end) is not int or not 1<=frame_end<=65535:raise ValueError('Unreviewed clip end')
    end=frame_end*40
    if sampling=='boundaries':return sorted({0,1,end//2,end-1,end})
    if sampling=='half-frames':return list(range(0,end+1,20))
    raise ValueError('Unknown sample policy')


def initial_poses(raw,skin):
    return {node['name']:{'position':list(node['position']),
        'rotation':list(struct.unpack_from('<4f',raw,node['position_offset']+12)),
        'scale':list(node['scale'])} for node in skin['nodes']}


def check_pose(row):
    if (row.get('native_synthetic_pose_match') is not True or row.get('inputs_preserved') is not True
            or any(row.get(k) is not False for k in ('extra_pose_evaluated','matrix_rotation_fallback_evaluated',
                'event_or_scene_called','skin_evaluated','model_loading_qualified','game_started','library_loaded'))
            or type(row.get('max_error')) not in (int,float) or not math.isfinite(row['max_error'])
            or not 0<=row['max_error']<=2e-6):raise ValueError('Incomplete native pose-chain receipt')
    pose=row.get('pose')
    if not isinstance(pose,dict) or set(pose)!={'position','rotation','scale'}:raise ValueError('Invalid pose-chain shape')
    for kind,width in (('position',3),('rotation',4),('scale',3)):
        if (not isinstance(pose[kind],list) or len(pose[kind])!=width
                or any(type(v) not in (int,float) or not math.isfinite(v) for v in pose[kind])):
            raise ValueError('Invalid pose-chain components')


def evaluate(skin,initial,tracks,time,pose_machine,palette_machine,skin_machine):
    poses={};pose_error=0;channels=0;untracked=0
    for name,seed in initial.items():
        track=tracks.get(name);curves={} if track is None else track['channels']
        if set(curves)-{'position','rotation','scale'}:raise ValueError('Unreviewed pose-chain channel')
        selected={kind:key_window(channel,time) for kind,channel in curves.items()}
        slots=[{'active':True,'weight':1,'time':time,'channels':selected}] if selected else []
        row=pose_machine.apply(seed,slots);check_pose(row);poses[name]=row['pose']
        channels+=len(selected);untracked+=not bool(selected);pose_error=max(pose_error,row['max_error'])
    by_index={node['index']:node for node in skin['nodes']}
    bone_by_node={node:i for i,node in enumerate(skin['joint_node_indices'])}
    joints=[]
    for index in skin['joint_node_indices']:
        node=by_index[index];parent=node['parent_id']
        joints.append({**poses[node['name']],
            'parent':-1 if parent==skin['nodes'][0]['index'] else bone_by_node[parent]})
    palette=palette_machine.assemble(joints,skin['inverse_binds']);check_palette(palette,len(joints))
    vertices=skin_machine.deform(skin['vertices'],skin['pairs'],palette['palette'],skin['parents'])
    check_skin(vertices,len(skin['vertices']))
    return {'pose_max_error':pose_error,'palette_max_error':max(palette['max_errors'].values()),
        'skin_max_error':vertices['max_error'],'node_poses':len(poses),'channels':channels,
        'untracked_node_poses':untracked,'joints':len(joints),'vertices':vertices['vertices']}


def audit(sources,hands,pose_machine,palette_machine,skin_machine,*,sampling='boundaries',progress=None):
    pins=json.loads(MANIFEST.read_text(encoding='utf-8'))['sources']
    if set(sources)!=REQUIRED or set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned chain inputs')
    for name,raw in sources.items():
        if len(raw)!=pins[name]['size'] or hashlib.sha256(raw).hexdigest()!=pins[name]['sha256']:
            raise ValueError('Changed pinned animation input')
    for name,raw in hands.items():
        if len(raw)!=HAND_PINS[name][1] or hashlib.sha256(raw).hexdigest()!=HAND_PINS[name][2]:
            raise ValueError('Changed pinned hands input')
    weapon,_=derive(sources['models/#fpvbeneliaim.4ds'])
    weapon_names={node['name'] for node in parse_4ds_nodes(weapon)['nodes']}
    reports={};counts=('samples','node_poses','channels','untracked_node_poses','joints','vertices')
    residuals=('pose_max_error','palette_max_error','skin_max_error')
    for hand_name in HAND_MODELS:
        skin=read_reviewed(hands[hand_name]);initial=initial_poses(hands[hand_name],skin);clips={}
        if len(initial)!=len(skin['nodes']) or set(initial)&weapon_names:raise ValueError('Ambiguous hand/weapon targets')
        for state in STATES:
            clip=parse_5ds(sources['models/#fpvbeneli'+state+'.5ds'])
            tracks={track['name']:track for track in clip['tracks']}
            if len(tracks)!=len(clip['tracks']) or set(tracks)-set(initial)-weapon_names:
                raise ValueError('Duplicate or unresolved pose-chain target')
            stats=dict.fromkeys((*counts,*residuals),0)
            for time in times(clip['frame_end'],sampling):
                row=evaluate(skin,initial,tracks,time,pose_machine,palette_machine,skin_machine)
                stats['samples']+=1
                for key in counts[1:]:stats[key]+=row[key]
                for key in residuals:stats[key]=max(stats[key],row[key])
            clips[state]={'frame_end':clip['frame_end'],'hand_tracks':len(set(tracks)&set(initial)),**stats}
            if progress:progress(hand_name,state,stats)
        reports[hand_name]=clips
    return {'schema_version':1,'scope':'private_benelli_pose_palette_skin_explicit_rest_seed',
        'library_sha256':DLL_SHA,'sampling':sampling,'seed_policy':'reset_stock_hand_rest_at_every_sample',
        'reports':reports,'totals':{key:sum(c[key] for clips in reports.values() for c in clips.values()) for key in counts},
        'max_errors':{key:max(c[key] for clips in reports.values() for c in clips.values()) for key in residuals},
        'native_pose_palette_skin_chain_checked':True,'root_pose_evaluated':True,'root_render_transform_applied':False,
        'game_initial_pose_policy_qualified':False,'runtime_clip_transitions_qualified':False,
        'time_unit_seconds_qualified':False,'events_or_audio_called':False,'loaded_scene_qualified':False,
        'gpu_called':False,'library_loaded':False,'game_started':False,'game_modified':False,
        'engine_validated':False,'playable_weapon':False,'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--sampling',choices=('boundaries','half-frames'),default='boundaries')
    parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        sources,excluded=read_sources(args.game,json.loads(MANIFEST.read_text(encoding='utf-8')),archives_only=args.archives_only)
        hands,hand_excluded=read_hands(args.game,archives_only=args.archives_only);raw=(args.game/'LS3DF.dll').read_bytes()
        report=audit(sources,hands,PoseOracle(raw),PaletteOracle(raw),SkinOracle(raw),sampling=args.sampling,
            progress=lambda hand,state,stats:print('Checked chain: '+hand+' / '+state+' / '+str(stats['samples'])+' samples',file=sys.stderr,flush=True))
        report['excluded_loose_overrides']={**excluded,**hand_excluded}
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('reports','excluded_loose_overrides')},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Benelli native pose chain refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
