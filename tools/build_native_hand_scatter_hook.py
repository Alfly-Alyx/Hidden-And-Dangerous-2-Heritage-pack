#!/usr/bin/env python3
"""Build the disabled scatter callback and run only original invented probes."""
from copy import deepcopy
import argparse
import json
import struct
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from build_native_hand_pipeline import invented_case,compare
from build_native_hand_scatter import SOURCES as SCATTER_SOURCES,HEADER,NATIVE
from native_hand_scatter_hook import HandScatterHookOracle,BINARY_SHA

SOURCES=[*SCATTER_SOURCES,NATIVE/'hand_scatter_hook.c',NATIVE/'hand_hook.S']
PROBE_SOURCES=[NATIVE/'hand_scatter_hook_native_probe.c',NATIVE/'hand_hook_native_probe.S']
BASENAME='hand-scatter-hook-v1.dll.disabled'
PROBE_NAME='hand-scatter-hook-native-probe.exe'
PROBE_MESSAGE='PASS: 8 scatter-adapter cases, separate heap records, full 108-byte x87 state and refusal guards'
EXPECTED_CALLS={'Hd2OnModelHandPose':1,'Hd2CorrectScatteredHandPose':1,'Hd2CorrectHandPose':1,
                'Hd2PrepareArms':1,'Hd2SolveArm':2,'Hd2CommitArms':1}


def restore_arena(machine,blocks,offsets,arena):
    result=bytearray(arena)
    for i,at in enumerate(offsets):
        alignment=machine.pointers[i]-machine.pages[i]
        result[at:at+0x170]=blocks[i][alignment:alignment+0x170]
    return bytes(result)


def synthetic_audit(machine):
    valid=[];refused=[];registration=[]
    for count in (11,128):
        for turned in (False,True):
            for alignment in (0,4):
                data,arena,offsets,roles=invented_case(count,turned)
                machine.seed(data,arena,offsets,roles,alignment=alignment)
                if machine.configure():raise ValueError('Scatter adapter valid registration failed')
                for frame in range(4):
                    machine.uc.mem_write(machine.pointers[1]+0xb0,struct.pack('<f',.4-frame*.003))
                    observed=deepcopy(data)
                    for i,pointer in enumerate(machine.pointers):
                        raw=bytes(machine.uc.mem_read(pointer,0x170))
                        observed['poses'][i]=list(struct.unpack_from('<3f',raw,0xb0)+struct.unpack_from('<4f',raw,0xc0)+struct.unpack_from('<3f',raw,0xd0))
                    before,after,receipt=machine.frame()
                    if receipt['status'] or not receipt['attempted'] or receipt['compiled_calls']!=EXPECTED_CALLS:
                        raise ValueError('Scatter adapter complete callback failed')
                    error=compare(observed,restore_arena(machine,before,offsets,arena),restore_arena(machine,after,offsets,arena),offsets,roles)
                    valid.append({'count':count,'turned':turned,'alignment':alignment,'frame':frame,'max_rotation_error':error,'receipt':receipt})
                if machine.configure(False):raise ValueError('Scatter adapter valid unregister failed')
    for case in ('foreign_model','unregistered_poisoned_context','busy','precision','invalidated_count',
                 'late_kind','late_callback','late_parent','late_quaternion','right_unreachable'):
        machine.seed(*invented_case(),alignment=4)
        if machine.configure():raise ValueError('Scatter refusal registration failed')
        kwargs={};attempted=True;status=0;calls=dict(EXPECTED_CALLS)
        if case=='foreign_model':kwargs={'other_model':True};attempted=False
        elif case=='unregistered_poisoned_context':
            if machine.configure(False):raise ValueError('Scatter unregister failed')
            machine.uc.mem_write(machine.CONTEXT+4,struct.pack('<I',0xffffffff));attempted=False
        elif case=='busy':machine.uc.mem_write(machine.CONTEXT+40,struct.pack('<I',1));attempted=False
        elif case=='precision':kwargs={'control':0x37f};status=6
        elif case=='invalidated_count':machine.uc.mem_write(machine.CONTEXT+8,struct.pack('<I',129));status=7
        elif case in ('late_kind','late_callback'):
            at=0xf8 if case=='late_kind' else 0xe0
            machine.uc.mem_write(machine.pointers[10]+at,struct.pack('<I',1 if case=='late_kind' else 0x1208));status=143
        elif case=='late_parent':
            machine.uc.mem_write(machine.pointers[10]+0x108,bytes(4));status=3
            calls={k:v for k,v in calls.items() if k in ('Hd2OnModelHandPose','Hd2CorrectScatteredHandPose')}
        elif case=='late_quaternion':
            machine.uc.mem_write(machine.pointers[10]+0xc0,bytes(16));status=114
            calls.pop('Hd2SolveArm');calls.pop('Hd2CommitArms')
        elif case=='right_unreachable':
            machine.uc.mem_write(machine.pointers[2]+0xb0,struct.pack('<f',3));status=134;calls.pop('Hd2CommitArms')
        if not attempted or status in (6,7):calls={'Hd2OnModelHandPose':1}
        before,after,receipt=machine.frame(**kwargs)
        if before!=after or receipt['status']!=status or receipt['attempted']!=attempted or receipt['compiled_calls']!=calls:
            raise ValueError('Scatter adapter refusal failed: '+case)
        refused.append({'case':case,'receipt':receipt})
        if case=='busy':
            if machine.configure(False)!=1:raise ValueError('Scatter busy unregister allowed')
            machine.uc.mem_write(machine.CONTEXT+40,bytes(4))
        if machine.configure(False):raise ValueError('Scatter refusal cleanup failed')
    for offset,value in ((8,129),(20,10),(36,61807),(40,1)):
        machine.seed(*invented_case());machine.uc.mem_write(machine.CONTEXT+offset,struct.pack('<I',value))
        status=machine.configure()
        if status!=2:raise ValueError('Scatter invalid registration allowed')
        registration.append({'offset':offset,'value':value,'status':status})
    return {'valid':valid,'refused':refused,'registration_refusals':registration,
            'max_rotation_error':max(r['max_rotation_error'] for r in valid)}


