#!/usr/bin/env python3
"""Audit Benelli FPV sources; optionally build a PRIVATE disabled static model.

All official sources are read-only and pinned. No Item, sound event, projectile,
5DS export, table patch, deployment or game launch. Default: audit in memory.
"""
from __future__ import annotations

import argparse
from contextlib import ExitStack
import hashlib
import json
import io
import math
from pathlib import Path
import re
import struct
import sys
import wave

from dta_archive import DtaArchive
from menu_gui_audit import parse_4ds_nodes, FourDsReader
from five_ds import parse_5ds
from model_transform import world_transforms
from benelli_fpv_static import derive, geometry, NAMES
from asset_presence_audit import benelli_shoot_evidence, BENELLI_SHOOT_SHA256

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'experimental/BENELLI_M4_ADDITIVE/fpv-sources.json'
STATES=('aim','aimshot','arm','daim','disarm','idle1','jammed','rel','shot')
ARCHIVES=('models.dta','Maps.dta','Sounds.dta','others.DTA','LangEnglish.dta','Patch.dta','SabreSquadron.dta')
REQUIRED={f'models/#fpvbeneli{state}.{suffix}' for state in STATES for suffix in ('4ds','5ds')} | {
    'models/w_garandfpv.4ds','maps/d_benellim4.bmp','maps/d_benellim4paz.bmp',
    'maps/wi_it-benelli.bmp','maps/w_shell.bmp','tables/fpvanims.sav','tables/item_shoot.tbl',
    'sounds/f_bene_a.wav','sounds/bene_r.wav','tables/ingamesounds.def'}
SOUNDS={'I Benelli M4':'f_bene_a.wav','I Benelli M4 Reload':'bene_r.wav'}


def sha(raw): return hashlib.sha256(raw).hexdigest()


def read_sources(game, manifest, *, archives_only=False):
    if (not isinstance(manifest,dict) or manifest.get('schema_version')!=1
            or not isinstance(manifest.get('sources'),dict) or set(manifest['sources'])!=REQUIRED):
        raise ValueError('Incomplete or unexpected FPV source inventory')
    for proof in manifest['sources'].values():
        if (not isinstance(proof,dict) or set(proof)!={'archive','size','sha256'}
                or proof['archive'] not in ARCHIVES or type(proof['size']) is not int or proof['size']<=0
                or not isinstance(proof['sha256'],str) or not re.fullmatch('[0-9a-f]{64}',proof['sha256'])):
            raise ValueError('Invalid pinned FPV source')
    data,excluded={},{}
    with ExitStack() as stack:
        effective={}
        for archive_name in (*ARCHIVES,'PatchX01.dta'):
            path=game/archive_name
            if archive_name=='PatchX01.dta' and not path.exists(): continue
            archive=stack.enter_context(DtaArchive(path))
            seen=set()
            for entry in archive.entries:
                name=entry.name.replace('\\','/').casefold()
                if name not in REQUIRED: continue
                if name in seen: raise ValueError('Ambiguous FPV source: '+name)
                if archive_name=='PatchX01.dta': raise ValueError('Unreviewed PatchX01 FPV override: '+name)
                seen.add(name); effective[name]=(archive_name,archive,entry)
        for name,pin in manifest['sources'].items():
            if name not in effective: raise ValueError('Missing FPV source: '+name)
            archive_name,archive,entry=effective[name]
            raw=archive.read(entry)
            if archive_name!=pin['archive'] or len(raw)!=pin['size'] or sha(raw)!=pin['sha256']:
                raise ValueError('FPV source changed or shadowed: '+name)
            loose=game.joinpath(*name.split('/'))
            if loose.exists():
                if not archives_only: raise ValueError('Loose FPV override requires explicit archive-only inspection: '+name)
                other=loose.read_bytes(); excluded[name]={'size':len(other),'sha256':sha(other)}
            data[name]=raw
    return data,excluded


