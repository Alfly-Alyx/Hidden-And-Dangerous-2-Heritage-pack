#!/usr/bin/env python3
"""Combine original held, backpack and skinned hose into one disabled visual rig.

One clip controls both held pivot and hose joints. Fixed pack only; no player,
camera, native loader, physical hose, event, effect or functional weapon.
"""
from copy import deepcopy
import argparse
import json
import struct

import build_modern_asset as asset
from build_modern_equipment_hose import inputs,compile_hose_bank,header,bounds,digest,CASES,ROOT
from build_modern_equipment_animation import compile_equipment_bank
from build_modern_equipment_components import compile_components
from build_modern_animation_bank import ALIASES
from four_ds_skin import read_reviewed
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import compose,point
import modern_animation as motion


def assemble_models(sources,origins,root,bounding_points):
    """Only called with freshly generated modern sources, never external paths."""
    if set(sources)!=set(origins) or set(sources)!={'held','backpack','hose'}:
        raise ValueError('Incomplete visual component assembly')
    parsed={role:parse_4ds_nodes(raw) for role,raw in sources.items()}
    prefixes=[sources[role][:model['node_count_offset']] for role,model in parsed.items()]
    if len(set(prefixes))!=1:raise ValueError('Component material tables differ')
    count=1+sum(model['node_count'] for model in parsed.values())
    raw=bytearray(prefixes[0]+asset.pack('H',count));raw.extend(b'\x06'+header(root,parent=0))
    raw.extend(asset.pack('8f',*bounds(bounding_points)))
    base=1;all_names={root.casefold()};index_maps={}
    for role,source in sources.items():
        model=parsed[role];nodes=model['nodes'];index_maps[role]={}
        if model['has_animation'] or not nodes or nodes[0]['parent_id']:
            raise ValueError('Expected unanimated independent source root')
        for node in nodes:
            if not node['name'].startswith(('PROTOTYPE_HERITAGE_','MOD_')) or node['name'].casefold() in all_names:
                raise ValueError('Unmarked or ambiguous assembly node')
            all_names.add(node['name'].casefold())
            if node['parent_id']>=node['index'] or (node['index']!=1 and not node['parent_id']):
                raise ValueError('Component hierarchy is not root-first')
            block=bytearray(source[node['start']:node['end']])
            parent=node['parent_id']+base if node['parent_id'] else 1
            struct.pack_into('<H',block,node['parent_offset']-node['start'],parent)
            if node['index']==1:
                if node['position']!=[0,0,0]:raise ValueError('Unexpected component root origin')
                struct.pack_into('<3f',block,node['position_offset']-node['start'],*origins[role])
            raw.extend(block);index_maps[role][node['index']]=node['index']+base
        base+=len(nodes)
    raw.extend(b'\0');raw=bytes(raw);checked=parse_4ds_nodes(raw)
    if checked['node_count']!=count:raise ValueError('Assembled node count changed')
    # Apart from parent IDs and explicit root positions, every original block
    # must be byte-identical, including skin inverse binds and both LOD weights.
    by_index={n['index']:n for n in checked['nodes']}
    for role,source in sources.items():
        for node in parsed[role]['nodes']:
            new=by_index[index_maps[role][node['index']]]
            original=source[node['start']:node['end']];block=bytearray(raw[new['start']:new['end']])
            p=node['parent_offset']-node['start'];block[p:p+2]=original[p:p+2]
            if node['index']==1:
                p=node['position_offset']-node['start'];block[p:p+12]=original[p:p+12]
            if bytes(block)!=original:raise ValueError('Assembly rewrote component geometry or skin')
    return raw,index_maps


