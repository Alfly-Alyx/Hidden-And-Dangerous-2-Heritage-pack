#!/usr/bin/env python3
"""Audit native world-preserving hierarchy changes without loading the game."""
import argparse
import json
import math
from pathlib import Path
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from native_parent_world import NativeParentWorldOracle,TOLERANCE

CASES=('move_leaf','detach_leaf','move_model','same_parent')
EXPECTED_CALLS={
    'move_leaf':{'world_cache':6,'quaternion_matrix':6,'matrix_product':5,'inverse_matrix':1,'scale_extract':1,'orientation_rebuild':1},
    'detach_leaf':{'world_cache':5,'quaternion_matrix':5,'matrix_product':4,'scale_extract':1,'orientation_rebuild':1},
    'move_model':{'world_cache':2,'quaternion_matrix':2,'matrix_product':1,'inverse_matrix':1,'scale_extract':1,'orientation_rebuild':1},
    'same_parent':{}}
ERRORS=('world_caches','local_matrices','scales','preserved_world')


def summarize(rows):
    if not isinstance(rows,list) or len(rows)!=32:raise ValueError('Expected complete world parent matrix')
    wanted={(c,t,p,f) for c in CASES for t in (False,True) for p in (False,True) for f in (1,3)};seen=set()
    errors={k:0.0 for k in ERRORS};calls={};checks=0;changed=0
    for row in rows:
        if (not isinstance(row,dict) or row.get('case') not in CASES or type(row.get('turned')) is not bool
                or type(row.get('patched')) is not bool or type(row.get('flags')) is not int):raise ValueError('Unreviewed world receipt')
        key=(row['case'],row['turned'],row['patched'],row['flags'])
        if key not in wanted or key in seen:raise ValueError('Duplicate or unreviewed world scenario')
        seen.add(key);expected_changed=row['case']!='same_parent'
        for name in ('all_world_transforms_preserved','unrelated_bytes_and_membership_unchanged','native_image_fully_restored'):
            if row.get(name) is not True:raise ValueError('World preservation claim not established')
        for name in ('native_immediate_refresh_executed','scene_notifications_executed','native_allocator_or_destructor_executed',
                     'game_started','game_modified','hand_correction_executed','live_model_lifetime_qualified'):
            if row.get(name) is not False:raise ValueError('World receipt exceeds reviewed scope')
        if row.get('changed') is not expected_changed:raise ValueError('World mutation/no-op differs')
        for name in ('moved_quaternion_left_stale_by_native_matrix_path','fourth_scale_slot_is_nonsemantic_copied_padding'):
            if row.get(name) is not expected_changed:raise ValueError('World matrix-path limitation omitted')
        for name in ('parent_prologue_checks','compiled_parent_notifications'):
            if type(row.get(name)) is not int or row[name]!=int(row['patched']):raise ValueError('World native notification gate differs')
        observed=row.get('native_calls')
        if (not isinstance(observed,dict) or observed!=EXPECTED_CALLS[row['case']]
                or any(type(v) is not int for v in observed.values())):raise ValueError('World native execution counts differ')
        if (type(row.get('native_world_cache_objects')) is not int
                or row['native_world_cache_objects']!=observed.get('world_cache',0)):raise ValueError('World cache object count differs')
        values=row.get('max_errors')
        if not isinstance(values,dict) or set(values)!=set(ERRORS):raise ValueError('Missing world measurements')
        for name,value in values.items():
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=TOLERANCE:raise ValueError('Invalid world measurement')
            errors[name]=max(errors[name],value)
        for name,value in observed.items():calls[name]=calls.get(name,0)+value
        checks+=row['parent_prologue_checks'];changed+=int(expected_changed)
    return {'scenarios':len(rows),'changed_operations':changed,'no_op_operations':len(rows)-changed,
            'guarded_operations':checks,'native_calls':calls,'max_errors':errors}


def audit(output,library,collection,hook,lifecycle,parent):
    if output.exists():raise ValueError('World parent output already exists')
    inputs={'native_library':library,'collection':collection,'correction_registry':hook,'lifecycle_delivery':lifecycle,'parent_delivery':parent}
    raw={name:path.read_bytes() for name,path in inputs.items()}
    m=NativeParentWorldOracle(*(raw[name] for name in inputs))
    output.mkdir(parents=True,exist_ok=False)
    rows=[m.scenario_world(case,turned,patched,flags) for case in CASES for turned in (False,True)
          for patched in (False,True) for flags in (1,3)]
    totals=summarize(rows)
    report={'schema_version':1,'scope':'private_native_parent_world_preservation','runtime_status':'pending',
        'inputs_sha256':{name:digest(data) for name,data in raw.items()},'totals':totals,'scenarios':rows,
        'fresh_diagnostic_tree_per_scenario':True,'uniform_positive_scales_only':True,'postchange_world_composition_is_independent_reference':True,
        'native_immediate_refresh_executed':False,'scene_notifications_executed':False,'quaternion_cache_regeneration_qualified':False,
        'live_model_lifetime_qualified':False,'production_client_refusal_handling_qualified':False,'game_started':False,'game_modified':False}
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-name',required=True)
    for name in ('library','compiled-collection','compiled-hook','compiled-lifecycle','compiled-parent'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name)
        report=audit(output,args.library,args.compiled_collection,args.compiled_hook,args.compiled_lifecycle,args.compiled_parent)
        print(json.dumps({'output':str(output),**report['totals']},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError) as error:
        print('Native parent world audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
