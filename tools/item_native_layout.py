"""Independent decoding of the item descriptor layout in the reviewed 1.12 client.

No native code, writes or slot allocation. Offsets are relative to the entire
508-byte present record. Raw member names deliberately do not invent gameplay
meaning. Table descriptor serialization is NOT saved-game serialization.
"""
from __future__ import annotations
import hashlib
import struct

# Serialized sizes returned by the ten native action descriptor serializers.
ACTION_SIZES = (0, 36, 40, 136, 128, 16, 12, 12, 28, 16, 0)
# Two descriptors include 40 editor-only bytes not copied into the live object.
ACTION_COPIED_SIZES = (0, 36, 40, 96, 88, 16, 12, 12, 28, 16, 0)
DERIVED_MEMBERS = {0: (0x54,), 1: (0x58, 0x5c, 0x60, 0x54),
                   2: (0x54, 0x58, 0x5c, 0x60, 0x64)}
BASE_MEMBERS = {68: 0x0c, 108: 0x14, 112: 0x18, 116: 0x1c,
                120: 0x38, 124: 0x3c, 128: 0x40, 132: 0x44}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode_record(raw):
    if len(raw) != 508 or struct.unpack_from('<I', raw)[0] != 1:
        raise ValueError('Expected one 508-byte present item record')
    kind = struct.unpack_from('<I', raw, 4)[0]
    if kind not in DERIVED_MEMBERS:
        raise ValueError('Unreviewed native item kind')
    offset = 136
    actions = []
    for channel in range(2):
        if offset + 4 > len(raw):
            raise ValueError('Truncated native action selector')
        selector = struct.unpack_from('<I', raw, offset)[0]
        if selector >= len(ACTION_SIZES):
            raise ValueError('Unreviewed native action selector')
        size = ACTION_SIZES[selector]
        copied = ACTION_COPIED_SIZES[selector]
        if offset + 4 + size > len(raw):
            raise ValueError('Truncated native action descriptor')
        actions.append({'channel': channel, 'selector': selector,
                        'selector_offset': offset, 'payload_offset': offset + 4,
                        'serialized_size': size, 'native_copied_size': copied,
                        'payload_sha256': sha(raw[offset+4:offset+4+size]),
                        'native_copied_sha256': sha(raw[offset+4:offset+4+copied])})
        offset += 4 + size
    # The base serializer measures 168 bytes plus both action payloads. Only
    # 136 plus payloads are actively consumed before the derived-member seek.
    derived_offset = offset + 32
    if derived_offset + len(DERIVED_MEMBERS[kind])*4 > len(raw):
        raise ValueError('Native descriptor exceeds its item record')
    members = {f'0x{member:02x}': {'record_offset': source,
               'value_raw': struct.unpack_from('<I', raw, source)[0]}
               for source, member in BASE_MEMBERS.items()}
    for index, member in enumerate(DERIVED_MEMBERS[kind]):
        source = derived_offset + 4*index
        members[f'0x{member:02x}'] = {'record_offset': source,
                                    'value_raw': struct.unpack_from('<I', raw, source)[0]}
    return {'kind': kind, 'record_sha256': sha(raw), 'actions': actions,
            'opaque_gap_offset': offset, 'opaque_gap_size': 32,
            'derived_offset': derived_offset, 'members': members,
            'descriptor_serialized_size': derived_offset-8+len(DERIVED_MEMBERS[kind])*4,
            'saved_game_serialization_qualified': False,
            'gameplay_semantics_qualified': False}


def fpv_loaded_cell(group_id, state_id, channel_ordinal):
    """Index math at 0x490eb0/0x491072; channels use file order, not chunk ID.

    The bounded domain is our safety check, not a claim the old loader checks
    these bounds. The oracle separately verifies the 500 x 13 x 48-byte array
    constructor arguments; this still does not qualify live weapon behavior.
    """
    if (type(group_id) is not int or not 100 <= group_id < 600
            or type(state_id) is not int or not 2000 <= state_id < 2013
            or type(channel_ordinal) is not int or not 0 <= channel_ordinal < 4):
        raise ValueError('FPV cell outside the reviewed 500-slot, 13-state, 4-channel domain')
    slot = group_id-100
    state = state_id-2000
    stride = slot*13+state
    return {'slot_index': slot, 'state_index': state,
            'channel_ordinal': channel_ordinal,
            'name_member_offset': 0xb0+stride*48+channel_ordinal*4,
            'value_member_offset': 0xc0+stride*48+channel_ordinal*4}


def fpv_native_projection(parsed):
    """Reject structures the reviewed loader would not consume as described.

    The historical loader runs exactly thirteen state iterations, four channel
    iterations in FILE ORDER and reads at most one name/value per channel.
    Chunk IDs alone do not protect a reordered channel payload.
    """
    cells=[]
    for group in parsed['groups']:
        states=group['states']
        if len(states)!=13 or {s['id'] for s in states}!=set(range(2000,2013)):
            raise ValueError('Native FPV loader requires thirteen distinct state IDs')
        for state in states:
            channels=state['channels']
            if [c['id'] for c in channels]!=[3000,3001,3002,3003]:
                raise ValueError('Native FPV channels must retain their reviewed file order')
            for index,channel in enumerate(channels):
                variants=channel['variants']
                if len(variants)>1:
                    raise ValueError('Native FPV loader only consumes the first variant per channel')
                cell=fpv_loaded_cell(group['id'],state['id'],index)
                cells.append({**cell,'resource':variants[0] if variants else None})
    return {'group_count':len(parsed['groups']),'cell_count':len(cells), 'cells':cells,
            'native_shape_compatible':True,'live_animation_qualified':False}
