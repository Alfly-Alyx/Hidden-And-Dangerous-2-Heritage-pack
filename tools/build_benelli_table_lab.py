#!/usr/bin/env python3
"""Build a PRIVATE disabled full-table Benelli lab; never install or launch.

Only reviewed archive bases are supported. Existing loose central tables are
NOT overwritten, merged or called equivalent to the archive-based laboratory.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path,PurePosixPath
import re
import sys

import build_benelli_descriptor_lab as descriptor_lab
from benelli_table_audit import TABLE_PINS
from item_table_additive import build,restore,sha,fingerprint
from items_sav import parse as parse_items

ROOT=Path(__file__).resolve().parents[1]
ITEM_LAYERS=('SabreSquadron.dta','PatchX01.dta')
FPV_SOURCE=('SabreSquadron.dta','tables/fpvanims.sav')


def prepare(tables,sources,machine,*,inventory,item_layer,table_machine=None,fpv_machine=None,hands=None,
            verify_resource_requests=False):
    if (table_machine is None)!=(fpv_machine is None):raise ValueError('Both native table oracles are required together')
    if verify_resource_requests and fpv_machine is None:raise ValueError('Resource requests require native table traversal')
    if item_layer not in ITEM_LAYERS:raise ValueError('Unreviewed item layer; Base/Patch cannot host this candidate')
    if inventory is None:raise ValueError('Prepared inventory texts are required for the full-table lab')
    item_source=(item_layer,'tables/items.sav')
    for key in (item_source,FPV_SOURCE):
        if key not in tables:raise ValueError('Missing explicitly selected table source')
        if (len(tables[key]),sha(tables[key]))!=TABLE_PINS[key]:raise ValueError('Changed selected table source')
    files,descriptor_report=descriptor_lab.prepare(tables,sources,machine,inventory=inventory)
    if not descriptor_report['modern_design_decisions']['text_id_allocated']:
        raise ValueError('Inventory text remains unresolved')
    descriptor=files['PROTOTYPE_Benelli.item.disabled'];fragment=files['PROTOTYPE_Benelli.fpvgroup.disabled']
    current,proof=build(tables[item_source],tables[FPV_SOURCE],descriptor,fragment,slot=descriptor_lab.SYNTHETIC_SLOT)
    originals=restore(current,proof)
    if originals!={'items':tables[item_source],'fpv':tables[FPV_SOURCE]}:
        raise ValueError('Full table transaction failed exact reversal')

    parsed=parse_items(current['items']);checked=[]
    for slot in parsed['slots']:
        if not slot['present']:continue
        raw=current['items'][slot['offset']:slot['offset']+slot['size']]
        native=machine.inspect_record(raw,slot['slot'])
        if native.get('native_decode_matches') is not True or native.get('native_descriptor_measure_matches') is not True:
            raise ValueError('Native descriptor verification incomplete')
        checked.append(slot['slot'])
    if descriptor_lab.SYNTHETIC_SLOT not in checked:raise ValueError('Candidate missing from full table')
    rig_binding=None
    if hands is not None:
        from benelli_fpv_rig_audit import audit as audit_rig
        rig_binding=audit_rig(sources,hands,tables)
    traversal=None;resource_requests=None
    if table_machine is not None:
        traversal={'items':table_machine.inspect_table(current['items']),
                   'fpv':fpv_machine.inspect_table(current['fpv'])}
        item_check=traversal['items'];fpv_check=traversal['fpv']
        if (item_check.get('table_sha256')!=sha(current['items'])
                or item_check.get('native_slot_loop_matches') is not True
                or item_check.get('native_loaded_descriptors_match') is not True
                or item_check.get('source_read_only_unchanged') is not True
                or fpv_check.get('table_sha256')!=sha(current['fpv'])
                or fpv_check.get('native_nested_traversal_matches') is not True
                or fpv_check.get('native_strings_and_values_match') is not True
                or fpv_check.get('source_read_only_unchanged') is not True
                or fpv_check.get('unpopulated_cells_unchanged') is not True):
            raise ValueError('Native full-table traversal verification incomplete')
        if verify_resource_requests:
            from fpv_resource_oracle import inspect_loaded_requests
            resource_requests=inspect_loaded_requests(fpv_machine,current['fpv'],descriptor_lab.SYNTHETIC_SLOT)
    files={**files,'Tables/items.sav.disabled':current['items'],'Tables/FpvAnims.sav.disabled':current['fpv']}
    report={'schema_version':1,'scope':'private_disabled_benelli_full_table_lab',
        'provenance':'ASSEMBLAGE_MODERNE_RESSOURCES_MIXTES',
        'item_source':'::'.join(item_source),'fpv_source':'::'.join(FPV_SOURCE),
        'descriptor_lab':descriptor_report,'transaction':proof,
        'reverse_verified_in_memory':True,
        'native_descriptor_records_checked':len(checked),'native_descriptor_slots_checked':checked,
        'native_whole_table_loader_executed':False,
        'native_table_traversal':traversal,
        'native_animation_resource_requests':resource_requests,
        'separate_hands_weapon_binding_plan':rig_binding,
        'files':{name:fingerprint(raw) for name,raw in files.items()},
        'pending_requirements':[p for p in descriptor_report['pending_requirements'] if p!='additive_table_transaction']
            +['isolated_deployment_transaction_and_override_merge','native_whole_table_loading_tests'],
        'disabled_table_entry_prepared':True,'disabled_fpv_group_prepared':True,
        'item_slot_allocated_in_game':False,'global_slot_reservation':False,
        'loose_overrides_merged':False,'installation_allowed':False,
        'game_started':False,'game_modified':False,'playable_weapon':False,
        'full_save_compatibility_qualified':False}
    return files,report


def output_directory(name,root=ROOT):
    if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',name)
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',name)):
        raise ValueError('Unsafe full-table laboratory name')
    base=root/'.analysis'/'item-table-labs';output=base/name
    for path in (root,root/'.analysis',base,output):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
            raise ValueError('Linked full-table laboratory path')
    if output.exists():raise ValueError('Full-table laboratory already exists')
    return output


def write_lab(output,files,report):
    # Fixed safe names are currently produced by prepare(). Keep this guard
    # at the write boundary so later builders cannot introduce active files.
    for name in files:
        path=PurePosixPath(name)
        if (path.is_absolute() or any(part in ('.','..') for part in name.split('/'))
                or any(c in name for c in ('\\',':')) or not name.endswith('.disabled')):
            raise ValueError('Unsafe or active laboratory output name')
    output.mkdir(parents=True,exist_ok=False)
    for name,raw in files.items():
        target=output.joinpath(*name.split('/'));target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(raw)
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    with (output/'LIRE_AVANT_ESSAI.txt').open('x',encoding='utf-8') as stream:
        stream.write('LABORATOIRE PRIVE DESACTIVE - ASSEMBLAGE MODERNE, PAS UNE ARME VALIDEE.\n'
            'Les tables derivees de vos archives ne doivent pas etre redistribuees.\n'
            'Aucune surcharge personnelle fusionnee. NE PAS COPIER DANS LE JEU.\n'
            'Retrait exact verifie en memoire, pas une transaction de deploiement.\n'
            'Sauvegardes, contrats FPV et comportement moteur restent non qualifies.\n')
    # Read back all emitted payloads. Partial output from any failure remains
    # inert and is never reported as a successfully verified laboratory.
    for name,raw in files.items():
        if output.joinpath(*name.split('/')).read_bytes()!=raw:
            raise ValueError('Laboratory payload read-back mismatch')


def main(argv=None):
    from benelli_table_audit import read_tables
    from build_benelli_fpv_lab import read_sources,MANIFEST
    from build_modern_inventory_text_lab import read_text_sources,occupied_item_text_ids,CATALOGUE
    from custom_mission_packages import TEXT_ID_START,TEXT_ID_END
    from item_state_oracle import StateOracle
    from item_table_oracle import TableOracle
    from fpv_resource_oracle import FpvResourceOracle
    from benelli_fpv_rig_audit import read_hands
    from item_native_contract import SOURCE_SHA
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--item-layer',required=True,choices=ITEM_LAYERS)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--output-name')
    args=parser.parse_args(argv)
    try:
        output=output_directory(args.output_name) if args.output_name else None
        if sha((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
        sources,source_excluded=read_sources(args.game,manifest,archives_only=args.archives_only)
        hands,hand_excluded=read_hands(args.game,archives_only=args.archives_only)
        inventory={'catalogue':json.loads(CATALOGUE.read_text(encoding='utf-8')),
                   'sources':read_text_sources(args.game),
                   'occupied_item_text_ids':occupied_item_text_ids(args.game,tables),
                   'mission_range':(TEXT_ID_START,TEXT_ID_END)}
        image=args.image.read_bytes()
        files,report=prepare(tables,sources,StateOracle(image),inventory=inventory,item_layer=args.item_layer,
                             table_machine=TableOracle(image),fpv_machine=FpvResourceOracle(image),hands=hands,
                             verify_resource_requests=True)
        report['resource_source_pins']=manifest['sources']
        report['excluded_loose_overrides']={**excluded,**source_excluded,**hand_excluded}
        if output:write_lab(output,files,report)
        print(json.dumps({'output':str(output) if output else None,
            **{key:report[key] for key in ('item_source','fpv_source','native_descriptor_records_checked',
                'reverse_verified_in_memory','installation_allowed','game_modified','pending_requirements')},
            'transaction':report['transaction'],
            'separate_hands_variants':len(report['separate_hands_weapon_binding_plan']['hands_variants']),
            'native_animation_resource_requests':len(report['native_animation_resource_requests']),
            'native_table_traversal':{key:{field:result[field] for field in
                (('slots_visited','present_descriptors_checked') if key=='items' else
                 ('groups_visited','populated_channels_checked','unpopulated_cells_unchanged'))}
                for key,result in report['native_table_traversal'].items()}},ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Benelli full-table laboratory refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
