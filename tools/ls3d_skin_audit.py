#!/usr/bin/env python3
"""Invented skin matrices and vertices; reports omit all geometry payloads."""
import argparse
import json
import math
from pathlib import Path
import random
import sys

from ls3d_math_oracle import DLL_SHA
from ls3d_skin_oracle import SkinOracle,TOLERANCE

IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]


def cases():
    translation=IDENTITY.copy();translation[12:15]=[2,-3,1]
    rotation=[0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1]
    scaled=IDENTITY.copy();scaled[0]=2;scaled[5]=.5;scaled[10]=-1
    matrices=[IDENTITY,translation,rotation,scaled]
    vertices=[[.125,-.75,1.25,.6,0,.8,.25,.75],[-2,.25,.5,0,1,0,1,0]]
    for parent in (0,1,2,3,4):
        for bone in (1,2,3,4):
            for byte in (0,1,64,128,192,254,255):
                yield vertices,[[bone,byte]]*2,matrices,[parent]*4
    yield [],[],matrices,[0]*4
    rng=random.Random(65060)
    matrices=[]
    for _ in range(64):
        matrix=[rng.uniform(-2,2) for _ in range(16)]
        for i,v in ((3,0),(7,0),(11,0),(15,1)):matrix[i]=v
        matrices.append(matrix)
    for _ in range(8):
        yield ([[rng.uniform(-2,2) for _ in range(8)] for _ in range(256)],
               [[rng.randrange(1,65),byte] for byte in range(256)],matrices,
               [rng.randrange(0,65) for _ in range(64)])
    yield ([[.25,-.5,1,0,0,1,0,0]]*2048,[[64,255]]*2048,matrices,[0]*64)


def check_receipt(row,vertices):
    if (any(row.get(k) is not True for k in ('native_skin_kernel_match','inputs_preserved','uv_output_untouched'))
            or row.get('bone_index_base')!=1 or row.get('blend_byte_divisor')!=256
            or any(row.get(k) is not False for k in ('normals_renormalized','matrix_palette_assembly_qualified',
                'scene_loaded','library_loaded','game_started','engine_validated'))
            or type(row.get('max_error')) not in (int,float) or not math.isfinite(row['max_error'])
            or not 0<=row['max_error']<=TOLERANCE):raise ValueError('Incomplete native skin receipt')
    if (type(row.get('vertices')) is not int or row['vertices']!=vertices
            or not isinstance(row.get('values'),list) or len(row['values'])!=vertices
            or any(not isinstance(v,list) or len(v)!=6 or any(type(x) not in (int,float)
                or not math.isfinite(x) for x in v) for v in row['values'])
            or not isinstance(row.get('branches'),dict)
            or set(row['branches'])!={'rigid','parent_matrix','parent_identity'}
            or any(type(v) is not int or v<0 for v in row['branches'].values())
            or sum(row['branches'].values())!=vertices):raise ValueError('Invalid native skin values or counts receipt')


def audit(machine):
    count=vertices=0;error=0;branches={'rigid':0,'parent_matrix':0,'parent_identity':0}
    for args in cases():
        row=machine.deform(*args);check_receipt(row,len(args[0]))
        count+=1;vertices+=row['vertices'];error=max(error,row['max_error'])
        for name in branches:branches[name]+=row['branches'][name]
    return {'schema_version':1,'scope':'synthetic_cpu_skin_kernel_supplied_palette',
        'library_sha256':DLL_SHA,'cases':count,'vertices':vertices,'branches':branches,'max_error':error,
        'tolerance':TOLERANCE,'bone_index_base':1,'blend_byte_divisor':256,'normals_renormalized':False,
        'matrix_palette_assembly_qualified':False,'scene_loaded':False,'library_loaded':False,
        'game_started':False,'game_modified':False,'engine_validated':False,'geometry_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',required=True,type=Path);parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(SkinOracle(args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native skin audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
