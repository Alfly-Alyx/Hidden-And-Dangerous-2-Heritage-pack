#!/usr/bin/env python3
"""Build and exercise the original combined numerical hand pipeline offline."""
from copy import deepcopy
import argparse
import json
import math
import struct
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_animation_bank import euler
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA,reference_arm
from build_native_hand_targets import reference_inputs
from ls3d_palette_oracle import local_matrix,product
from ls3d_math_oracle import f32
from model_transform import native_affine
from native_arm_pose_commit import reference_commit
from native_hand_pipeline import HandPipelineOracle,BINARY_SHA,WORK_SIZE

SOURCES=[ROOT/'experimental/RECONSTRUCTION_BACKLOG/native'/name for name in
         ('hand_pipeline.c','hand_targets.c','hand_constraints.c','arm_pose_commit.c')]
BASENAME='hand-pipeline-v1.dll.disabled'


def make_arena(data,offsets):
    arena=bytearray(65536)
    for pose,at in zip(data['poses'],offsets):
        for index,offset,count in ((0,0xb0,3),(3,0xc0,4),(7,0xd0,3)):
            struct.pack_into('<'+'f'*count,arena,at+offset,*pose[index:index+count])
        struct.pack_into('<I',arena,at+0xe0,8);struct.pack_into('<I',arena,at+0xf8,10)
    return bytes(arena)


def invented_case(count=11,turned=False):
    if count not in (11,128):raise ValueError('Unsupported invented pipeline count')
    poses=[[0,0,0,0,0,0,1,1,1,1] for _ in range(count)]
    poses[1][:3]=[.4,.1,.1];poses[2][:3]=[.35,-.1,.1]
    parents=[-1,0,0,-1,3,4,5,-1,7,8,9]+[-1]*(count-11)
    for i in (5,9):poses[i][0]=.3
    for i in (6,10):poses[i][0]=.25
    if turned:
        for i,angle in ((0,5),(3,12),(7,-12)):poses[i][3:7]=euler([0,0,angle])
    else:poses[0][3:7]=[0,0,0,-1]
    matrices=[]
    for p,parent in zip(poses,parents):
        p=[f32(v) for v in p];local=local_matrix({'position':p[:3],'rotation':p[3:7],'scale':p[7:]})
        matrices.append(local if parent==-1 else product(local,matrices[parent]))
    rest=[]
    for clavicle in (3,7):
        for i in (clavicle+1,clavicle+2,clavicle+3):
            m=matrices[i];rest.extend(m[r+4*c] for r in range(3) for c in range(3));rest.extend(m[12:15])
        m=matrices[clavicle];rest.extend(m[r+4*c] for r in range(3) for c in range(3))
    grip=[.01,0,0,1,0,0,0,1,0,0,0,1,.01,0,0]
    roles=[0,1,2,5,9,4,5,6,8,9,10];offsets=[i*0x200 for i in range(count)]
    data={'poses':poses,'parents':parents,'roles':roles[:5],'rest':rest,'grips':grip+grip}
    return data,make_arena(data,offsets),offsets,roles


def compare(data,before,after,offsets,roles):
    inputs=reference_inputs(data);replacements=[];error=0
    for side in range(2):
        expected=reference_arm(inputs[60*side:60*(side+1)],1 if side==0 else -1)
        for j,q in enumerate(expected):
            at=offsets[roles[5+3*side+j]];actual=list(struct.unpack_from('<4f',after,at+0xc0))
            a=native_affine([0,0,0],actual,[1,1,1])[0];b=native_affine([0,0,0],q,[1,1,1])[0]
            error=max(error,*(abs(a[r][c]-b[r][c]) for r in range(3) for c in range(3)))
            if actual[3]<0:raise ValueError('Pipeline failed to canonicalize quaternion')
            replacements.append(actual)
    arm_offsets=[offsets[i] for i in roles[5:]]
    snapshots=[list(struct.unpack_from('<4f',before,at+0xc0)) for at in arm_offsets]
    flags=[struct.unpack_from('<I',before,at+0xe0)[0] for at in arm_offsets]
    expected,status=reference_commit(before,arm_offsets,snapshots,replacements,flags)
    if status or after!=expected or not math.isfinite(error) or error>2e-6:
        raise ValueError('Compiled pipeline differs from independent rotations or byte contract')
    return error


