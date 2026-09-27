#!/usr/bin/env python3
"""Private derived animations rebaked for the original flat FPV candidate.

Native hand/hose keys stay exact. Held visuals/anchors receive root-relative
positions; their rotations keep the original pivot keys. No game integration.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path
import struct

import build_modern_asset as asset
import modern_animation as motion
from build_modern_equipment_fpv_rig import compile_flat_rig
from build_equipment_hand_animation import compile_hand_bank,HAND_NAMES,PROVENANCE,IDENTITY
from build_equipment_hand_grips import RECIPE,posed_hand_mesh
from build_modern_equipment_assembly import CASES,ROOT,inputs
from build_modern_equipment_hose import digest,compile_hose_bank
from build_modern_animation_bank import ALIASES
from benelli_fpv_rig_audit import read_hands,HAND_MODELS,HAND_PINS
from animation_tick_audit import model_poses
from benelli_pose_chain_audit import key_window
from ls3d_pose_oracle import reference as pose_reference
from ls3d_palette_oracle import reference as palette_reference,product
from ls3d_skin_oracle import reference as skin_reference,transformed
from four_ds_skin import read_reviewed
from ls3d_math_oracle import f32
from menu_gui_audit import parse_4ds_nodes
from five_ds import parse_5ds,HEADER


def numeric_world(nodes,seeds,tracks,time):
    """Reviewed numeric reference, not a claim of actual native execution."""
    joints=[];poses={}
    for node in nodes:
        channels={kind:key_window(channel,time) for kind,channel in tracks.get(node['name'],{}).items()}
        slots=[{'active':True,'weight':1,'time':time,'channels':channels}] if channels else []
        pose=pose_reference(seeds[node['name']],slots)['pose'];poses[node['name']]=pose
        joints.append({**pose,'parent':node['parent_id']-1})
    result=palette_reference(joints,[IDENTITY]*len(nodes))
    return {n['name']:m for n,m in zip(nodes,result['world_matrices'])},poses


def constant(kind,row,end):
    return {kind:{'frames':[0,end],'values':[row[:],row[:]]}}


def position_curve(rows,end):
    blobs=[struct.pack('<3f',*row) for row in rows]
    if len(rows)!=end+1:raise ValueError('Incomplete flat position bake')
    same=all(blob==blobs[0] for blob in blobs)
    return {'frames':[0,end] if same else list(range(end+1)),
            'values':[rows[0],rows[-1]] if same else rows}


def rebake_clip(original,flat,rig_report,animation):
    """Called only on our freshly built original rig and private derived bank."""
    nodes=parse_4ds_nodes(original)['nodes'];flat_nodes=parse_4ds_nodes(flat)['nodes']
    clip=parse_5ds(animation);end=clip['frame_end'];tracks={t['name']:t['channels'] for t in clip['tracks']}
    names,seeds=model_poses(original);seeds=dict(zip(names,seeds));by_name={n['name']:n for n in nodes}
    if set(tracks)-set(names)-HAND_NAMES:raise ValueError('Unknown track during FPV rebake')
    if (digest(original)!=rig_report['source_sha256'] or digest(flat)!=rig_report['model_sha256']
            or not 1<=end<=179):raise ValueError('Changed source or unsupported FPV bake duration')
    root=rig_report['removed_dummy_root'];skin=rig_report['source_hose_skin'];pivot=by_name['MOD_held_pivot']
    dynamic=set()
    for node in nodes:
        current=node
        while current['parent_id']:
            if current['index']==pivot['index']:dynamic.add(node['name']);break
            current=nodes[current['parent_id']-1]
    samples={name:[] for name in names};root_rows=[]
    for frame in range(end+1):
        world,poses=numeric_world(nodes,seeds,tracks,frame*40)
        if any(poses[root][k]!=v for k,v in (('rotation',[0,0,0,1]),('scale',[1,1,1]))):
            raise ValueError('Unreviewed animated assembly root basis')
        if any(poses[skin][k]!=v for k,v in (('position',[0,0,0]),('rotation',[0,0,0,1]),('scale',[1,1,1]))):
            raise ValueError('Unreviewed local hose skin motion')
        offset=world[root][12:15];root_rows.append(offset)
        for name in names:samples[name].append([f32(a-b) for a,b in zip(world[name][12:15],offset)])
    # There is no normalization/conjugation of pre-existing native rotations.
    output=[{'name':t['name'],'channels':deepcopy(t['channels'])} for t in clip['tracks'] if t['name'] in HAND_NAMES]
    root_channels={'position':position_curve(root_rows,end),**constant('rotation',[0,0,0,1],end),
                   **constant('scale',[1,1,1],end)}
    output.append({'name':'fpv_weapon','channels':root_channels})
    bones=set()
    for node in nodes[1:]:
        name=node['name']
        if name==skin:continue
        if node['frame_type']==10:
            if not name.startswith('MOD_hose_bone_') or node['parent_id']!=by_name[skin]['index'] or name not in tracks:
                raise ValueError('Unreviewed skinned joint ownership')
            channels=deepcopy(tracks[name]);bones.add(name)
        else:
            channels={'position':position_curve(samples[name],end),**constant('scale',[1,1,1],end)}
            if name in dynamic:channels['rotation']=deepcopy(tracks['MOD_held_pivot']['rotation'])
            else:
                if len(channels['position']['frames'])!=2:raise ValueError('Unexpected non-held motion')
                channels.update(constant('rotation',[0,0,0,1],end))
        output.append({'name':rig_report['source_to_fpv_names'][name],'channels':channels})
    allowed=HAND_NAMES|{n['name'] for n in flat_nodes}
    raw=motion._encode_transform_tracks(end,output,preserve_native_rotations=True,
        name_validator=lambda name:name in allowed)
    if len(raw)-HEADER>0xf000:raise ValueError('Flat FPV clip exceeds reviewed native body size')
    if len(output)>128:raise ValueError('Too many flat FPV animation targets')
    actual={t['name']:t['channels'] for t in parse_5ds(raw)['tracks']}
    for name in (set(tracks)&HAND_NAMES)|bones:
        if actual[name]!=tracks[name]:raise ValueError('FPV rebake changed hand or hose keys')
    return raw,{'frames':end+1,'frame_end':end,'tracks':len(output),'bytes':len(raw),
        'hand_tracks':len(set(tracks)&HAND_NAMES),'preserved_hose_tracks':len(bones),
        'held_root_relative_tracks':len(dynamic),'hand_and_hose_channels_preserved':True,
        'original_clip_sha256':digest(animation),'animation_sha256':digest(raw),
        'root_ownership_changed':True,'native_loader_executed':False,'engine_validated':False}


def compile_fpv_bank(case,hand_raw,spec):
    flat,original,rig_report=compile_flat_rig(case)
    actual,source_clips,hand_report=compile_hand_bank(case,hand_raw,spec)
    if actual!=original:raise ValueError('Mismatched source rigs for flat FPV bake')
    variant='H' if hand_report['hand_source']==HAND_MODELS[0] else 'R'
    clips={};rows={}
    for name,(_,source) in source_clips.items():
        raw,report=rebake_clip(original,flat,rig_report,source)
        stem=f'PROTOTYPE_{case}{variant}{ALIASES[name]}'
        if len(stem)>19:raise ValueError('Flat FPV alias too long')
        clips[name]=(stem,raw);rows[name]={'stem':stem,**report}
    return flat,clips,{'schema_version':1,'case':case,'provenance':PROVENANCE,'runtime_status':'pending',
        'hand_source':hand_report['hand_source'],'hand_sha256':hand_report['hand_sha256'],
        'rig':rig_report,'clips':rows,'specification_sha256':hand_report['specification_sha256'],
        'original_animation_keys_read':False,'commercial_geometry_exported':False,
        'native_loader_executed':False,'native_clone_qualified':False,
        'camera_calibrated':False,'events_or_functional_weapon_implemented':False,
        'game_started':False,'game_modified':False,'engine_validated':False}


def flat_preview_meshes(case,rig,animation,time,lod=0):
    """Private geometric reference from flat SERIALIZED poses, not rendering."""
    if type(lod) is not int or lod not in (0,1):raise ValueError('Unknown preview LOD')
    clip=parse_5ds(animation);motion.integer(time,0,clip['frame_end']*40,'preview time')
    args=inputs(case);nodes=parse_4ds_nodes(rig)['nodes'];names,seeds=model_poses(rig)
    tracks={t['name']:t['channels'] for t in clip['tracks']}
    world,_=numeric_world(nodes,dict(zip(names,seeds)),tracks,time)
    meshes=[]
    for pair in asset.build_meshes(args[0]):
        if pair[0].name=='MOD_hose':continue
        meshes.append(tuple(asset.Mesh(mesh.name,mesh.material,
            [tuple(transformed(p,world[mesh.name])) for p in mesh.points],mesh.triangles) for mesh in pair))
    hose=read_reviewed(compile_hose_bank(*args)[0],allow_multiple_lods=True,lod=lod)
    by_index={n['index']:n for n in hose['nodes']}
    matrices=[product(inverse,world[by_index[node]['name']])
        for node,inverse in zip(hose['joint_node_indices'],hose['inverse_binds'])]
    values=skin_reference(hose['vertices'],hose['pairs'],matrices,hose['parents'])
    mesh=asset.Mesh('MOD_hose',3,[tuple(v[:3]) for v in values],
        [tuple(range(i,i+3)) for i in range(0,len(values),3)])
    mesh.validate();meshes.append((mesh,mesh));return meshes


def preview_bank(case,hand_raw,rig,clips,output):
    """Modern flat rig and private source hands; no camera qualification."""
    from PIL import Image,ImageDraw
    recipe=deepcopy(inputs(case)[0]);recipe['materials'].append(
        {'name':'private_hand_preview','diffuse':[.68,.65,.60]})
    source=next(name for name in HAND_MODELS if (len(hand_raw),digest(hand_raw))==HAND_PINS[name][1:])
    label=Path(source).stem;names,seeds=model_poses(hand_raw);seeds=dict(zip(names,seeds))
    samples=(('Idle1',0),('Aim',12),('Arm',0),('Arm',13.5),('Rel',32),('Jammed',16))
    contact=Image.new('RGB',(1600,1410),'#101820');draw=ImageDraw.Draw(contact)
    draw.text((24,15),f'DERIVE / PRIVATE HANDS / FLAT FPV SERIALIZED CLIPS / {case} / {label} / NOT GAME VALIDATED',fill='#d4bd80')
    for i,(name,frame) in enumerate(samples):
        raw=clips[name][1];clip=parse_5ds(raw);tracks={t['name']:t['channels'] for t in clip['tracks']}
        time=int(frame*40);poses={}
        for node in names:
            channels={kind:key_window(channel,time) for kind,channel in tracks[node].items()}
            poses[node]=pose_reference(seeds[node],[{'active':True,'weight':1,'time':time,'channels':channels}])['pose']
        meshes=flat_preview_meshes(case,rig,raw,time)
        hand=posed_hand_mesh(hand_raw,poses,len(recipe['materials']));meshes.append((hand,hand))
        path=output/f'{label}_{name}_{frame:05.1f}.png'
        asset.preview(recipe,meshes,path,labels=('PRIVE / MAINS DERIVEES / MONTAGE FPV APLATI',
            'Clips serialises - reference numerique - sans textures commerciales - hors moteur'))
        with Image.open(path) as picture:contact.paste(picture.resize((800,450)),((i%2)*800,60+(i//2)*450))
        draw.text(((i%2)*800+20,45+(i//2)*450),f'{name} / frame {frame}',fill='white')
    contact.save(output/(label+'_contact.png'))


def build(case,hands,spec,output,*,previews=False):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hand sources')
    for name,raw in hands.items():
        if (len(raw),digest(raw))!=HAND_PINS[name][1:]:raise ValueError('Changed pinned hand source')
    banks=[compile_fpv_bank(case,hands[name],spec) for name in HAND_MODELS]
    if banks[0][0]!=banks[1][0]:raise ValueError('Hand variant changed flat FPV geometry')
    output.mkdir(parents=True,exist_ok=False)
    (output/f'PROTOTYPE_{case}_FPV.4ds.disabled').write_bytes(banks[0][0])
    for _,clips,_ in banks:
        for stem,raw in clips.values():(output/(stem+'.5ds.disabled')).write_bytes(raw)
    if previews:
        for (rig,clips,_),source in zip(banks,HAND_MODELS):preview_bank(case,hands[source],rig,clips,output)
    report={'schema_version':1,'provenance':PROVENANCE,'runtime_status':'pending','private_only':True,
        'variants':{row['hand_source']:row for _,_,row in banks},
        'commercial_hand_models_exported':False,'auto_load_companions_created':False,
        'private_derived_previews_created':previews,'preview_is_native_game_rendering':False,
        'files':{p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--game',required=True,type=Path);parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--output-name');parser.add_argument('--previews',action='store_true');args=parser.parse_args(argv)
    try:
        hands,excluded=read_hands(args.game,archives_only=args.archives_only);spec=json.loads(RECIPE.read_text(encoding='utf-8'))
        if args.previews and not args.output_name:raise ValueError('Previews require a fresh private output directory')
        if args.output_name:report=build(args.case,hands,spec,asset.output_directory(ROOT,args.output_name),previews=args.previews)
        else:report={'variants':{name:compile_fpv_bank(args.case,hands[name],spec)[2] for name in HAND_MODELS}}
        report['excluded_loose_overrides']=excluded;print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private flat FPV animation refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
