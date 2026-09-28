#!/usr/bin/env python3
"""Merge three private disabled snapshot labs, then inspect their joint tables.

Only named children of .analysis/item-table-labs are accepted. No installation,
game launch or fresh claim about the current game state follows from this tool.
"""
import argparse
import json
from pathlib import Path
import sys

from build_benelli_table_lab import ROOT,output_directory,write_lab
from build_modern_animation_bank import ALIASES
from fpv_resource_oracle import inspect_loaded_requests
from item_table_additive import fingerprint
from items_sav import parse as parse_items
from reconstruction_sandbox import relative,destination,normal,tree
from rigid_weapon_bundle import CASES,SHORT,SLOTS,CENTRAL,build,restore,payloads


def load_lab(name,*,root=ROOT):
    if len(relative(name))!=1:raise ValueError('Expected one private laboratory name')
    base=root/'.analysis'/'item-table-labs'
    for path in (root,root/'.analysis',base):normal(path)
    folder=destination(base,name);normal(folder)
    manifest=destination(folder,'MANIFEST.json')
    if manifest.stat().st_size>16*1024*1024:raise ValueError('Oversized input manifest')
    report=json.loads(manifest.read_text(encoding='utf-8'))
    if not isinstance(report,dict) or not isinstance(report.get('files'),dict):raise ValueError('Missing input payload manifest')
    if set(tree(folder))!=set(report['files'])|{'MANIFEST.json','LIRE_AVANT_ESSAI.txt'}:
        raise ValueError('Unlisted or missing laboratory file')
    files={}
    for name,info in report['files'].items():
        if not name.endswith('.disabled'):raise ValueError('Active input file')
        path=destination(folder,name)
        if not path.is_file() or path.stat().st_size>16*1024*1024:raise ValueError('Invalid input payload size/type')
        raw=path.read_bytes()
        if fingerprint(raw)!=info:raise ValueError('Input payload differs from its manifest')
        files[name]=raw
    return files,report


def inspect(files,report,state_machine,table_machine,fpv_machine,loader):
    if {n:fingerprint(r) for n,r in files.items()}!=report['files']:raise ValueError('Changed combined payloads')
    current={k:files[n] for k,n in CENTRAL.items()}
    restore(current,report['transaction']);checked=[]
    for slot in parse_items(current['items'])['slots']:
        if not slot['present']:continue
        raw=current['items'][slot['offset']:slot['offset']+slot['size']]
        row=state_machine.inspect_record(raw,slot['slot'])
        if row.get('native_decode_matches') is not True or row.get('native_descriptor_measure_matches') is not True:
            raise ValueError('Incomplete combined descriptor inspection')
        checked.append(slot['slot'])
    traversals={'items':table_machine.inspect_table(current['items']),'fpv':fpv_machine.inspect_table(current['fpv'])}
    flags={'items':('native_slot_loop_matches','native_loaded_descriptors_match','source_read_only_unchanged'),
           'fpv':('native_nested_traversal_matches','native_strings_and_values_match','source_read_only_unchanged','unpopulated_cells_unchanged')}
    for key,fields in flags.items():
        if (traversals[key].get('table_sha256')!=fingerprint(current[key])['sha256']
                or any(traversals[key].get(f) is not True for f in fields)):
            raise ValueError('Incomplete combined table traversal')
    requests={};loads={};hand=report['hand_variant']
    for case in CASES:
        requests[case]=inspect_loaded_requests(fpv_machine,current['fpv'],SLOTS[case])
        stems={f'PROTOTYPE_{SHORT[case]}P{hand}{alias}' for alias in ALIASES.values()}
        if {r['requested_name'] for r in requests[case]}!={s+'.I3D' for s in stems}:
            raise ValueError('Combined table requests wrong weapon clips')
        loads[case]={}
        for stem in sorted(stems):
            raw=files[stem+'.5ds.disabled'];row=loader.load(raw,stem+'.I3D')
            if (row.get('animation_sha256')!=fingerprint(raw)['sha256']
                    or row.get('native_animation_open_and_relocation_executed') is not True
                    or row.get('relocated_body_and_name_match') is not True
                    or row.get('requested_memory_filename')!=stem+'.5ds'):
                raise ValueError('Incomplete combined animation load')
            loads[case][stem]=row
    return {**report,'native_descriptor_slots_checked':checked,'native_descriptor_records_checked':len(checked),
            'native_table_traversal':traversals,'native_animation_resource_requests':requests,
            'native_animation_loads':loads,'native_subsystems_use_separate_emulators':True,
            'native_scene_loading_or_clone_executed':False,'simultaneous_runtime_use_qualified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for case in CASES:parser.add_argument('--'+case.lower(),required=True,help='Name of an existing private disabled lab')
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        output=output_directory(args.output_name)
        names={c:getattr(args,c.lower()) for c in CASES};labs={c:load_lab(n) for c,n in names.items()}
        files,report=build(labs)
        from item_state_oracle import StateOracle
        from item_table_oracle import TableOracle
        from fpv_resource_oracle import FpvResourceOracle
        from ls3d_animation_load_oracle import AnimationLoadOracle
        image=args.image.read_bytes()
        report=inspect(files,report,StateOracle(image),TableOracle(image),FpvResourceOracle(image),
                       AnimationLoadOracle(args.library.read_bytes()))
        # Snapshot names are provenance, never paths supplied by a manifest.
        report['input_lab_names']=names
        report['snapshots_revalidated_against_current_game']=False
        for case,name in names.items():
            if load_lab(name)!=labs[case]:raise ValueError('Input laboratory changed during composition')
        write_lab(output,files,report)
        print(json.dumps({'output':str(output),'files':len(files)+2,
            'native_descriptor_records_checked':report['native_descriptor_records_checked'],
            'native_animation_requests':sum(len(v) for v in report['native_animation_resource_requests'].values()),
            'native_animation_loads':sum(len(v) for v in report['native_animation_loads'].values()),
            'reverse_verified_in_memory':True,'playable_weapons':False}));return 0
    except (OSError,ValueError,KeyError,TypeError,ImportError) as error:
        print('Private combined weapon lab refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