def textures(data):
    r=FourDsReader(data); r.take(14); count=r.u16(); names=[]
    for _ in range(count):
        flags=r.u32(); r.take(72); has_texture=False
        if flags & (1<<19): r.take(4); names.append(r.take(r.u8()).rstrip(b'\0').decode('cp1252'))
        if flags & (1<<18):
            has_texture=True; names.append(r.take(r.u8()).rstrip(b'\0').decode('cp1252'))
        if flags & (1<<30) and not flags & (1<<24):
            has_texture=True; names.append(r.take(r.u8()).rstrip(b'\0').decode('cp1252'))
        if not has_texture: r.take(1)
        if flags & ((1<<25)|(1<<26)): r.take(18)
    return sorted(set(n.casefold() for n in names if n))


def inspect_pair(model,animation):
    parsed=parse_4ds_nodes(model); clip=parse_5ds(animation)
    world_transforms(model,parsed['nodes'])  # rejects cycles, invalid parents/transforms
    by_name={node['name'].casefold():node for node in parsed['nodes']}
    if len(by_name)!=parsed['node_count'] or parsed['node_count']!=45 or not parsed['has_animation']:
        raise ValueError('Unexpected Benelli animation model skeleton')
    if not NAMES<=set(by_name): raise ValueError('Incomplete Benelli weapon subtree')
    for track in clip['tracks']:
        if track['name'].casefold() not in by_name:
            raise ValueError('Animation track missing from its paired model')
    meshes=[]
    from model_instance import visual_geometry
    for node in parsed['nodes']:
        if node['frame_type']==1:
            meshes.append({'name':node['name'],'lods':visual_geometry(model,node)})
    return {'model_nodes':parsed['node_count'],'joint_nodes':sum(n['frame_type']==10 for n in parsed['nodes']),
            'frame_end_inclusive':clip['frame_end'],'track_count':clip['track_count'],
            'key_count':sum(len(c['frames']) for t in clip['tracks'] for c in t['channels'].values()),
            'weapon_track_names':[t['name'] for t in clip['tracks'] if t['name'].casefold() in NAMES],
            'unresolved_track_names':[],'frame_rate':None,'duration_seconds':None,
            'meshes':meshes,'textures':textures(model),'engine_validated':False}


def sound_references(data):
    """Resolve filename children in the two named sound definitions, not events."""
    def children(start,end):
        result=[]
        while start<end:
            if end-start<6: raise ValueError('Truncated sound definition chunk')
            kind,size=struct.unpack_from('<HI',data,start)
            if size<6 or start+size>end: raise ValueError('Invalid sound definition chunk')
            result.append((kind,start+6,start+size)); start+=size
        return result
    references={}
    for label,filename in SOUNDS.items():
        name=label.encode('ascii')+b'\0'; marker=struct.pack('<HI',0x4ba,6+len(name))+name
        if data.count(marker)!=1: raise ValueError('Missing or ambiguous Benelli sound definition')
        label_start=data.index(marker); start=label_start-6
        if start<0: raise ValueError('Missing sound definition owner')
        kind,size=struct.unpack_from('<HI',data,start); end=start+size
        if kind!=0x4b0 or size<6 or end>len(data): raise ValueError('Invalid sound definition owner')
        fields=children(start+6,end)
        if [k for k,_,_ in fields]!=[0x4ba,0x51e,0x514]:
            raise ValueError('Unexpected Benelli sound definition structure')
        files=[data[a:b].rstrip(b'\0').decode('ascii') for k,a,b in children(fields[2][1],fields[2][2]) if k==0x578]
        if files!=[filename]: raise ValueError('Benelli sound filename differs from its definition')
        references[label]={'filename':filename,'offset':start,'size':size,'sha256':sha(data[start:end]),
                           'event_binding_qualified':False}
    return references


