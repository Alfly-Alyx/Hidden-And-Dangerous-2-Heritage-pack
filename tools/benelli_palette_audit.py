#!/usr/bin/env python3
"""Private stock-hand rest/diagnostic poses through native palette and skin.

Diagnostic joint rotations are invented, not historical Benelli animation.
Only counts and numerical residuals are exported from commercial resources.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

from benelli_fpv_rig_audit import HAND_PINS,HAND_MODELS,read_hands
from four_ds_skin import read_reviewed
from ls3d_math_oracle import DLL_SHA
from ls3d_palette_oracle import PaletteOracle
from ls3d_palette_audit import check_receipt as check_palette
from ls3d_skin_oracle import SkinOracle
from ls3d_skin_audit import check_receipt as check_skin


def rest_poses(raw,skin):
    by_index={node['index']:node for node in skin['nodes']}
    bone_by_node={node:i for i,node in enumerate(skin['joint_node_indices'])}
    result=[]
    for index in skin['joint_node_indices']:
        node=by_index[index]
        parent=-1 if node['parent_id']==skin['nodes'][0]['index'] else bone_by_node[node['parent_id']]
        result.append({'position':node['position'],'rotation':list(struct.unpack_from('<4f',raw,node['position_offset']+12)),
                       'scale':node['scale'],'parent':parent})
    return result


def scenarios(raw,skin):
    poses=rest_poses(raw,skin);yield 'rest',poses
    for index in range(len(poses)):
        changed=deepcopy(poses)
        # Deliberate replacement, not an inferred historic pose or local delta.
        changed[index]['rotation']=[0,0,math.sin(.1),math.cos(.1)]
        yield 'diagnostic_joint_'+str(index),changed


def audit(hands,palette_machine,skin_machine,progress=None):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hands')
    for name,raw in hands.items():
        _,size,digest=HAND_PINS[name]
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Changed pinned hands')
    variants={}
    for name in HAND_MODELS:
        raw=hands[name];skin=read_reviewed(raw)
        stats={'poses':0,'joints_evaluated':0,'vertices_evaluated':0,'skin_max_error':0,
            'palette_max_errors':dict.fromkeys(('local_matrices','world_matrices','palette'),0),
            'rest_max_displacement':0}
        for label,poses in scenarios(raw,skin):
            palette=palette_machine.assemble(poses,skin['inverse_binds']);check_palette(palette,len(poses))
            row=skin_machine.deform(skin['vertices'],skin['pairs'],palette['palette'],skin['parents'])
            check_skin(row,len(skin['vertices']))
            stats['poses']+=1;stats['joints_evaluated']+=len(poses);stats['vertices_evaluated']+=row['vertices']
            stats['skin_max_error']=max(stats['skin_max_error'],row['max_error'])
            for key,error in palette['max_errors'].items():stats['palette_max_errors'][key]=max(stats['palette_max_errors'][key],error)
            if label=='rest':
                error=max(abs(a-b) for vertex,result in zip(skin['vertices'],row['values']) for a,b in zip(vertex[:3],result[:3]))
                if error>1e-5:raise ValueError('Native hands rest displacement exceeds tolerance')
                stats['rest_max_displacement']=error
        variants[name]={'size':len(raw),'sha256':HAND_PINS[name][2],**stats}
        if progress:progress(name,stats)
    return {'schema_version':1,'scope':'private_hands_joint_palette_and_skin_diagnostic_poses',
        'library_sha256':DLL_SHA,'variants':variants,'poses':sum(r['poses'] for r in variants.values()),
        'joints_evaluated':sum(r['joints_evaluated'] for r in variants.values()),
        'vertices_evaluated':sum(r['vertices_evaluated'] for r in variants.values()),
        'native_joint_palette_and_skin_qualified':True,'commercial_animation_evaluated':False,
        'loaded_scene_qualified':False,'animation_pose_selection_qualified':False,
        'gpu_called':False,'library_loaded':False,'game_started':False,'game_modified':False,
        'engine_validated':False,'playable_weapon':False,'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        hands,excluded=read_hands(args.game,archives_only=args.archives_only);library=(args.game/'LS3DF.dll').read_bytes()
        report=audit(hands,PaletteOracle(library),SkinOracle(library),
                     lambda name,_:print('Checked joint palette and skin: '+name,file=sys.stderr,flush=True))
        report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Benelli native palette audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
