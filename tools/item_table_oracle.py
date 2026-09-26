"""Bounded native traversal of all 500 item slots, entirely in private memory.

The original loop, constructors and descriptor readers execute. File opening,
allocation/read of the source file, UI/error handling and cleanup are NOT run.
No OS calls, native processes, installed tables or game saves are accessed.
"""
from __future__ import annotations
import struct

from item_native_contract import Oracle,sha
from item_native_layout import decode_record
from items_sav import parse as parse_items


def validated_table(raw):
    parsed=parse_items(raw,capacity=500)
    for slot in parsed['slots']:
        if slot['present']:decode_record(raw[slot['offset']:slot['offset']+slot['size']])
    return parsed


class TableOracle(Oracle):
    TABLE_MANAGER=0x3500000
    TABLE_INPUT=0x3600000
    TABLE_INPUT_SIZE=0x3e000
    TABLE_ARENA=0x3700000
    TABLE_ARENA_SIZE=0x40000
    LOOP_START=0x7dca3c
    LOOP_END=0x7dcb00

    def __init__(self,image):
        super().__init__(image)
        self.table_active=False;self.table_slots=[];self.visited=[];self.table_source=0
        self.uc.mem_map(self.TABLE_MANAGER,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_map(self.TABLE_INPUT,self.TABLE_INPUT_SIZE,self.uni.UC_PROT_READ)
        self.uc.mem_map(self.TABLE_ARENA,self.TABLE_ARENA_SIZE,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)

    def allocate(self,size):
        if not self.table_active:return super().allocate(size)
        if (type(size) is not int or not 0<size<=4096
                or not self.TABLE_ARENA<=self.next_address
                or self.next_address+((size+15)&~15)>self.TABLE_ARENA+self.TABLE_ARENA_SIZE):
            raise ValueError('Native table allocation outside bounded private arena')
        pointer=self.next_address;self.next_address+=(size+15)&~15
        self.allocations[pointer]=size;self.uc.mem_write(pointer,b'\xcd'*size)
        return pointer

    def on_code(self,uc,address,size,context):
        if self.table_active and self.LOOP_START<=address and address+size<=self.LOOP_END:
            if address==0x7dca46:
                slot=self.uc.reg_read(self.reg.UC_X86_REG_EBX)
                if slot!=len(self.visited) or slot>=500:
                    raise ValueError('Native table loop skipped, repeated or exceeded a slot')
                expected=self.table_slots[slot]
                if (self.uc.reg_read(self.reg.UC_X86_REG_EBP)!=self.table_source+expected['offset']
                        or self.uc.reg_read(self.reg.UC_X86_REG_ESI)!=self.TABLE_MANAGER+0x10+slot*4
                        or self.uc.reg_read(self.reg.UC_X86_REG_EDI)!=500):
                    raise ValueError('Native table cursor, destination or bound differs from parser')
                self.visited.append(slot)
            return
        super().on_code(uc,address,size,context)

    def verify_loaded_record(self,obj,raw,slot):
        layout=decode_record(raw)
        if self.get(obj+4)!=layout['kind'] or self.get(obj+8)!=slot:
            raise ValueError('Native table constructor kind/slot mismatch')
        for member,expected in layout['members'].items():
            if self.get(obj+int(member,16))!=expected['value_raw']:
                raise ValueError('Native table descriptor member mismatch')
        for offset,member in ((8,0x24),(28,0x2c),(48,0x34)):
            expected=raw[offset:offset+20];pointer=self.get(obj+member)
            if ((not expected[0] and pointer) or (expected[0] and
                    bytes(self.uc.mem_read(pointer,20))!=expected)):
                raise ValueError('Native table model/icon name mismatch')
        for action in layout['actions']:
            pointer=self.get(obj+0x48+4*action['channel'])
            if action['selector']==0:
                if pointer:raise ValueError('Native table unexpectedly allocated absent action')
            elif sha(bytes(self.uc.mem_read(pointer+4,action['native_copied_size'])))!=action['native_copied_sha256']:
                raise ValueError('Native table action descriptor mismatch')
        return layout

    def inspect_table(self,raw):
        parsed=validated_table(raw)
        self.allocations.clear();self.next_address=self.TABLE_ARENA
        self.table_slots=parsed['slots'];self.visited=[]
        # Place the input's final byte at the end of its read-only mapping.
        self.table_source=self.TABLE_INPUT+self.TABLE_INPUT_SIZE-len(raw)
        self.uc.mem_write(self.table_source,raw)
        self.uc.mem_write(self.TABLE_MANAGER,b'\xcd'*4096)
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,self.STACK+0x8000)
        self.uc.reg_write(self.reg.UC_X86_REG_EDI,self.TABLE_MANAGER)
        self.uc.reg_write(self.reg.UC_X86_REG_EBP,self.table_source)
        self.table_active=True
        try:
            self.uc.emu_start(self.LOOP_START,self.LOOP_END,count=1_000_000,timeout=5_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.LOOP_END:
                raise ValueError('Native table loop exceeded instruction/time budget')
            if (self.visited!=list(range(500))
                    or self.uc.reg_read(self.reg.UC_X86_REG_EBP)!=self.table_source+parsed['serialized_size']
                    or self.uc.reg_read(self.reg.UC_X86_REG_EBX)!=500
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESI)!=self.TABLE_MANAGER+0x10+2000):
                raise ValueError('Native table loop final state mismatch')
            checked=0;descriptor_hashes={};object_pointers=set()
            for slot in parsed['slots']:
                pointer=self.get(self.TABLE_MANAGER+0x10+slot['slot']*4)
                if not slot['present']:
                    if pointer:raise ValueError('Native table filled an empty slot')
                    continue
                if pointer not in self.allocations or pointer in object_pointers:
                    raise ValueError('Native table object missing or aliases another slot')
                object_pointers.add(pointer)
                record=raw[slot['offset']:slot['offset']+slot['size']]
                layout=self.verify_loaded_record(pointer,record,slot['slot'])
                descriptor_hashes[str(slot['slot'])]=layout['record_sha256'];checked+=1
            if bytes(self.uc.mem_read(self.table_source,len(raw)))!=raw:
                raise ValueError('Native table traversal changed read-only source')
            return {'schema_version':1,'scope':'offline_native_500_slot_traversal',
                'table_size':len(raw),'table_sha256':sha(raw),'slots_visited':len(self.visited),
                'present_descriptors_checked':checked,'empty_pointers_checked':500-checked,
                'descriptor_sha256_by_slot':descriptor_hashes,
                'native_end_offset':parsed['serialized_size'],
                'allocation_tail_bytes_not_parsed_as_slots':parsed['allocation_tail_size'],
                'private_allocated_bytes':self.next_address-self.TABLE_ARENA,
                'private_allocation_count':len(self.allocations),
                'native_slot_loop_matches':True,'native_loaded_descriptors_match':True,
                'source_read_only_unchanged':True,
                'file_io_or_error_paths_executed':False,'native_whole_file_loader_executed':False,
                'game_started':False,'game_modified':False,'saved_game_compatibility_qualified':False}
        finally:
            self.table_active=False
