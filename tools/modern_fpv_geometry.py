"""Read fresh marked modern flat geometry for private, serialized previews.

The temporary joint-only skin is a parser adapter in memory, not a game file.
Commercial models must use their existing separately pinned private reader.
"""
import struct

from menu_gui_audit import FourDsReader, parse_4ds_nodes
from four_ds_skin import read_reviewed


def geometry(raw, lod=0):
    if type(lod) is not int or lod not in (0, 1):
        raise ValueError('Unreviewed modern geometry LOD')
    parsed = parse_4ds_nodes(raw)
    nodes = parsed['nodes']
    if (parsed['has_animation'] or not nodes or nodes[0]['name'] != 'fpv_weapon'
            or nodes[0]['frame_type'] != 1 or nodes[0]['visual_type'] not in (0, 2)
            or nodes[0]['parent_id'] or any(n['parent_id'] != 1 for n in nodes[1:])
            or any(not n['properties'].startswith('MODERNE;') for n in nodes)
            or any(n['name'] != 'fpv_weapon' and not n['name'].startswith(('MOD_', 'PROTOTYPE_')) for n in nodes)
            or len({n['name'] for n in nodes}) != len(nodes)):
        raise ValueError('Expected marked original flat FPV geometry')
    bones = [n for n in nodes if n['frame_type'] == 10]
    skinned = nodes[0]['visual_type'] == 2
    if len(bones) != (8 if skinned else 0):
        raise ValueError('Expected eight hose joints or a wholly rigid modern bank')
    hose = None
    if skinned:
        selected = [nodes[0]]+bones
        adapter = (raw[:parsed['node_count_offset']]+struct.pack('<H', len(selected))
                   +b''.join(raw[n['start']:n['end']] for n in selected)+b'\0')
        hose = read_reviewed(adapter, allow_multiple_lods=True, lod=lod, include_faces=True)
    meshes = []
    for node in (nodes[1:] if skinned else nodes):
        if node['frame_type'] in (6, 10):
            continue
        if node['frame_type'] != 1 or node['visual_type'] != 0:
            raise ValueError('Unexpected additional modern visual kind')
        r = FourDsReader(raw[:node['end']])
        r.position = node['name_offset']+node['name_length']
        r.take(r.u8())
        if r.u16() != 0 or r.u8() != 2:
            raise ValueError('Expected non-instanced two-LOD modern mesh')
        for level in range(2):
            r.take(4)
            if r.u32() != 0:
                raise ValueError('Additional vertex channels are not reviewed')
            count = r.u16()
            vertices = [list(struct.unpack('<8f', r.take(32))) for _ in range(count)]
            groups = []
            for _ in range(r.u8()):
                faces = [list(struct.unpack('<3H', r.take(6))) for _ in range(r.u16())]
                material = r.u16()
                if not 1 <= material <= parsed['material_count'] or any(max(f) >= count for f in faces):
                    raise ValueError('Invalid modern mesh face group')
                groups.append({'material': material, 'triangles': faces})
            if level == lod:
                meshes.append({'name': node['name'], 'vertices': vertices, 'face_groups': groups})
        if r.position != node['end']:
            raise ValueError('Unparsed modern mesh payload')
    return meshes, hose
