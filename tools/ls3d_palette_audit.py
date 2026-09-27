#!/usr/bin/env python3
"""Synthetic joint hierarchies through native matrix/palette assembly."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

from ls3d_math_oracle import DLL_SHA
from ls3d_palette_oracle import PaletteOracle,TOLERANCE
from ls3d_skin_audit import IDENTITY


def pose(parent=-1,position=(0,0,0),rotation=(0,0,0,1),scale=(1,1,1)):
    return {'parent':parent,'position':list(position),'rotation':list(rotation),'scale':list(scale)}


def cases():
    rng=random.Random(5307)
    for count in (1,2,4,16,36,64):
        for hierarchy in ('chain','star','forest'):
            for reverse in (False,True):
                order=list(range(count))[::(-1 if reverse else 1)];indices={old:new for new,old in enumerate(order)}
                original=[]
                for index in range(count):
                    parent=index-1 if hierarchy=='chain' else 0
                    if index==0 or (hierarchy=='forest' and index%3==0):parent=-1
                    angle=rng.uniform(-.1,.1);axis=index%3;q=[0,0,0,math.cos(angle/2)];q[axis]=math.sin(angle/2)
                    original.append(pose(parent,position=[rng.uniform(-.01,.01) for _ in range(3)],
                                         rotation=q,scale=[rng.uniform(.99,1.01) for _ in range(3)]))
                poses=[{**original[i],'parent':indices[original[i]['parent']] if original[i]['parent']!=-1 else -1} for i in order]
                inverses=[]
                for _ in range(count):
                    m=IDENTITY.copy();m[12:15]=[rng.uniform(-.1,.1) for _ in range(3)];inverses.append(m)
                yield poses,inverses
    for q in ((0,0,0,1),(0,0,0,-1),(0,0,1,0),(0,0,math.sqrt(.5),math.sqrt(.5)),(.001,0,0,1)):
        for scale in ((1,1,1),(.25,1.5,2)):
            yield [pose(position=(.3,-.2,.1),rotation=q,scale=scale)],[IDENTITY]


def check_receipt(row,count):
    if (any(row.get(k) is not True for k in ('native_palette_match','inputs_preserved','joint_only_palette_assembly_qualified'))
            or any(row.get(k) is not False for k in ('loaded_scene_qualified','animation_pose_selection_qualified',
                                                    'gpu_called','library_loaded','game_started'))
            or type(row.get('joints')) is not int or row['joints']!=count
            or row.get('local_rotations_built')!=count
            or any(type(row.get(k)) is not int or row[k]<0 for k in ('local_rotations_built','matrix_products','cached_ancestor_reuses'))):
        raise ValueError('Incomplete native palette receipt')
    errors=row.get('max_errors')
    keys=('local_matrices','world_matrices','palette')
    if (not isinstance(errors,dict) or set(errors)!=set(keys)
            or any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=TOLERANCE for v in errors.values())):
        raise ValueError('Invalid native palette residual receipt')
    for key in keys:
        if (not isinstance(row.get(key),list) or len(row[key])!=count or any(not isinstance(m,list) or len(m)!=16
                or any(type(v) not in (int,float) or not math.isfinite(v) for v in m) for m in row[key])):
            raise ValueError('Invalid native palette matrix receipt')


def audit(machine):
    count=joints=products=reuses=0;errors=dict.fromkeys(('local_matrices','world_matrices','palette'),0)
    for poses,inverses in cases():
        row=machine.assemble(poses,inverses);check_receipt(row,len(poses))
        count+=1;joints+=row['joints'];products+=row['matrix_products'];reuses+=row['cached_ancestor_reuses']
        for key in errors:errors[key]=max(errors[key],row['max_errors'][key])
    return {'schema_version':1,'scope':'synthetic_joint_only_native_palette',
        'library_sha256':DLL_SHA,'cases':count,'joints':joints,'matrix_products':products,
        'cached_ancestor_reuses':reuses,'max_errors':errors,'tolerance':TOLERANCE,
        'joint_only_palette_assembly_qualified':True,'loaded_scene_qualified':False,
        'animation_pose_selection_qualified':False,'gpu_called':False,'library_loaded':False,
        'game_started':False,'game_modified':False,'geometry_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',required=True,type=Path);parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(PaletteOracle(args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native palette audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
