#!/usr/bin/env python3
"""Compile the bounded model-vector collector and check guarded invented objects."""
import argparse
import json
import struct
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from build_native_hand_model_binding import NATIVE,ORDERS,seed_fixture
from native_hand_model_collect import HandModelCollectionOracle,BINARY_SHA,WORK_SIZE
from native_hand_model_binding import OUTPUT_SIZE

SOURCES=[NATIVE/'hand_model_binding.c',NATIVE/'hand_model_collect.c']
HEADERS=[NATIVE/'hand_model_binding.h',NATIVE/'hand_model_collect.h',NATIVE/'hand_scatter.h']
BASENAME='hand-model-collect-v1.dll.disabled'
REFUSALS={'owned_count':1,'output_size':1,'work_size':1,'null_model':2,'short_model':2,'unaligned_model':2,
    'null_vector':2,'short_vector':2,'unaligned_vector':2,'overflow_vector':2,'model_kind':2,
    'vector_identity':2,'model_count':2,'excess_model_count':2,'insufficient_vector':2,
    'foreign_node':3,'duplicate_node':3,'duplicate_owned':3,'missing_owned':3,
    'short_record':12,'parent_outside':13,'cycle':13,'missing_marker':15,'arm_kind':15,
    'changed_kind':4,'changed_vector':4,'changed_count':4,'changed_entry':4}


def permutation(count,order):
    indices=list(range(count))
    if order=='ordered':return indices
    if order=='reversed':return indices[::-1]
    if order=='permuted':return [(i*37)%count for i in indices]
    if order=='rotated':return indices[5:]+indices[:5]
    raise ValueError('Unreviewed collection order')


def fixture(machine,count=11,vector_order='ordered',owned_order='reversed',alignment=0,case='valid',kind_tag=0):
    if case!='valid' and case not in REFUSALS:raise ValueError('Unreviewed collection refusal')
    if type(kind_tag) is not int or kind_tag not in (0,1):raise ValueError('Unreviewed model type tag')
    binding_case=case if case in ('short_record','parent_outside','cycle','missing_marker','arm_kind') else 'valid'
    records,_,blocks=seed_fixture(machine,count,'ordered',alignment,binding_case)
    pointers=[records[i]['pointer'] for i in permutation(count,vector_order)]
    records=[records[i] for i in permutation(count,owned_order)]
    if case=='foreign_node':pointers[-1]=0xdeadbeec
    elif case=='duplicate_node':pointers[-1]=pointers[0]
    elif case=='duplicate_owned':records[-1]=dict(records[0])
    elif case=='missing_owned':records[-1]={**records[-1],'pointer':0xdeadbeec}
    model=bytearray(b'Z'*4096);vector=bytearray(b'Z'*4096)
    struct.pack_into('<I',model,0xf8,(kind_tag<<16)|9)
    struct.pack_into('<I',model,0x120,machine.VECTOR);struct.pack_into('<I',model,0x128,count)
    struct.pack_into('<'+'I'*count,vector,0,*pointers)
    for key,offset,value in (('model_kind',0xf8,10),('vector_identity',0x120,machine.VECTOR+4),
                           ('model_count',0x128,count-1),('excess_model_count',0x128,129)):
        if case==key:struct.pack_into('<I',model,offset,value)
    machine.uc.mem_write(machine.MODEL,bytes(model));machine.uc.mem_write(machine.VECTOR,bytes(vector))
    overrides={'owned_count':{5:129},'output_size':{7:OUTPUT_SIZE-1},'work_size':{9:WORK_SIZE-1},
        'null_model':{0:0},'short_model':{1:0x128},'unaligned_model':{0:machine.MODEL+1},
        'null_vector':{2:0},'short_vector':{3:40},'unaligned_vector':{2:machine.VECTOR+1},
        'overflow_vector':{2:0xfffffffc},'insufficient_vector':{3:count*4-4}}.get(case)
    if case.startswith('changed_'):
        machine.late_fault={'changed_kind':(machine.MODEL+0xf8,0x10009),
            'changed_vector':(machine.MODEL+0x120,machine.VECTOR+4),'changed_count':(machine.MODEL+0x128,count-1),
            'changed_entry':(machine.VECTOR+4*(count-1),pointers[0])}[case]
        at,value=machine.late_fault
        struct.pack_into('<I',model if at<machine.VECTOR else vector,at-(machine.MODEL if at<machine.VECTOR else machine.VECTOR),value)
    _,_,receipt=machine.collect(machine.MODEL,0x12c,machine.VECTOR,count*4,records,overrides=overrides)
    if (any(bytes(machine.uc.mem_read(page,4096))!=block for page,block in blocks)
            or bytes(machine.uc.mem_read(machine.MODEL,4096))!=bytes(model)
            or bytes(machine.uc.mem_read(machine.VECTOR,4096))!=bytes(vector)):
        raise ValueError('Collection changed native data, names or page guards')
    if receipt['status']!=REFUSALS.get(case,0) or machine.injected!=case.startswith('changed_'):
        raise ValueError('Collection status or late snapshot refusal differs: '+case)
    return {'count':count,'vector_order':vector_order,'owned_order':owned_order,'alignment':alignment,
            'model_type_tag':kind_tag,'case':case,'receipt':receipt}


def synthetic_audit(machine):
    valid=[fixture(machine,count,vector_order,owned_order,alignment,kind_tag=alignment//4)
           for count in (11,128) for vector_order in ORDERS for owned_order in ('reversed','rotated') for alignment in (0,4)]
    refused=[fixture(machine,128 if case=='insufficient_vector' else 11,'permuted','reversed',4,case) for case in REFUSALS]
    return {'valid':valid,'refused':refused}


def build(output):
    if output.exists():raise ValueError('Collection laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local compiler required; nothing downloaded')
    inputs=[*SOURCES,*HEADERS];sources={p.name:p.read_bytes() for p in inputs}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-Wl,-image-base=0x30000000','-o',str(binary),*(str(p) for p in SOURCES)],check=True,cwd=ROOT)
    raw=binary.read_bytes();tests=synthetic_audit(HandModelCollectionOracle(raw))
    if any(p.read_bytes()!=sources[p.name] for p in inputs):raise ValueError('Collection sources changed during build')
    report={'schema_version':1,'scope':'private_original_hand_model_collection','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,'compiled_sha256':BINARY_SHA,
        'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'synthetic_audit':tests,
        'native_model_vector_collected':True,'native_nodes_written':False,'memory_ownership_supplied':True,
        'model_lifetime_qualified':False,'game_started':False,'windows_library_loaded':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output);audit=report['synthetic_audit']
        print(json.dumps({'output':str(output),'valid':len(audit['valid']),'refused':len(audit['refused']),'sha256':BINARY_SHA},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError,subprocess.CalledProcessError) as error:
        print('Compiled hand model collection refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
