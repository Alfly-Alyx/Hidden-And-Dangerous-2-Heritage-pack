#!/usr/bin/env python3
"""Private hands in the native CPU kernel with supplied diagnostic palettes.

No commercial mesh, matrix or animation key is exported. Synthetic palettes
are NOT animation poses and do not qualify native hierarchy/palette assembly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from benelli_fpv_rig_audit import HAND_PINS,HAND_MODELS,read_hands
from four_ds_skin import read_reviewed
from model_transform import compose
from ls3d_math_oracle import DLL_SHA
from ls3d_skin_oracle import SkinOracle
from ls3d_skin_audit import IDENTITY,check_receipt


def rest_palette(skin):
    matrices=[]
    for node,values in zip(skin['joint_node_indices'],skin['inverse_binds']):
        inverse=([[values[i+j*4] for j in range(3)] for i in range(3)],values[12:15])
        matrix,position=compose(skin['rest_world'][node],inverse)
        matrices.append([matrix[i][j] if i<3 and j<3 else position[i] if j==3 and i<3
                         else int(i==j) for j in range(4) for i in range(4)])
    return matrices


def palettes(skin):
    count=len(skin['parents']);identity=[IDENTITY.copy() for _ in range(count)]
    yield 'identity',identity
    yield 'reference_rest',rest_palette(skin)
    translated=[m.copy() for m in identity]
    for m in translated:m[12:15]=[.125,-.25,.5]
    yield 'uniform_diagnostic_translation',translated
    for bone in range(count):
        matrices=[m.copy() for m in identity]
        matrices[bone]=[0,1,0,0,-1,0,0,0,0,0,1,0,.125,-.25,.5,1]
        yield 'single_diagnostic_matrix_'+str(bone),matrices


def audit(hands,machine,progress=None):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hands')
    for name,raw in hands.items():
        _,size,digest=HAND_PINS[name]
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('Changed pinned hands')
    variants={}
    for name in HAND_MODELS:
        skin=read_reviewed(hands[name]);stats={'cases':0,'vertices_evaluated':0,'max_error':0,
            'reference_rest_max_displacement':0,'identity_max_displacement':0,
            'branches':{'rigid':0,'parent_matrix':0,'parent_identity':0}}
        for label,matrices in palettes(skin):
            row=machine.deform(skin['vertices'],skin['pairs'],matrices,skin['parents'])
            check_receipt(row,len(skin['vertices']))
            stats['cases']+=1;stats['vertices_evaluated']+=row['vertices']
            stats['max_error']=max(stats['max_error'],row['max_error'])
            for key,value in row['branches'].items():stats['branches'][key]+=value
            if label in ('identity','reference_rest'):
                residual=max(abs(a-b) for vertex,result in zip(skin['vertices'],row['values'])
                             for a,b in zip(vertex[:3],result[:3]))
                if residual>1e-5:raise ValueError('Hands failed identity/reference-rest displacement')
                stats[label+'_max_displacement']=residual
        variants[name]={'size':len(hands[name]),'sha256':HAND_PINS[name][2],
                        'skin_rest_audit':skin['report'],**stats}
        if progress:progress(name,stats)
    return {'schema_version':1,'scope':'private_hands_cpu_kernel_with_diagnostic_palettes',
        'library_sha256':DLL_SHA,'variants':variants,
        'cases':sum(v['cases'] for v in variants.values()),
        'vertices_evaluated':sum(v['vertices_evaluated'] for v in variants.values()),
        'max_error':max(v['max_error'] for v in variants.values()),
        'native_skin_kernel_qualified':True,'bone_index_base':1,'blend_byte_divisor':256,
        'matrix_palette_assembly_qualified':False,'animation_pose_evaluated':False,
        'scene_loaded':False,'library_loaded':False,'game_started':False,'game_modified':False,
        'engine_validated':False,'playable_weapon':False,'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        hands,excluded=read_hands(args.game,archives_only=args.archives_only)
        report=audit(hands,SkinOracle((args.game/'LS3DF.dll').read_bytes()),
                     lambda name,_:print('Checked skin kernel: '+name,file=sys.stderr,flush=True))
        report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Benelli native skin audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
