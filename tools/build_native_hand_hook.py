#!/usr/bin/env python3
"""Build an original disabled hand adapter; emulate and run invented probes only."""
from copy import deepcopy
import argparse
import json
import struct
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from build_native_hand_pipeline import SOURCES as PIPELINE_SOURCES,invented_case,compare
from native_hand_hook import HandHookOracle,BINARY_SHA

NATIVE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native'
SOURCES=[*PIPELINE_SOURCES,NATIVE/'hand_hook.c',NATIVE/'hand_hook.S']
PROBE_SOURCES=[NATIVE/n for n in ('hand_fpu_probe.c','hand_fpu_probe.S','hand_hook_native_probe.c','hand_hook_native_probe.S')]
BASENAME='hand-hook-v1.dll.disabled'
EXPECTED_CALLS={'Hd2OnModelHandPose':1,'Hd2CorrectHandPose':1,'Hd2PrepareArms':1,'Hd2SolveArm':2,'Hd2CommitArms':1}
PROBE_MESSAGES={
    'hand-fpu-probe.exe':'PASS: all 108 x87 state bytes preserved, including exception addresses',
    'hand-hook-native-probe.exe':'PASS: 6 actual-adapter cases, full 108-byte x87 state, model forwarding and arena refusal'}


def current_data(machine,data,offsets):
    result=deepcopy(data)
    for i,at in enumerate(offsets):
        raw=bytes(machine.uc.mem_read(machine.ARENA+at,0x170))
        result['poses'][i]=list(struct.unpack_from('<3f',raw,0xb0)+struct.unpack_from('<4f',raw,0xc0)
                                +struct.unpack_from('<3f',raw,0xd0))
    return result


def synthetic_audit(machine):
    valid=[];refusals=[];registration=[]
    for count in (11,128):
        for turned in (False,True):
            data,arena,offsets,roles=invented_case(count,turned);machine.seed(data,arena,offsets,roles)
            if machine.configure()!=0:raise ValueError('Valid hook registration refused')
            for step in range(4):
                # A supplied animated marker changes in the existing arena.
                # The immutable source buffer deliberately retains the old pose.
                machine.uc.mem_write(machine.ARENA+offsets[1]+0xb0,struct.pack('<f',.4-step*.003))
                before=bytes(machine.uc.mem_read(machine.ARENA,65536));observed=current_data(machine,data,offsets)
                after,receipt=machine.frame()
                if not receipt['attempted'] or receipt['status'] or receipt['compiled_calls']!=EXPECTED_CALLS:
                    raise ValueError('Valid compiled adapter did not run its complete chain')
                expected=struct.pack('<'+'f'*(count*10),*(v for p in observed['poses'] for v in p))
                if bytes(machine.uc.mem_read(machine.POSES,count*40))!=expected:
                    raise ValueError('Adapter snapshot is not the current arena pose')
                error=compare(observed,before,after,offsets,roles)
                valid.append({'count':count,'turned':turned,'step':step,'max_rotation_error':error,'receipt':receipt})
            if machine.configure(False)!=0:raise ValueError('Hook failed to unregister')
    for label in ('foreign_model','unregistered','busy','precision','invalidated_count','right_unreachable',
                  'late_kind','late_callback','late_quaternion','unregistered_poisoned_context'):
        data,arena,offsets,roles=invented_case();machine.seed(data,arena,offsets,roles)
        if machine.configure():raise ValueError('Refusal fixture registration failed')
        kwargs={};status=0;attempted=True;calls=dict(EXPECTED_CALLS)
        if label=='foreign_model':kwargs={'other_model':True};attempted=False
        elif label in ('unregistered','unregistered_poisoned_context'):
            if machine.configure(False):raise ValueError('Refusal fixture failed to unregister')
            attempted=False
            if label.endswith('poisoned_context'):machine.uc.mem_write(machine.CONTEXT+4,struct.pack('<I',0xffffffff))
        elif label=='busy':machine.uc.mem_write(machine.CONTEXT+52,struct.pack('<I',1));attempted=False
        elif label=='precision':kwargs={'control':0x37f};status=6
        elif label=='invalidated_count':machine.uc.mem_write(machine.CONTEXT+16,struct.pack('<I',129));status=7
        elif label=='right_unreachable':
            machine.uc.mem_write(machine.ARENA+offsets[2]+0xb0,struct.pack('<f',3));status=34;calls.pop('Hd2CommitArms')
        elif label in ('late_kind','late_callback'):
            at=offsets[-1]+(0xf8 if label=='late_kind' else 0xe0)
            machine.uc.mem_write(machine.ARENA+at,struct.pack('<I',1 if label=='late_kind' else 0x1208));status=43
        elif label=='late_quaternion':
            machine.uc.mem_write(machine.ARENA+offsets[-1]+0xc0,bytes(16));status=14
            calls.pop('Hd2SolveArm');calls.pop('Hd2CommitArms')
        if not attempted or status in (6,7):calls={'Hd2OnModelHandPose':1}
        before=bytes(machine.uc.mem_read(machine.ARENA,65536));after,receipt=machine.frame(**kwargs)
        if after!=before or receipt['attempted'] is not attempted or receipt['status']!=status or receipt['compiled_calls']!=calls:
            raise ValueError('Adapter refusal failed: '+label)
        refusals.append({'case':label,'receipt':receipt})
        if label=='busy':
            if machine.configure(False)!=1:raise ValueError('Busy adapter allowed unregister')
            machine.uc.mem_write(machine.CONTEXT+52,bytes(4))
        if machine.configure(False):raise ValueError('Refusal fixture failed cleanup')
    for field,value in ((16,129),(28,10),(48,7535),(52,1)):
        machine.seed(*invented_case());machine.uc.mem_write(machine.CONTEXT+field,struct.pack('<I',value))
        status=machine.configure()
        if status!=2:raise ValueError('Invalid context registration succeeded')
        registration.append({'context_offset':field,'value':value,'status':status})
    return {'valid':valid,'refusals':refusals,'registration_refusals':registration,
        'max_rotation_error':max(row['max_rotation_error'] for row in valid),
        'emulator_restore_limitations':machine.emulator_restore_limitations[:],
        'commercial_inputs_used':False,'native_refresh_executed':False,'game_started':False}


