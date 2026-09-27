#!/usr/bin/env python3
"""Original two-LOD skinned visual hose, synchronized to authored held motions.

No physical simulation, arbitrary-pose solver, player attachment or gameplay.
No commercial geometry, animation key or native library is read by this builder.
"""
import argparse
import hashlib
import json
import math

import build_modern_asset as asset
from build_modern_equipment_animation import inputs as held_inputs,compile_equipment_bank
from build_modern_equipment_components import CASES,DIRECTORY,ROOT,compile_components
from build_modern_animation_bank import ALIASES
from five_ds import parse_5ds
from four_ds_skin import read_reviewed
from menu_gui_audit import parse_4ds_nodes
from model_transform import conjugate,compose,point
import modern_animation as motion


def digest(value):return hashlib.sha256(value).hexdigest()


def header(name,position=(0,0,0),parent=1):
    return (asset.pack('H3f4f3ffB',parent,*position,0,0,0,1,1,1,1,0,9)
            +asset.counted(name)+asset.counted('MODERNE;Heritage;visual_hose_skin;pending'))


def bounds(points):
    return [v for fn in (min,max) for v in
            (*[fn(p[i] for p in points) for i in range(3)],0)]


def bone_for_vertex(index,rings,sides):
    if index<rings*sides:return index//sides
    if index==rings*sides:return 0
    if index==rings*sides+1:return rings-1
    raise ValueError('Unknown capped sweep vertex')


