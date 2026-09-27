"""Full pinned SetAnimation on synthetic models and privately relocated clips.

Native slot setup, target lookup, descriptors, restart and detach run together.
Only bounded owner allocation/free are Python doubles. No file/scene loader,
pose, event, renderer, library entry point or operating-system API executes.
"""
from copy import deepcopy
import struct

from five_ds import HEADER, parse_5ds
from ls3d_binding_oracle import name_bytes, select_name
from ls3d_math_oracle import MathOracle, f32

START = 0x100342f0
RANGES = ((START, 0x10034336), (0x1003439a, 0x100343c8),
          (0x10020260, 0x100204bf),
          (0x10020740, 0x100207ba), (0x100207d4, 0x100207e2),
          (0x1002083c, 0x10020871), (0x100206b0, 0x10020709),
          (0x10020709, 0x10020737),
          (0x10004c80, 0x10004c92), (0x10004ccd, 0x10004cd1),
          (0x10004e60, 0x10004e74), (0x10004ed0, 0x10004edc))
ALLOC = 0x1008d41c
FREE = 0x1008d310


def validate(names, clips, operations, model_kind=9):
    if not isinstance(names, list) or len(names) > 128:
        raise ValueError('Unreviewed attachment target count')
    for name in names:
        name_bytes(name)
    if type(model_kind) is not int or model_kind not in (9, 0):
        raise ValueError('Unreviewed attachment container')
    if not isinstance(clips, dict) or not 1 <= len(clips) <= 9:
        raise ValueError('Unreviewed attachment clip count')
    parsed = {}
    for key, item in clips.items():
        name_bytes(key)
        if not isinstance(item, dict) or set(item) != {'data', 'mode'}:
            raise ValueError('Unexpected attachment clip record')
        if type(item['mode']) is not int or not 0 <= item['mode'] <= 3:
            raise ValueError('Unreviewed clip default mode')
        raw = item['data']
        if not isinstance(raw, bytes) or len(raw) - HEADER > 0xf000:
            raise ValueError('Unreviewed attachment clip size')
        parsed[key] = parse_5ds(raw)
        if parsed[key]['track_count'] > 128:
            raise ValueError('Unreviewed attachment track count')
        for track in parsed[key]['tracks']:
            name_bytes(track['name'])
    if not isinstance(operations, list) or not 1 <= len(operations) <= 32:
        raise ValueError('Unreviewed attachment operation count')
    clean = []
    for op in operations:
        if not isinstance(op, dict) or set(op) != {'clip', 'slot', 'weight', 'mode'}:
            raise ValueError('Unexpected attachment operation')
        if op['clip'] is not None and (not isinstance(op['clip'], str) or op['clip'] not in clips):
            raise ValueError('Unknown attachment clip')
        if type(op['slot']) is not int or not 0 <= op['slot'] < 8:
            raise ValueError('Invalid attachment slot')
        if type(op['mode']) is not int or not 0 <= op['mode'] <= 3:
            raise ValueError('Unreviewed attachment mode')
        weight = f32(op['weight'])
        if not 0 <= weight <= 2:
            raise ValueError('Unreviewed attachment weight')
        clean.append({**op, 'weight': weight})
    return parsed, clean


def reference_sequence(names, clips, operations, model_kind=9):
    parsed, operations = validate(names, clips, operations, model_kind)
    slots = [dict(clip=None, active=False, mode=3, time=17, previous=19,
                  last_delta=23, weight=.25) for _ in range(8)]
    owners = {}; dirty = False; allocated = freed = 0; touched = set(); snapshots = []
    for op in operations:
        slot = slots[op['slot']]; old = slot['clip']; new = op['clip']
        if old != new:
            for descriptors in owners.values():
                descriptors[op['slot']] = None
            slot['clip'] = new
        if new is not None:
            slot.update(active=True, mode=op['mode'] or clips[new]['mode'],
                        time=0, previous=-40, weight=op['weight'])
            for index, track in enumerate(parsed[new]['tracks']):
                node = select_name(names, track['name'])
                if node is None:
                    continue
                if node not in owners:
                    owners[node] = [None] * 8; allocated += 1; touched.add(node)
                owners[node][op['slot']] = (new, index)
            dirty = True
        elif old is not None:
            slot['active'] = False
        # Native pruning first checks every controller active flag. A target
        # with no descriptors can remain while ANY slot is active.
        if old != new or new is not None:
            if not any(row['active'] for row in slots):
                expired = [node for node, ds in owners.items() if not any(ds)]
                for node in expired:
                    del owners[node]; freed += 1
        snapshots.append(deepcopy({'slots': slots, 'owners': owners, 'dirty': dirty,
            'allocated': allocated, 'freed': freed, 'touched': sorted(touched),
            'references': {key: 1 + sum(row['clip'] == key for row in slots) for key in clips}}))
    return snapshots