def synthetic_audit(machine):
    valid=[];invalid=[]
    for count in (11,128):
        for turned in (False,True):
            data,arena,offsets,roles=invented_case(count,turned)
            for step in range(9):
                saved=deepcopy(data);after,receipt=machine.correct(data,arena,offsets,roles)
                if receipt['status'] or data!=saved:raise ValueError('Valid compiled pipeline failed')
                error=compare(data,arena,after,offsets,roles)
                valid.append({'count':count,'turned':turned,'retention_step':step,'max_rotation_error':error,'receipt':receipt})
                for i in roles[5:]:data['poses'][i][3:7]=list(struct.unpack_from('<4f',after,offsets[i]+0xc0))
                arena=after
    for label in ('short_roles','short_workspace','duplicate_offset','misaligned_offset','outside_offset','wrong_elbow_role',
                  'late_hierarchy','late_stale_pose','nonrest_clavicle','nan_grip','left_unreachable','right_unreachable',
                  'late_kind','late_flags','late_callback','late_zero_quaternion'):
        data,arena,offsets,roles=invented_case();kwargs={};status=0
        if label=='short_roles':kwargs={'role_count':10};status=1
        elif label=='short_workspace':kwargs={'work_bytes':WORK_SIZE-1};status=1
        elif label=='duplicate_offset':offsets[-1]=offsets[-2];status=2
        elif label=='misaligned_offset':offsets[-1]+=1;status=2
        elif label=='outside_offset':offsets[-1]=65536;status=2
        elif label=='wrong_elbow_role':roles[3]=8;data['roles']=roles[:5];status=2
        elif label=='late_hierarchy':data['parents'][10]=8;status=3
        elif label=='late_stale_pose':data['poses'][10][0]+=.001;status=4
        elif label=='nonrest_clavicle':data['poses'][7][3:7]=euler([0,0,30]);arena=make_arena(data,offsets);status=5
        elif label=='nan_grip':data['grips'][0]=float('nan');status=12
        elif label in ('left_unreachable','right_unreachable'):
            data['poses'][1 if label=='left_unreachable' else 2][0]=3;arena=make_arena(data,offsets)
            status=24 if label=='left_unreachable' else 34
        elif label in ('late_kind','late_flags','late_callback'):
            mutable=bytearray(arena);at=offsets[-1]+(0xf8 if label=='late_kind' else 0xe0)
            struct.pack_into('<I',mutable,at,1 if label=='late_kind' else 0x1208 if label=='late_callback' else 0)
            arena=bytes(mutable);status=43
        elif label=='late_zero_quaternion':data['poses'][10][3:7]=[0,0,0,0];arena=make_arena(data,offsets);status=14
        after,receipt=machine.correct(data,arena,offsets,roles,**kwargs)
        if receipt['status']!=status or after!=arena:raise ValueError('Pipeline invalid case failed: '+label)
        if label in ('left_unreachable','right_unreachable'):
            expected={'Hd2CorrectHandPose':1,'Hd2PrepareArms':1,'Hd2SolveArm':1 if label=='left_unreachable' else 2}
            if receipt['compiled_calls']!=expected:raise ValueError('Pipeline crossed the failing arm boundary')
        invalid.append({'case':label,'receipt':receipt})
    return {'valid':valid,'invalid':invalid,'max_rotation_error':max(r['max_rotation_error'] for r in valid),
            'commercial_inputs_used':False,'game_started':False}


def build(output):
    if output.exists():raise ValueError('Pipeline laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local TinyCC compiler required; nothing downloaded')
    sources={p.name:p.read_bytes() for p in SOURCES};output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-DHD2_HAND_PIPELINE=1','-Wl,-image-base=0x26000000',
        '-o',str(binary),*[str(p) for p in SOURCES]],check=True,cwd=ROOT)
    if any(p.read_bytes()!=sources[p.name] for p in SOURCES):raise ValueError('Pipeline sources changed during compilation')
    raw=binary.read_bytes();tests=synthetic_audit(HandPipelineOracle(raw))
    report={'schema_version':1,'scope':'private_original_compiled_hand_pipeline','runtime_status':'pending',
        'sources':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,'compiled_sha256':BINARY_SHA,
        'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'synthetic_audit':tests,
        'operating_system_imports':0,'windows_library_loaded':False,'game_started':False,
        'client_hook_implemented':False,'live_model_binding_implemented':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output);audit=report['synthetic_audit']
        print(json.dumps({'output':str(output),'compiled_sha256':report['compiled_sha256'],
            'valid_cases':len(audit['valid']),'invalid_cases':len(audit['invalid']),
            'max_rotation_error':audit['max_rotation_error']}));return 0
    except (OSError,ValueError,KeyError,ImportError,subprocess.CalledProcessError) as error:
        print('Compiled hand pipeline refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
