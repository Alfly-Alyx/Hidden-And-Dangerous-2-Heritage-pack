#!/usr/bin/env python3
"""Build disabled original weapon-only rigid animation pairs, never install."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import build_modern_asset as asset
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import quaternion
import modern_animation as motion

ROOT=Path(__file__).resolve().parents[1]
CASES={'FG42':'FG42','MG34':'MG34_PORTABLE'}
ALIASES={'Idle1':'Idle','Aim':'Aim','Daim':'Daim','Arm':'Arm','Disarm':'Darm',
         'Shot':'Shot','AimShot':'ASht','Rel':'Rel','Jammed':'Jam'}


def euler(value):
    x,y,z=(math.radians(a) for a in asset.vector(value))
    if any(abs(a)>2*math.pi for a in (x,y,z)):raise ValueError('Rotation outside reviewed domain')
    sx,cx,sy,cy,sz,cz=math.sin(x),math.cos(x),math.sin(y),math.cos(y),math.sin(z),math.cos(z)
    # Rz * Ry * Rx, exactly the original static part-transform order.
    return quaternion([[cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx],
                       [sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx],
                       [-sy,cy*sx,cy*cx]])


def compile_bank(recipe,spec):
    if (spec.get('schema_version')!=1 or spec.get('provenance')!='MODERNE'
            or spec.get('runtime_status')!='pending' or spec.get('name') not in CASES):
        raise ValueError('Expected an original unvalidated bank')
    if set(spec)-{'schema_version','name','provenance','runtime_status','description',
                  'preview_fps','model_sha256','groups','clips'}:
        raise ValueError('Unknown bank fields, including functional bindings')
    fps=motion.integer(spec['preview_fps'],1,60,'authoring preview rate')
    meshes=asset.build_meshes(recipe);source=asset.encode_4ds(recipe,meshes)
    digest=hashlib.sha256(source).hexdigest()
    if digest!=spec['model_sha256']:raise ValueError('Modern source geometry changed')
    rig,report=motion.rig_model(source,spec['groups'])
    controls={'ROOT':(report['root'],[0,0,0])}
    controls.update({name:(name,pivot) for name,pivot in report['pivots'].items()})
    if not isinstance(spec['clips'],list) or len(spec['clips'])!=len(ALIASES):
        raise ValueError('Expected nine explicitly authored modern clips')
    clips={};reports={}
    for description in spec['clips']:
        if not isinstance(description,dict) or set(description)!={'name','frame_end','loop','motions'}:
            raise ValueError('Invalid modern clip description')
        name=description['name']
        if name not in ALIASES or name in clips or type(description['loop']) is not bool:
            raise ValueError('Invalid or duplicate modern clip')
        end=motion.integer(description['frame_end'],1,600,'modern clip length')
        motions=description['motions']
        if not isinstance(motions,dict) or set(motions)-set(controls):
            raise ValueError('Animation names an unknown pivot')
        tracks=[]
        for control,(node,pivot) in controls.items():
            keys=motions.get(control,[[0,[0,0,0],[0,0,0]],[end,[0,0,0],[0,0,0]]])
            if not isinstance(keys,list) or not 2<=len(keys)<=256:
                raise ValueError('Invalid authored motion keys')
            frames=[];positions=[];rotations=[]
            for key in keys:
                if not isinstance(key,list) or len(key)!=3:raise ValueError('Malformed motion key')
                frames.append(motion.integer(key[0],0,end,'motion frame'))
                positions.append([a+b for a,b in zip(pivot,asset.vector(key[1]))])
                rotations.append(euler(key[2]))
            if frames[0]!=0 or frames[-1]!=end:
                raise ValueError('Every control must define both clip boundaries')
            if description['loop'] and (positions[0]!=positions[-1] or
                    any(abs(a-b)>1e-8 for a,b in zip(rotations[0],rotations[-1]))):
                raise ValueError('Loop does not close')
            tracks.append({'name':node,'channels':{'rotation':{'frames':frames,'values':rotations},
                                                   'position':{'frames':frames,'values':positions}}})
        animation=motion.encode_5ds({'provenance':'MODERNE','runtime_status':'pending',
                                    'frame_end':end,'tracks':tracks})
        # Validate every integer frame under the explicitly modern interpolation.
        for frame in range(end+1):motion.pose(rig,animation,frame)
        stem=f"PROTOTYPE_{spec['name']}_{ALIASES[name]}"
        if len(stem.encode('ascii'))>19:raise ValueError('Native alias exceeds nineteen characters')
        clips[name]=(stem,animation)
        reports[name]={'stem':stem,'frame_end':end,'loop':description['loop'],
                       'tracks':len(tracks),'animation_sha256':hashlib.sha256(animation).hexdigest(),
                       'preview_seconds':end/fps,'engine_seconds':None}
    return rig,clips,meshes,{'schema_version':1,'provenance':'MODERNE','runtime_status':'pending',
             'model_source_sha256':digest,'rig_sha256':hashlib.sha256(rig).hexdigest(),
             'recipe_sha256':hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest(),
             'rig':report,'clips':reports,'preview_fps':fps,'native_fps_known':False,
             'interpolation':'MODERN_LOCAL_ABSOLUTE_LINEAR_POSITION_SHORTEST_ARC_SLERP',
             'commercial_assets_read':False,'game_modified':False,'game_launched':False,
             'player_hands':False,'player_skeleton_binding':False,'playable_weapon':False,
             'event_tracks':False,'sounds':False,'damage':False,'item_allocated':False}


def build(recipe,spec,output):
    rig,clips,meshes,report=compile_bank(recipe,spec)
    output.mkdir(parents=True,exist_ok=False)
    (output/f"PROTOTYPE_{spec['name']}_Rig.4ds.disabled").write_bytes(rig)
    for name,(stem,animation) in clips.items():
        companion=rig[:-1]+b'\1'
        if parse_4ds_nodes(companion)['has_animation']!=1:raise ValueError('Companion flag failed')
        if set(t['name'] for t in parse_5ds(animation)['tracks'])-set(n['name'] for n in parse_4ds_nodes(companion)['nodes']):
            raise ValueError('Unbound companion track')
        (output/(stem+'.4ds.disabled')).write_bytes(companion)
        (output/(stem+'.5ds.disabled')).write_bytes(animation)
    # Six static authored reload poses. This is not a captured native animation.
    from PIL import Image,ImageDraw
    contact=Image.new('RGB',(1600,1410),'#101820')
    draw=ImageDraw.Draw(contact)
    draw.text((24,15),f"MODERNE / {spec['name']} / RELOAD POSES / NO PLAYER HANDS / NOT ENGINE VALIDATED",fill='#d4bd80')
    end=report['clips']['Rel']['frame_end']
    for i,frame in enumerate((0,16,32,48,64,80)):
        actual=round(frame*end/80)
        posed=motion.animated_meshes(recipe,meshes,rig,clips['Rel'][1],actual)
        path=output/f"Rel_frame_{actual:03d}.png"
        asset.preview(recipe,posed,path)
        with Image.open(path) as preview:
            contact.paste(preview.resize((800,450)),((i%2)*800,60+(i//2)*450))
        draw.text(((i%2)*800+20,45+(i//2)*450),f"Authored frame {actual}/{end}",fill='white')
    contact.save(output/'reload_contact.png')
    report['companion_pairs']=len(clips)
    report['companion_auto_load_flag']=True
    report['companion_auto_load_engine_validated']=False
    report['files']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--output-name')
    args=parser.parse_args()
    folder=ROOT/'experimental'/CASES[args.case]
    recipe=json.loads((folder/'modern-world-model.json').read_text(encoding='utf-8'))
    spec=json.loads((folder/'modern-animation-bank.json').read_text(encoding='utf-8'))
    if args.output_name:
        report=build(recipe,spec,asset.output_directory(ROOT,args.output_name))
    else:
        report=compile_bank(recipe,spec)[3]
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