def run_console_probe(binary):
    if binary.name not in PROBE_MESSAGES:raise ValueError('Unreviewed native console probe')
    process=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=30,cwd=ROOT)
    if process.stderr or process.stdout.strip()!=PROBE_MESSAGES[binary.name]:raise ValueError('Native probe did not confirm success')
    return {'size':binary.stat().st_size,'sha256':digest(binary.read_bytes()),'stdout':process.stdout.strip(),
            'exit_code':process.returncode,'standalone_original_console_executed':True,'game_started':False}


def build(output):
    if output.exists():raise ValueError('Hand hook laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local TinyCC compiler required; nothing downloaded')
    sources={p.name:p.read_bytes() for p in [*SOURCES,*PROBE_SOURCES]}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-DHD2_HAND_PIPELINE=1','-Wl,-image-base=0x28000000',
        '-o',str(binary),*[str(p) for p in SOURCES]],check=True,cwd=ROOT)
    raw=binary.read_bytes();audit=synthetic_audit(HandHookOracle(raw));probes={}
    for name,inputs in (
        ('hand-fpu-probe.exe',[NATIVE/'hand_fpu_probe.c',NATIVE/'hand_fpu_probe.S']),
        ('hand-hook-native-probe.exe',[NATIVE/'hand_hook_native_probe.c',NATIVE/'hand_hook_native_probe.S',*SOURCES])):
        exe=output/name
        subprocess.run([str(COMPILER),'-DHD2_HAND_PIPELINE=1','-o',str(exe),*[str(p) for p in inputs]],check=True,cwd=ROOT)
        probes[name]=run_console_probe(exe)
    if any(p.read_bytes()!=sources[p.name] for p in [*SOURCES,*PROBE_SOURCES]):raise ValueError('Adapter source changed during build')
    report={'schema_version':1,'scope':'private_original_hand_adapter','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,
        'compiled_sha256':BINARY_SHA,'binary_size':len(raw),'synthetic_audit':audit,'host_cpu_probes':probes,
        'complete_x87_roundtrip_verified_on_host_cpu':True,'adapter_x87_state_verified_on_host_cpu':True,
        'dll_operating_system_imports':0,'windows_dll_loaded':False,'game_started':False,
        'client_hook_installed':False,'live_model_binding_implemented':False,'native_refresh_executed':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output);audit=report['synthetic_audit']
        print(json.dumps({'output':str(output),'compiled_sha256':report['compiled_sha256'],
            'valid_cases':len(audit['valid']),'callback_refusals':len(audit['refusals']),
            'registration_refusals':len(audit['registration_refusals']),'max_rotation_error':audit['max_rotation_error'],
            'native_probes':{k:v['stdout'] for k,v in report['host_cpu_probes'].items()}}));return 0
    except (OSError,ValueError,KeyError,ImportError,subprocess.CalledProcessError,subprocess.TimeoutExpired) as error:
        print('Compiled hand adapter refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
