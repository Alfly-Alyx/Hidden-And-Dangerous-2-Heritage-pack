#!/usr/bin/env python3
"""Prepare modern inventory labels in a PRIVATE disabled, reversible text lab.

Installed text tables are intentionally read as a current snapshot (including
existing user additions), not replaced with historical archive defaults.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

from texty_additive import ENCODINGS,RESERVED,validate,collision_check,append_labels,remove_append,sha

ROOT=Path(__file__).resolve().parents[1]
CATALOGUE=ROOT/'experimental/RECONSTRUCTION_BACKLOG/modern-inventory-texts.json'


def linked(path):return path.is_symlink() or getattr(path,'is_junction',lambda:False)()


def read_text_sources(game):
    root=game/'Text'
    if linked(game) or linked(root) or not root.is_dir():raise ValueError('Missing or linked game text root')
    sources={};normalized=set()
    for path in sorted(root.rglob('*'),key=lambda p:str(p).casefold()):
        if not path.name.casefold().startswith('texty') or path.suffix.casefold()!='.txt':continue
        if not path.is_file():raise ValueError('Text source is not a regular file')
        relative=path.relative_to(game)
        if any(linked(parent) for parent in (path,*path.parents) if parent!=game and game in (parent,*parent.parents)):
            raise ValueError('Linked text source')
        name=relative.as_posix();key=name.casefold()
        if key in normalized:raise ValueError('Case-colliding text sources')
        normalized.add(key);sources[name]=path.read_bytes()
    if not sources:raise ValueError('No installed text tables')
    return sources


def prepare(catalogue,sources,*,occupied_item_text_ids,mission_range):
    labels=validate(catalogue,mission_range=mission_range)
    ids={row['text_id'] for row in labels}
    if ids&set(occupied_item_text_ids):raise ValueError('Modern label ID already referenced by an item')
    collision_check(sources,ids)
    outputs={};proofs={};missing_base=[];languages=set()
    normalized={name.casefold() for name in sources}
    for name,raw in sorted(sources.items()):
        parts=name.replace('\\','/').split('/')
        if parts[-1].casefold()!='texty_dd.txt':continue
        if len(parts)!=3 or parts[0].casefold()!='text' or parts[1].casefold() not in ENCODINGS:
            raise ValueError('Unreviewed expansion text language/path')
        language=parts[1].casefold()
        if language in languages:raise ValueError('Duplicate expansion text language')
        languages.add(language)
        if ('text/'+language+'/texty.txt') not in normalized:missing_base.append(language)
        result,proof=append_labels(raw,labels,language)
        if remove_append(result,proof)!=raw:raise ValueError('Text addition does not reverse exactly')
        outputs[name+'.disabled']=result;proofs[name]={'language':language,**proof,'reverse_verified_in_memory':True}
    if not outputs:raise ValueError('No supported expansion text table')
    return outputs,{'schema_version':1,'scope':'private_disabled_modern_inventory_texts',
        'provenance':'MODERNE_ORIGINAL_ADDITIONS_TO_INSTALLED_SNAPSHOT',
        'catalogue_sha256':sha(json.dumps(catalogue,sort_keys=True,ensure_ascii=False).encode('utf-8')),
        'project_reserved_range':list(RESERVED),'creator_reserved_range':list(mission_range),
        'labels':{row['key']:{'text_id':row['text_id'],'values':row['values']} for row in labels},
        'sources':{name:{'size':len(raw),'sha256':sha(raw)} for name,raw in sources.items()},
        'proofs':proofs,'source_tables_checked':len(sources),'languages_prepared':sorted(languages),
        'languages_without_base_text_table':missing_base,
        'collision_scan':'conservative_numeric_tokens_not_full_legacy_parser',
        'existing_legacy_duplicates_and_comments_preserved':True,
        'game_modified':False,'game_started':False,'text_id_allocated_in_disabled_lab':True,
        'global_text_id_freedom_qualified':False,'native_text_loader_qualified':False,
        'rendering_and_font_coverage_qualified':False,'japan_label_policy':'ASCII_MODERN_marker',
        'files':{name:{'size':len(raw),'sha256':sha(raw)} for name,raw in outputs.items()}}


def occupied_item_text_ids(game,tables):
    from items_sav import parse
    occupied=set()
    for (_archive,name),raw in tables.items():
        if name=='tables/items.sav':occupied.update(s['text_id'] for s in parse(raw)['slots'] if s['present'])
    loose=game/'Tables/items.sav'
    if loose.exists():
        if linked(loose) or linked(loose.parent):raise ValueError('Linked installed item table')
        occupied.update(s['text_id'] for s in parse(loose.read_bytes())['slots'] if s['present'])
    return occupied


def output_directory(name,root=ROOT):
    if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',name)
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',name)):
        raise ValueError('Unsafe inventory text laboratory name')
    base=root/'.analysis/inventory-text-labs';output=base/name
    if any(linked(path) for path in (root,root/'.analysis',base,output)):
        raise ValueError('Linked inventory text laboratory path')
    if output.exists():raise ValueError('Inventory text laboratory already exists')
    return output


def main(argv=None):
    from benelli_table_audit import read_tables
    from custom_mission_packages import TEXT_ID_START,TEXT_ID_END
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--output-name')
    args=parser.parse_args(argv)
    try:
        output=output_directory(args.output_name) if args.output_name else None
        catalogue=json.loads(CATALOGUE.read_text(encoding='utf-8'))
        tables,_=read_tables(args.game,archives_only=args.archives_only)
        sources=read_text_sources(args.game)
        files,report=prepare(catalogue,sources,occupied_item_text_ids=occupied_item_text_ids(args.game,tables),
                             mission_range=(TEXT_ID_START,TEXT_ID_END))
        if output:
            output.mkdir(parents=True,exist_ok=False)
            for name,raw in files.items():
                target=output.joinpath(*name.split('/'));target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as stream:stream.write(raw)
            with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({key:report[key] for key in ('source_tables_checked','languages_prepared','languages_without_base_text_table',
            'project_reserved_range','creator_reserved_range','labels','game_modified','native_text_loader_qualified')},ensure_ascii=False,indent=2))
        print('Private output: '+str(output) if output else 'Memory-only preparation')
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern inventory text laboratory refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
