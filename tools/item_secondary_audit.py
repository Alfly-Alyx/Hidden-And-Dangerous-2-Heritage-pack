#!/usr/bin/env python3
"""Read-only secondary-action argument audit, with bounded native CPU blocks.

No client, scene, animation, audio, save, renderer or input polling is run.
Commercial bytes remain private; only a fresh optional JSON report is written.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from item_native_contract import ROOT,SOURCE_SHA,sha
from item_native_layout import decode_record
from item_secondary_oracle import SecondaryOracle,checked_action,checked_interpolation,as_float


def audit(tables,machine):
    from benelli_table_audit import TABLE_PINS
    from items_sav import parse as parse_items
    from item_editor_table import require_row
    from build_benelli_descriptor_lab import specification
    from item_weapon_descriptor import build_weapon
    layers={};targets=set()
    for archive in ('others.DTA','Patch.dta','SabreSquadron.dta','PatchX01.dta'):
        key=(archive,'tables/items.sav')
        if key not in tables or (len(tables[key]),sha(tables[key]))!=TABLE_PINS[key]:
            raise ValueError('Missing or changed reviewed secondary-action source')
        data=tables[key];records=[]
        for slot in parse_items(data)['slots']:
            if not slot['present']:continue
            raw=data[slot['offset']:slot['offset']+slot['size']]
            if decode_record(raw)['actions'][1]['selector']!=5:continue
            result=checked_action(machine,raw,slot['slot']);targets.add(result['scalar_raw'])
            records.append(result)
        layers[archive]={'records_checked':len(records),'records':records}
    key=('others.DTA','tables/item_shoot.tbl')
    if key not in tables or (len(tables[key]),sha(tables[key]))!=TABLE_PINS[key]:raise ValueError('Changed shoot source')
    row=require_row(tables[key],9,stride=135,name_column=2,name='Benelli')
    data=tables['SabreSquadron.dta','tables/items.sav'];baseline=parse_items(data)['slots'][23]
    spec=specification(row['fields'],data[baseline['offset']:baseline['offset']+baseline['size']])
    spec['text_id']=21500 # Same disabled v3 record, not a runtime text reservation.
    modern=build_weapon(spec);modern_result=checked_action(machine,modern,359);targets.add(modern_result['scalar_raw'])
    synthetic=[]
    for mode in (4,6,7,0xffffffff):
        spec['secondary']['mode_raw']=mode
        synthetic.append(checked_action(machine,build_weapon(spec),359))
    cameras=[]
    for target_raw in sorted(targets):
        target=as_float(target_raw)
        for current,step in ((0.1,0),(0.1,16),(2.5,16),(0.1,1000),(2.5,1000),(target,16)):
            cameras.append(checked_interpolation(machine,current,target,step))
    return {'schema_version':1,'scope':'bounded_secondary_action_and_camera_argument_paths',
            'layers':layers,'modern_benelli':modern_result,'synthetic_mode_cases':synthetic,'camera_cases':cameras,
            'distinct_camera_targets':len(targets),'complete_aim_operation_executed':False,
            'input_and_cooldown_gates_qualified':False,'native_scene_methods_executed':False,
            'animation_timing_qualified':False,'game_started':False,'game_modified':False,'playable_weapon':False}


def main(argv=None):
    from benelli_table_audit import read_tables
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Use a fresh report path')
        if sha((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        report=audit(tables,SecondaryOracle(args.image.read_bytes()));report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({'layers':{k:v['records_checked'] for k,v in report['layers'].items()},
                          'modern_benelli':report['modern_benelli'],'camera_cases':len(report['camera_cases']),
                          'synthetic_mode_cases':len(report['synthetic_mode_cases']),
                          'game_started':False,'game_modified':False},ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Secondary-action audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
