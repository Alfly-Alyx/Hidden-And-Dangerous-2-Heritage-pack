#!/usr/bin/env python3
"""Compile our import-free solver and run invented offline x86 cases only."""
from copy import deepcopy
import argparse
import json
from pathlib import Path
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_modern_animation_bank import euler
from hand_pose_ik import two_bone,sub,norm,unit,cross,bend_plane_rotation
from model_transform import matmul,matvec,rotation,inverse,decompose,conjugate,native_affine
from native_hand_constraints import ArmSolverOracle,CODE_SHA

COMPILER=ROOT/'tmp/native-menu-toolchain/tcc/tcc.exe'
COMPILER_SHA='11b86934bb2833f57fa0453a605ca342aee9207e193faea9b973baa2b2b4c35b'
SOURCE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native/hand_constraints.c'
BASENAME='hand-constraints-v1.dll.disabled' # Stable ABI-1 basename, not quality/version promotion.


def reference_arm(values,side):
    bases=[[[values[12*b+3*i+j] for j in range(3)] for i in range(3)] for b in range(3)]
    points=[values[12*b+9:12*b+12] for b in range(3)]
    parent=[values[36+3*i:39+3*i] for i in range(3)]
    turn=[values[48+3*i:51+3*i] for i in range(3)];wrist=values[45:48];pole=values[57:60]
    upper=sub(points[1],points[0]);fore=sub(points[2],points[1])
    elbow=two_bone(points[0],wrist,pole,norm(upper),norm(fore))
    ut=sub(elbow,points[0]);ft=sub(wrist,elbow);normal=[side*v for v in unit(cross(ut,ft))]
    wanted=[matmul(bend_plane_rotation(upper,ut,normal),bases[0]),
            matmul(bend_plane_rotation(fore,ft,normal),bases[1]),matmul(turn,bases[2])]
    return [conjugate(decompose((matmul(inverse(parent if i==0 else wanted[i-1]),wanted[i]),[0,0,0]))[1])
            for i in range(3)]


def invented_values(*,turned=False,target=(.35,.1,.1),residual_scale=False):
    parent=rotation(euler([20,-15,30] if turned else [0,0,0]));shoulder=[.03,-.02,.01]
    upper=matmul(parent,rotation(euler([5,3,10])))
    fore=matmul(upper,rotation(euler([0,0,5])))
    hand=matmul(fore,rotation(euler([-80,0,0])))
    elbow=[a+b for a,b in zip(shoulder,matvec(upper,[.3,0,0]))]
    wrist=[a+b for a,b in zip(elbow,matvec(fore,[.25,0,0]))]
    values=[]
    for basis,point in ((upper,shoulder),(fore,elbow),(hand,wrist)):
        values.extend(v for row in basis for v in row);values.extend(point)
    values.extend(v for row in parent for v in row)
    values.extend(a+b for a,b in zip(shoulder,target))
    values.extend(v for row in rotation(euler([25,15,-35])) for v in row)
    values.extend([.01,.35,-.05])
    if residual_scale:
        for start in (0,12,24,36):
            for row in range(3):
                for col,factor in enumerate((1+2e-8,1-3e-8,1+1e-8)):
                    values[start+3*row+col]*=factor
    return values


def synthetic_audit(machine):
    tested=[];worst=0
    for turned,residual in ((False,False),(True,False),(False,True),(True,True)):
        for target in ((.35,.1,.1),(.12,.3,-.08),(-.25,.2,.1)):
            for side in (1,-1):
                values=invented_values(turned=turned,target=target,residual_scale=residual);saved=deepcopy(values)
                output,receipt=machine.solve(values,side)
                if receipt['status']!=0 or values!=saved:raise ValueError('Compiled invented arm failed or mutated inputs')
                expected=reference_arm(values,side);error=0
                for i in range(3):
                    a=native_affine([0,0,0],output[4*i:4*i+4],[1,1,1])[0]
                    b=native_affine([0,0,0],expected[i],[1,1,1])[0]
                    error=max(error,*(abs(a[r][c]-b[r][c]) for r in range(3) for c in range(3)))
                if error>5e-12:raise ValueError('Compiled invented rotations differ from independent reference')
                worst=max(worst,error);tested.append({'turned_parent':turned,'residual_scale':residual,'target':target,'side':side,
                                                    'rotation_matrix_error':error,'receipt':receipt})
    failures=[]
    for label,changes,kwargs,status in (
            ('short_input',{},dict(count=59),1),('short_output',{},dict(capacity=11),1),
            ('invalid_side',{},dict(side=0),1),('nan',{45:float('nan')},{},2),
            ('infinity',{45:float('inf')},{},2),('nonrotation',{0:2},{},3),
            ('unreachable',{45:2,46:2,47:2},{},4),
            ('singular_elbow_hint',{57:.03,58:-.02,59:.01},{},5)):
        values=invented_values()
        for index,value in changes.items():values[index]=value
        kwargs={'side':1,**kwargs};output,receipt=machine.solve(values,**kwargs)
        if output is not None or receipt['status']!=status:raise ValueError('Compiled invalid input was not rejected correctly')
        failures.append({'case':label,'receipt':receipt})
    return {'invented_valid_cases':len(tested),'invented_invalid_cases':len(failures),
            'max_rotation_matrix_error':worst,'valid':tested,'invalid':failures,
            'commercial_inputs_used':False,'game_started':False,'engine_hook_implemented':False}


def build(output):
    if output.exists():raise ValueError('Compiled laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local TinyCC compiler required; nothing downloaded')
    source=SOURCE.read_bytes();output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-DHD2_CONSTRAINTS_STANDALONE',
                    '-o',str(binary),str(SOURCE)],check=True,cwd=ROOT)
    if SOURCE.read_bytes()!=source:raise ValueError('Solver source changed during compilation')
    raw=binary.read_bytes();machine=ArmSolverOracle(raw);tests=synthetic_audit(machine)
    report={'schema_version':1,'scope':'private_original_compiled_arm_solver','runtime_status':'pending',
        'source_sha256':digest(source),'compiler_sha256':COMPILER_SHA,'compiled_sha256':digest(raw),'code_sha256':CODE_SHA,
        'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'synthetic_audit':tests,
        'operating_system_imports':0,'windows_startup_refuses_load':True,'windows_library_loaded':False,
        'source_or_game_patched':False,'game_started':False,'engine_hook_implemented':False,
        'pending_requirements':['live_pose_read_write_contract','post_blend_call_site','skeleton_identity_binding',
                                'lifetime_and_reentrancy','frame_budget','surface_contacts','gameplay_validation']}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output)
        print(json.dumps({'output':str(output),'compiled_sha256':report['compiled_sha256'],
            **{k:report['synthetic_audit'][k] for k in ('invented_valid_cases','invented_invalid_cases','max_rotation_matrix_error')},
            'engine_hook_implemented':False}));return 0
    except (OSError,ValueError,KeyError,ImportError,subprocess.CalledProcessError) as error:
        print('Compiled arm build refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
