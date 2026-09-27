#!/usr/bin/env python3
"""Original rigid FG42/MG34/ZK383 flat +Z-forward FPV candidate banks.

Weapon-only: no commercial hands, camera placement, Item, event or installation.
The newly serialized hierarchy and clips are checked together; old clips cannot
be mixed with these models. Preview placement is diagnostic only.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import struct

import build_modern_asset as asset
import build_modern_animation_bank as bank
import modern_animation as motion
from animation_tick_audit import model_poses
from build_equipment_fpv_animation import numeric_world,position_curve,constant
from build_modern_equipment_fpv_rig import rewritten_node
from build_modern_equipment_hose import digest
from five_ds import parse_5ds
from ls3d_frame_find_oracle import reference as find_reference
from ls3d_skin_oracle import transformed
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms
from modern_fpv_axes import _remap_generated_model,position,native_rotation,matrix
from modern_fpv_geometry import geometry

CASES=('FG42','MG34','ZK383')
SHORT={'FG42':'FG42','MG34':'MG34','ZK383':'ZK3'}


def original(case):
    if case not in CASES:raise ValueError('Unknown original rigid weapon case')
    if case=='ZK383':
        from build_zk383_animation_bank import inputs,compile_bank
        recipe,spec=inputs();compiled=compile_bank(recipe,spec)
    else:
        folder=asset.ROOT/'experimental'/bank.CASES[case]
        recipe=json.loads((folder/'modern-world-model.json').read_text(encoding='utf-8'))
        spec=json.loads((folder/'modern-animation-bank.json').read_text(encoding='utf-8'))
        compiled=bank.compile_bank(recipe,spec)
    return recipe,spec,compiled


def flatten(raw):
    nodes=parse_4ds_nodes(raw)['nodes'];parsed=parse_4ds_nodes(raw)
    if (parsed['has_animation'] or not nodes or nodes[0]['frame_type']!=6 or nodes[0]['parent_id']
            or not nodes[0]['name'].startswith('PROTOTYPE_HERITAGE_') or nodes[0]['position']!=[0,0,0]
            or len({n['name'].casefold() for n in nodes})!=len(nodes)):
        raise ValueError('Expected original rigid animation hierarchy')
    by_name={n['name']:n for n in nodes}
    for node in nodes:
        if (not node['properties'].startswith('MODERNE;')
                or not node['name'].startswith(('PROTOTYPE_HERITAGE_','MOD_'))
                or node['frame_type'] not in (1,6)
                or (node['frame_type']==1 and node['visual_type']!=0)
                or struct.unpack_from('<4f',raw,node['position_offset']+12)!=(0,0,0,1)
                or node['scale']!=[1,1,1] or node['parent_id']>=node['index']
                or (node['index']!=1 and not node['parent_id'])):
            raise ValueError('Unreviewed rigid rest node')
        if node['parent_id']>1:
            parent=nodes[node['parent_id']-1]
            if parent['parent_id']!=1 or parent['frame_type']!=6:
                raise ValueError('Only one layer of original rigid pivots is reviewed')
    receiver=by_name.get('MOD_receiver')
    if (receiver is None or receiver['frame_type']!=1 or receiver['parent_id']!=1
            or receiver['position']!=[0,0,0]):
        raise ValueError('Missing stationary root-local original receiver')
    world=world_transforms(raw,nodes)
    selected=[receiver]+[n for n in nodes[1:] if n['name']!=receiver['name']]
    output=bytearray(raw[:parsed['node_count_offset']]+asset.pack('H',len(selected)))
    names={}
    for i,node in enumerate(selected):
        name='fpv_weapon' if i==0 else node['name'];names[node['name']]=name
        output.extend(rewritten_node(raw,node,name,0 if i==0 else 1,world[node['index']][1]))
    output.extend(b'\0');output=bytes(output)
    after=parse_4ds_nodes(output)['nodes']
    for before,node in zip(selected,after):
        if raw[before['name_offset']+before['name_length']:before['end']]!=output[node['name_offset']+node['name_length']:node['end']]:
            raise ValueError('Rigid flattening changed geometry or LOD payload')
    found=find_reference([{'name':n['name'],'frame_type':n['frame_type'],'parent':n['parent_id']-1} for n in after],'fpv_weapon',1)
    if found!={'index':0,'direct_children':list(range(1,len(after)))}:
        raise ValueError('Rigid root does not satisfy reviewed direct registration contract')
    return output,{'source_sha256':digest(raw),'flat_sha256':digest(output),'source_to_fpv_names':names,
        'removed_dummy_root':nodes[0]['name'],'visual_root_source':'MOD_receiver',
        'nodes':len(after),'geometry_and_lods_preserved_before_axis_remap':True}


def rebake(source,flat,description,raw):
    if digest(source)!=description['source_sha256'] or digest(flat)!=description['flat_sha256']:
        raise ValueError('Changed rigid rebake geometry')
    nodes=parse_4ds_nodes(source)['nodes'];by_name={n['name']:n for n in nodes}
    clip=parse_5ds(raw);end=clip['frame_end'];tracks={t['name']:t['channels'] for t in clip['tracks']}
    root=description['removed_dummy_root'];names,seeds=model_poses(source)
    if (not 1<=end<=179 or root not in tracks or set(tracks)-set(names)
            or any(set(channels)!={'position','rotation'} for channels in tracks.values())):
        raise ValueError('Unreviewed rigid source animation channels')
    for name in tracks:
        if name!=root and (by_name[name]['parent_id']!=1 or by_name[name]['frame_type']!=6):
            raise ValueError('Only direct original pivots may have source tracks')
    relative={name:channels for name,channels in tracks.items() if name!=root}
    samples={name:[] for name in description['source_to_fpv_names']}
    for frame in range(end+1):
        world,_=numeric_world(nodes,dict(zip(names,seeds)),relative,frame*40)
        for name in samples:samples[name].append(world[name][12:15])
    result=[]
    for old,new in description['source_to_fpv_names'].items():
        if new=='fpv_weapon':channels=deepcopy(tracks[root])
        else:
            node=by_name[old];parent=nodes[node['parent_id']-1]['name']
            controlling=old if old in relative else (parent if parent in relative else None)
            channels={'position':position_curve(samples[old],end),
                'rotation':deepcopy(relative[controlling]['rotation']) if controlling else
                           constant('rotation',[0,0,0,1],end)['rotation']}
        channels.update(constant('scale',[1,1,1],end))
        for kind,channel in channels.items():
            convert=native_rotation if kind=='rotation' else position
            channel['values']=[convert(v) for v in channel['values']]
        result.append({'name':new,'channels':channels})
    data=motion.encode_5ds({'provenance':'MODERNE','runtime_status':'pending','frame_end':end,'tracks':result},
                           preserve_native_rotations=True)
    if len(data)-18>0xf000:raise ValueError('Rigid FPV animation exceeds reviewed native body capacity')
    return data


def compare(source,view,description,old,new):
    snodes=parse_4ds_nodes(source)['nodes'];vnodes=parse_4ds_nodes(view)['nodes']
    sn,sp=model_poses(source);vn,vp=model_poses(view)
    old_tracks={t['name']:t['channels'] for t in parse_5ds(old)['tracks']}
    new_tracks={t['name']:t['channels'] for t in parse_5ds(new)['tracks']}
    end=parse_5ds(old)['frame_end'];errors={'keys':0,'half_keys':0};worst=None
    for time in range(0,end*40+1,20):
        expected,_=numeric_world(snodes,dict(zip(sn,sp)),old_tracks,time)
        actual,_=numeric_world(vnodes,dict(zip(vn,vp)),new_tracks,time)
        kind='keys' if time%40==0 else 'half_keys'
        for old_name,new_name in description['source_to_fpv_names'].items():
            error=max(abs(a-b) for a,b in zip(matrix(expected[old_name]),actual[new_name]))
            if error>max(errors.values()):worst={'time':time,'node':new_name,'error':error}
            errors[kind]=max(errors[kind],error)
    if errors['keys']>5e-6:raise ValueError('Rigid FPV rebake changed a keyed transform')
    return {'samples':2*end+1,'matrix_max_errors':errors,'worst':worst,
            'numeric_native_reference':True,'native_code_executed':False,
            'continuous_equivalence_proven':False}


def compile_bank(case):
    recipe,spec,(source,old_clips,_,original_report)=original(case)
    flat,description=flatten(source);view,counts=_remap_generated_model(flat)
    restored,inverse_counts=_remap_generated_model(view)
    if restored!=flat or counts!=inverse_counts:raise ValueError('Rigid view axes not byte reversible')
    clips={};rows={}
    for name,(_,old) in old_clips.items():
        new=rebake(source,flat,description,old)
        stem=f'PROTOTYPE_{SHORT[case]}V{bank.ALIASES[name]}'
        if len(stem)>19:raise ValueError('Rigid FPV alias too long')
        rows[name]={'stem':stem,'sha256':digest(new),'bytes':len(new),
                    'source_clip_sha256':digest(old),**compare(source,view,description,old,new)}
        clips[name]=(stem,new)
    return recipe,view,clips,{'schema_version':1,'case':case,'provenance':'MODERNE','runtime_status':'pending',
        'source_rig_sha256':digest(source),'model_sha256':digest(view),'flattening':description,
        'axis_mapping':'x,y,z -> x,z,y','axis_remap_counts':counts,'byte_reversible_axis_remap':True,
        'original_bank_recipe_sha256':original_report['recipe_sha256'],'clips':rows,
        'old_banks_compatible':False,'player_hands':False,'camera_placement_authored':False,
        'commercial_assets_read':False,'native_loader_executed':False,'native_clone_qualified':False,
        'events_or_gameplay_implemented':False,'item_allocated':False,'game_started':False,
        'game_modified':False,'engine_validated':False}


def preview_meshes(view,raw,time,lod=0):
    meshes,skin=geometry(view,lod)
    if skin is not None:raise ValueError('Unexpected skin in rigid-only view bank')
    names,seeds=model_poses(view)
    world,_=numeric_world(parse_4ds_nodes(view)['nodes'],dict(zip(names,seeds)),
        {t['name']:t['channels'] for t in parse_5ds(raw)['tracks']},time)
    return [asset.Mesh(m['name'],g['material'],[tuple(transformed(v[:3],world[m['name']])) for v in m['vertices']],
                       [tuple(t) for t in g['triangles']]) for m in meshes for g in m['face_groups']]


def build(case,output):
    recipe,view,clips,report=compile_bank(case);output.mkdir(parents=True,exist_ok=False)
    (output/f'PROTOTYPE_{SHORT[case]}_FPV.4ds.disabled').write_bytes(view)
    from fpv_perspective_preview import preview
    offset=[.07,-.15,.25] # Applied to PNG only; deliberately not model/animation data.
    for name,(stem,raw) in clips.items():(output/(stem+'.5ds.disabled')).write_bytes(raw)
    for name,time in (('Idle1',0),('Aim',480),('Rel',1400)):
        meshes=preview_meshes(view,clips[name][1],time)
        shifted=[asset.Mesh(m.name,m.material,[tuple(a+b for a,b in zip(p,offset)) for p in m.points],m.triangles) for m in meshes]
        preview(recipe,shifted,output/(name+'_diagnostic.png'),case+' / '+name+' / WEAPON ONLY / PREVIEW OFFSET',horizontal_fov=65)
    report['preview_only_translation']=offset
    report['files']={p.name:digest(p.read_bytes()) for p in sorted(output.iterdir())}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--output-name');args=parser.parse_args(argv)
    try:
        report=build(args.case,asset.output_directory(asset.ROOT,args.output_name)) if args.output_name else compile_bank(args.case)[3]
        print(json.dumps({k:v for k,v in report.items() if k not in ('clips','files')},indent=2))
        print(json.dumps({'samples':sum(r['samples'] for r in report['clips'].values()),
            'max_errors':{key:max(r['matrix_max_errors'][key] for r in report['clips'].values()) for key in ('keys','half_keys')}}))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern rigid FPV bank refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
