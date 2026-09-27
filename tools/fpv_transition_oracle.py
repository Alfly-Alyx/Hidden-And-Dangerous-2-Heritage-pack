"""Pinned tail of FPV clip selection; already-loaded cache and prior list.

Starts after the branch deciding whether an active previous clip is saved.
This does not execute that decision, allocation, resource loading or refresh.
"""
import struct

from item_native_contract import Oracle
from item_native_layout import fpv_loaded_cell

BLENDED = 0x493186
IMMEDIATE = 0x4931d3
END = 0x493291
RANGES = ((BLENDED, 0x49319a), (IMMEDIATE, END))


def reference(item, state, channel, previous_slots, blended):
    if (type(item) is not int or type(state) is not int or type(blended) is not bool
            or not isinstance(previous_slots, list) or len(previous_slots) > 8
            or any(type(v) is not int or not 0 <= v < 8 for v in previous_slots)
            or len(set(previous_slots)) != len(previous_slots)):
        raise ValueError('Unreviewed transition input')
    cell = fpv_loaded_cell(item+100, state+2000, channel)
    slot = next((i for i in range(3) if i not in previous_slots), 3)
    return {'item_slot': item, 'state_index': state, 'channel': channel,
        'selected_slot': slot, 'selected_slot_already_present': slot in previous_slots,
        'weight': 0.0 if blended else 1.0, 'rate': 5.0 if blended else 0.0,
        'clip_cache_member': cell['name_member_offset']-0x10, 'mode_argument': 0}


class TransitionOracle(Oracle):
    ATTACH = Oracle.STOP + 0x100
    REFRESH = Oracle.STOP + 0x120

    def __init__(self, image):
        super().__init__(image)
        self.active = False; self.writes = (); self.recorded = []
        self.uc.hook_add(self.uni.UC_HOOK_MEM_WRITE, self.on_write)

    def on_write(self, uc, access, address, size, value, context):
        if not self.active or not any(a <= address and address+size <= b for a,b in
                ((self.STACK, self.STACK+65536), *self.writes)):
            raise ValueError('Transition write outside reviewed state/stack')

    def on_code(self, uc, address, size, context):
        if not self.active:
            raise ValueError('Transition execution outside active phase')
        if address in (self.ATTACH, self.REFRESH):
            stack = uc.reg_read(self.reg.UC_X86_REG_ESP)
            count = 5 if address == self.ATTACH else 1
            words = struct.unpack('<'+'I'*(count+1), uc.mem_read(stack, 4*(count+1)))
            if words[1] != self.INPUT+0x100:
                raise ValueError('Unexpected transition model receiver')
            if address == self.ATTACH:
                if words[0] != 0x493288 or words[2] != self.INPUT+0x300 or words[5] != 0:
                    raise ValueError('Unexpected transition attachment call')
                self.recorded.append({'operation': 'attach', 'slot': words[3],
                    'weight': struct.unpack('<f', struct.pack('<I', words[4]))[0], 'mode': words[5]})
            else:
                if words[0] != END:
                    raise ValueError('Unexpected transition refresh call')
                self.recorded.append({'operation': 'refresh'})
            uc.reg_write(self.reg.UC_X86_REG_ESP, stack+4*(count+1))
            uc.reg_write(self.reg.UC_X86_REG_EAX, 0)
            uc.reg_write(self.reg.UC_X86_REG_EIP, words[0])
            return
        if not any(a <= address and address+size <= b for a,b in RANGES):
            raise ValueError('Unreviewed transition instruction or call')

    def prepare(self, item, state, channel, previous_slots, blended):
        expected = reference(item, state, channel, previous_slots, blended)
        if self.active:
            raise ValueError('Nested transition phase')
        source = bytearray(4096); target = bytearray(0x4d000); prior = bytearray(65536)
        struct.pack_into('<I', source, 0x100, self.INPUT+0x200)
        struct.pack_into('<I', source, 0x284, self.ATTACH)
        struct.pack_into('<I', source, 0x224, self.REFRESH)
        struct.pack_into('<I', target, 0x40, self.INPUT+0x100)
        struct.pack_into('<I', target, 0x54, item)
        struct.pack_into('<I', target, expected['clip_cache_member'], self.INPUT+0x300)
        struct.pack_into('<III', target, 0x84, self.HEAP, self.HEAP+len(previous_slots)*16, self.HEAP+128)
        for index, slot in enumerate(previous_slots):
            struct.pack_into('<IIff', prior, index*16, index+1, slot, 5, .5)
        self.uc.mem_write(self.INPUT, bytes(source)); self.uc.mem_write(self.FPV, bytes(target))
        self.uc.mem_write(self.HEAP, bytes(prior)); self.uc.mem_write(self.STACK, bytes(65536))
        stack = self.STACK+0x8000; frame = self.STACK+0x9000
        self.put(stack+0x10, channel); self.put(frame+8, state)
        for name in ('EAX','EBX','ECX','EDX','EDI'):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name), 0)
        for name, value in (('ESP',stack),('EBP',frame),('ESI',self.FPV),('EFLAGS',2)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.active = True; self.recorded = []
        self.writes = ((self.FPV+0x70,self.FPV+0x80),(self.FPV+0x90,self.FPV+0x98))
        try:
            self.uc.emu_start(BLENDED if blended else IMMEDIATE, END, count=4096, timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != END:
                raise ValueError('Transition instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP) != stack:
                raise ValueError('Transition slice stack differs')
        finally:
            self.active = False; self.writes = ()
        actual = bytes(self.uc.mem_read(self.FPV,len(target)))
        if struct.unpack_from('<IIff',actual,0x70) != (self.INPUT+0x300, expected['selected_slot'], expected['rate'],expected['weight']):
            raise ValueError('Native transition clip/slot/weight/rate differs')
        if struct.unpack_from('<II',actual,0x90) != (channel,state):
            raise ValueError('Native transition state/channel differs')
        calls = [{'operation':'attach','slot':expected['selected_slot'],'weight':expected['weight'],'mode':0},
                 {'operation':'refresh'}]
        if self.recorded != calls:
            raise ValueError('Native transition arguments differ')
        mutable = set(range(0x70,0x80)) | set(range(0x90,0x98))
        if (bytes(self.uc.mem_read(self.INPUT,len(source))) != bytes(source)
                or bytes(self.uc.mem_read(self.HEAP,len(prior))) != bytes(prior)
                or any(a != b and i not in mutable for i,(a,b) in enumerate(zip(target,actual)))):
            raise ValueError('Transition changed unrelated data')
        return {**expected, 'model_call_arguments':calls, 'native_transition_tail_match':True,
            'inputs_preserved':True, 'prior_list_is_supplied':True, 'entry_branch_is_supplied':True,
            'model_calls_recorded_not_executed':True, 'allocation_called':False,
            'resource_loader_called':False, 'scene_loaded':False, 'game_started':False}
