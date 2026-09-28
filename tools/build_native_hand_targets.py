#!/usr/bin/env python3
"""Build original compiled target preparation and test invented buffers."""
from copy import deepcopy
import argparse
import json
import math
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_animation_bank import euler
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA,invented_values
from ls3d_palette_oracle import local_matrix,product
from ls3d_math_oracle import f32
from model_transform import rotation,matmul,matvec
from native_hand_targets import TargetPreparationOracle,BINARY_SHA

SOURCE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native/hand_targets.c'
BASENAME='hand-targets-v1.dll.disabled'


def invented_data(count=9,turned=False):
    poses=[[.012,.006,-.004,*euler([2*(i%4),-3,5] if turned else [0,0,0]),1,1,1] for i in range(count)]
    poses[0][7:]=[.9999998,1,1.0000001]
    if not turned:poses[0][3:7]=[1e-7,0,0,1] # Native identity shortcut.
    grip=[.02,.01,0,*[v for row in rotation(euler([20,10,-15])) for v in row],.03,-.01,.005]
    return {'poses':poses,'parents':list(range(-1,count-1)),'roles':[0,1,2,3,4],
            'rest':invented_values()[:45]+invented_values(turned=True)[:45],'grips':grip+grip}


def reference_inputs(data):
    matrices=[]
    for row,parent in zip(data['poses'],data['parents']):
        row=[f32(v) for v in row] # Match the float32 ABI, not the author's Python doubles.
        local=local_matrix({'position':row[:3],'rotation':row[3:7],'scale':row[7:]})
        matrices.append(local if parent==-1 else product(local,matrices[parent]))
    roles=data['roles'];held=matrices[roles[0]];basis=[[held[i+4*j] for j in range(3)] for i in range(3)]
    result=[]
    for side in range(2):
        grip=data['grips'][15*side:15*(side+1)]
        turn=matmul(basis,[grip[3+3*i:6+3*i] for i in range(3)])
        contact=matvec(basis,grip[:3]);palm=matvec(turn,grip[12:])
        target=[a+b-c for a,b,c in zip(matrices[roles[1+side]][12:15],contact,palm)]
        result.extend(data['rest'][45*side:45*(side+1)]+target+[v for row in turn for v in row]
                      +matrices[roles[3+side]][12:15])
    return result


def synthetic_audit(machine):
    valid=[];invalid=[]
    for count in (5,9,64,128):
        for turned in (False,True):
            data=invented_data(count,turned);saved=deepcopy(data);expected=reference_inputs(data)
            actual,receipt=machine.prepare(data)
            if receipt['status']!=0 or data!=saved:raise ValueError('Valid target preparation failed')
            error=max(abs(a-b) for a,b in zip(actual,expected))
            if not math.isfinite(error) or error>2e-6:raise ValueError('Compiled target preparation differs')
            valid.append({'count':count,'turned':turned,'max_input_error':error,'receipt':receipt})
    cases=[('nan_pose',lambda d:d['poses'][0].__setitem__(0,float('nan')),{},2),
           ('infinite_pose',lambda d:d['poses'][0].__setitem__(0,float('inf')),{},2),
           ('zero_scale',lambda d:d['poses'][0].__setitem__(7,0),{},2),
           ('zero_quaternion',lambda d:d['poses'][0].__setitem__(slice(3,7),[0,0,0,0]),{},4),
           ('forward_parent',lambda d:d['parents'].__setitem__(0,0),{},3),
           ('duplicate_role',lambda d:d['roles'].__setitem__(4,0),{},3),
           ('outside_role',lambda d:d['roles'].__setitem__(4,9),{},3),
           ('nan_rest',lambda d:d['rest'].__setitem__(0,float('nan')),{},2),
           ('oversized_grip',lambda d:d['grips'].__setitem__(0,11),{},2),
           ('output_capacity',lambda d:None,{'capacity':119},1),
           ('short_workspace',lambda d:None,{'short_workspace':True},1),
           ('large_count',lambda d:None,{'invalid_count':True},1),
           ('composed_overflow',lambda d:[row.__setitem__(0,9) for row in d['poses']],{},5)]
    for label,mutate,kwargs,status in cases:
        data=invented_data();mutate(data);actual,receipt=machine.prepare(data,**kwargs)
        if actual is not None or receipt['status']!=status:raise ValueError('Invalid target preparation accepted')
        invalid.append({'case':label,'receipt':receipt})
    return {'valid_cases':valid,'invalid_cases':invalid,'max_input_error':max(r['max_input_error'] for r in valid),
            'commercial_inputs_used':False,'game_started':False}


def build(output):
    if output.exists():raise ValueError('Target preparation laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local TinyCC compiler required; nothing downloaded')
    source=SOURCE.read_bytes();output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-Wl,-image-base=0x24000000',
                    '-o',str(binary),str(SOURCE)],check=True,cwd=ROOT)
    if SOURCE.read_bytes()!=source:raise ValueError('Target preparation source changed during compilation')
    raw=binary.read_bytes();tests=synthetic_audit(TargetPreparationOracle(raw))
    report={'schema_version':1,'scope':'private_original_compiled_hand_targets','runtime_status':'pending',
        'source_sha256':digest(source),'compiler_sha256':COMPILER_SHA,'compiled_sha256':BINARY_SHA,
        'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'synthetic_audit':tests,
        'operating_system_imports':0,'windows_library_loaded':False,'game_started':False,
        'client_hook_implemented':False,'live_model_binding_implemented':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output)
        print(json.dumps({'output':str(output),'compiled_sha256':report['compiled_sha256'],
            'valid_cases':len(report['synthetic_audit']['valid_cases']),
            'invalid_cases':len(report['synthetic_audit']['invalid_cases']),
            'max_input_error':report['synthetic_audit']['max_input_error']}));return 0
    except (OSError,ValueError,KeyError,ImportError,subprocess.CalledProcessError) as error:
        print('Compiled hand targets refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