def compile_assembly(recipe,partition,held_spec,hose_spec):
    components,_=compile_components(recipe,partition)
    held,held_clips,_,held_report=compile_equipment_bank(recipe,partition,held_spec)
    hose,hose_clips,_,hose_report=compile_hose_bank(recipe,partition,held_spec,hose_spec)
    sources={'held':held,'backpack':components['backpack']['data'],'hose':hose}
    origins={role:components[role]['report']['source_origin'] for role in ('held','backpack')};origins['hose']=[0,0,0]
    root='PROTOTYPE_HERITAGE_'+partition['name']+'_Assembly'
    points=[p for high,_ in asset.build_meshes(recipe) for p in high.points]
    raw,maps=assemble_models(sources,origins,root,points);clips={};reports={}
    for name,(_,held_data) in held_clips.items():
        a,b=parse_5ds(held_data),parse_5ds(hose_clips[name][1])
        if a['frame_end']!=b['frame_end']:raise ValueError('Visual component clip durations differ')
        tracks=[]
        for track in a['tracks']+b['tracks']:
            channels=deepcopy(track['channels'])
            if track['name']==held_report['rig']['root']:
                if any(v!=[0,0,0] for v in channels['position']['values']):
                    raise ValueError('Held root motion cannot be silently recentered')
                channels['position']['values']=[origins['held'][:] for _ in channels['position']['values']]
            tracks.append({'name':track['name'],'channels':channels})
        animation=motion.encode_5ds({'provenance':'MODERNE','runtime_status':'pending',
            'frame_end':a['frame_end'],'tracks':tracks},preserve_native_rotations=True)
        reread=parse_5ds(animation)
        if [t['channels'] for t in reread['tracks']]!=[t['channels'] for t in tracks]:
            # The recentered root positions serialize to float32, like 4DS.
            for expected,actual in zip(tracks,reread['tracks']):
                for kind,channel in expected['channels'].items():
                    rounded=[[struct.unpack('<f',struct.pack('<f',v))[0] for v in row] for row in channel['values']]
                    if actual['channels'][kind]!={'frames':channel['frames'],'values':rounded}:
                        raise ValueError('Assembly altered existing native transform keys')
        stem=f"PROTOTYPE_{partition['name']}_A{ALIASES[name]}"
        if len(stem)>19:raise ValueError('Assembly alias too long')
        clips[name]=(stem,animation)
        reports[name]={'stem':stem,'frame_end':a['frame_end'],'tracks':len(tracks),
            'animation_sha256':digest(animation),'loop':held_report['clips'][name]['loop']}
    return raw,clips,{'schema_version':1,'provenance':'MODERNE','runtime_status':'pending','name':partition['name'],
        'root':root,'rig_sha256':digest(raw),'node_count':parse_4ds_nodes(raw)['node_count'],
        'sources':{role:digest(data) for role,data in sources.items()},'source_index_maps':maps,
        'component_origins':origins,'clips':reports,'rigid_and_skin_share_one_clip':True,
        'skin_joint_ids_preserved':True,'native_keys_preserved_except_held_root_origin':True,
        'component_bytes_preserved_except_parent_ids_and_root_positions':True,
        'held_recipe_sha256':held_report['recipe_sha256'],'hose_specification_sha256':hose_report['specification_sha256'],
        'fixed_backpack':True,'player_skeleton_bound':False,'fpv_camera_calibrated':False,
        'arbitrary_pose_solver':False,'collision_solver':False,'native_loader_executed':False,
        'events_or_effects':False,'functional_weapon_implemented':False,'engine_validated':False,
        'commercial_assets_read':False,'game_launched':False,'game_modified':False}


def assembly_preview(recipe,rig,animation,frame,hose_source,lod=0):
    """Render the actual combined hierarchy and the actual combined 5DS tracks."""
    nodes={n['name']:n for n in parse_4ds_nodes(rig)['nodes']};transforms=motion.pose(rig,animation,frame)
    result=[]
    for pair in asset.build_meshes(recipe):
        if pair[0].name=='MOD_hose':continue
        node=nodes[pair[0].name]
        result.append(tuple(asset.Mesh(mesh.name,mesh.material,
            [tuple(point(transforms[node['index']],p)) for p in mesh.points],mesh.triangles) for mesh in pair))
    skin=read_reviewed(hose_source,allow_multiple_lods=True,lod=lod);palettes=[]
    local_nodes={n['index']:n for n in skin['nodes']}
    for index,values in zip(skin['joint_node_indices'],skin['inverse_binds']):
        inverse=([[values[i+j*4] for j in range(3)] for i in range(3)],values[12:15])
        actual=nodes[local_nodes[index]['name']]['index'];palettes.append(compose(transforms[actual],inverse))
    vertices=[tuple(point(palettes[bone-1],v[:3])) for v,(bone,_) in zip(skin['vertices'],skin['pairs'])]
    mesh=asset.Mesh('MOD_hose',3,vertices,[tuple(range(i,i+3)) for i in range(0,len(vertices),3)])
    mesh.validate();result.append((mesh,mesh));return result


def build(recipe,partition,held_spec,hose_spec,output):
    raw,clips,report=compile_assembly(recipe,partition,held_spec,hose_spec)
    hose_source=compile_hose_bank(recipe,partition,held_spec,hose_spec)[0]
    output.mkdir(parents=True,exist_ok=False)
    (output/f"PROTOTYPE_{partition['name']}_ARig.4ds.disabled").write_bytes(raw)
    for stem,animation in clips.values():
        (output/(stem+'.4ds.disabled')).write_bytes(raw[:-1]+b'\1')
        (output/(stem+'.5ds.disabled')).write_bytes(animation)
    from PIL import Image,ImageDraw
    contact=Image.new('RGB',(1600,1410),'#101820');draw=ImageDraw.Draw(contact)
    draw.text((24,15),f"MODERNE / {partition['name']} / ONE COMBINED RIG & CLIP / FIXED PACK / NO PLAYER / NOT ENGINE VALIDATED",fill='#d4bd80')
    for i,(clip,frame) in enumerate((('Idle1',0),('Aim',12),('Arm',0),('Disarm',24),('Rel',32),('Jammed',16))):
        path=output/f'{clip}_{frame:03d}.png'
        asset.preview(recipe,assembly_preview(recipe,raw,clips[clip][1],frame,hose_source),path)
        with Image.open(path) as picture:contact.paste(picture.resize((800,450)),((i%2)*800,60+(i//2)*450))
        draw.text(((i%2)*800+20,45+(i//2)*450),f'{clip} / authored frame {frame}',fill='white')
    contact.save(output/'assembly_contact.png');report['companion_auto_load_engine_validated']=False
    report['files']={p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--output-name');args=parser.parse_args(argv)
    try:
        if args.output_name:report=build(*inputs(args.case),asset.output_directory(ROOT,args.output_name))
        else:report=compile_assembly(*inputs(args.case))[2]
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern visual assembly refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
