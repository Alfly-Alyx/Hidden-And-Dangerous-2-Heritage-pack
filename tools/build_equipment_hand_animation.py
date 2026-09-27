#!/usr/bin/env python3
"""Private derived native clips: authored hands and modern equipment together.

Only commercial REST skeletons are used, under exact pins. No original
animation keys are read. Derived clips contain source-dependent transforms
and must stay private; original hand geometry is never exported.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path
import struct

import build_modern_asset as asset
import modern_animation as motion
from build_equipment_hand_grips import RECIPE,validate_spec,effective_hands,posed_hand_mesh
from build_modern_equipment_assembly import inputs,compile_assembly,assembly_preview,CASES,ROOT
from build_modern_equipment_hose import digest,compile_hose_bank
from build_modern_animation_bank import ALIASES
from benelli_fpv_rig_audit import read_hands,HAND_MODELS,HAND_PINS
from hand_pose_ik import author_pose,pinned_skin
from five_ds import parse_5ds
from animation_tick_audit import model_poses
from benelli_pose_chain_audit import key_window
from ls3d_pose_oracle import reference as pose_reference
from ls3d_palette_oracle import reference as palette_reference
from model_transform import matmul,matvec
from menu_gui_audit import parse_4ds_nodes

PROVENANCE='DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL'
PARTS=('Clavicle','UpperArm','Forearm','Hand','Finger0','Finger01')+tuple(
    'Finger'+str(finger)+suffix for finger in range(1,5) for suffix in ('','1','2'))
HAND_NAMES=frozenset({'a',*(f'Bip01 {side} {part}' for side in ('L','R') for part in PARTS)})
IDENTITY=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]


def wrist_from_native(held,anchor,hand):
    """Modern grip offset from native-convention held and anchor matrices."""
    basis=[[held[i+4*j] for j in range(3)] for i in range(3)]
    contact=matvec(basis,hand['contact_offset'])
    palm=matvec(matmul(basis,hand['rest_to_equipment_rotation']),hand['wrist_to_contact_in_rest'])
    return [a+b-c for a,b,c in zip(anchor[12:15],contact,palm)]


def native_grip_targets(rig,animation,frame,spec,case):
    """Author against the reviewed native numeric reference, not ideal Slerp.

    In particular abs(w)>=1 yields an identity native basis, even when tiny
    serialized xyz components are nonzero. No emulation is claimed here;
    a separate native audit checks the produced clips.
    """
    parsed=parse_5ds(animation);motion.integer(frame,0,parsed['frame_end'],'grip frame')
    nodes=parse_4ds_nodes(rig)['nodes'];by_name={n['name']:n for n in nodes}
    names,seeds=model_poses(rig);seeds=dict(zip(names,seeds))
    tracks={t['name']:t['channels'] for t in parsed['tracks']};held=by_name['MOD_held_pivot']
    held_root=nodes[held['parent_id']-1];root=nodes[held_root['parent_id']-1]
    selected=[root,held_root,held,by_name['MOD_left_hand'],by_name['MOD_right_hand']]
    parents=(-1,0,1,2,2);joints=[];time=frame*40
    for node,parent in zip(selected,parents):
        if node['parent_id']!=(0 if parent==-1 else selected[parent]['index']):
            raise ValueError('Unreviewed diagnostic held hierarchy')
        curves={kind:key_window(channel,time) for kind,channel in tracks.get(node['name'],{}).items()}
        slots=[{'active':True,'weight':1,'time':time,'channels':curves}] if curves else []
        pose=pose_reference(seeds[node['name']],slots)['pose']
        if parent==-1:
            if any(pose['position']):raise ValueError('Unexpected assembly root position')
            pose['position']=f32_row(spec['equipment_translation'],3)
        joints.append({**pose,'parent':parent})
    world=palette_reference(joints,[IDENTITY]*5)['world_matrices'];matrix=world[2]
    basis=[[matrix[i+4*j] for j in range(3)] for i in range(3)];hands=effective_hands(spec,case)
    return {side:{'position':wrist_from_native(matrix,world[anchor],hands[side]),
        'rotation':matmul(basis,hands[side]['rest_to_equipment_rotation']),
        'pole':hands[side]['elbow_pole'][:]} for side,anchor in (('L',3),('R',4))}


def derived_name(name):
    return name in HAND_NAMES or (motion.NAME.fullmatch(name) and name.startswith(('MOD_','PROTOTYPE_')))


def encode_derived_clip(clip):
    """Separate provenance gate; no relabeling as a wholly original clip."""
    if (not isinstance(clip,dict) or set(clip)!={'provenance','runtime_status','frame_end','tracks'}
            or clip['provenance']!=PROVENANCE or clip['runtime_status']!='pending'):
        raise ValueError('Not an explicitly private derived hand clip')
    raw=motion._encode_transform_tracks(clip['frame_end'],clip['tracks'],
        preserve_native_rotations=True,name_validator=derived_name)
    if len(raw)-18>0xf000:raise ValueError('Derived clip exceeds reviewed native body size')
    if any(len(channel['frames'])>180 for track in clip['tracks'] for channel in track['channels'].values()):
        raise ValueError('Derived clip exceeds reviewed native key count')
    return raw


def f32_row(values,width):
    values=asset.vector(values,width)
    return list(struct.unpack('<'+'f'*width,struct.pack('<'+'f'*width,*values)))


def bake_tracks(samples,names,end):
    """Bake integer-frame authored poses; compress only bit-equal constants."""
    motion.integer(end,1,179,'derived bake end')
    if (not isinstance(names,list) or len(names)!=37 or set(names)!=HAND_NAMES
            or not isinstance(samples,list) or len(samples)!=end+1):
        raise ValueError('Incomplete reviewed hand bake')
    for sample in samples:
        if not isinstance(sample,dict) or set(sample)!=HAND_NAMES:
            raise ValueError('Missing authored hand node')
        if any(not isinstance(pose,dict) or set(pose)!={'position','rotation','scale'} for pose in sample.values()):
            raise ValueError('Incomplete authored hand transform')
    tracks=[]
    for name in names:
        channels={}
        for kind,width in (('position',3),('rotation',4),('scale',3)):
            rows=[f32_row(sample[name][kind],width) for sample in samples]
            if kind=='rotation':
                for row in rows:motion.unit_quaternion(row)
            constant=all(struct.pack('<'+'f'*width,*row)==struct.pack('<'+'f'*width,*rows[0]) for row in rows)
            if kind!='rotation' and not constant:raise ValueError('Hand bake moved or stretched a bone')
            channels[kind]={'frames':[0,end] if constant else list(range(end+1)),
                            'values':[rows[0],rows[-1]] if constant else rows}
        tracks.append({'name':name,'channels':channels})
    return tracks


def combine_tracks(hand_tracks,assembly_animation,root,translation):
    """Retain every modern track; add only the authoring-space root offset."""
    clip=parse_5ds(assembly_animation);end=clip['frame_end'];translation=list(asset.vector(translation))
    tracks=deepcopy(hand_tracks)+[{'name':t['name'],'channels':deepcopy(t['channels'])} for t in clip['tracks']]
    if not motion.NAME.fullmatch(root) or not root.startswith('PROTOTYPE_'):
        raise ValueError('Unreviewed modern assembly root')
    tracks.append({'name':root,'channels':{'position':{'frames':[0,end],'values':[translation[:],translation[:]]}}})
    raw=encode_derived_clip({'provenance':PROVENANCE,'runtime_status':'pending','frame_end':end,'tracks':tracks})
    parsed=parse_5ds(raw)
    # No quantization, conjugation or renormalization of existing native keys.
    actual={t['name']:t['channels'] for t in parsed['tracks']}
    for track in clip['tracks']:
        if actual[track['name']]!=track['channels']:raise ValueError('Modern assembly key changed during hand merge')
    return raw


def compile_hand_bank(case,raw,spec):
    source,skin=pinned_skin(raw)
    names=[n['name'] for n in skin['nodes']]
    if len(names)!=37 or set(names)!=HAND_NAMES:raise ValueError('Reviewed hand hierarchy changed')
    rig,assembly_clips,assembly=compile_assembly(*inputs(case));validate_spec(spec,case,rig)
    grips={side:{'finger_curl_degrees':hand['finger_curl_degrees']} for side,hand in effective_hands(spec,case).items()}
    clips={};reports={};count=0
    variant='H' if source==HAND_MODELS[0] else 'R'
    for name,(_,animation) in assembly_clips.items():
        end=assembly['clips'][name]['frame_end']
        samples=[author_pose(raw,native_grip_targets(rig,animation,frame,spec,case),grips,
            arm_rotation_policy='bend_plane')[0] for frame in range(end+1)]
        tracks=bake_tracks(samples,names,end)
        combined=combine_tracks(tracks,animation,assembly['root'],spec['equipment_translation'])
        stem=f'PROTOTYPE_{case}_{variant}{ALIASES[name]}'
        if len(stem)>19:raise ValueError('Derived clip alias too long')
        clips[name]=(stem,combined);parsed=parse_5ds(combined);count+=end+1
        reports[name]={'stem':stem,'frame_end':end,'tracks':parsed['track_count'],'bytes':len(combined),
            'sha256':digest(combined),'dense_hand_rotation_tracks':sum(len(t['channels']['rotation']['frames'])>2 for t in tracks)}
    return rig,clips,{'schema_version':1,'case':case,'provenance':PROVENANCE,'runtime_status':'pending',
        'hand_source':source,'hand_sha256':HAND_PINS[source][2],'assembly_sha256':digest(rig),
        'specification_sha256':digest(json.dumps(spec,sort_keys=True).encode()),'authored_integer_poses':count,
        'clips':reports,'source_rest_positions_and_scales_in_private_clips':True,'native_rotations_preserved':True,
        'targets_follow_native_numeric_rotation_and_pose_reference':True,
        'arm_rotation_policy':'bend_plane',
        'original_animation_keys_read':False,'commercial_geometry_exported':False,'commercial_textures_exported':False,
        'native_loader_executed':False,'time_unit_seconds_qualified':False,'finger_contact_qualified':False,
        'thumb_pose_authored':False,'camera_calibrated':False,'player_or_ai_attachment_qualified':False,
        'events_or_functional_weapon_implemented':False,'game_started':False,'game_modified':False,'engine_validated':False}


def preview_bank(case,hand_raw,rig,clips,output):
    """Private geometric previews sampled from SERIALIZED derived clips."""
    from PIL import Image,ImageDraw
    args=inputs(case);recipe=deepcopy(args[0]);hose=compile_hose_bank(*args)[0]
    recipe['materials'].append({'name':'private_hand_preview','diffuse':[.68,.65,.60]})
    source,_=pinned_skin(hand_raw);label=Path(source).stem
    names,seeds=model_poses(hand_raw);seeds=dict(zip(names,seeds))
    samples=(('Idle1',0),('Aim',12),('Arm',0),('Arm',13.5),('Rel',32),('Jammed',16))
    contact=Image.new('RGB',(1600,1410),'#101820');draw=ImageDraw.Draw(contact)
    draw.text((24,15),f'DERIVE / PRIVATE SOURCE HANDS / SERIALIZED CLIPS / {case} / {label} / NOT GAME VALIDATED',fill='#d4bd80')
    for i,(name,frame) in enumerate(samples):
        clip=parse_5ds(clips[name][1]);tracks={t['name']:t['channels'] for t in clip['tracks']}
        time=int(frame*40);poses={}
        for node in names:
            channels={kind:key_window(channel,time) for kind,channel in tracks[node].items()}
            poses[node]=pose_reference(seeds[node],[{'active':True,'weight':1,'time':time,'channels':channels}])['pose']
        gear=encode_derived_clip({'provenance':PROVENANCE,'runtime_status':'pending','frame_end':clip['frame_end'],
            'tracks':[{'name':t['name'],'channels':t['channels']} for t in clip['tracks'] if t['name'] not in HAND_NAMES]})
        meshes=assembly_preview(args[0],rig,gear,frame,hose)
        hand=posed_hand_mesh(hand_raw,poses,len(recipe['materials']));meshes.append((hand,hand))
        filename=f'{label}_{name}_{frame:05.1f}.png';path=output/filename
        asset.preview(recipe,meshes,path,labels=('PRIVE / MAINS DERIVEES / CLIPS MODERNES SERIALISES',
            'Mains commerciales grisees - flexion moderne des bras - apercu geometrique hors moteur'))
        with Image.open(path) as picture:contact.paste(picture.resize((800,450)),((i%2)*800,60+(i//2)*450))
        draw.text(((i%2)*800+20,45+(i//2)*450),f'{name} / frame {frame}',fill='white')
    contact.save(output/(label+'_contact.png'))


def build(case,hands,spec,output,*,previews=False):
    # Validate the complete reader contract before creating any output.
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hand sources')
    for source,data in hands.items():
        if (len(data),digest(data))!=HAND_PINS[source][1:]:raise ValueError('Changed pinned hand source')
    banks=[compile_hand_bank(case,hands[source],spec) for source in HAND_MODELS]
    if banks[0][0]!=banks[1][0]:raise ValueError('Hand variants changed modern geometry')
    output.mkdir(parents=True,exist_ok=False)
    # No hand model and no auto-loading companion: binding to a loaded scene
    # has not been qualified. Every generated binary remains disabled.
    (output/f'PROTOTYPE_{case}_ARig.4ds.disabled').write_bytes(banks[0][0])
    for _,clips,_ in banks:
        for stem,animation in clips.values():(output/(stem+'.5ds.disabled')).write_bytes(animation)
    if previews:
        for (rig,clips,_),source in zip(banks,HAND_MODELS):preview_bank(case,hands[source],rig,clips,output)
    report={'schema_version':1,'provenance':PROVENANCE,'runtime_status':'pending','private_only':True,
        'variants':{row['hand_source']:row for _,_,row in banks},
        'commercial_hand_model_exported':False,'auto_load_companions_created':False,
        'private_derived_previews_created':previews,'preview_is_native_game_rendering':False,
        'files':{p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--output-name')
    parser.add_argument('--previews',action='store_true');args=parser.parse_args(argv)
    try:
        hands,excluded=read_hands(args.game,archives_only=args.archives_only);spec=json.loads(RECIPE.read_text(encoding='utf-8'))
        if args.previews and not args.output_name:raise ValueError('Previews require a fresh private output directory')
        if args.output_name:report=build(args.case,hands,spec,asset.output_directory(ROOT,args.output_name),previews=args.previews)
        else:report={'variants':{name:compile_hand_bank(args.case,hands[name],spec)[2] for name in HAND_MODELS}}
        report['excluded_loose_overrides']=excluded
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private derived hand animation refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
