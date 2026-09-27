#!/usr/bin/env python3
"""Private derived-hand previews with modern authored grips on original equipment.

Commercial hand geometry/rest skeleton is read under source pins, never written
as a model or published. This stage produces previews, not native clips/FPV.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path

import build_modern_asset as asset
from build_modern_equipment_assembly import inputs,compile_assembly,assembly_preview,CASES,ROOT
from build_modern_equipment_hose import compile_hose_bank,DIRECTORY,digest
from benelli_fpv_rig_audit import read_hands,HAND_MODELS,HAND_PINS
from four_ds_skin import read_reviewed
from hand_pose_ik import author_pose,vector,validate_basis
from menu_gui_audit import parse_4ds_nodes
from model_transform import matmul,matvec
from ls3d_palette_oracle import reference as palette_reference
from ls3d_skin_oracle import reference as skin_reference
import modern_animation as motion

RECIPE=DIRECTORY/'modern-hand-grips.json'
SAMPLES=(('Idle1',0),('Aim',12),('Arm',0),('Disarm',24),('Rel',32),('Jammed',16))


def validate_spec(spec,case,rig):
    fields={'schema_version','provenance','runtime_status','description','assembly_sha256','equipment_translation','hands','case_overrides'}
    if (not isinstance(spec,dict) or set(spec)!=fields or spec['schema_version']!=1
            or spec['provenance']!='MODERNE_SUR_SOURCE_COMMERCIALE' or spec['runtime_status']!='pending'
            or set(spec['assembly_sha256'])!=set(CASES) or spec['assembly_sha256'].get(case)!=digest(rig)
            or set(spec['hands'])!={'L','R'}):raise ValueError('Changed or unreviewed modern grip specification')
    vector(spec['equipment_translation'])
    overrides=spec['case_overrides']
    if (not isinstance(overrides,dict) or set(overrides)-set(CASES)
            or any(not isinstance(row,dict) or set(row)-{'L','R'} for row in overrides.values())):
        raise ValueError('Unreviewed case-specific grips')
    for row in overrides.values():
        for hand in row.values():
            if not isinstance(hand,dict) or set(hand)-{'rest_to_equipment_rotation','contact_offset'}:
                raise ValueError('Unreviewed grip override')
    for hand in effective_hands(spec,case).values():
        if set(hand)!={'rest_to_equipment_rotation','wrist_to_contact_in_rest','contact_offset','elbow_pole','finger_curl_degrees'}:
            raise ValueError('Unreviewed grip fields')
        validate_basis(hand['rest_to_equipment_rotation'])
        for key in ('wrist_to_contact_in_rest','contact_offset','elbow_pole'):vector(hand[key])


def effective_hands(spec,case):
    hands=deepcopy(spec['hands'])
    for side,values in spec['case_overrides'].get(case,{}).items():hands[side].update(values)
    return hands


def targets(rig,animation,frame,spec,case):
    nodes={n['name']:n for n in parse_4ds_nodes(rig)['nodes']};posed=motion.pose(rig,animation,frame)
    held=posed[nodes['MOD_held_pivot']['index']][0];result={}
    hands=effective_hands(spec,case)
    for side,label in (('L','left'),('R','right')):
        hand=hands[side];basis=matmul(held,hand['rest_to_equipment_rotation'])
        anchor=posed[nodes['MOD_'+label+'_hand']['index']][1]
        contact=matvec(held,hand['contact_offset']);palm=matvec(basis,hand['wrist_to_contact_in_rest'])
        result[side]={'position':[a+b+c-d for a,b,c,d in zip(anchor,spec['equipment_translation'],contact,palm)],
                      'rotation':basis,'pole':hand['elbow_pole'][:]}
    return result


def posed_hand_mesh(raw,poses,material):
    skin=read_reviewed(raw,include_faces=True);by_index={n['index']:n for n in skin['nodes']}
    bone_by_node={node:i for i,node in enumerate(skin['joint_node_indices'])}
    joints=[]
    for index in skin['joint_node_indices']:
        node=by_index[index];parent=node['parent_id']
        joints.append({**poses[node['name']],'parent':-1 if parent==1 else bone_by_node[parent]})
    palette=palette_reference(joints,skin['inverse_binds'])['palette']
    values=skin_reference(skin['vertices'],skin['pairs'],palette,skin['parents'])
    # Pinned commercial hands contain 22 repeated-index triangles each. They
    # have no surface, even at rest. Omit them only from this private preview;
    # no commercial model, index buffer or native skin input is rewritten.
    triangles=[tuple(face) for group in skin['face_groups'] for face in group['triangles'] if len(set(face))==3]
    mesh=asset.Mesh('DERIVED_fpv_hands',material,[tuple(v[:3]) for v in values],triangles)
    mesh.validate();return mesh


def compile_grips(case,hands,spec):
    if set(hands)!=set(HAND_PINS):raise ValueError('Incomplete pinned hand source set')
    for name,raw in hands.items():
        if (len(raw),digest(raw))!=HAND_PINS[name][1:]:raise ValueError('Changed pinned hand source')
    args=inputs(case);rig,clips,assembly=compile_assembly(*args);validate_spec(spec,case,rig)
    grips={side:{'finger_curl_degrees':hand['finger_curl_degrees']} for side,hand in effective_hands(spec,case).items()}
    rows={};previews={}
    for source in HAND_MODELS:
        stats={'poses':0,'max_wrist_error':0,'max_local_position_residual':0,'max_local_scale_residual':0}
        geometry=read_reviewed(hands[source],include_faces=True)
        degenerate=sum(len(set(face))!=3 for group in geometry['face_groups'] for face in group['triangles'])
        if degenerate!=22:raise ValueError('Reviewed hand preview degenerates changed')
        stats['source_repeated_index_triangles_omitted_from_preview']=degenerate
        stats['source_triangles']=geometry['report']['triangles']
        for name,(_,animation) in clips.items():
            end=assembly['clips'][name]['frame_end']
            for frame in range(end+1):
                poses,report=author_pose(hands[source],targets(rig,animation,frame,spec,case),grips)
                stats['poses']+=1;stats['max_wrist_error']=max(stats['max_wrist_error'],*[r['wrist_error'] for r in report['arms'].values()])
                for key in ('max_local_position_residual','max_local_scale_residual'):stats[key]=max(stats[key],report[key])
                if (name,frame) in SAMPLES:previews[(source,name,frame)]=poses
        rows[source]={'sha256':HAND_PINS[source][2],**stats}
    return (rig,clips,previews),{'schema_version':1,'case':case,'provenance':'DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL',
        'runtime_status':'pending','assembly_sha256':assembly['rig_sha256'],
        'specification_sha256':digest(json.dumps(spec,sort_keys=True).encode()),'variants':rows,
        'authored_grip_targets':True,'commercial_hand_geometry_used_privately':True,'commercial_textures_rendered':False,
        'commercial_geometry_or_keys_exported':False,'original_hand_geometry_modified':False,
        'original_animation_keys_read':False,'native_clips_created':False,'thumb_pose_authored':False,
        'finger_contact_qualified':False,'camera_calibrated':False,'native_loader_executed':False,
        'player_or_ai_attachment_qualified':False,'engine_validated':False,'game_started':False,'game_modified':False}


def build(case,hands,spec,output):
    (rig,clips,poses),report=compile_grips(case,hands,spec);args=inputs(case)
    hose=compile_hose_bank(*args)[0];recipe=deepcopy(args[0])
    recipe['materials'].append({'name':'private_hand_preview','diffuse':[.68,.65,.60]})
    output.mkdir(parents=True,exist_ok=False)
    from PIL import Image,ImageDraw
    for source in HAND_MODELS:
        label=Path(source).stem;contact=Image.new('RGB',(1600,1410),'#101820');draw=ImageDraw.Draw(contact)
        draw.text((24,15),f'DERIVE / PRIVATE COMMERCIAL HANDS / MODERN GRIPS / {case} / {label} / NOT ENGINE VALIDATED',fill='#d4bd80')
        for i,(name,frame) in enumerate(SAMPLES):
            meshes=assembly_preview(args[0],rig,clips[name][1],frame,hose)
            meshes=[tuple(asset.Mesh(m.name,m.material,[tuple(a+b for a,b in zip(p,spec['equipment_translation']))
                     for p in m.points],m.triangles) for m in pair) for pair in meshes]
            hand=posed_hand_mesh(hands[source],poses[(source,name,frame)],len(recipe['materials']));meshes.append((hand,hand))
            path=output/f'{label}_{name}_{frame:03d}.png'
            asset.preview(recipe,meshes,path,labels=('PRIVE / MAINS DERIVEES DU JEU / POSES MODERNES',
                'Equipement original moderne - mains commerciales grisees - sans textures originales - hors moteur'))
            with Image.open(path) as picture:contact.paste(picture.resize((800,450)),((i%2)*800,60+(i//2)*450))
            draw.text(((i%2)*800+20,45+(i//2)*450),f'{name} / authored frame {frame}',fill='white')
        contact.save(output/(label+'_contact.png'))
    report['files']={p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--output-name');args=parser.parse_args(argv)
    try:
        hands,excluded=read_hands(args.game,archives_only=args.archives_only);spec=json.loads(RECIPE.read_text(encoding='utf-8'))
        if args.output_name:report=build(args.case,hands,spec,asset.output_directory(ROOT,args.output_name))
        else:report=compile_grips(args.case,hands,spec)[1]
        report['excluded_loose_overrides']=excluded
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private modern hand grip refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
