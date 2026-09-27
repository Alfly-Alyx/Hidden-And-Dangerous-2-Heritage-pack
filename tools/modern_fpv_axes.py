"""Explicit modern authoring (+Y forward/+Z up) -> FPV (+Z forward/+Y up).

The Y/Z exchange has determinant -1. Geometry normals and winding, native
quaternions, inverse binds and bone boxes must ALL change together. This is
only for freshly generated modern models; commercial hand meshes are untouched.
"""
import struct

from build_modern_equipment_fpv_rig import compile_flat_rig
from build_modern_equipment_hose import digest
from menu_gui_audit import FourDsReader, parse_4ds_nodes
from ls3d_math_oracle import vector, unit

AXES = (0, 2, 1)
MATRIX_AXES = (0, 2, 1, 3)


def position(value):
    value = vector(value, 3, 10)
    return [value[i] for i in AXES]


def native_rotation(value):
    x, y, z, w = unit(value)
    return [-x, -z, -y, w]


def matrix(value):
    value = vector(value, 16, 10)
    return [value[r*4+c] for r in MATRIX_AXES for c in MATRIX_AXES]


def bounds(value):
    value = vector(value, 8, 10)
    return position(value[:3])+[value[3]]+position(value[4:7])+[value[7]]


def _remap_generated_model(raw):
    parsed = parse_4ds_nodes(raw)
    nodes = parsed['nodes']
    if (parsed['has_animation'] or not nodes or nodes[0]['name'] != 'fpv_weapon'
            or nodes[0]['frame_type'] != 1 or nodes[0]['visual_type'] not in (0, 2)
            or any(not n['properties'].startswith('MODERNE;') for n in nodes)
            or any(n['name'] != 'fpv_weapon' and not n['name'].startswith(('MOD_', 'PROTOTYPE_')) for n in nodes)):
        raise ValueError('Expected marked freshly generated flat FPV equipment')
    result = bytearray(raw)
    totals = dict(vertices=0, triangles=0, inverse_binds=0, boxes=0, nodes=len(nodes))
    for node in nodes:
        offset = node['position_offset']
        struct.pack_into('<3f', result, offset, *position(node['position']))
        struct.pack_into('<4f', result, offset+12, *native_rotation(struct.unpack_from('<4f', raw, offset+12)))
        struct.pack_into('<3f', result, offset+28, *position(node['scale']))
        if node['frame_type'] == 6:
            offset = node['name_offset']+node['name_length']
            offset += 1+raw[offset]
            if offset+32 != node['end']:
                raise ValueError('Unreviewed modern dummy bounds')
            struct.pack_into('<8f', result, offset, *bounds(struct.unpack_from('<8f', raw, offset)))
            totals['boxes'] += 1
            continue
        if node['frame_type'] == 10:
            continue
        if node['frame_type'] != 1 or node['visual_type'] not in (0, 2):
            raise ValueError('Unreviewed modern view geometry kind')
        reader = FourDsReader(raw[:node['end']])
        reader.position = node['name_offset']+node['name_length']
        reader.take(reader.u8())
        if reader.u16() != 0:
            raise ValueError('Instanced modern view geometry is not reviewed')
        lod_count = reader.u8()
        if lod_count != 2:
            raise ValueError('Expected both original modern LODs')
        for _ in range(lod_count):
            reader.take(4)
            if reader.u32() != 0:
                raise ValueError('Extra vertex channels are not reviewed')
            count = reader.u16()
            for _ in range(count):
                offset = reader.position
                vertex = struct.unpack('<8f', reader.take(32))
                struct.pack_into('<6f', result, offset, *position(vertex[:3]), *position(vertex[3:6]))
            totals['vertices'] += count
            for _ in range(reader.u8()):
                triangles = reader.u16()
                for _ in range(triangles):
                    offset = reader.position
                    a, b, c = struct.unpack('<3H', reader.take(6))
                    if max(a, b, c) >= count:
                        raise ValueError('Modern view triangle outside vertex array')
                    struct.pack_into('<3H', result, offset, a, c, b)
                totals['triangles'] += triangles
                reader.take(2)
        if node['visual_type'] == 2:
            count = reader.u8()
            if count != 8:
                raise ValueError('Expected eight modern hose joints')
            offset = reader.position
            struct.pack_into('<8f', result, offset, *bounds(struct.unpack('<8f', reader.take(32))))
            totals['boxes'] += 1
            reader.take(count)
            for _ in range(count):
                offset = reader.position
                struct.pack_into('<16f', result, offset, *matrix(struct.unpack('<16f', reader.take(64))))
                offset = reader.position
                struct.pack_into('<8f', result, offset, *bounds(struct.unpack('<8f', reader.take(32))))
                totals['inverse_binds'] += 1
                totals['boxes'] += 1
            for _ in range(lod_count):
                reader.take(reader.u32()*2)  # Vertex-to-bone membership is unchanged.
        if reader.position != node['end']:
            raise ValueError('Unparsed modern view payload')
    remapped = bytes(result)
    checked = parse_4ds_nodes(remapped)
    if len(remapped) != len(raw) or checked['node_count'] != parsed['node_count']:
        raise ValueError('Modern view remap changed structure or length')
    return remapped, totals


def compile_view_rig(case):
    original, _, source_report = compile_flat_rig(case)
    result, counts = _remap_generated_model(original)
    restored, inverse_counts = _remap_generated_model(result)
    if restored != original or counts != inverse_counts:
        raise ValueError('Modern axis conversion is not byte-reversible')
    return result, {'schema_version': 1, 'provenance': 'MODERNE', 'runtime_status': 'pending',
        'source_model_sha256': source_report['model_sha256'], 'model_sha256': digest(result),
        'mapping': 'x,y,z -> x,z,y', 'changes_handedness': True,
        'triangle_winding_reversed': True, 'normals_transformed': True,
        'inverse_binds_and_bounds_transformed': True, 'byte_reversible': True, 'counts': counts,
        'commercial_geometry_modified': False, 'old_animation_banks_compatible': False,
        'rebaked_hand_and_equipment_clips_required': True, 'camera_calibrated': False,
        'native_loader_executed': False, 'game_started': False, 'game_modified': False}
