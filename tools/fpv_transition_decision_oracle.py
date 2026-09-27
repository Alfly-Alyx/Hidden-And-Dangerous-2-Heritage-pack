"""Pinned FPV active-clip decision and native append into a bounded prior list.

Executes the client's decision and LS3DF IsAnimationActive, not a supplied
branch. Cache, controller and spare list capacity are synthetic. Attachment
and refresh are argument-recording doubles; no loader, allocation or game.
"""
import struct

from fpv_transition_oracle import TransitionOracle, reference as tail_reference, END
from ls3d_math_oracle import BASE, f32, verify_library

START = 0x492f8e
IS_ACTIVE = 0x10034600
RANGES = ((START, 0x492fd5), (0x4930a2, 0x4930f8),
          (0x493182, 0x49319a), (0x4931d3, END),
          (0x493580, 0x4935c1), (0x4935d0, 0x49360f),
          (IS_ACTIVE, 0x1003462b))


def record(row):
    if not isinstance(row, dict) or set(row) != {'slot', 'rate', 'weight'}:
        raise ValueError('Unexpected transition record')
    if type(row['slot']) is not int or not 0 <= row['slot'] < 8:
        raise ValueError('Unreviewed controller slot')
    rate, weight = f32(row['rate']), f32(row['weight'])
    if not 0 <= rate <= 10 or not 0 <= weight <= 1:
        raise ValueError('Unreviewed transition rate or weight')
    return {'slot': row['slot'], 'rate': rate, 'weight': weight}


def reference(item, state, channel, current, previous, active, controller_present=True):
    if type(active) is not bool or type(controller_present) is not bool:
        raise ValueError('Expected explicit controller flags')
    if not isinstance(previous, list) or len(previous) > 7:
        raise ValueError('Expected bounded prior list with spare capacity')
    prior = [record(row) for row in previous]
    current = None if current is None else record(current)
    slots = [row['slot'] for row in prior] + ([] if current is None else [current['slot']])
    if len(slots) != len(set(slots)):
        raise ValueError('Duplicate supplied controller slots')
    blended = current is not None and active and controller_present
    if blended:
        prior.append(current)
    tail = tail_reference(item, state, channel, [row['slot'] for row in prior], blended)
    return {**tail, 'current': {'slot': tail['selected_slot'], 'rate': tail['rate'],
                              'weight': tail['weight']},
            'previous': prior, 'previous_clip_saved': blended,
            'native_active_queries': int(current is not None)}


