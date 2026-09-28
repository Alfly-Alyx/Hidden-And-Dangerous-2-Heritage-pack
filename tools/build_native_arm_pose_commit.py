#!/usr/bin/env python3
"""Build original disabled commit component and audit invented private trees."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_animation_bank import euler
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from native_arm_pose_commit import PersistentArmCommitOracle,BINARY_SHA
from ls3d_math_oracle import verify_library,DLL_SHA

SOURCE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native/arm_pose_commit.c'
BASENAME='arm-pose-commit-v1.dll.disabled'


def invented_case(parents):
    poses=[{'position':[.025,.01,.005],'rotation':euler([2*i,3,1]),'scale':[1,1,1],'parent':parent}
           for i,parent in enumerate(parents)]
    identity=[float(i%5==0) for i in range(16)]
    return poses,[identity]*len(poses),[1,2,3,5,6,7],[euler([5*i,10,7]) for i in range(6)]


def synthetic_audit(machine):
    trees=[list(range(-1,8)),[-1]*9,[-1,0,1,2,3,0,5,6,7]]
    valid=[machine.exercise(*invented_case(parents)) for parents in trees]
    invalid=[machine.exercise(*invented_case(trees[2]),failure=failure) for failure in
             ('late_snapshot','late_flags','late_kind','late_quaternion','duplicate','range','alignment','callback')]
    if any(r['committed_rotations']!=6 or r['local_rotations_rebuilt']!=6 or r['owner_change_counter']!=6 for r in valid):
        raise ValueError('Unexpected synthetic pose commit or refresh count')
    return {'valid_cases':valid,'invalid_cases':invalid,'max_matrix_error':max(r['max_matrix_error'] for r in valid),
            'commercial_pose_inputs_used':False,'compiled_commit_checked':True,'game_started':False}


def build(output,library):
    if output.exists():raise ValueError('Commit laboratory already exists')
    verify_library(library)
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local TinyCC compiler required; nothing downloaded')
    source=SOURCE.read_bytes();output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-Wl,-image-base=0x22000000',
                    '-o',str(binary),str(SOURCE)],check=True,cwd=ROOT)
    if source!=SOURCE.read_bytes():raise ValueError('Commit source changed during build')
    raw=binary.read_bytes();tests=synthetic_audit(PersistentArmCommitOracle(library,raw))
    report={'schema_version':1,'scope':'original_compiled_pose_commit_and_private_native_cache_refresh',
            'runtime_status':'pending','source_sha256':digest(source),'compiler_sha256':COMPILER_SHA,
            'library_sha256':DLL_SHA,'compiled_sha256':BINARY_SHA,'synthetic_audit':tests,
            'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},
            'native_library_loaded':False,'client_hook_implemented':False,'game_started':False,
            'game_or_source_modified':False,'live_pointer_discovery_implemented':False,
            'cross_thread_atomicity_implemented':False,'owning_visual_bounds_evaluated':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output,(args.game/'LS3DF.dll').read_bytes())
        print(json.dumps({'output':str(output),'compiled_sha256':report['compiled_sha256'],
            'valid_cases':len(report['synthetic_audit']['valid_cases']),
            'invalid_cases':len(report['synthetic_audit']['invalid_cases']),
            'max_matrix_error':report['synthetic_audit']['max_matrix_error']}));return 0
    except (ValueError,OSError,KeyError,ImportError,subprocess.CalledProcessError) as error:
        print('Original pose commit build refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
