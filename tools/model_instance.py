"""Resolve a typed mission model instance and one direct 4DS child, read-only.

No name-union fallback: the selected instance must name the selected model,
and the selected node must be a unique direct visual child in that model.
Geometric ownership is not proof of physics/collision behaviour.
"""
from __future__ import annotations

import math
import re
import struct

from menu_gui_audit import FourDsReader, parse_4ds_nodes
from objective_audit import blocks, direct, walk

MODEL_PATH = re.compile(r'models/[a-z0-9_]+\.4ds\Z')


def one_field(record, kind):
    matches = direct(record, kind)
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous typed model field')
    return matches[0].payload


def text_field(record, kind):
    raw = one_field(record, kind)
    if not raw.endswith(b'\0') or b'\0' in raw[:-1]:
        raise ValueError('Model field is not a terminated string')
    return raw[:-1].decode('cp1252')


def model_instance(scene: bytes, name: str) -> dict:
    tree = blocks(scene, 0, len(scene))
    if tree is None:
        raise ValueError('Invalid model-instance scene structure')
    matches = []
    for record in walk(tree):
        if record.kind != 0x4010:
            continue
        names = direct(record, 0x10)
        if len(names) == 1 and names[0].payload.rstrip(b'\0').decode('cp1252').casefold() == name.casefold():
            matches.append(record)
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous serialized model instance')
    record = matches[0]
    if one_field(record, 0x4011) != struct.pack('<I', 9):
        raise ValueError('Selected frame is not a model instance')
    model = text_field(record, 0x2012).casefold()
    model_path = 'models/' + model + ('' if model.endswith('.4ds') else '.4ds')
    if not MODEL_PATH.fullmatch(model_path):
        raise ValueError('Unreviewed model instance resource path')
    result = {'instance': text_field(record, 0x10), 'model_entry': model_path,
              'record_offset': record.start}
    for kind, key, count in ((0x20,'local_position',3),(0x2C,'world_position',3),
                             (0x22,'rotation_serialized',4),(0x2D,'scale',3)):
        raw = one_field(record, kind)
        if len(raw) != count*4:
            raise ValueError('Invalid instance transform size')
        value = struct.unpack('<' + 'f'*count, raw)
        if not all(math.isfinite(n) for n in value):
            raise ValueError('Nonfinite instance transform')
        result[key] = list(value)
    return result


def visual_geometry(data: bytes, node: dict) -> list[dict]:
    if node['frame_type'] != 1 or node['visual_type'] != 0:
        raise ValueError('Only an independent plain visual mesh is supported')
    reader = FourDsReader(data)
    reader.position = node['name_offset'] + node['name_length']
    reader.take(reader.u8())
    if reader.u16() != 0:
        raise ValueError('Instanced geometry needs a separate ownership audit')
    lod_count = reader.u8()
    if not lod_count:
        raise ValueError('Selected mesh has no geometry')
    lods = []
    for _ in range(lod_count):
        distance = struct.unpack('<f', reader.take(4))[0]
        extra_count = reader.u32()
        count = reader.u16()
        if not count or extra_count > 64 or not math.isfinite(distance):
            raise ValueError('Invalid model geometry header')
        points = []
        for _ in range(count):
            vertex = struct.unpack('<8f', reader.take(32))
            if not all(math.isfinite(n) for n in vertex):
                raise ValueError('Invalid model vertex')
            points.append(vertex[:3])
        reader.take(extra_count*count*4)
        faces = 0
        materials = []
        for _ in range(reader.u8()):
            face_count = reader.u16()
            faces += face_count
            for _ in range(face_count):
                indices = struct.unpack('<3H', reader.take(6))
                if any(i >= count for i in indices):
                    raise ValueError('Model face outside vertex array')
            materials.append(reader.u16())
        if not faces:
            raise ValueError('Selected mesh has no triangles')
        lods.append({'vertices': count, 'triangles': faces, 'clipping_range': distance,
                     'materials': materials,
                     'local_bounds': [[fn(p[i] for p in points) for i in range(3)] for fn in (min,max)]})
    if reader.position != node['end']:
        raise ValueError('Unparsed selected mesh data')
    return lods


def resolve_model_child(scene: bytes, model: bytes, owner: str, spec: dict) -> dict:
    if not isinstance(spec, dict) or set(spec) != {'instance','node','model_entry'}:
        raise ValueError('Invalid model-owner specification')
    if (not all(isinstance(v,str) and v for v in spec.values())
            or not MODEL_PATH.fullmatch(spec['model_entry'])
            or '.' in spec['instance'] or '.' in spec['node']
            or owner.casefold() != (spec['instance']+'.'+spec['node']).casefold()):
        raise ValueError('Owner must identify one reviewed model child')
    instance = model_instance(scene, spec['instance'])
    if instance['model_entry'] != spec['model_entry']:
        raise ValueError('Instance points to a different model')
    parsed = parse_4ds_nodes(model)
    matches = [n for n in parsed['nodes'] if n['name'].casefold() == spec['node'].casefold()]
    if len(matches) != 1 or matches[0]['parent_id'] != 0:
        raise ValueError('Missing, nested or ambiguous direct model child')
    node = matches[0]
    if any(n['parent_id'] == node['index'] for n in parsed['nodes']):
        raise ValueError('Selected child owns other nodes; separate hierarchy review required')
    rotation = struct.unpack_from('<4f', model, node['position_offset'] + 12)
    if (not all(math.isfinite(v) for v in (*node['position'], *node['scale'], *rotation))
            or any(v == 0 for v in node['scale'])):
        raise ValueError('Invalid child transform')
    lods = visual_geometry(model, node)
    if any(not 1 <= material <= parsed['material_count'] for lod in lods for material in lod['materials']):
        raise ValueError('Selected mesh references an invalid material')
    return {'instance': instance, 'node': {**{key: node[key] for key in
            ('name','index','parent_id','position','scale','frame_type','visual_type')},
            'rotation_serialized': list(rotation)},
            'lods': lods, 'model_has_animation': parsed['has_animation'],
            'physics_validated': False, 'world_child_transform_computed': False}
