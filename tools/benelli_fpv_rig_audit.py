#!/usr/bin/env python3
"""Read-only structural binding plan for stock hands + the modern Benelli FPV.

Commercial models, textures and animation keys remain private and unmodified.
The report is a linkage plan, not a merged model or a playable first-person rig.
"""
from __future__ import annotations
import argparse
from contextlib import ExitStack
import json
from pathlib import Path
import sys

from dta_archive import DtaArchive
from fpv_rig_binding import bind
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms
from five_ds import parse_5ds
from build_benelli_fpv_lab import read_sources,MANIFEST,STATES,textures,sha
from benelli_fpv_static import derive
from benelli_table_audit import read_tables
from items_sav import parse as parse_items

HAND_PINS={
 'models/fpv_hands.4ds':('models.dta',49154,'5a418cba65daca969417b0d38e0c467bd8b58f49f12260961dc3ee163afe8678'),
 'models/fpv_hands_r.4ds':('models.dta',52813,'7a81c876cbce814c0a8e3dc7abe3c1fe2887c2e2f3cc3dd520d83c28e1f93555'),
 'maps/la_ruka01.bmp':('Maps.dta',66616,'8275739e06d957e181f9f6f05f12b3a479e3f5515d6feaa8880a7e01cb04e646'),
 'maps/la_ruka02.bmp':('Maps.dta',17464,'87b0ee2bd6dc9bd02bf39a1aa2eff39fad5f80ad05dcbaa95dd5092a9369e7b9'),
 'maps_u/e_br_bdarm.bmp':('Maps_U.dta',9272,'12ce6359c6b07f2c8e12d6ca6e341c8f26f184c11275e7ff8128382617e7c869'),
}
HAND_MODELS=('models/fpv_hands.4ds','models/fpv_hands_r.4ds')
HAND_ARCHIVES=('models.dta','Maps.dta','Maps_U.dta','others.DTA','LangEnglish.dta',
               'Patch.dta','SabreSquadron.dta','PatchX01.dta')


def read_hands(game,*,archives_only=False):
    effective={};excluded={}
    with ExitStack() as stack:
        for archive_name in HAND_ARCHIVES:
            path=game/archive_name
            if archive_name=='PatchX01.dta' and not path.exists():continue
            archive=stack.enter_context(DtaArchive(path));seen=set()
            for entry in archive.entries:
                name=entry.name.replace('\\','/').casefold()
                if name not in HAND_PINS:continue
                if name in seen:raise ValueError('Duplicate FPV hands source in an archive')
                seen.add(name);effective[name]=(archive_name,archive,entry)
        result={}
        for name,(expected_archive,size,digest) in HAND_PINS.items():
            if name not in effective:raise ValueError('Missing FPV hands source: '+name)
            archive_name,archive,entry=effective[name];raw=archive.read(entry)
            if (archive_name,len(raw),sha(raw))!=(expected_archive,size,digest):
                raise ValueError('Changed or shadowed FPV hands source: '+name)
            result[name]=raw
        candidates=set(HAND_PINS)
        # Record alternate loose texture namespaces too. This does not claim
        # a native search order between Maps and Maps_U or compressed variants.
        for name in HAND_PINS:
            if name.endswith('.bmp'):candidates.update(folder+'/'+name.split('/')[-1] for folder in ('maps','maps_u'))
        for name in sorted(candidates):
            loose=game.joinpath(*name.split('/'))
            if not loose.exists():continue
            if not archives_only:raise ValueError('Loose FPV hands override: '+name)
            raw=loose.read_bytes();excluded[name]={'size':len(raw),'sha256':sha(raw)}
    return result,excluded