def encode_skin(recipe,meshes,hose,pivot,name):
    """Keep both original hose LOD vertex/index/material payloads; add a skin."""
    source=asset.encode_4ds(recipe,meshes);model=parse_4ds_nodes(source)
    levels=next(pair for pair in meshes if pair[0].name=='MOD_hose')
    rings=len(hose['path']);names=[f'MOD_hose_bone_{i:02d}' for i in range(rings)]
    if not 4<=rings<=64:raise ValueError('Unreviewed hose ring count')
    raw=bytearray(source[:model['node_count_offset']]);raw.extend(asset.pack('H',rings+1))
    root='PROTOTYPE_HERITAGE_'+name+'_HoseSkin'
    raw.extend(asset.pack('BBH',1,2,0x1800)+header(root,parent=0)+asset.pack('HB',0,2))
    pair_levels=[]
    for lod,(mesh,distance) in enumerate(zip(levels,(25,0))):
        vertices=mesh.expanded();sides=hose['segments'] if lod==0 else max(6,hose['segments']//2)
        if len(mesh.points)!=rings*sides+2 or len(vertices)>2048:
            raise ValueError('Unreviewed hose topology or vertex budget')
        pairs=[[bone_for_vertex(i,rings,sides)+1,0] for face in mesh.triangles for i in face]
        pair_levels.append(pairs)
        raw.extend(asset.pack('fIH',distance,0,len(vertices)))
        for vertex in vertices:raw.extend(asset.pack('8f',*vertex))
        raw.extend(asset.pack('BH',1,len(mesh.triangles)))
        for i in range(0,len(vertices),3):raw.extend(asset.pack('3H',i,i+1,i+2))
        raw.extend(asset.pack('H',mesh.material))
    raw.extend(bytes([rings])+asset.pack('8f',*bounds(levels[0].points))+bytes(rings))
    # Independent influence frames share the held pivot, not the ring centers.
    # This gives the terminal ring EXACTLY the held rigid transform even between
    # keys, instead of approximating its curved path with linear center keys.
    inverse=[1,0,0,0,0,1,0,0,0,0,1,0,*[-v for v in pivot],1]
    for bone in range(rings):
        points=[asset.sub(p,pivot) for i,p in enumerate(levels[0].points)
                if bone_for_vertex(i,rings,hose['segments'])==bone]
        raw.extend(asset.pack('16f',*inverse)+asset.pack('8f',*bounds(points)))
    for pairs in pair_levels:
        raw.extend(asset.pack('I',len(pairs)))
        raw.extend(bytes(value for pair in pairs for value in pair))
    for i,bone in enumerate(names):raw.extend(b'\x0a'+header(bone,pivot)+asset.pack('I',i))
    raw.extend(b'\0');raw=bytes(raw)
    for lod,mesh in enumerate(levels):
        checked=read_reviewed(raw,allow_multiple_lods=True,lod=lod)
        if checked['pairs']!=pair_levels[lod] or checked['report']['triangles']!=len(mesh.triangles):
            raise ValueError('Skin LOD readback differs')
        original=mesh.expanded()
        encoded=b''.join(asset.pack('8f',*v) for v in original)
        reread=b''.join(asset.pack('8f',*v) for v in checked['vertices'])
        if encoded!=reread:raise ValueError('Original hose vertices changed')
    return raw,levels,names


def influence_weights(path):
    lengths=[0.0]
    for a,b in zip(path,path[1:]):lengths.append(lengths[-1]+math.dist(a,b))
    # First two rings stay on the fixed pack; last two follow the held piece.
    start,end=lengths[1],lengths[-2]
    if end-start<1e-6:raise ValueError('Insufficient middle hose span')
    result=[]
    for distance in lengths:
        t=max(0,min(1,(distance-start)/(end-start)))
        result.append(t*t*t*(t*(6*t-15)+10))
    return result


def skin_mesh(raw,animation,frame,lod=0):
    """Offline geometry preview, using serialized skin/binds/weights, not a re-sweep."""
    skin=read_reviewed(raw,allow_multiple_lods=True,lod=lod)
    transforms=motion.pose(raw,animation,frame);palettes=[]
    for node,values in zip(skin['joint_node_indices'],skin['inverse_binds']):
        inverse=([[values[i+j*4] for j in range(3)] for i in range(3)],values[12:15])
        palettes.append(compose(transforms[node],inverse))
    points=[]
    for vertex,(bone,byte) in zip(skin['vertices'],skin['pairs']):
        if byte:raise ValueError('Unreviewed modern hose blend byte')
        points.append(tuple(point(palettes[bone-1],vertex[:3])))
    mesh=asset.Mesh('MOD_hose',3,points,[tuple(range(i,i+3)) for i in range(0,len(points),3)])
    mesh.validate();return mesh


def compile_hose_bank(recipe,partition,held_spec,spec):
    keys={'schema_version','name','provenance','runtime_status','description',
          'held_rig_sha256','held_recipe_sha256','method'}
    if (not isinstance(spec,dict) or set(spec)!=keys or spec['schema_version']!=1
            or spec['name']!=partition['name'] or spec['name'] not in CASES
            or spec['provenance']!='MODERNE' or spec['runtime_status']!='pending'
            or spec['method']!='independent_ring_frames_smootherstep_fixed_pack_authored_held'):
        raise ValueError('Expected reviewed original visual hose specification')
    held,held_clips,_,held_report=compile_equipment_bank(recipe,partition,held_spec)
    if (digest(held)!=spec['held_rig_sha256'] or held_report['recipe_sha256']!=spec['held_recipe_sha256']):
        raise ValueError('Held animation source changed')
    components,_=compile_components(recipe,partition)
    pivot=components['held']['report']['source_origin'];meshes=asset.build_meshes(recipe)
    hose=next(p for p in recipe['parts'] if p['name']=='MOD_hose')
    if hose.get('closed',False) or hose.get('transform'):raise ValueError('Expected open original hose')
    raw,levels,bones=encode_skin(recipe,meshes,hose,pivot,spec['name'])
    weights=influence_weights(hose['path']);clips={};reports={}
    root=parse_4ds_nodes(raw)['nodes'][0]['name']
    for name,(held_alias,held_data) in held_clips.items():
        parsed=parse_5ds(held_data);end=parsed['frame_end']
        track=next(t for t in parsed['tracks'] if t['name']=='MOD_held_pivot')
        frames=track['channels']['position']['frames']
        if frames!=track['channels']['rotation']['frames']:raise ValueError('Held SRT keys differ')
        tracks=[{'name':root,'channels':{
            'position':{'frames':[0,end],'values':[[0,0,0],[0,0,0]]},
            'rotation':{'frames':[0,end],'values':[[0,0,0,1],[0,0,0,1]]}}}]
        for bone,weight in zip(bones,weights):
            positions=[[p+weight*v for p,v in zip(pivot,key)] for key in track['channels']['position']['values']]
            rotations=[motion.slerp([0,0,0,1],conjugate(q),weight) for q in track['channels']['rotation']['values']]
            tracks.append({'name':bone,'channels':{'position':{'frames':frames,'values':positions},
                                                  'rotation':{'frames':frames,'values':rotations}}})
        animation=motion.encode_5ds({'provenance':'MODERNE','runtime_status':'pending','frame_end':end,'tracks':tracks})
        stem=f"PROTOTYPE_{spec['name']}_H{ALIASES[name]}"
        if len(stem)>19:raise ValueError('Hose alias too long')
        clips[name]=(stem,animation)
        reports[name]={'stem':stem,'frame_end':end,'tracks':len(tracks),'animation_sha256':digest(animation),
                      'synchronized_held_alias':held_alias,'loop':held_report['clips'][name]['loop']}
    return raw,clips,levels,{'schema_version':1,'name':spec['name'],'provenance':'MODERNE','runtime_status':'pending',
        'method':spec['method'],'rig_sha256':digest(raw),'specification_sha256':digest(json.dumps(spec,sort_keys=True).encode()),
        'source_model_sha256':partition['source_model_sha256'],'held_rig_sha256':digest(held),
        'held_recipe_sha256':held_report['recipe_sha256'],'root':root,'bones':bones,'influence_weights':weights,
        'pivot':pivot,'lod_triangles':[len(mesh.triangles) for mesh in levels],
        'lod_vertices':[len(mesh.expanded()) for mesh in levels],'clips':reports,
        'original_hose_geometry_preserved':True,'independent_root_joint_frames':True,'bone_index_base':1,
        'hose_deformation_implemented':True,'authored_synchronized_clips_only':True,'pack_is_fixed':True,
        'arbitrary_pose_solver':False,'length_preserving':False,'collision_solver':False,
        'player_skeleton_bound':False,'native_loader_executed':False,'events_or_effects':False,
        'functional_weapon_implemented':False,'commercial_assets_read':False,'game_modified':False,
        'game_launched':False,'engine_validated':False}


def assembly_meshes(recipe,partition,held_spec,rig,clip,frame,lod=0):
    held,held_clips,held_meshes,_=compile_equipment_bank(recipe,partition,held_spec)
    components,_=compile_components(recipe,partition);origin=components['held']['report']['source_origin']
    result=[]
    for pair in motion.animated_meshes(recipe,held_meshes,held,held_clips[clip][1],frame):
        result.append(tuple(asset.Mesh(mesh.name,mesh.material,
            [tuple(a+b for a,b in zip(p,origin)) for p in mesh.points],mesh.triangles) for mesh in pair))
    wanted=set(partition['components']['backpack']['parts'])
    result.extend(pair for pair in asset.build_meshes(recipe) if pair[0].name in wanted)
    hose=skin_mesh(rig[0],rig[1][clip][1],frame,lod);result.append((hose,hose))
    return result


def build(recipe,partition,held_spec,spec,output):
    compiled=compile_hose_bank(recipe,partition,held_spec,spec);raw,clips,_,report=compiled
    output.mkdir(parents=True,exist_ok=False)
    (output/f"PROTOTYPE_{spec['name']}_HRig.4ds.disabled").write_bytes(raw)
    for stem,animation in clips.values():
        (output/(stem+'.4ds.disabled')).write_bytes(raw[:-1]+b'\1')
        (output/(stem+'.5ds.disabled')).write_bytes(animation)
    from PIL import Image,ImageDraw
    contact=Image.new('RGB',(1600,1410),'#101820');draw=ImageDraw.Draw(contact)
    draw.text((24,15),f"MODERNE / {spec['name']} / SKINNED VISUAL HOSE / FIXED PACK / NO PLAYER / NOT ENGINE VALIDATED",fill='#d4bd80')
    samples=(('Idle1',0),('Aim',12),('Arm',0),('Disarm',24),('Rel',32),('Jammed',16))
    for i,(clip,frame) in enumerate(samples):
        preview=output/f'{clip}_{frame:03d}.png'
        asset.preview(recipe,assembly_meshes(recipe,partition,held_spec,compiled,clip,frame),preview)
        with Image.open(preview) as picture:contact.paste(picture.resize((800,450)),((i%2)*800,60+(i//2)*450))
        draw.text(((i%2)*800+20,45+(i//2)*450),f'{clip} / authored frame {frame}',fill='white')
    contact.save(output/'hose_contact.png')
    report['companion_auto_load_engine_validated']=False
    report['files']={p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report


def inputs(case):
    return (*held_inputs(case),json.loads((DIRECTORY/f'modern-{CASES[case]}-hose-animation.json').read_text(encoding='utf-8')))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--output-name');args=parser.parse_args(argv)
    try:
        if args.output_name:report=build(*inputs(args.case),asset.output_directory(ROOT,args.output_name))
        else:report=compile_hose_bank(*inputs(args.case))[3]
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern visual hose refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
