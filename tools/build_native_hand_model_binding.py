#!/usr/bin/env python3
"""Compile the original named-node binder and exercise invented guarded forests."""
import argparse
import json
import struct
import subprocess
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_native_hand_constraints import COMPILER,COMPILER_SHA
from native_hand_model_binding import HandModelBindingOracle,BINARY_SHA,NAMES,PARENTS,OUTPUT_SIZE,WORK_SIZE

NATIVE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/native'
SOURCE=NATIVE/'hand_model_binding.c'
HEADERS=[NATIVE/'hand_model_binding.h',NATIVE/'hand_scatter.h']
BASENAME='hand-model-binding-v1.dll.disabled'
ORDERS=('ordered','reversed','permuted','rotated')
REFUSALS={'count':1,'output_size':1,'work_size':1,'null_model':1,'short_record':2,'overlap':2,
    'pointer_overflow':2,'name_span':2,'parent_outside':3,'cycle':3,'unterminated':4,'embedded_nul':4,
    'non_ascii':4,'duplicate_folded_name':4,'name_pointer':4,'missing_marker':5,'arm_kind':5,
    'marker_parent':5,'upper_parent':5,'weapon_parent':5,'changed_parent':6,'changed_name_pointer':6,'changed_kind':6}


def seed_fixture(machine,count=11,order='ordered',alignment=0,case='valid'):
    if count not in (11,128) or order not in ORDERS or type(alignment) is not int or alignment not in (0,4):
        raise ValueError('Unreviewed binding fixture layout')
    if case!='valid' and case not in REFUSALS:raise ValueError('Unreviewed binding refusal')
    names=[*NAMES,*('MOD_extra_'+str(i) for i in range(count-11))]
    parents=[*PARENTS,*(i-1 for i in range(11,count))]
    pointers=[machine.NODES+((i*37)%128)*0x2000+alignment for i in range(count)]
    if case=='parent_outside':parents[-1]=-2
    elif case=='cycle':parents[3]=4
    elif case=='missing_marker':names[1]='MOD_missing_left'
    elif case=='duplicate_folded_name':names[1]=names[2].lower()
    elif case=='marker_parent':parents[1]=3
    elif case=='upper_parent':parents[4]=-1
    elif case=='weapon_parent':parents[0]=3
    blocks=[];records=[]
    for i in range(count):
        page=pointers[i]-alignment;name=page+0x800;raw=names[i].encode('ascii')+b'\0'
        parent=machine.MODEL if parents[i]==-1 else 0xdeadbeef if parents[i]==-2 else pointers[parents[i]]
        block=bytearray(b'Z'*4096);block[alignment:alignment+0x170]=bytes(0x170);block[0x800:0x800+len(raw)]=raw
        struct.pack_into('<I',block,alignment+0xe8,name);struct.pack_into('<I',block,alignment+0x108,parent)
        struct.pack_into('<I',block,alignment+0xf8,1 if i==0 else 6 if i in (1,2) or i>=11 else 10)
        if case=='arm_kind' and i==10:struct.pack_into('<I',block,alignment+0xf8,1)
        if case=='name_pointer' and i==10:struct.pack_into('<I',block,alignment+0xe8,0)
        if i==10:
            if case=='unterminated':block[0x800+len(raw)-1]=ord('X')
            elif case=='embedded_nul':block[0x800]=0
            elif case=='non_ascii':block[0x800]=255
        machine.uc.mem_write(page,bytes(block));blocks.append((page,bytes(block)))
        records.append({'pointer':pointers[i],'bytes':0x170,'name_pointer':name,'name_bytes':len(raw),
                        'name':names[i],'parent':parent})
    if case=='short_record':records[-1]['bytes']=0x108
    elif case=='overlap':records[-1]['pointer']=records[-2]['pointer']
    elif case=='pointer_overflow':records[-1]['pointer']=0xfffffffc
    elif case=='name_span':records[-1]['name_bytes']=65
    permutation=list(range(count))
    if order=='reversed':permutation.reverse()
    elif order=='permuted':permutation=[(i*37)%count for i in range(count)]
    elif order=='rotated':permutation=permutation[5:]+permutation[:5]
    records=[records[i] for i in permutation]
    overrides={'count':{2:129},'output_size':{4:OUTPUT_SIZE-1},'work_size':{6:WORK_SIZE-1},'null_model':{0:0}}.get(case)
    machine.late_fault=None;machine.injected=False
    if case.startswith('changed_'):
        offset,value={'changed_parent':(0x108,machine.MODEL),'changed_name_pointer':(0xe8,0),'changed_kind':(0xf8,1)}[case]
        machine.late_fault=(pointers[10]+offset,value)
        page,block=blocks[10];expected=bytearray(block);struct.pack_into('<I',expected,alignment+offset,value)
        blocks[10]=(page,bytes(expected))
    return records,overrides,blocks


def fixture(machine,count=11,order='ordered',alignment=0,case='valid'):
    records,overrides,blocks=seed_fixture(machine,count,order,alignment,case)
    _,_,receipt=machine.bind(machine.MODEL,records,overrides=overrides)
    if any(bytes(machine.uc.mem_read(page,4096))!=block for page,block in blocks):
        raise ValueError('Binding changed a native record, name or page guard')
    if receipt['status']!=REFUSALS.get(case,0) or machine.injected!=case.startswith('changed_'):
        raise ValueError('Binding status or late snapshot refusal differs: '+case)
    return {'count':count,'order':order,'alignment':alignment,'case':case,'receipt':receipt}


def synthetic_audit(machine):
    valid=[fixture(machine,count,order,alignment) for count in (11,128) for order in ORDERS for alignment in (0,4)]
    refused=[fixture(machine,11,'reversed',4,case) for case in REFUSALS]
    return {'valid':valid,'refused':refused}


def build(output):
    if output.exists():raise ValueError('Binding laboratory already exists')
    if not COMPILER.is_file() or digest(COMPILER.read_bytes())!=COMPILER_SHA:
        raise ValueError('Reviewed local compiler required; nothing downloaded')
    inputs=[SOURCE,*HEADERS];sources={p.name:p.read_bytes() for p in inputs}
    output.mkdir(parents=True,exist_ok=False);binary=output/BASENAME
    subprocess.run([str(COMPILER),'-shared','-nostdlib','-Wl,-image-base=0x2e000000','-o',str(binary),str(SOURCE)],check=True,cwd=ROOT)
    raw=binary.read_bytes();tests=synthetic_audit(HandModelBindingOracle(raw))
    if any(p.read_bytes()!=sources[p.name] for p in inputs):raise ValueError('Binding sources changed during build')
    report={'schema_version':1,'scope':'private_original_hand_model_binding','runtime_status':'pending',
        'source_sha256':{k:digest(v) for k,v in sources.items()},'compiler_sha256':COMPILER_SHA,'compiled_sha256':BINARY_SHA,
        'files':{BASENAME:{'size':len(raw),'sha256':digest(raw)}},'synthetic_audit':tests,
        'native_nodes_written':False,'live_model_discovery_implemented':False,'model_lifetime_qualified':False,
        'game_started':False,'windows_library_loaded':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name);report=build(output);audit=report['synthetic_audit']
        print(json.dumps({'output':str(output),'valid':len(audit['valid']),'refused':len(audit['refused']),'sha256':BINARY_SHA},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError,subprocess.CalledProcessError) as error:
        print('Compiled hand model binding refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
