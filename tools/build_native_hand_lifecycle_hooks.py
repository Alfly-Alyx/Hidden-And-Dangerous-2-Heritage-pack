#!/usr/bin/env python3
"""Build private lifecycle entry shims and execute bounded native mutations."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from native_hand_lifecycle_hooks import NativeHandLifecycleHooksOracle,BINARY_SHA,SITES,BASE,EXPORTS
from native_hand_model_collect import BINARY_SHA as COLLECTION_SHA
from native_hand_scatter_hook import BINARY_SHA as HOOK_SHA
from ls3d_math_oracle import verify_library,DLL_SHA

NATIVE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native'
SOURCES=[NATIVE/name for name in ('hand_lifecycle.c','hand_lifecycle_hooks.c','hand_lifecycle_hooks.S')]
HEADERS=[NATIVE/name for name in ('hand_lifecycle.h','hand_scatter_context.h','hand_scatter.h')]
BASENAME='hand-lifecycle-hooks-v1.dll.disabled'


def build(output,library,collection,hook):
    if output.exists():raise ValueError('Lifecycle entry laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local compiler required; nothing downloaded')
    library_raw=library.read_bytes();verify_library(library_raw)
    collection_raw=collection.read_bytes();hook_raw=hook.read_bytes()
    if digest(collection_raw)!=COLLECTION_SHA or digest(hook_raw)!=HOOK_SHA:raise ValueError('Reviewed collection and registry required')
    inputs=[*SOURCES,*HEADERS];sources={p.name:p.read_bytes() for p in inputs}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-Wl,-image-base=0x34000000','-o',str(binary),*(str(p) for p in SOURCES)],check=True,cwd=ROOT)
    raw=binary.read_bytes();machine=NativeHandLifecycleHooksOracle(library_raw,collection_raw,hook_raw,raw)
    for name,site in ((b'Hd2LifecycleAddEntry',0x100341c0),(b'Hd2LifecycleRemoveEntry',0x10034260),(b'Hd2LifecycleReleaseEntry',0x1001c370)):
        if machine.setup_call(name,[])!=SITES[site][1]:raise ValueError('Compiled lifecycle entry pointer differs')
    rows=[machine.scenario(count) for count in (11,128)]
    if any(p.read_bytes()!=sources[p.name] for p in inputs):raise ValueError('Lifecycle delivery sources changed during build')
    report={'schema_version':1,'scope':'private_native_hand_lifecycle_delivery','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,
        'compiled_sha256':BINARY_SHA,'library_sha256':DLL_SHA,'collection_sha256':COLLECTION_SHA,'registry_sha256':HOOK_SHA,
        'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'native_scenarios':rows,
        'native_prologue_checks':sum(row['native_prologue_checks'] for row in rows),
        'patches_are_private_emulator_only':True,'production_client_refusal_handling_qualified':False,
        'native_allocator_or_destructor_executed':False,'game_started':False,'windows_library_loaded':False,
        'game_modified':False,'model_lifetime_qualified':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True)
    for name in ('library','compiled-collection','compiled-hook'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output,args.library,args.compiled_collection,args.compiled_hook)
        print(json.dumps({'output':str(output),'native_scenarios':len(report['native_scenarios']),
            'native_prologue_checks':report['native_prologue_checks'],'sha256':BINARY_SHA},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError,subprocess.CalledProcessError) as error:
        print('Compiled native lifecycle delivery refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