def audio_metadata(raw):
    from audit_audio_resources import pcm_metadata
    result=pcm_metadata(raw)
    if (result['channels'],result['sample_width_bytes'],result['sample_rate_hz'])!=(1,2,22050):
        raise ValueError('Unexpected Benelli sound PCM format')
    with wave.open(io.BytesIO(raw),'rb') as wav: samples=wav.readframes(wav.getnframes())
    values=[v for v, in struct.iter_unpack('<h',samples)]
    if not values: raise ValueError('Empty Benelli sound')
    peak=max(abs(v) for v in values); rms=math.sqrt(sum(v*v for v in values)/len(values))
    result.update(peak_abs_pcm16=peak,rms_dbfs=20*math.log10(rms/32768) if rms else None,
                  synchronized_to_animation=False)
    return result


def audit(data,manifest,excluded):
    pairs={state:inspect_pair(data[f'models/#fpvbeneli{state}.4ds'],data[f'models/#fpvbeneli{state}.5ds'])
           for state in STATES}
    for pair in pairs.values():
        if any('maps/'+name not in data for name in pair['textures']):
            raise ValueError('Model material refers to an unpinned texture')
    table_names={v.decode('ascii').casefold() for v in re.findall(rb'(?i)#FPVBeneli[A-Za-z0-9]+',data['tables/fpvanims.sav'])}
    if table_names!={'#fpvbeneli'+state for state in STATES}:
        raise ValueError('FPV table state references differ from the reviewed set')
    garand=parse_4ds_nodes(data['models/w_garandfpv.4ds'])
    roots=[n for n in garand['nodes'] if n['name'].casefold()=='fpv_weapon']
    if len(roots)!=1: raise ValueError('Ambiguous static reference weapon root')
    root=roots[0]
    rotation=struct.unpack_from('<4f',data['models/w_garandfpv.4ds'],root['position_offset']+12)
    if (garand['has_animation'] or root['parent_id'] or root['position']!=[0,0,0]
            or root['scale']!=[1,1,1] or rotation not in ((0,0,0,1),(0,0,0,-1))):
        raise ValueError('Static reference no longer has the reviewed neutral weapon root')
    shoot=benelli_shoot_evidence(data['tables/item_shoot.tbl'])
    if not shoot['header_ok'] or shoot['sha256']!=BENELLI_SHOOT_SHA256:
        raise ValueError('Historical Benelli shoot record changed')
    references=sound_references(data['tables/ingamesounds.def'])
    audio={name:audio_metadata(data['sounds/'+name]) for name in SOUNDS.values()}
    return {'schema_version':1,'scope':'private_benelli_fpv_lab','sources':manifest['sources'],
            'pairs':pairs,'table_state_names':sorted(table_names),
            'table_event_timing_decoded':False,'historical_shoot_record':shoot,
            'shoot_numeric_semantics':'unqualified','excluded_loose_overrides':excluded,
            'sound_definitions':references,'audio':audio,
            'source_mode':'pinned_commercial_archives','playable_weapon':False,
            'item_slot_allocated':False,'compass_modified':False,'game_modified':False,
            'game_launched':False,'runtime_status':'pending'}


def output_directory(name,root=ROOT):
    if (not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',name)
            or re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])',name)):
        raise ValueError('Unsafe FPV output name')
    base=root/'.analysis'/'fpv-labs'; output=base/name
    for path in (root,root/'.analysis',base,output):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
            raise ValueError('Linked FPV output directory')
    if output.exists(): raise ValueError('FPV output already exists; use a fresh name')
    return output


