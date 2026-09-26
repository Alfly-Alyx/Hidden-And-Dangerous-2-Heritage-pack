#!/usr/bin/env python3
"""Resolve weapon sound bank/index references and verify bounded native flow.

Reads pinned commercial sources, writes at most a fresh JSON report. No audio
playback/export, whole game operation, table mutation or new sound allocation.
"""
import argparse
import json
from pathlib import Path
import struct
import sys

from sound_definition import parse as parse_sounds,resolve
from item_shoot_projection import encode_field
from item_native_layout import decode_record
from items_sav import parse as parse_items


def reference(parsed,bank,index):
    entry=resolve(parsed,bank,index)
    return {'bank':bank,'index':index,'absent_sentinel':entry is None,
            'label':entry['label'] if entry else None,
            'definition_sha256':entry['sha256'] if entry else None,
            'filenames':[v['filename'] for v in entry['variants']] if entry else [],
            'audio_playback_qualified':False}


def editor_references(fields,parsed):
    refs=[]
    for column,bank in ((8,2),(10,3)):
        value=fields[column]
        try:index=struct.unpack('<I',encode_field(value,'decimal'))[0]
        except ValueError:
            import re
            if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,14}',value):raise
            refs.append({'column':column,'bank':bank,'symbol':value,'resolved':False});continue
        refs.append({'column':column,'resolved':True,**reference(parsed,bank,index)})
    return refs


def inspect(tables,sources,machine):
    from item_editor_table import parse as parse_editor
    from build_benelli_descriptor_lab import specification
    from item_weapon_descriptor import build_weapon
    parsed=parse_sounds(sources['tables/ingamesounds.def'])
    if len(parsed['banks'])<=3 or [parsed['banks'][i]['label'] for i in (2,3)]!=['Weapon Shooting','Weapon Manipulation']:
        raise ValueError('Unreviewed sound bank owners')
    layers={}
    for (archive,name),data in tables.items():
        if name!='tables/items.sav':continue
        results=[]
        for slot in parse_items(data)['slots']:
            if not slot['present'] or slot['kind']!=1:continue
            raw=data[slot['offset']:slot['offset']+slot['size']]
            if decode_record(raw)['actions'][0]['selector']!=4:continue
            flow=machine.selection(raw,slot['slot'])
            results.append({'slot':slot['slot'],'record_sha256':slot['sha256'],'native_flow':flow,
                            'references':{key:reference(parsed,flow[key]['bank'],flow[key]['index']) for key in ('shoot','reload')}})
        layers[archive]={'records_checked':len(results),'records':results}
    rows=parse_editor(tables['others.DTA','tables/item_shoot.tbl'])['rows']
    orphans=[]
    for index,name in ((9,'Benelli'),(27,'FG 42'),(32,'MG 34')):
        row=rows[index]
        if row['fields'][2]!=name:raise ValueError('Changed orphan shoot row')
        orphans.append({'row':index,'name':name,'references':editor_references(row['fields'],parsed)})
    for ref,expected,label in zip(orphans[0]['references'],('f_bene_a.wav','bene_r.wav'),('I Benelli M4','I Benelli M4 Reload')):
        if not ref['resolved'] or ref['filenames']!=[expected] or ref['label']!=label:
            raise ValueError('Benelli index does not resolve to its pinned sound definition')
        if 'sounds/'+expected not in sources:raise ValueError('Missing pinned Benelli sound')
    sabre=tables['SabreSquadron.dta','tables/items.sav'];slot=parse_items(sabre)['slots'][23]
    modern=build_weapon(specification(rows[9]['fields'],sabre[slot['offset']:slot['offset']+slot['size']]))
    modern_flow=machine.selection(modern,359)
    if (modern_flow['shoot'],modern_flow['reload'])!=({'bank':2,'index':36},{'bank':3,'index':54}):
        raise ValueError('Modern Benelli sound argument flow changed')
    return {'schema_version':1,'scope':'ordered_sound_definition_and_native_weapon_argument_flow',
            'sound_definition_sha256':parsed['sha256'],
            'bank_count':len(parsed['banks']),'entry_count':parsed['entry_count'],'variant_count':parsed['variant_count'],
            'empty_entries':sum(not e['variants'] for b in parsed['banks'] for e in b['entries']),
            'opaque_lookup':parsed['opaque_lookup'],'native_ordered_append':machine.append_order(),
            'native_synthetic_lookups':[machine.lookup(bank,index,[len(b['entries']) for b in parsed['banks']])
                for bank,index in ((0,0),(2,36),(3,54),(2,54),(2,55),(13,0),(14,0),(2,0xffffffff),(0xffffffff,0))],
            'layers_compared_to_one_effective_sound_definition':layers,
            'orphan_references':orphans,'modern_benelli_native_flow':modern_flow,
            'shoot_column_8_sound_reference_qualified':True,'shoot_column_10_sound_reference_qualified':True,
            'sound_playback_qualified':False,'audio_timing_or_variant_choice_qualified':False,
            'complete_sound_loader_executed':False,'game_started':False,'game_modified':False,'audio_exported':False}


def main(argv=None):
    from benelli_table_audit import read_tables
    from build_benelli_fpv_lab import read_sources,MANIFEST
    from item_native_contract import ROOT,SOURCE_SHA,sha
    from item_sound_oracle import SoundOracle
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
        source_manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
        sources,source_excluded=read_sources(args.game,source_manifest,archives_only=args.archives_only)
        report=inspect(tables,sources,SoundOracle(args.image.read_bytes()))
        report['resource_source_pins']=source_manifest['sources']
        report['excluded_loose_overrides']={**excluded,**source_excluded}
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('resource_source_pins','native_ordered_append','layers_compared_to_one_effective_sound_definition')},indent=2))
        print(json.dumps({'layers':{k:v['records_checked'] for k,v in report['layers_compared_to_one_effective_sound_definition'].items()}},indent=2))
        return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Weapon sound audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
