#!/usr/bin/env python3
"""Original flat FPV candidate rig, preserving all modern geometry/skin bytes.

The existing hose skin becomes visual root fpv_weapon. Every other original
node is a direct child, as required by the reviewed client registration loop.
This changes coordinate ownership: old animation banks MUST NOT be attached.
"""
import argparse
import json
import struct

import build_modern_asset as asset
from build_modern_equipment_assembly import inputs,compile_assembly,CASES,ROOT
from build_modern_equipment_hose import digest
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms
from ls3d_frame_find_oracle import reference as find_reference


def rewritten_node(raw,node,name,parent,position):
    """Rewrite only SRT/name/parent header; geometry/skin payload stays exact."""
    head=bytearray(raw[node['start']:node['name_offset']-1])
    struct.pack_into('<H',head,node['parent_offset']-node['start'],parent)
    struct.pack_into('<3f4f3f',head,node['position_offset']-node['start'],
        *position,0,0,0,1,1,1,1)
    name=name.encode('ascii')
    return bytes(head)+bytes([len(name)])+name+raw[node['name_offset']+node['name_length']:node['end']]


def flatten_original(raw):
    parsed=parse_4ds_nodes(raw);nodes=parsed['nodes']
    if (parsed['has_animation'] or not nodes or nodes[0]['frame_type']!=6 or nodes[0]['parent_id']
            or not nodes[0]['name'].startswith('PROTOTYPE_HERITAGE_')):
        raise ValueError('Expected freshly generated original assembly root')
    if len({n['name'].casefold() for n in nodes})!=len(nodes):raise ValueError('Ambiguous modern assembly nodes')
    for node in nodes:
        if not node['name'].startswith(('PROTOTYPE_HERITAGE_','MOD_')):
            raise ValueError('Unmarked original assembly node')
        if node['frame_type'] not in (1,6,10) or (node['frame_type']==1 and node['visual_type'] not in (0,2)):
            raise ValueError('Unreviewed modern frame kind')
        q=struct.unpack_from('<4f',raw,node['position_offset']+12)
        if q!=(0,0,0,1) or node['scale']!=[1,1,1]:
            raise ValueError('Flattening requires the reviewed translation-only rest hierarchy')
        if node['parent_id']>=node['index'] or (node['index']!=1 and not node['parent_id']):
            raise ValueError('Unreviewed original assembly ownership')
    skins=[n for n in nodes if n['frame_type']==1 and n['visual_type']==2]
    if len(skins)!=1 or skins[0]['parent_id']!=1:raise ValueError('Expected one root-local hose skin')
    skin=skins[0];world=world_transforms(raw,nodes)
    if nodes[0]['position']!=[0,0,0] or world[skin['index']][1]!=[0,0,0]:
        raise ValueError('Unexpected original skin/root origin')
    selected=[skin]+[n for n in nodes[1:] if n['index']!=skin['index']]
    output=bytearray(raw[:parsed['node_count_offset']]+asset.pack('H',len(selected)))
    maps={}
    for index,node in enumerate(selected,1):
        name='fpv_weapon' if index==1 else node['name'];maps[node['name']]=name
        output.extend(rewritten_node(raw,node,name,0 if index==1 else 1,world[node['index']][1]))
    output.extend(b'\0');output=bytes(output);checked=parse_4ds_nodes(output)
    if checked['node_count']!=len(nodes)-1:raise ValueError('Flat FPV lost an unexpected node')
    after={n['name']:n for n in checked['nodes']}
    for old in selected:
        new=after[maps[old['name']]]
        if raw[old['name_offset']+old['name_length']:old['end']]!=output[new['name_offset']+new['name_length']:new['end']]:
            raise ValueError('FPV flattening changed geometry/LOD/skin payload')
        if max(abs(a-b) for a,b in zip(new['position'],world[old['index']][1]))>2e-7:
            raise ValueError('FPV flattening changed rest translation')
    scene=[{'name':n['name'],'frame_type':n['frame_type'],'parent':n['parent_id']-1} for n in checked['nodes']]
    found=find_reference(scene,'fpv_weapon',1)
    if found!={'index':0,'direct_children':list(range(1,len(selected)))}:
        raise ValueError('Flat FPV search or direct registration contract failed')
    return output,{'schema_version':1,'provenance':'MODERNE','runtime_status':'pending',
        'source_sha256':digest(raw),'model_sha256':digest(output),'nodes':len(selected),
        'removed_dummy_root':nodes[0]['name'],'source_hose_skin':skin['name'],'source_to_fpv_names':maps,
        'root_name':'fpv_weapon','root_frame_type':1,'root_visual_type':2,
        'all_remaining_nodes_are_direct_children':True,'original_geometry_lods_and_skin_bytes_preserved':True,
        'hand_models_included':False,'old_animation_banks_compatible':False,
        'rebaked_animation_bank_required':True,'native_loader_executed':False,
        'native_clone_qualified':False,'camera_calibrated':False,'engine_validated':False,
        'commercial_assets_used':False,'game_started':False,'game_modified':False}


def compile_flat_rig(case):
    original,_,_=compile_assembly(*inputs(case));flat,report=flatten_original(original)
    return flat,original,report


def build(case,output):
    raw,_,report=compile_flat_rig(case);output.mkdir(parents=True,exist_ok=False)
    filename=f'PROTOTYPE_{case}_FPV.4ds.disabled';(output/filename).write_bytes(raw)
    report['files']={filename:digest(raw)}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--output-name');args=parser.parse_args(argv)
    try:
        report=build(args.case,asset.output_directory(ROOT,args.output_name)) if args.output_name else compile_flat_rig(args.case)[2]
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern flat FPV rig refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
