#!/usr/bin/env python3
"""Build and privately exercise the original non-contiguous hand-pose bridge."""
import argparse
import json
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from build_native_hand_pipeline import SOURCES as PIPELINE_SOURCES,invented_case
from native_hand_scatter import HandScatterOracle,BINARY_SHA,CASES,WORK_SIZE

NATIVE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native'
SOURCES=[*PIPELINE_SOURCES,NATIVE/'hand_scatter.c']
HEADER=NATIVE/'hand_scatter.h'
BASENAME='hand-scatter-v1.dll.disabled'


def synthetic_audit(machine):
    rows=[]
    for count in (11,128):
        for turned in (False,True):
            for alignment in (0,4):
                row=machine.correct(*invented_case(count,turned),alignment=alignment)
                if row['status'] or row['native_write_operations']!=120:
                    raise ValueError('Valid scatter case refused or wrong write count')
                rows.append(row)
    statuses={'count':1,'role_count':1,'work_size':1,'null_model':1,'short_record':2,'overlap':2,'pointer_overflow':2,
        'parent_cycle':3,'parent_changed':3,'wrong_role':102,'late_kind':143,'late_callback':143,
        'unreachable':134,'zero_quaternion':114,
        **{key:4 for key in CASES if key.startswith('changed_')}}
    refused=[]
    for case in CASES[1:]:
        row=machine.correct(*invented_case(),case=case,alignment=4)
        if row['status']!=statuses[case] or row['native_write_operations']:
            raise ValueError('Scatter refusal mismatch: '+case)
        refused.append(row)
    return {'valid':rows,'refused':refused,'max_rotation_error':max(r['max_rotation_error'] for r in rows)}


def build(output):
    if output.exists():raise ValueError('Scatter laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local compiler required; nothing downloaded')
    sources={p.name:p.read_bytes() for p in [*SOURCES,HEADER]}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-DHD2_HAND_PIPELINE=1','-Wl,-image-base=0x2a000000',
        '-o',str(binary),*[str(p) for p in SOURCES]],check=True,cwd=ROOT)
    if any(p.read_bytes()!=sources[p.name] for p in [*SOURCES,HEADER]):raise ValueError('Scatter sources changed during build')
    raw=binary.read_bytes();tests=synthetic_audit(HandScatterOracle(raw))
    report={'schema_version':1,'scope':'private_original_scattered_hand_pose_bridge','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,'compiled_sha256':BINARY_SHA,
        'workspace_bytes':WORK_SIZE,'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'synthetic_audit':tests,
        'game_started':False,'windows_library_loaded':False,'client_hook_implemented':False,
        'live_model_discovery_implemented':False,'allocation_ownership_is_supplied':True}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output);audit=report['synthetic_audit']
        print(json.dumps({'output':str(output),'valid':len(audit['valid']),'refused':len(audit['refused']),
            'max_rotation_error':audit['max_rotation_error'],'sha256':BINARY_SHA},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError,subprocess.CalledProcessError) as error:
        print('Compiled hand scatter refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