class TransitionDecisionOracle(TransitionOracle):
    def __init__(self, image, library):
        verify_library(library)
        super().__init__(image)
        import pefile
        pe = pefile.PE(data=library)
        if pe.FILE_HEADER.Machine != 0x14c or pe.OPTIONAL_HEADER.ImageBase != BASE:
            raise ValueError('Unexpected active-query library')
        mapped = pe.get_memory_mapped_image()
        self.uc.mem_map(BASE, (len(mapped)+4095)&~4095,
                        self.uni.UC_PROT_READ | self.uni.UC_PROT_EXEC)
        self.uc.mem_write(BASE, mapped)
        self.queries = []

    def on_code(self, uc, address, size, context):
        if not self.active:
            raise ValueError('Decision execution outside active phase')
        if address in (self.ATTACH, self.REFRESH):
            return super().on_code(uc, address, size, context)
        if address == IS_ACTIVE:
            stack = uc.reg_read(self.reg.UC_X86_REG_ESP)
            ret, model, slot = struct.unpack('<III', uc.mem_read(stack, 12))
            if ret != 0x492fa9 or model != self.INPUT+0x100 or slot != self.old_slot:
                raise ValueError('Unexpected active-query receiver or caller')
            self.queries.append(slot)  # The actual native query still executes.
        if address in (0x493580, 0x4935d0):
            stack = uc.reg_read(self.reg.UC_X86_REG_ESP)
            args = struct.unpack('<IIII', uc.mem_read(stack, 16))
            expected = ((0x4930bf, self.old_end, self.old_end, self.old_end+16)
                        if address == 0x493580 else
                        (0x4930e1, self.old_end, 1, self.FPV+0x70))
            if args != expected:
                raise ValueError('Unexpected bounded prior-copy invocation')
        if not any(a <= address and address+size <= b for a, b in RANGES):
            raise ValueError(f'Unreviewed transition-decision instruction: {address:#x}')

    def select(self, item, state, channel, current, previous, active, controller_present=True):
        expected = reference(item, state, channel, current, previous, active, controller_present)
        if self.active:
            raise ValueError('Nested transition decision')
        current = None if current is None else record(current)
        previous = [record(row) for row in previous]
        source, target, heap = bytearray(4096), bytearray(0x4d000), bytearray(65536)
        model, vtable, controller = self.INPUT+0x100, self.INPUT+0x200, self.HEAP+0x1000
        prior = self.HEAP+0x100
        struct.pack_into('<I', source, 0x100, vtable)
        struct.pack_into('<I', source, 0x230, controller if controller_present else 0)
        for offset, destination in ((0x84, self.ATTACH), (0xac, IS_ACTIVE), (0x24, self.REFRESH)):
            struct.pack_into('<I', source, 0x200+offset, destination)
        struct.pack_into('<I', target, 0x40, model)
        struct.pack_into('<I', target, 0x54, item)
        struct.pack_into('<I', target, expected['clip_cache_member'], self.INPUT+0x300)
        self.old_slot = current['slot'] if current else 0
        if current is not None:
            struct.pack_into('<IIff', target, 0x70, self.INPUT+0x340,
                             current['slot'], current['rate'], current['weight'])
            heap[0x100c+current['slot']*0x1c] = int(active)
        self.old_end = prior+len(previous)*16
        struct.pack_into('<III', target, 0x84, prior, self.old_end, prior+128)
        for i, row in enumerate(previous):
            struct.pack_into('<IIff', heap, 0x100+i*16, self.INPUT+0x380+i*4,
                             row['slot'], row['rate'], row['weight'])
        self.uc.mem_write(self.INPUT, bytes(source))
        self.uc.mem_write(self.FPV, bytes(target))
        self.uc.mem_write(self.HEAP, bytes(heap))
        self.uc.mem_write(self.STACK, bytes(65536))
        stack, frame = self.STACK+0x8000, self.STACK+0x9000
        self.put(stack+0x10, channel)
        self.put(frame+8, state)
        for name in ('EAX', 'EBX', 'ECX', 'EDX'):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), 0)
        for name, value in (('ESP', stack), ('EBP', frame), ('ESI', self.FPV),
                            ('EDI', channel), ('EFLAGS', 2)):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), value)
        self.active, self.recorded, self.queries = True, [], []
        self.writes = ((self.FPV+0x70, self.FPV+0x80), (self.FPV+0x88, self.FPV+0x8c),
                       (self.FPV+0x90, self.FPV+0x98), (self.old_end, self.old_end+16))
        try:
            self.uc.emu_start(START, END, count=8192, timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != END:
                raise ValueError('Transition decision instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP) != stack:
                raise ValueError('Transition decision stack differs')
        finally:
            self.active, self.writes = False, ()
        wanted = bytearray(target)
        struct.pack_into('<IIff', wanted, 0x70, self.INPUT+0x300, expected['selected_slot'],
                         expected['rate'], expected['weight'])
        struct.pack_into('<II', wanted, 0x90, channel, state)
        if expected['previous_clip_saved']:
            start = self.old_end-self.HEAP
            heap[start:start+16] = target[0x70:0x80]
            struct.pack_into('<I', wanted, 0x88, self.old_end+16)
        calls = [{'operation': 'attach', 'slot': expected['selected_slot'],
                  'weight': expected['weight'], 'mode': 0}, {'operation': 'refresh'}]
        if (bytes(self.uc.mem_read(self.INPUT, len(source))) != bytes(source)
                or bytes(self.uc.mem_read(self.FPV, len(wanted))) != bytes(wanted)
                or bytes(self.uc.mem_read(self.HEAP, len(heap))) != bytes(heap)
                or self.queries != ([] if current is None else [current['slot']])
                or self.recorded != calls):
            raise ValueError('Native transition decision, full-state copy or calls differ')
        return {**expected, 'model_call_arguments': calls, 'native_decision_and_copy_match': True,
                'native_active_query_executed': current is not None, 'inputs_preserved': True,
                'entry_branch_is_supplied': False, 'spare_capacity_is_supplied': True,
                'attach_and_refresh_recorded_not_executed': True,
                'allocation_called': False, 'resource_loader_called': False,
                'scene_loaded': False, 'library_loaded': False, 'game_started': False}
