#!/usr/bin/env python3
"""Build disabled parent-change interception and audit it beside native membership."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from native_hand_parent_hooks import NativeHandParentHooksOracle,BINARY_SHA,ENTRY
from native_hand_lifecycle_hooks import BINARY_SHA as LIFECYCLE_SHA
from native_hand_lifecycle import STATE_SIZE,CONFIGURE
from native_hand_model_collect import BINARY_SHA as COLLECTION_SHA
from native_hand_scatter_hook import BINARY_SHA as HOOK_SHA,ACTIVE
from ls3d_math_oracle import verify_library,DLL_SHA

NATIVE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native'
SOURCES=[NATIVE/name for name in ('hand_parent_hooks.c','hand_parent_hooks.S')]
HEADERS=[NATIVE/name for name in ('hand_lifecycle.h','hand_scatter_context.h','hand_scatter.h')]
BASENAME='hand-parent-hooks-v1.dll.disabled'


def guard_audit(m,count):
    """Use already seeded owned views; forbid CPU access to every native object."""
    h=m.adapter;foreign=m.FOREIGN+4;model=m.MODELS[0];nodes=m.pointers
    cases=[('model_detach',model,0,1),('first_detach',nodes[0],0,1),
        ('middle_detach',nodes[count//2],0,1),('last_detach',nodes[-1],0,1),
        ('destination_model',foreign,model,1),('destination_node',foreign,nodes[count//2],1),
        ('owned_to_foreign',nodes[count//2],foreign,1),('unrelated',foreign,m.MODELS[1],0),
        ('saturated_invalidations',model,0,1)]
    cases.extend((name,model,0,status) for name,status in (
        ('null_state',3),('unaligned_state',3),('state_size',3),('null_frame',3),
        ('busy',2),('changed_count',3),('unaligned_views',3),('missing_configure',3)))
    rows=[]
    for label,frame,parent,status in cases:
        if struct.unpack('<I',m.uc.mem_read(ACTIVE,4))[0]:raise ValueError('Parent matrix started with active registry')
        m.uc.mem_write(m.STATE,bytes(STATE_SIZE))
        if m.setup_call(b'Hd2WatchHandContext',[m.STATE,STATE_SIZE,h.CONTEXT,CONFIGURE]):raise ValueError('Parent matrix watch failed')
        args=[m.STATE,STATE_SIZE,frame,parent]
        if label=='null_state':args[0]=0
        elif label=='unaligned_state':args[0]+=1
        elif label=='state_size':args[1]-=1
        elif label=='null_frame':args[2]=0
        elif label=='busy':m.uc.mem_write(h.CONTEXT+40,struct.pack('<I',1))
        elif label=='changed_count':m.uc.mem_write(h.CONTEXT+8,struct.pack('<I',129))
        elif label=='unaligned_views':m.uc.mem_write(h.CONTEXT+4,struct.pack('<I',m.collector.OUTPUT+9))
        elif label=='missing_configure':m.uc.mem_write(m.STATE+4,bytes(4))
        elif label=='saturated_invalidations':m.uc.mem_write(m.STATE+16,b'\xff'*4)
        before=[bytes(m.uc.mem_read(at,size)) for at,size in ((m.STATE,4096),(h.CONTEXT,4096),(ACTIVE,4))]
        for page in m.pages:m.uc.mem_protect(page,4096,0)
        try:actual=m.setup_parent(b'Hd2BeforeHandParentChange',args)
        finally:
            for page in m.pages:m.uc.mem_protect(page,4096,m.uni.UC_PROT_READ|m.uni.UC_PROT_WRITE)
        if actual!=status:raise ValueError('Parent matrix status differs: '+label)
        if actual==1:
            if m.guard_state()!=(0,0,1,4,0xffffffff if label=='saturated_invalidations' else 1):raise ValueError('Parent matrix state differs')
            if struct.unpack('<I',m.uc.mem_read(ACTIVE,4))[0]:raise ValueError('Parent matrix registry still active')
            saved=m.guard_state()
            if m.setup_parent(b'Hd2BeforeHandParentChange',args) or m.guard_state()!=saved:raise ValueError('Repeated parent event changed inactive state')
        elif before!=[bytes(m.uc.mem_read(at,size)) for at,size in ((m.STATE,4096),(h.CONTEXT,4096),(ACTIVE,4))]:
            raise ValueError('Refused/unrelated parent event changed state: '+label)
        m.check_pages(m.state)
        m.uc.mem_write(h.CONTEXT+8,struct.pack('<I',count));m.uc.mem_write(h.CONTEXT+40,bytes(4))
        m.uc.mem_write(h.CONTEXT+4,struct.pack('<I',m.collector.OUTPUT+8))
        if m.guard_state()[0]:
            m.uc.mem_write(m.STATE+4,struct.pack('<I',CONFIGURE))
            if m.setup_call(b'Hd2BeforeHandModelChange',[m.STATE,STATE_SIZE,model,0,3])!=1:raise ValueError('Parent matrix cleanup failed')
        rows.append({'case':label,'nodes':count,'status':actual,'native_objects_cpu_inaccessible_during_guard':True,
                     'native_objects_unchanged':True,'refused_or_unrelated_state_unchanged':actual!=1})
    h.check_constants();return rows


def build(output,library,collection,hook,lifecycle):
    if output.exists():raise ValueError('Parent laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:raise ValueError('Reviewed local compiler required; nothing downloaded')
    library_raw=library.read_bytes();verify_library(library_raw)
    collection_raw=collection.read_bytes();hook_raw=hook.read_bytes();lifecycle_raw=lifecycle.read_bytes()
    if any(digest(raw)!=pin for raw,pin in ((collection_raw,COLLECTION_SHA),(hook_raw,HOOK_SHA),(lifecycle_raw,LIFECYCLE_SHA))):
        raise ValueError('Reviewed collection, registry and lifecycle delivery required')
    inputs=[*SOURCES,*HEADERS];sources={p.name:p.read_bytes() for p in inputs}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-Wl,-image-base=0x36000000','-o',str(binary),*(str(p) for p in SOURCES)],check=True,cwd=ROOT)
    raw=binary.read_bytes();m=NativeHandParentHooksOracle(library_raw,collection_raw,hook_raw,lifecycle_raw,raw)
    if m.setup_parent(b'Hd2ParentHookEntry',[])!=ENTRY:raise ValueError('Parent compiled entry pointer differs')
    scenarios=[];guards=[]
    for count in (11,128):
        scenarios.append(m.scenario_parent(count));guards.extend(guard_audit(m,count))
    if any(p.read_bytes()!=sources[p.name] for p in inputs):raise ValueError('Parent sources changed during build')
    report={'schema_version':1,'scope':'private_native_parent_change_delivery','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,'compiled_sha256':BINARY_SHA,
        'library_sha256':DLL_SHA,'collection_sha256':COLLECTION_SHA,'registry_sha256':HOOK_SHA,'lifecycle_sha256':LIFECYCLE_SHA,
        'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'native_scenarios':scenarios,'guard_cases':guards,
        'native_prologue_checks':sum(row['parent_prologue_checks'] for row in scenarios),
        'patches_are_private_emulator_only':True,'world_transform_preservation_executed':False,
        'production_client_refusal_handling_qualified':False,'native_allocator_or_destructor_executed':False,
        'game_started':False,'game_modified':False,'windows_library_loaded':False,'model_lifetime_qualified':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True)
    for name in ('library','compiled-collection','compiled-hook','compiled-lifecycle'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output,args.library,args.compiled_collection,args.compiled_hook,args.compiled_lifecycle)
        print(json.dumps({'output':str(output),'native_scenarios':len(report['native_scenarios']),
            'native_prologue_checks':report['native_prologue_checks'],'guard_cases':len(report['guard_cases']),'sha256':BINARY_SHA},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError,subprocess.CalledProcessError) as error:
        print('Compiled parent lifecycle refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