def run_probe(path):
    if path.name!=PROBE_NAME:raise ValueError('Unreviewed original scatter console probe')
    result=subprocess.run([str(path)],check=True,capture_output=True,text=True,timeout=30,cwd=ROOT)
    if result.stdout.strip()!=PROBE_MESSAGE or result.stderr.strip():raise ValueError('Scatter console probe did not confirm success')
    return {'message':result.stdout.strip(),'exit_code':result.returncode,'all_108_x87_bytes_preserved':True,
            'separate_heap_records_checked':True,'game_started':False}


def build(output):
    if output.exists():raise ValueError('Scatter adapter laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local compiler required; nothing downloaded')
    inputs=[*SOURCES,HEADER,NATIVE/'hand_scatter_context.h',*PROBE_SOURCES];sources={p.name:p.read_bytes() for p in inputs}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-DHD2_HAND_PIPELINE=1','-Wl,-image-base=0x2c000000',
        '-o',str(binary),*[str(p) for p in SOURCES]],check=True,cwd=ROOT)
    raw=binary.read_bytes();tests=synthetic_audit(HandScatterHookOracle(raw));probe=output/PROBE_NAME
    subprocess.run([str(COMPILER),'-DHD2_HAND_PIPELINE=1','-o',str(probe),*[str(p) for p in [*SOURCES,*PROBE_SOURCES]]],check=True,cwd=ROOT)
    native=run_probe(probe)
    if any(p.read_bytes()!=sources[p.name] for p in inputs):raise ValueError('Scatter adapter sources changed during build')
    report={'schema_version':1,'scope':'private_original_scattered_hand_adapter','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,'compiled_sha256':BINARY_SHA,
        'files':{p.name:{'size':len(p.read_bytes()),'sha256':digest(p.read_bytes())} for p in (binary,probe)},
        'synthetic_audit':tests,'native_probe':native,'game_started':False,'windows_library_loaded':False,
        'client_hook_installed':False,'live_model_discovery_implemented':False,'allocation_ownership_is_supplied':True}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output);audit=report['synthetic_audit']
        print(json.dumps({'output':str(output),'valid':len(audit['valid']),'refused':len(audit['refused']),
            'registration_refusals':len(audit['registration_refusals']),'native_probe':report['native_probe'],
            'max_rotation_error':audit['max_rotation_error'],'sha256':BINARY_SHA},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError,subprocess.CalledProcessError) as error:
        print('Compiled scatter hand adapter refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