def native_assets(derived):
    """Short, explicit prototype aliases fit native 20-byte model-name fields."""
    from items_sav import model_name_field
    from build_modern_asset import RECIPE, build_meshes, encode_4ds
    recipe=json.loads(RECIPE.read_text(encoding='utf-8'))
    modern=encode_4ds(recipe,build_meshes(recipe))
    parsed=parse_4ds_nodes(modern)
    if parsed['has_animation']:raise ValueError('World resource must remain static')
    resources={'PROTOTYPE_BenFPV':derived,'PROTOTYPE_BenM4':modern}
    proofs={name:{'size':len(raw),'sha256':sha(raw),'item_model_field_hex':model_name_field(name).hex(),
                  'provenance':'DERIVE_DU_JEU' if name.endswith('FPV') else 'MODERNE_ORIGINAL',
                  'disabled':True,'runtime_status':'pending'} for name,raw in resources.items()}
    return resources,{'resources':proofs,'world_recipe_sha256':sha(json.dumps(recipe,sort_keys=True).encode()),
                      'item_table_modified':False,'item_slot_allocated':False}


def build(data,report,output,*,inspector=False,with_native_assets=False):
    derived,proof=derive(data['models/#fpvbeneliaim.4ds'])
    vertices,faces,names=geometry(derived)
    proof.update(size=len(derived),sha256=sha(derived),vertices=len(vertices),triangles=len(faces),
                 source='models/#fpvbeneliaim.4ds')
    report={**report,'derived_static':proof}
    inspector_html=None
    if inspector:
        from benelli_fpv_inspector import render
        inspector_html=render(data,STATES)  # validate every pair before writing
        report['inspector']={'pose_mode':'4ds_bind_pose_only','key_mode':'raw_samples_no_interpolation',
                             'animation_playback':False,'network_access':False,'private_only':True}
    aliases={}
    if with_native_assets:aliases,report['native_assets']=native_assets(derived)
    output.mkdir(parents=True,exist_ok=False)
    model_name='PROTOTYPE_HERITAGE_BenelliFPV.4ds.disabled'
    (output/model_name).write_bytes(derived)
    for name,raw in aliases.items():(output/(name+'.4ds.disabled')).write_bytes(raw)
    from model_wireframe import projection_png
    projection_png(vertices,faces,['DERIVE LOCAL / NON JOUABLE',*names],output/'preview.png')
    if inspector_html is not None:
        (output/'INSPECTEUR_LOCAL_NE_PAS_PARTAGER.html').write_text(inspector_html,encoding='utf-8')
    (output/'LIRE_AVANT_ESSAI.txt').write_text(
        'DERIVE DU JEU, USAGE LOCAL UNIQUEMENT. Ne pas redistribuer ce modele.\n'
        'Extraction et recalage modernes, geometrie et materiaux officiels.\n'
        'Aucune arme jouable, aucun Item ni son synchronise. Pas de deploiement.\n'
        'Le modele statique ne valide pas les animations ni les regles de tir.\n',encoding='utf-8')
    report['files']={p.name:sha(p.read_bytes()) for p in sorted(output.iterdir())}
    (output/'MANIFEST.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--output-name')
    parser.add_argument('--inspector',action='store_true',help='Include a private raw-key/static-model inspector; requires --output-name')
    parser.add_argument('--native-assets',action='store_true',help='Also generate both disabled assets with short native-table-compatible prototype names')
    args=parser.parse_args(argv)
    try:
        if (args.inspector or args.native_assets) and not args.output_name:
            raise ValueError('--inspector/--native-assets requires --output-name')
        output=output_directory(args.output_name) if args.output_name else None
        manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
        data,excluded=read_sources(args.game,manifest,archives_only=args.archives_only)
        report=audit(data,manifest,excluded)
        if output: report=build(data,report,output,inspector=args.inspector,with_native_assets=args.native_assets)
        print(json.dumps({'pairs':len(report['pairs']),'pinned_sources':len(report['sources']),
                          'frames':{k:v['frame_end_inclusive'] for k,v in report['pairs'].items()},
                          'derived_static':report.get('derived_static'),
                          'output':str(output) if output else None,'game_modified':False,
                          'playable_weapon':False,'runtime_status':'pending'},indent=2))
        return 0
    except (OSError,ValueError,KeyError,EOFError,wave.Error) as error:
        print('FPV laboratory refused: '+str(error),file=sys.stderr)
        return 1


if __name__=='__main__': raise SystemExit(main())
