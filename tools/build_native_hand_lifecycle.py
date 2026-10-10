#!/usr/bin/env python3
"""Compile the explicit retirement guard and pair it with the pinned hand registry."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from build_native_hand_pipeline import invented_case
from native_hand_lifecycle import HandLifecycleOracle,BINARY_SHA,STATE_SIZE,CONFIGURE
from native_hand_scatter_hook import ACTIVE,BINARY_SHA as HOOK_SHA

NATIVE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native'
SOURCE=NATIVE/'hand_lifecycle.c'
HEADERS=[NATIVE/name for name in ('hand_lifecycle.h','hand_scatter_context.h','hand_scatter.h')]
BASENAME='hand-lifecycle-v1.dll.disabled'
REFUSALS={'state_size':2,'null_context':2,'unaligned_context':2,'null_configure':2,'busy_new':3,
    'generation_exhausted':4,'occupied':1,'event_size':3,'event_kind':3,'missing_node':3,
    'release_extra_node':3,'changed_count':3,'busy_current':2,'inconsistent_state':3}


def seed(machine,count=11):
    if struct.unpack('<I',machine.uc.mem_read(ACTIVE,4))[0]:raise ValueError('Retire lifecycle before reseeding')
    machine.seed(*invented_case(count),alignment=4)
    machine.uc.mem_write(machine.STATE,bytes(STATE_SIZE)+b'Z'*(4096-STATE_SIZE))
    if machine.invoke_guard(b'Hd2HandLifecycleSize',[])!=STATE_SIZE:raise ValueError('Lifecycle state ABI differs')


def valid_case(machine,count,kind,target,index=0):
    seed(machine,count)
    if machine.watch() or machine.state()!=(machine.CONTEXT,CONFIGURE,1,0,0):raise ValueError('Lifecycle watch failed')
    model=machine.MODEL if target=='model' else machine.pointers[index] if target=='node' and kind==3 else 0xdeadbeec
    node=0 if kind==3 else machine.pointers[index] if target=='node' else 0xdead0000
    before=bytes(machine.uc.mem_read(machine.STATE,STATE_SIZE));matched=target!='foreign'
    # No native object may be read by the guard, even on a matching node event.
    for page in machine.pages:machine.uc.mem_protect(page,4096,0)
    try:status=machine.event(model,node,kind)
    finally:
        for page in machine.pages:machine.uc.mem_protect(page,4096,machine.uni.UC_PROT_READ|machine.uni.UC_PROT_WRITE)
    calls=dict(machine.calls)
    if status!=int(matched):raise ValueError('Lifecycle event match differs')
    if matched:
        if machine.state()!=(0,0,1,kind,1) or struct.unpack('<I',machine.uc.mem_read(ACTIVE,4))[0]:
            raise ValueError('Lifecycle did not retire both registries before forwarding')
        snapshot=machine.state()
        if machine.event(model,node,kind) or machine.state()!=snapshot:raise ValueError('Repeated inactive event changed state')
        probe=machine.retired_callback_probe()
        if machine.watch() or machine.state()!=(machine.CONTEXT,CONFIGURE,2,0,1):raise ValueError('Explicit lifecycle rearm failed')
    else:
        if bytes(machine.uc.mem_read(machine.STATE,STATE_SIZE))!=before or calls!={'Hd2BeforeHandModelChange':1}:
            raise ValueError('Unrelated lifecycle event changed registry')
        probe=None
    if machine.event(machine.MODEL,0,3)!=1:raise ValueError('Lifecycle cleanup refused')
    return {'nodes':count,'event':kind,'target':target,'node_index':index if target=='node' else None,
        'status':status,'compiled_calls':calls,'native_objects_cpu_inaccessible_during_event':True,
        'retired_callback':probe,'native_lifecycle_event_is_host_supplied':True,'native_mutation_forwarded':False}


def refused_case(machine,case):
    seed(machine)
    if case not in REFUSALS:raise ValueError('Unreviewed lifecycle refusal')
    name=b'Hd2WatchHandContext';args=[machine.STATE,STATE_SIZE,machine.CONTEXT,CONFIGURE]
    if case=='state_size':args[1]-=1
    elif case=='null_context':args[2]=0
    elif case=='unaligned_context':args[2]+=1
    elif case=='null_configure':args[3]=0
    elif case=='busy_new':machine.uc.mem_write(machine.CONTEXT+40,struct.pack('<I',1))
    elif case=='generation_exhausted':machine.uc.mem_write(machine.STATE+8,struct.pack('<I',0xffffffff))
    else:
        if machine.watch():raise ValueError('Lifecycle refusal setup failed')
        if case!='occupied':
            name=b'Hd2BeforeHandModelChange';args=[machine.STATE,STATE_SIZE,machine.MODEL,machine.pointers[0],1]
            if case=='event_size':args[1]-=1
            elif case=='event_kind':args[4]=4
            elif case=='missing_node':args[3]=0
            elif case=='release_extra_node':args[4]=3
            elif case=='changed_count':machine.uc.mem_write(machine.CONTEXT+8,struct.pack('<I',129))
            elif case=='busy_current':machine.uc.mem_write(machine.CONTEXT+40,struct.pack('<I',1))
            elif case=='inconsistent_state':machine.uc.mem_write(machine.STATE+4,bytes(4))
    before=[bytes(machine.uc.mem_read(at,size)) for at,size in ((machine.STATE,4096),(machine.CONTEXT,4096),(ACTIVE,4))]
    status=machine.invoke_guard(name,args);calls=dict(machine.calls)
    after=[bytes(machine.uc.mem_read(at,size)) for at,size in ((machine.STATE,4096),(machine.CONTEXT,4096),(ACTIVE,4))]
    if status!=REFUSALS[case] or after!=before:raise ValueError('Lifecycle refusal changed watched state: '+case)
    machine.uc.mem_write(machine.CONTEXT+8,struct.pack('<I',11));machine.uc.mem_write(machine.CONTEXT+40,bytes(4))
    if machine.state()[0]:
        if case=='inconsistent_state':machine.uc.mem_write(machine.STATE+4,struct.pack('<I',CONFIGURE))
        if machine.event(machine.MODEL,0,3)!=1:raise ValueError('Lifecycle refusal cleanup failed')
    return {'case':case,'status':status,'compiled_calls':calls,'failed_state_unchanged':True,'native_mutation_forwarded':False}


def synthetic_audit(machine):
    valid=[]
    for count in (11,128):
        for kind in (1,2,3):
            valid.append(valid_case(machine,count,kind,'model'))
            for index in (0,count//2,count-1):valid.append(valid_case(machine,count,kind,'node',index))
            valid.append(valid_case(machine,count,kind,'foreign'))
    return {'valid':valid,'refused':[refused_case(machine,case) for case in REFUSALS]}


def build(output,hook):
    if output.exists():raise ValueError('Lifecycle laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local compiler required; nothing downloaded')
    hook_raw=hook.read_bytes()
    if digest(hook_raw)!=HOOK_SHA:raise ValueError('Reviewed scatter registry image required')
    inputs=[SOURCE,*HEADERS];sources={p.name:p.read_bytes() for p in inputs}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-Wl,-image-base=0x32000000','-o',str(binary),str(SOURCE)],check=True,cwd=ROOT)
    raw=binary.read_bytes();tests=synthetic_audit(HandLifecycleOracle(hook_raw,raw))
    if any(p.read_bytes()!=sources[p.name] for p in inputs):raise ValueError('Lifecycle sources changed during build')
    report={'schema_version':1,'scope':'private_original_hand_lifecycle_guard','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,
        'compiled_sha256':BINARY_SHA,'registry_sha256':HOOK_SHA,'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},
        'synthetic_audit':tests,'native_event_delivery_implemented':False,'model_lifetime_qualified':False,
        'game_started':False,'windows_library_loaded':False,'client_hook_installed':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True)
    parser.add_argument('--compiled-hook',type=Path,required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output,args.compiled_hook);audit=report['synthetic_audit']
        print(json.dumps({'output':str(output),'valid':len(audit['valid']),'refused':len(audit['refused']),'sha256':BINARY_SHA},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError,subprocess.CalledProcessError) as error:
        print('Compiled hand lifecycle refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