def audit(sources,hands,tables):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete FPV hands source set')
    for name,raw in hands.items():
        _,size,digest=HAND_PINS[name]
        if (len(raw),sha(raw))!=(size,digest):raise ValueError('Changed pinned hands payload')
    static,derivation=derive(sources['models/#fpvbeneliaim.4ds'])
    weapon=parse_4ds_nodes(static);world_transforms(static,weapon['nodes'])
    variants={}
    texture_candidates={}
    for name in hands:
        if name.endswith('.bmp'):texture_candidates.setdefault(name.split('/')[-1],[]).append(name)
    for hand_name in HAND_MODELS:
        raw=hands[hand_name];model=parse_4ds_nodes(raw);world_transforms(raw,model['nodes'])
        if model['node_count']!=37:raise ValueError('Changed reviewed hands node count')
        material_textures=textures(raw)
        if any(len(texture_candidates.get(name,[]))!=1 for name in material_textures):
            raise ValueError('Unresolved or ambiguous stock hands texture source')
        clips={}
        for state in STATES:
            animated=sources['models/#fpvbeneli'+state+'.4ds']
            animation_model=parse_4ds_nodes(animated);world_transforms(animated,animation_model['nodes'])
            clip=parse_5ds(sources['models/#fpvbeneli'+state+'.5ds'])
            if not animation_model['has_animation']:raise ValueError('Animation companion flag missing')
            binding=bind(model['nodes'],weapon['nodes'],animation_model['nodes'],clip['tracks'])
            clips[state]={'frame_end':clip['frame_end'],'track_count':clip['track_count'],**binding}
        variants[hand_name]={'size':len(raw),'sha256':sha(raw),'node_count':model['node_count'],
            'material_texture_sources':{name:texture_candidates[name][0] for name in material_textures},
            'native_texture_namespace_or_compression_selection_qualified':False,'clips':clips}
    references={}
    stems={Path(name).stem.casefold() for name in HAND_MODELS}
    for (archive,name),raw in tables.items():
        if name!='tables/items.sav':continue
        slots=[s for s in parse_items(raw)['slots'] if s.get('fpv_model','').casefold() in stems]
        # Sabre/PatchX01 slot 270 really has native kind 1 despite its clothing
        # name. Preserve this anomaly; do not rewrite it or call every reference
        # a qualified uniform-selection path.
        references[archive]=[{'slot':s['slot'],'kind':s['kind'],'internal_name':s['internal_name'],
                              'fpv_model':s['fpv_model']} for s in slots]
    return {'schema_version':1,'scope':'private_benelli_separate_hands_weapon_binding_plan',
        'provenance':'COMMERCIAL_HANDS_AND_CLIPS_WITH_MODERN_WEAPON_EXTRACTION',
        'hand_source_pins':{name:{'archive':pin[0],'size':pin[1],'sha256':pin[2]} for name,pin in HAND_PINS.items()},
        'static_weapon':{'size':len(static),'sha256':sha(static),'derivation':derivation},
        'hands_variants':variants,'commercial_item_references':references,
        'non_class2_reference_slots':{archive:[s['slot'] for s in slots if s['kind']!=2]
                                     for archive,slots in references.items()},
        'separate_model_targets_per_variant':45,'animation_pairs_checked_per_variant':9,
        'native_binding_execution_qualified':False,'skin_deformation_qualified':False,
        'camera_and_animation_events_qualified':False,'game_started':False,'game_modified':False,
        'playable_weapon':False,'geometry_or_animation_keys_exported':False,
        'pending':['native_model_and_animation_name_binding','skin_deformation_and_rest_pose',
                   'partial_track_pose_inheritance','camera_and_event_timing','native_texture_search_and_compression']}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh path')
        manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
        sources,excluded=read_sources(args.game,manifest,archives_only=args.archives_only)
        hands,hand_excluded=read_hands(args.game,archives_only=args.archives_only)
        tables,table_excluded=read_tables(args.game,archives_only=args.archives_only)
        report=audit(sources,hands,tables)
        report['animation_source_pins']=manifest['sources']
        report['excluded_loose_overrides']={**excluded,**hand_excluded,**table_excluded}
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({'variants':{name:{'targets':v['node_count']+8,
            'textures':v['material_texture_sources'],'clips':{state:{key:clip[key] for key in
            ('frame_end','track_count','hand_track_count','weapon_track_count')}
            for state,clip in v['clips'].items()}} for name,v in report['hands_variants'].items()},
            'item_references_per_layer':{k:len(v) for k,v in report['commercial_item_references'].items()},
            'pending':report['pending']},ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Benelli FPV rig audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
