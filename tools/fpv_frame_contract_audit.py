#!/usr/bin/env python3
"""Native synthetic frame search plus modern assembly structural diagnosis."""
import argparse
import json
from pathlib import Path
import sys
from ls3d_frame_find_oracle import FrameFindOracle
from ls3d_math_oracle import DLL_SHA
from build_modern_equipment_assembly import inputs,compile_assembly,CASES
from build_modern_equipment_fpv_rig import compile_flat_rig
from menu_gui_audit import parse_4ds_nodes


def audit(library):
    oracle=FrameFindOracle(library)
    tree=[{'name':'fpv_weapon','frame_type':6,'parent':-1},
          {'name':'FPV_Weapon','frame_type':1,'parent':0},
          {'name':'magazine','frame_type':6,'parent':0},
          {'name':'joint','frame_type':10,'parent':2},
          {'name':'fpv_weapon','frame_type':1,'parent':-1}]
    controls=[]
    for flags in (1,0x21,0xffff,0x20001,0x20021,0x2ffff):
        for query in ('fpv_weapon','FPV_Weapon','magazine','joint','missing'):
            controls.append(oracle.find(tree,query,flags))
    cases={}
    for case in CASES:
        raw,_,report=compile_assembly(*inputs(case));nodes=parse_4ds_nodes(raw)['nodes']
        scene=[{'name':n['name'],'frame_type':n['frame_type'],'parent':n['parent_id']-1} for n in nodes]
        # Actual modern source lacks the required name. A diagnostic rename
        # then isolates type filtering, without changing any file/model.
        missing=oracle.find(scene,'fpv_weapon',1)
        renamed=[dict(node) for node in scene];renamed[0]['name']='fpv_weapon'
        dummy=oracle.find(renamed,'fpv_weapon',1)
        included=oracle.find(renamed,'fpv_weapon',0x21)
        if missing['index'] is not None or dummy['index'] is not None or included['index']!=0:
            raise ValueError('Unexpected modern FPV root contract result')
        flat,_,flat_report=compile_flat_rig(case);flat_nodes=parse_4ds_nodes(flat)['nodes']
        flat_scene=[{'name':n['name'],'frame_type':n['frame_type'],'parent':n['parent_id']-1} for n in flat_nodes]
        repaired=oracle.find(flat_scene,'fpv_weapon',1)
        if repaired['index']!=0 or repaired['direct_children']!=list(range(1,len(flat_nodes))):
            raise ValueError('Flat modern rig does not satisfy native selection/enumeration')
        cases[case]={'model_sha256':report['rig_sha256'],'nodes':len(nodes),
            'actual_fpv_visual_lookup':missing,'dummy_alias_visual_lookup':dummy,
            'dummy_alias_explicitly_allowed_lookup':included,
            'flat_fpv_model_sha256':flat_report['model_sha256'],'flat_fpv_nodes':len(flat_nodes),
            'flat_fpv_visual_lookup':repaired,
            'unregistered_descendants_if_only_root_and_direct_children_are_added':
                len(nodes)-1-len(included['direct_children'])}
    return {'schema_version':1,'scope':'native_frame_find_type_filter_and_direct_child_enumeration',
        'library_sha256':DLL_SHA,'synthetic_queries':len(controls),'controls':controls,'cases':cases,
        'fpv_weapon_search_mask':1,'magazine_search_mask':0x21,
        'client_search_masks_statically_observed_not_client_executed':True,
        'client_direct_child_registration_statically_observed':True,
        'native_loader_executed':False,'clone_or_model_add_executed':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--library',required=True,type=Path)
    parser.add_argument('--json-output',type=Path);args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        report=audit(args.library.read_bytes())
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k!='controls'},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native FPV frame contract refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
