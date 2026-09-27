"""Read-only HD2 single-mesh rest audit, bounded to the reviewed hands layout.

An identity skin root, one non-instanced LOD without extra vertex data, joint
IDs and one (one-based bone, byte) pair per vertex are required. This rest
audit does not execute the separate qualified skin kernel or apply weights.
Reports contain no mesh or matrix payloads.
"""
import math
import struct

from menu_gui_audit import FourDsReader,parse_4ds_nodes
from model_transform import compose,invert,world_transforms


def identity_error(transform):
    matrix,position=transform
    if not all(math.isfinite(v) for row in (*matrix,position) for v in row):
        raise ValueError('Nonfinite skin transform')
    return max([abs(matrix[i][j]-(i==j)) for i in range(3) for j in range(3)]
               +[abs(v) for v in position])


def floats(reader,count):
    values=struct.unpack('<'+'f'*count,reader.take(4*count))
    if not all(math.isfinite(v) for v in values):raise ValueError('Nonfinite skin data')
    return values


def read_reviewed(data):
    """Validated private data for local calculations; callers must not export it."""
    model=parse_4ds_nodes(data);nodes=model['nodes']
    if (not nodes or nodes[0]['frame_type']!=1 or nodes[0]['visual_type']!=2
            or nodes[0]['parent_id'] or any(n['frame_type']!=10 for n in nodes[1:])):
        raise ValueError('Expected one root skin and joint-only children')
    root=nodes[0];world=world_transforms(data,nodes)
    if identity_error(world[root['index']])>1e-7:
        raise ValueError('Only an identity skin root is reviewed')
    reader=FourDsReader(data[:root['end']])
    reader.position=root['name_offset']+root['name_length'];reader.take(reader.u8())
    if reader.u16()!=0 or reader.u8()!=1:raise ValueError('Expected non-instanced single LOD skin')
    floats(reader,1)
    if reader.u32()!=0:raise ValueError('Extra skin vertex data is not reviewed')
    vertices=reader.u16()
    if not vertices:raise ValueError('Empty skin geometry')
    vertex_values=floats(reader,8*vertices)
    triangles=0
    for _ in range(reader.u8()):
        count=reader.u16();triangles+=count
        indices=struct.unpack('<'+'H'*(count*3),reader.take(count*6))
        if any(i>=vertices for i in indices):raise ValueError('Skin face index outside vertices')
        if not 1<=reader.u16()<=model['material_count']:raise ValueError('Invalid skin material')
    bone_count=reader.u8();floats(reader,8)
    if not bone_count or len(nodes)!=bone_count+1:raise ValueError('Skin/joint count mismatch')
    parents=list(reader.take(bone_count))
    joints={};node_bones={}
    for node in nodes[1:]:
        bone=struct.unpack_from('<I',data,node['end']-4)[0]
        if bone>=bone_count or bone in joints:raise ValueError('Duplicate or out-of-range bone ID')
        joints[bone]=node;node_bones[node['index']]=bone
    errors=[];matrices=[]
    for bone in range(bone_count):
        node=joints[bone];parent=node['parent_id']
        if parent!=root['index'] and parent not in node_bones:
            raise ValueError('Joint parent outside reviewed skin')
        expected=0 if parent==root['index'] else node_bones[parent]+1
        if parents[bone]!=expected:raise ValueError('Skin parent byte disagrees with joint hierarchy')
        values=floats(reader,16);floats(reader,8);matrices.append(list(values))
        if any(abs(values[i]-expected)>1e-7 for i,expected in ((3,0),(7,0),(11,0),(15,1))):
            raise ValueError('Invalid homogeneous inverse bind')
        inverse_bind=([[values[i+j*4] for j in range(3)] for i in range(3)],list(values[12:15]))
        invert(inverse_bind) # Reject singular data even before residual checking.
        error=identity_error(compose(world[node['index']],inverse_bind))
        if error>1e-5:raise ValueError('Inverse bind disagrees with native joint rest transform')
        errors.append(error)
    weights=reader.u32()
    if weights!=vertices:raise ValueError('Only one bone/byte pair per vertex is reviewed')
    pairs=reader.take(2*weights)
    if any(not 1<=bone<=bone_count for bone in pairs[::2]):raise ValueError('Skin weight bone outside one-based palette')
    if reader.position!=root['end']:raise ValueError('Unparsed skin payload')
    report={'scope':'reviewed_hd2_identity_root_single_lod_skin_rest',
        'vertices':vertices,'triangles':triangles,'bones':bone_count,'weight_pairs':weights,
        'joint_ids_not_node_ordinals':True,'parent_bytes_verified':True,'vertex_bone_index_base':1,
        'native_rotation_convention':'xyzw_conjugated_to_active_column_vectors',
        'inverse_bind_max_identity_error':max(errors),'inverse_bind_tolerance':1e-5,
        'inverse_bind_rest_identity_verified':True,'weight_byte_semantics_qualified':False,
        'skin_deformation_qualified':False,'engine_validated':False,'geometry_exported':False}
    return {'report':report,'vertices':[list(vertex_values[i:i+8]) for i in range(0,len(vertex_values),8)],
        'pairs':[list(pairs[i:i+2]) for i in range(0,len(pairs),2)],'parents':parents,
        'inverse_binds':matrices,'joint_node_indices':[joints[i]['index'] for i in range(bone_count)],
        'nodes':nodes,'rest_world':world}


def audit_rest(data):
    return read_reviewed(data)['report']
