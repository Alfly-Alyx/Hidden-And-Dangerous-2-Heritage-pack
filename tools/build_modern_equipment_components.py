#!/usr/bin/env python3
"""Split original visual equipment into disabled held/backpack/static-hose assets.

Only generated modern source meshes are accepted. Native vertex/index/material
bytes remain unchanged; child transforms recenter independent components.
No commercial resource, player bone, deforming hose or gameplay is fabricated.
"""
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import struct

import build_modern_asset as asset
from menu_gui_audit import parse_4ds_nodes

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'experimental/FLAMMENWERFER_35_AND_NO2'
CASES={'F35':'flmwr35','F2':'flmthr2'}
PARTS=('held','backpack','hose')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def compile_components(recipe,spec):
    if (not isinstance(spec,dict) or set(spec)!={'schema_version','name','provenance','runtime_status',
            'source_model_sha256','description','components'} or spec['schema_version']!=1
            or spec['provenance']!='MODERNE' or spec['runtime_status']!='pending'
            or spec['name'] not in CASES or not isinstance(spec['components'],dict)
            or set(spec['components'])!=set(PARTS)):
        raise ValueError('Expected an explicit modern equipment component specification')
    meshes=asset.build_meshes(recipe);source=asset.encode_4ds(recipe,meshes)
    if digest(source)!=spec['source_model_sha256']:raise ValueError('Modern component source changed')
    parsed=parse_4ds_nodes(source);nodes={node['name']:node for node in parsed['nodes'][1:]}
    mesh_by_name={pair[0].name:pair for pair in meshes}
    anchors={anchor['name']:anchor for anchor in recipe['anchors']}
    hose=next(part for part in recipe['parts'] if part['name']=='MOD_hose')
    if hose['kind']!='sweep' or hose.get('closed',False) or hose.get('transform'):
        raise ValueError('Expected original open untransformed presentation hose')
    ends=[list(asset.vector(hose['path'][i])) for i in (0,-1)]
    if anchors['MOD_hose_anchor']['position']!=ends[1]:raise ValueError('Held hose anchor differs from authored hose end')
    used_parts=[];used_anchors=[];aliases=set()
    for role in PARTS:
        component=spec['components'][role]
        if not isinstance(component,dict) or set(component)!={'alias','origin_anchor','parts','anchors'}:
            raise ValueError('Unexpected component fields')
        alias=component['alias']
        if (not isinstance(alias,str) or not asset.NAME.fullmatch(alias) or not alias.startswith('PROTOTYPE_')
                or len(alias.encode('ascii'))>19 or alias.casefold() in aliases):
            raise ValueError('Invalid or colliding native component alias')
        aliases.add(alias.casefold())
        for key,known,used in (('parts',mesh_by_name,used_parts),('anchors',anchors,used_anchors)):
            values=component[key]
            if not isinstance(values,list) or any(not isinstance(v,str) or v not in known for v in values):
                raise ValueError('Unknown component member')
            used.extend(values)
        if not component['parts']:raise ValueError('Empty component mesh set')
        expected={'held':'MOD_right_hand','backpack':'MOD_backpack_anchor','hose':None}[role]
        if component['origin_anchor']!=expected or (expected is not None and expected not in component['anchors']):
            raise ValueError('Unreviewed component origin')
    if (len(used_parts)!=len(set(used_parts)) or set(used_parts)!=set(mesh_by_name)
            or len(used_anchors)!=len(set(used_anchors)) or set(used_anchors)!=set(anchors)):
        raise ValueError('Omitted or multiply owned equipment mesh/anchor')
    if spec['components']['hose']['parts']!=['MOD_hose'] or spec['components']['hose']['anchors']:
        raise ValueError('Static hose must be isolated without source anchors')
    if 'MOD_hose_anchor' not in spec['components']['held']['anchors']:
        raise ValueError('Hose endpoint must follow the held component')
    products={};reports={};reassembly_error=0
    for role in PARTS:
        component=spec['components'][role]
        origin=anchors[component['origin_anchor']]['position'] if component['origin_anchor'] else ends[0]
        origin=list(asset.vector(origin))
        selected=[nodes[name] for name in component['parts']+component['anchors']]
        component_meshes=[]
        for name in component['parts']:
            pair=mesh_by_name[name]
            component_meshes.append(tuple(asset.Mesh(mesh.name,mesh.material,
                [asset.sub(point,origin) for point in mesh.points],list(mesh.triangles)) for mesh in pair))
        bounds=[[fn(point[i] for high,_ in component_meshes for point in high.points) for i in range(3)] for fn in (min,max)]
        extra=[]
        if role=='backpack':extra=[('MOD_hose_pack_anchor',ends[0])]
        if role=='hose':extra=[('MOD_hose_start',ends[0]),('MOD_hose_end',ends[1])]
        if any(name in nodes for name,_ in extra):raise ValueError('New component anchor collides')
        raw=bytearray(source[:parsed['node_count_offset']])
        raw.extend(asset.pack('H',1+len(selected)+len(extra)))
        root_name='PROTOTYPE_HERITAGE_'+spec['name']+'_'+role
        raw.extend(b'\x06'+asset.node_header(root_name,parent=0))
        raw.extend(asset.pack('3fi3fi',*bounds[0],0,*bounds[1],0))
        for node in selected:
            if node['parent_id']!=1:raise ValueError('Expected root-local modern source node')
            block=bytearray(source[node['start']:node['end']]);offset=node['position_offset']-node['start']
            local=asset.sub(node['position'],origin)
            struct.pack_into('<3f',block,offset,*local);raw.extend(block)
            stored=struct.unpack_from('<3f',block,offset)
            reassembly_error=max(reassembly_error,max(abs(a+b-c) for a,b,c in zip(stored,origin,node['position'])))
        for name,point in extra:
            raw.extend(b'\x06'+asset.node_header(name,asset.sub(point,origin)))
            raw.extend(asset.pack('3fi3fi',-.002,-.002,-.002,0,.002,.002,.002,0))
        raw.extend(b'\0');raw=bytes(raw);checked=parse_4ds_nodes(raw)
        if checked['has_animation'] or checked['node_count']!=1+len(selected)+len(extra):
            raise ValueError('Component structure differs after encoding')
        children={node['name']:node for node in checked['nodes'][1:]}
        for node in selected:
            child=children[node['name']]
            before=source[node['start']:node['end']];after=bytearray(raw[child['start']:child['end']])
            offset=child['position_offset']-child['start']
            after[offset:offset+12]=before[node['position_offset']-node['start']:node['position_offset']-node['start']+12]
            if bytes(after)!=before:raise ValueError('Component changed source geometry, material or node data')
        if any(node['parent_id']!=1 for node in checked['nodes'][1:]):raise ValueError('Unexpected component hierarchy')
        local_anchors={name:list(children[name]['position']) for name in component['anchors']+[name for name,_ in extra]}
        report={'alias':component['alias'],'root':root_name,'model_sha256':digest(raw),'size':len(raw),
            'source_origin':origin,'parts':list(component['parts']),'anchors':local_anchors,
            'lod_triangles':[sum(len(pair[i].triangles) for pair in component_meshes) for i in (0,1)],
            'bounds':bounds,'source_node_bytes_preserved_except_local_translation':True,
            'target_player_bone':None,'player_attachment_qualified':False}
        products[role]={'data':raw,'meshes':component_meshes,'report':report};reports[role]=report
    links=[]
    for hose_anchor,target,anchor in (('MOD_hose_start','backpack','MOD_hose_pack_anchor'),
                                      ('MOD_hose_end','held','MOD_hose_anchor')):
        a=[x+y for x,y in zip(reports['hose']['anchors'][hose_anchor],reports['hose']['source_origin'])]
        b=[x+y for x,y in zip(reports[target]['anchors'][anchor],reports[target]['source_origin'])]
        error=max(abs(x-y) for x,y in zip(a,b))
        if error>1e-6:raise ValueError('Authored static component hose endpoint mismatch')
        links.append({'from':['hose',hose_anchor],'to':[target,anchor],'static_rest_error':error,
                      'runtime_link_created':False})
    if reassembly_error>1e-6:raise ValueError('Component recentering changed authored assembly')
    return products,{'schema_version':1,'provenance':'MODERNE','runtime_status':'pending',
        'name':spec['name'],'source_model_sha256':digest(source),
        'specification_sha256':digest(json.dumps(spec,sort_keys=True).encode()),'components':reports,
        'static_rest_links':links,'reassembly_max_error':reassembly_error,
        'all_source_parts_owned_once':True,'all_source_anchors_owned_once':True,
        'commercial_assets_read':False,'game_modified':False,'game_launched':False,
        'player_skeleton_bound':False,'hose_deformation_implemented':False,'fpv_camera_calibrated':False,
        'animations_created':False,'effect_or_damage_bound':False,'playable_weapon':False}


def build(recipe,spec,output):
    products,report=compile_components(recipe,spec)
    output.mkdir(parents=True,exist_ok=False)
    for role,product in products.items():
        alias=product['report']['alias'];preview_recipe=deepcopy(recipe);preview_recipe['name']=alias
        (output/(alias+'.4ds.disabled')).write_bytes(product['data'])
        obj,mtl=asset.encode_obj(preview_recipe,product['meshes'])
        (output/(alias+'.obj')).write_text(obj,encoding='utf-8')
        (output/(alias+'.mtl')).write_text(mtl,encoding='utf-8')
        asset.preview(preview_recipe,product['meshes'],output/(role+'_preview.png'))
    report['files']={path.name:digest(path.read_bytes()) for path in sorted(output.iterdir())}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--output-name')
    args=parser.parse_args(argv)
    try:
        stem=CASES[args.case]
        recipe=json.loads((DIRECTORY/f'modern-{stem}-world.json').read_text(encoding='utf-8'))
        spec=json.loads((DIRECTORY/f'modern-{stem}-components.json').read_text(encoding='utf-8'))
        if args.output_name:report=build(recipe,spec,asset.output_directory(ROOT,args.output_name))
        else:_,report=compile_components(recipe,spec)
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern equipment components refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
