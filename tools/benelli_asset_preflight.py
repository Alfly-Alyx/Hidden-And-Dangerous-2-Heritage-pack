#!/usr/bin/env python3
"""Read-only collision inventory for modern model aliases and stock dependencies.

This is NOT a native resource-search-order proof. Neighboring I3D/4DS/5DS and
texture variants are inventoried conservatively, never chosen or substituted.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path,PurePosixPath
import sys

from dta_archive import DtaArchive
from build_benelli_fpv_lab import read_sources,MANIFEST,ARCHIVES
from benelli_fpv_rig_audit import read_hands,HAND_PINS,HAND_ARCHIVES
from build_benelli_descriptor_lab import MODEL_PINS
from reconstruction_sandbox import normal,destination

FOLDERS=('Models','Maps','Maps_U','Maps_C','Sounds','Tables')
MODEL_SUFFIXES={'.i3d','.4ds','.5ds'}
TEXTURE_SUFFIXES={'.bmp','.dx1'}


def classify(name,source_names):
    name=name.replace('\\','/').casefold();path=PurePosixPath(name)
    if len(path.parts)!=2:return None
    folder,leaf=path.parts;stem=path.stem;suffix=path.suffix
    if folder=='models' and stem in {n.casefold() for n in MODEL_PINS} and suffix in MODEL_SUFFIXES:
        return 'modern_model_alias_collision'
    # Existing personalized central tables are handled by their own exact
    # snapshot composition, not misreported as an asset conflict here.
    if name in ('tables/items.sav','tables/fpvanims.sav','tables/item_shoot.tbl'):return None
    sources={n.replace('\\','/').casefold() for n in source_names}
    if name in sources:return 'pinned_resource_path'
    if folder=='models' and suffix in MODEL_SUFFIXES:
        stems={PurePosixPath(n).stem for n in sources if n.startswith('models/')}
        if stem in stems:return 'model_resolution_neighbor'
    if folder in ('maps','maps_u','maps_c') and suffix in TEXTURE_SUFFIXES:
        stems={PurePosixPath(n).stem for n in sources if n.startswith(('maps/','maps_u/','maps_c/'))}
        if any(stem==s or stem.startswith(s+'_') for s in stems):return 'texture_resolution_neighbor'
    return None


def fingerprint(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def inventory(game,source_names):
    normal(game);archives=[];rows=[];seen=set()
    for path in sorted(game.iterdir(),key=lambda p:p.name.casefold()):
        if path.suffix.casefold()!='.dta':continue
        normal(path)
        if not path.is_file():raise ValueError('Root archive is not a regular file')
        if path.name.casefold() in seen:raise ValueError('Case-ambiguous root archive')
        seen.add(path.name.casefold());stamp=(path.stat().st_size,path.stat().st_mtime_ns)
        with DtaArchive(path) as archive:
            index=[];relevant=set()
            for entry in archive.entries:
                name=entry.name.replace('\\','/').casefold();index.append([name,entry.size])
                kind=classify(name,source_names)
                if kind is None:continue
                if name in relevant:raise ValueError('Duplicate relevant archive resource')
                relevant.add(name)
                rows.append({'archive':path.name,'path':name,'classification':kind,**fingerprint(archive.read(entry))})
        if stamp!=(path.stat().st_size,path.stat().st_mtime_ns):raise ValueError('Archive changed during inventory')
        archives.append({'archive':path.name,'size':stamp[0],'entry_count':len(index),
            'name_size_index_sha256':hashlib.sha256(json.dumps(index,separators=(',',':')).encode('utf-8')).hexdigest(),
            'index_hash_is_full_archive_hash':False})
    if not archives:raise ValueError('No root DTA archives inspected')
    loose=[]
    for folder in FOLDERS:
        directory=destination(game,folder)
        if not directory.exists():continue
        if not directory.is_dir():raise ValueError('Asset namespace is not a directory')
        seen=set()
        for path in sorted(directory.iterdir(),key=lambda p:p.name.casefold()):
            name=folder+'/'+path.name;kind=classify(name,source_names)
            if kind is None:continue
            if path.name.casefold() in seen:raise ValueError('Case-ambiguous loose asset')
            seen.add(path.name.casefold());normal(path)
            if not path.is_file():raise ValueError('Relevant loose asset is not a regular file')
            loose.append({'path':name,'classification':kind,**fingerprint(path.read_bytes())})
    collisions=[row for row in rows if row['classification']=='modern_model_alias_collision']
    reviewed_archives={name.casefold() for name in (*ARCHIVES,*HAND_ARCHIVES)}
    unexpected=[row for row in rows if row['archive'].casefold() not in reviewed_archives]
    return {'schema_version':1,'scope':'benelli_model_alias_and_dependency_namespace_preflight',
        'archives':archives,'archive_resources':rows,'loose_asset_candidates':loose,
        'archive_modern_alias_collisions':collisions,'unexpected_archive_providers':unexpected,
        'no_candidate_collisions':not collisions and not loose and not unexpected,
        'loose_scope':'direct files in Models, Maps, Maps_U, Maps_C, Sounds and Tables',
        'modern_alias_extensions_checked':sorted(MODEL_SUFFIXES),'texture_extensions_checked':sorted(TEXTURE_SUFFIXES),
        'central_table_overrides_handled_separately':True,
        'native_search_order_qualified':False,'compressed_texture_choice_qualified':False,
        'global_id_reservation':False,'installation_allowed':False,'game_started':False,'game_modified':False}


def audit(game):
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    sources,_=read_sources(game,manifest,archives_only=True)
    hands,_=read_hands(game,archives_only=True)
    report=inventory(game,set(sources)|set(hands))
    report['reviewed_source_pins']={**manifest['sources'],
        **{name:{'archive':p[0],'size':p[1],'sha256':p[2]} for name,p in HAND_PINS.items()}}
    report['source_content_hashes_verified']=True
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; choose a fresh path')
        report=audit(args.game)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({'archives_inspected':len(report['archives']),
            'archive_resource_candidates':len(report['archive_resources']),
            'loose_asset_candidates':report['loose_asset_candidates'],
            'archive_modern_alias_collisions':report['archive_modern_alias_collisions'],
            'unexpected_archive_providers':report['unexpected_archive_providers'],
            'no_candidate_collisions':report['no_candidate_collisions'],'native_search_order_qualified':False,
            'game_modified':False},ensure_ascii=False,indent=2))
        return 0 if report['no_candidate_collisions'] else 1
    except (OSError,ValueError,KeyError) as error:
        print('Benelli asset preflight refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
