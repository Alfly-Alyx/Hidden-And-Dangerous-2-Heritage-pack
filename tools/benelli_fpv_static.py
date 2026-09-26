"""Derive a static FPV laboratory asset locally, never a playable weapon.

Commercial meshes/materials stay local. The modern operation selects the eight
weapon frames and rebases the two roots to fpv_weapon's coordinate system.
"""
import struct

from menu_gui_audit import parse_4ds_nodes, FourDsReader
from model_instance import visual_geometry
from model_transform import compose, invert, decompose, node_transform, world_transforms, point

NAMES = {'fpv_weapon','gunlock','cock','blsdum','cardum','shdum','shell01','magazine'}


def derive(data):
    parsed=parse_4ds_nodes(data)
    selected=[n for n in parsed['nodes'] if n['name'].casefold() in NAMES]
    if len(selected)!=len(NAMES) or {n['name'].casefold() for n in selected}!=NAMES:
        raise ValueError('Missing or ambiguous FPV weapon nodes')
    by_name={n['name'].casefold():n for n in selected}
    root=by_name['fpv_weapon']
    if root['parent_id'] or by_name['magazine']['parent_id']:
        raise ValueError('Unexpected FPV root ownership')
    if any(n['parent_id']!=root['index'] for n in selected if n['name'].casefold() not in ('fpv_weapon','magazine')):
        raise ValueError('Unexpected FPV child ownership')
    if any(n['parent_id'] in {s['index'] for s in selected} for n in parsed['nodes'] if n not in selected):
        raise ValueError('FPV subtree would discard an owned child')
    for n in selected:
        expected=1 if n['name'].casefold() in ('fpv_weapon','gunlock','cock','shell01') else 6
        if n['frame_type']!=expected: raise ValueError('Unexpected FPV mesh/anchor type')
        if expected==1:
            for lod in visual_geometry(data,n):
                if any(not 1<=m<=parsed['material_count'] for m in lod['materials']):
                    raise ValueError('Invalid FPV material reference')
    root_inverse=invert(node_transform(data,root))
    remap={n['index']:i for i,n in enumerate(selected,1)}
    output=bytearray(data[:parsed['node_count_offset']])
    output.extend(struct.pack('<H',len(selected)))
    residuals={}
    for node in selected:
        raw=bytearray(data[node['start']:node['end']])
        struct.pack_into('<H',raw,node['parent_offset']-node['start'],remap.get(node['parent_id'],0))
        if not node['parent_id']:
            if node['index']==root['index']:
                position,q,scale,error=[0,0,0],[0,0,0,1],[1,1,1],0
            else:
                position,q,scale,error=decompose(compose(root_inverse,node_transform(data,node)))
            struct.pack_into('<3f4f3f',raw,node['position_offset']-node['start'],*position,*q,*scale)
            residuals[node['name']]=error
        output.extend(raw)
    output.extend(b'\0')  # Static resource, never auto-load a companion 5DS.
    output=bytes(output)
    checked=parse_4ds_nodes(output)
    if checked['has_animation'] or checked['node_count']!=8: raise ValueError('Invalid generated static FPV')
    return output, {'provenance':'DERIVE_DU_JEU', 'operation':'MODERNE_EXTRACTION_ET_RECALAGE',
                    'source_nodes':parsed['node_count'],'static_nodes':8,
                    'removed_joint_nodes':sum(n['frame_type']==10 for n in parsed['nodes'] if n not in selected),
                    'material_bytes_preserved':output[:parsed['node_count_offset']]==data[:parsed['node_count_offset']],
                    'root_decomposition_residuals':residuals,
                    'playable_weapon':False,'animation_compatibility':'pending',
                    'runtime_status':'pending','commercial_vertices_redistributed':False}


def geometry(data):
    """First LOD, correctly composed 4DS hierarchy; no material/texture rendering."""
    parsed=parse_4ds_nodes(data)
    transforms=world_transforms(data,parsed['nodes'])
    vertices,faces=[],[]
    for node in parsed['nodes']:
        if node['frame_type']!=1: continue
        visual_geometry(data,node)
        r=FourDsReader(data); r.position=node['name_offset']+node['name_length']; r.take(r.u8())
        if r.u16(): raise ValueError('Instanced FPV geometry not supported')
        r.u8(); r.take(4); extra=r.u32(); count=r.u16()
        base=len(vertices)
        for _ in range(count):
            p=struct.unpack('<8f',r.take(32))[:3]
            vertices.append(tuple(point(transforms[node['index']],p)))
        r.take(extra*count*4)
        for _ in range(r.u8()):
            for _ in range(r.u16()):
                faces.append(tuple(base+i for i in struct.unpack('<3H',r.take(6))))
            r.u16()
    return vertices,faces,[n['name'] for n in parsed['nodes']]
