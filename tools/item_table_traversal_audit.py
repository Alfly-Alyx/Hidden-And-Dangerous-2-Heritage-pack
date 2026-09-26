#!/usr/bin/env python3
"""Audit pinned commercial item tables and prepared additions in memory only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from benelli_table_audit import TABLE_PINS,read_tables
from item_native_contract import ROOT,SOURCE_SHA,IMAGE_SHA
from item_table_additive import build,restore,sha
from item_table_oracle import TableOracle


def audit(tables,descriptor,fragment,machine):
    layers={}
    for archive in ('SabreSquadron.dta','PatchX01.dta'):
        key=(archive,'tables/items.sav')
        if key not in tables:
            if archive=='PatchX01.dta':continue
            raise ValueError('Missing reviewed Sabre table')
        fpv_key=('SabreSquadron.dta','tables/fpvanims.sav')
        for source in (key,fpv_key):
            if source not in tables or (len(tables[source]),sha(tables[source]))!=TABLE_PINS[source]:
                raise ValueError('Changed or missing pinned table for traversal audit')
        original=machine.inspect_table(tables[key])
        current,proof=build(tables[key],tables[fpv_key],descriptor,fragment,slot=359)
        changed=machine.inspect_table(current['items'])
        reverse=restore(current,proof)
        if reverse!={'items':tables[key],'fpv':tables[fpv_key]}:raise ValueError('Reversal mismatch')
        for result,raw in ((original,tables[key]),(changed,current['items'])):
            if (result.get('table_sha256')!=sha(raw) or result.get('native_slot_loop_matches') is not True
                    or result.get('native_loaded_descriptors_match') is not True
                    or result.get('source_read_only_unchanged') is not True
                    or type(result.get('slots_visited')) is not int or result['slots_visited']!=500):
                raise ValueError('Native traversal audit incomplete')
        layers[archive]={'original':original,'disabled_addition':changed,'transaction':proof,
                         'reverse_verified_in_memory':True}
    return {'schema_version':1,'scope':'private_native_item_table_traversal_audit',
        'source_executable_sha256':SOURCE_SHA,'private_image_sha256':IMAGE_SHA,'layers':layers,
        'base_255_slot_tables_executed':False,'native_file_io_executed':False,
        'native_fpv_table_loader_executed':False,'game_started':False,'game_modified':False,
        'global_slot_reservation':False,'full_save_compatibility_qualified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--descriptor-lab',required=True,type=Path)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh path')
        if sha((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        manifest=json.loads((args.descriptor_lab/'MANIFEST.json').read_text(encoding='utf-8'))
        if manifest.get('scope')!='private_disabled_benelli_descriptor_lab':raise ValueError('Unreviewed descriptor lab scope')
        inputs=[]
        for name in ('PROTOTYPE_Benelli.item.disabled','PROTOTYPE_Benelli.fpvgroup.disabled'):
            raw=(args.descriptor_lab/name).read_bytes()
            if manifest['files'][name]!={'size':len(raw),'sha256':sha(raw)}:raise ValueError('Changed descriptor laboratory payload')
            inputs.append(raw)
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        report=audit(tables,*inputs,TableOracle(args.image.read_bytes()))
        report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({archive:{kind:{k:v for k,v in layer[kind].items() if k!='descriptor_sha256_by_slot'}
            for kind in ('original','disabled_addition')} for archive,layer in report['layers'].items()},indent=2))
        return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Item table traversal audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