class AttachOracle(MathOracle):
    SOURCE = 0x3400000
    STATE = 0x3600000
    STATE_SIZE = 0x20000

    def __init__(self, raw):
        super().__init__(raw)
        self.uc.mem_map(self.SOURCE, 0xa0000, self.uni.UC_PROT_READ)
        self.uc.mem_map(self.STATE, self.STATE_SIZE, self.uni.UC_PROT_READ | self.uni.UC_PROT_WRITE)
        # Isolated x86 SEH head only, never a Windows thread/environment.
        self.uc.mem_map(0, 4096, self.uni.UC_PROT_READ | self.uni.UC_PROT_WRITE)
        self.allocated = {}; self.alloc_count = self.free_count = 0

    def on_code(self, uc, address, size, context):
        if self.phase != 'attach':
            return super().on_code(uc, address, size, context)
        if address in (ALLOC, FREE):
            stack = uc.reg_read(self.reg.UC_X86_REG_ESP)
            ret, arg = struct.unpack('<II', uc.mem_read(stack, 8))
            if address == ALLOC:
                if ret != 0x1002077e or arg != 0xf4:
                    raise ValueError('Unreviewed native allocation request')
                pointer = next((self.STATE + 0x10000 + i * 0x100 for i in range(128)
                                if self.STATE + 0x10000 + i * 0x100 not in self.allocated), None)
                if pointer is None:
                    raise ValueError('Bounded attachment owner arena exhausted')
                self.allocated[pointer] = arg; self.alloc_count += 1
                uc.mem_write(pointer, b'\xcd' * arg)
                uc.reg_write(self.reg.UC_X86_REG_EAX, pointer)
            else:
                if ret != 0x1002070f or arg not in self.allocated:
                    raise ValueError('Unreviewed native owner release')
                del self.allocated[arg]; self.free_count += 1
            uc.reg_write(self.reg.UC_X86_REG_ESP, stack + 4) # cdecl: caller pops arg.
            uc.reg_write(self.reg.UC_X86_REG_EIP, ret)
            return
        if not any(a <= address and address + size <= b for a, b in RANGES):
            raise ValueError(f'Unreviewed attachment instruction/call: {address:#x}')
        self.visited.add(address)

    def sequence(self, names, clips, operations, model_kind=9):
        parsed, operations = validate(names, clips, operations, model_kind)
        expected = reference_sequence(names, clips, operations, model_kind)
        if self.phase is not None:
            raise ValueError('Nested attachment phase')
        source = bytearray(0xa0000); state = bytearray(self.STATE_SIZE)
        model = self.STATE + 0x100; controller = self.STATE + 0x400
        struct.pack_into('<I', state, 0x230, controller)
        struct.pack_into('<H', state, 0x1f8, model_kind)
        offset, count_offset = (0x120, 0x128) if model_kind == 9 else (0x234, 0x23c)
        struct.pack_into('<I', state, 0x100 + offset, self.SOURCE + 0x400)
        struct.pack_into('<I', state, 0x100 + count_offset, len(names))
        struct.pack_into('<I', state, 0x400, model)
        struct.pack_into('<IIII', state, 0x4e8, self.STATE + 0x800, 128, 0, 128)
        for i in range(8):
            struct.pack_into('<Iiiif', state, 0x410 + i * 0x1c, 3, 17, 19, 23, .25)
        node_pointers = []
        for i, name in enumerate(names):
            node = self.STATE + 0x1000 + i * 0x100; node_pointers.append(node)
            string = 0x1000 + i * 64; raw = name_bytes(name)
            struct.pack_into('<I', source, 0x400 + i * 4, node)
            source[string:string+len(raw)] = raw
            struct.pack_into('<I', state, node-self.STATE+0xe8, self.SOURCE+string)
            struct.pack_into('<I', state, node-self.STATE+0xe0, 8)
        clip_pointers = {}; data_pointers = {}
        for i, (key, clip) in enumerate(clips.items()):
            pointer = self.STATE + 0xa000 + i * 0x100
            data_offset = 0x10000 + i * 0x10000; body = bytearray(clip['data'][HEADER:])
            for track in range(parsed[key]['track_count']):
                name, keys = struct.unpack_from('<II', body, 4+8*track)
                struct.pack_into('<II', body, 4+8*track, self.SOURCE+data_offset+name,
                                 self.SOURCE+data_offset+keys)
            source[data_offset:data_offset+len(body)] = body
            struct.pack_into('<IIIII', state, pointer-self.STATE,
                             0x1009b400, 1, clip['mode'], 0, self.SOURCE+data_offset)
            clip_pointers[key] = pointer; data_pointers[key] = self.SOURCE+data_offset
        self.uc.mem_write(self.SOURCE, bytes(source)); self.uc.mem_write(self.STATE, bytes(state))
        self.uc.mem_write(0, b'\xff' * 4 + bytes(4092))
        self.allocated = {}; self.alloc_count = self.free_count = 0
        writes = [(0, 4), (controller+4, controller+5), (controller+8, controller+0xe8),
                  (controller+0xf0, controller+0xf4), (self.STATE+0x800, self.STATE+0xa00),
                  (self.STATE+0x10000, self.STATE+0x18000)]
        writes.extend((node+0xe0, node+0xe4) for node in node_pointers)
        writes.extend((pointer+4, pointer+8) for pointer in clip_pointers.values())
        results = []
        for op, wanted in zip(operations, expected):
            stack = self.STACK + 0xf000; self.uc.mem_write(self.STACK, bytes(65536))
            weight_bits = struct.unpack('<I', struct.pack('<f', op['weight']))[0]
            self.uc.mem_write(stack, struct.pack('<6I', self.STOP, model,
                clip_pointers.get(op['clip'], 0), op['slot'], weight_bits, op['mode']))
            for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
                self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), 0)
            for name, value in (('ESP', stack), ('EFLAGS', 2), ('FPCW', 0x27f), ('FPSW', 0), ('FPTAG', 0xffff)):
                self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), value)
            self.phase = 'attach'; self.writes = tuple(writes); self.visited = set()
            try:
                self.uc.emu_start(START, self.STOP, count=6_000_000, timeout=20_000_000)
                if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != self.STOP:
                    raise ValueError('Attachment instruction/time budget exhausted')
                if self.uc.reg_read(self.reg.UC_X86_REG_ESP) != stack+24 or self.uc.reg_read(self.reg.UC_X86_REG_EAX) != 0:
                    raise ValueError('Attachment result/stack differs')
            finally:
                self.phase = None; self.writes = ()
            actual = bytes(self.uc.mem_read(self.STATE, self.STATE_SIZE))
            self.check_state(actual, wanted, parsed, clip_pointers, data_pointers, node_pointers)
            if bytes(self.uc.mem_read(self.SOURCE, len(source))) != bytes(source):
                raise ValueError('Attachment changed read-only clip/name inputs')
            if bytes(self.uc.mem_read(0, 4096)) != b'\xff' * 4 + bytes(4092):
                raise ValueError('Attachment did not restore isolated SEH head')
            allowed = {i-self.STATE for a,b in writes if a >= self.STATE for i in range(a,b)}
            if any(a != b and i not in allowed for i,(a,b) in enumerate(zip(state, actual))):
                raise ValueError('Attachment changed unrelated model/target fields')
            results.append({'slot': op['slot'], 'clip': op['clip'],
                'owners': len(wanted['owners']), 'allocated': wanted['allocated'], 'freed': wanted['freed'],
                'active_slots': sum(row['active'] for row in wanted['slots'])})
        return {'operations': results, 'native_attachment_sequence_match': True,
            'native_target_descriptors_checked': True, 'inputs_preserved': True,
            'owner_allocations': self.alloc_count, 'owner_releases': self.free_count,
            'allocator_is_bounded_double': True, 'model_controller_preallocated': True,
            'clip_relocation_is_synthetic': True, 'native_loader_executed': False,
            'poses_or_events_evaluated': False, 'scene_loaded': False,
            'library_loaded': False, 'game_started': False}

    def check_state(self, actual, wanted, parsed, clip_pointers, data_pointers, nodes):
        if actual[0x404] != int(wanted['dirty']):
            raise ValueError('Attachment dirty flag differs')
        for i, slot in enumerate(wanted['slots']):
            offset = 0x408 + i * 0x1c
            pointer, active, mode, time, previous, delta, weight = struct.unpack_from('<IB3xIiiif', actual, offset)
            if (pointer, active, mode, time, previous, delta, weight) != (
                    clip_pointers.get(slot['clip'], 0), int(slot['active']), slot['mode'],
                    slot['time'], slot['previous'], slot['last_delta'], slot['weight']):
                raise ValueError('Native slot initialization/restart/detach differs')
        for key, count in wanted['references'].items():
            if struct.unpack_from('<I', actual, clip_pointers[key]-self.STATE+4)[0] != count:
                raise ValueError('Native clip reference count differs')
        count = struct.unpack_from('<I', actual, 0x4f0)[0]
        pointers = list(struct.unpack_from('<'+'I'*count, actual, 0x800))
        if count != len(wanted['owners']) or set(pointers) != set(self.allocated) or len(set(pointers)) != count:
            raise ValueError('Native owner table differs')
        observed = set()
        for pointer in pointers:
            offset = pointer-self.STATE; target = struct.unpack_from('<I', actual, offset+0xec)[0]
            if target not in nodes:
                raise ValueError('Unexpected attached target')
            node = nodes.index(target)
            if node in observed or node not in wanted['owners']:
                raise ValueError('Duplicate/unexpected target owner')
            observed.add(node)
            if struct.unpack_from('<II', actual, offset) != (0x1009cac0, 0):
                raise ValueError('Native target owner header differs')
            if struct.unpack_from('<I', actual, offset+0xf0)[0] != self.STATE+0x400:
                raise ValueError('Native target owner controller differs')
            for slot, binding in enumerate(wanted['owners'][node]):
                base = offset + slot * 0x1c; flags = struct.unpack_from('<H', actual, base+0x24)[0]
                if binding is None:
                    if flags != 0:
                        raise ValueError('Detached channel flags not cleared')
                    continue
                key, index = binding; track = parsed[key]['tracks'][index]
                if flags != track['flags']:
                    raise ValueError('Native attached channel flags differ')
                cursor = track['offset'] + 4
                for kind, ptr, cnt, width in (('rotation', 0x10, 0x1e, 4), ('position', 0xc, 0x1c, 3), ('scale', 0x14, 0x20, 3)):
                    channel = track['channels'].get(kind); n = len(channel['frames']) if channel else 0
                    if struct.unpack_from('<H', actual, base+cnt)[0] != n:
                        raise ValueError('Native attached channel count differs')
                    if not channel:
                        continue
                    cursor += 2
                    if struct.unpack_from('<I', actual, base+ptr)[0] != data_pointers[key]+cursor-HEADER:
                        raise ValueError('Native attached channel pointer differs')
                    cursor += n*2
                    cursor += (-(cursor-HEADER)) % 16 if kind == 'rotation' else 2 if n % 2 == 0 else 0
                    cursor += n*width*4
                if cursor != track['end'] or struct.unpack_from('<H', actual, base+0x22)[0] != 0:
                    raise ValueError('Native attached descriptor/event boundary differs')
        for i, node in enumerate(nodes):
            if struct.unpack_from('<I', actual, node-self.STATE+0xe0)[0] != (8 | (0x10000000 if i in wanted['touched'] else 0)):
                raise ValueError('Native animated-node flag differs')
        if (self.alloc_count, self.free_count) != (wanted['allocated'], wanted['freed']):
            raise ValueError('Native owner allocation/release counts differ')
