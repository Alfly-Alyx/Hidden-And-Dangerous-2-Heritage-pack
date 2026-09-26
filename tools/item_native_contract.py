#!/usr/bin/env python3
"""Read-only offline oracle for reviewed HD2 1.12 descriptor routines.

Only an exactly pinned, privately decompressed image is accepted. Unicorn is
an isolated CPU emulator: this does not load a Windows executable, attach to a
process, patch a client, call an OS API or access game saves. Allocation/free
are bounded Python doubles. Unreviewed instruction destinations fail closed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from item_native_layout import decode_record, fpv_loaded_cell, fpv_native_projection

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SHA = '1eebde4710f800f712a05b1ecee2ba862c144f478df89b58e54c912e857ee78c'
IMAGE_SHA = '2c04629cf79b64c0c12f310187974f357ffbfc22bbc11f1488764cd078d3e7aa'
IMAGE_BASE = 0x401000
IMAGE_SIZE = 8101888
CONSTRUCTORS = {0: 0x7e0850, 1: 0x7e0940, 2: 0x7e0ac0}
RANGES = ((0x7df330, 0x7df7a3), (0x7df7e0, 0x7df82b),
          (0x7dff10, 0x7e0654), (0x7e0850, 0x7e086b),
          (0x7e08d0, 0x7e0932), (0x7e0940, 0x7e0962),
          (0x7e0a20, 0x7e0adb), (0x7e0b50, 0x7e0c00),
          (0x490ea3, 0x490eb5), (0x490f58, 0x490f68),
          (0x491072, 0x49108c), (0x491096, 0x4910a6),
          (0x49078a, 0x4907a9), (0x4907e1, 0x4907f2),
          (0x490803, 0x490815), (0x7d3ebd, 0x7d3ec5),
          (0x4923f8, 0x492406), (0x49121d, 0x491231),
          (0x492e21, 0x492e3a), (0x492e79, 0x492eb4))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_image(raw):
    if len(raw) != IMAGE_SIZE or sha(raw) != IMAGE_SHA:
        raise ValueError('Unreviewed decompressed client image; no native routine executed')


class Oracle:
    STOP = 0x3000000
    STACK = 0x3100000
    HEAP = 0x3200000
    INPUT = 0x3300000
    FPV = 0x3400000

    def __init__(self, image):
        verify_image(image)
        sys.path.insert(0, str(ROOT/'.research/binary-patch-deps'))
        import unicorn as uni
        from unicorn import x86_const as reg
        self.uni, self.reg = uni, reg
        self.uc = uni.Uc(uni.UC_ARCH_X86, uni.UC_MODE_32)
        self.uc.mem_map(IMAGE_BASE, (len(image)+4095)&~4095, uni.UC_PROT_READ|uni.UC_PROT_EXEC)
        self.uc.mem_write(IMAGE_BASE, image)
        self.uc.mem_map(self.STOP, 4096, uni.UC_PROT_READ|uni.UC_PROT_EXEC)
        self.uc.mem_map(self.STACK, 65536, uni.UC_PROT_READ|uni.UC_PROT_WRITE)
        self.uc.mem_map(self.HEAP, 65536, uni.UC_PROT_READ|uni.UC_PROT_WRITE)
        self.uc.mem_map(self.INPUT, 4096, uni.UC_PROT_READ)
        self.uc.mem_map(self.FPV, 0x4d000, uni.UC_PROT_READ|uni.UC_PROT_WRITE)
        self.allocations = {}
        self.next_address = self.HEAP
        self.uc.hook_add(uni.UC_HOOK_CODE, self.on_code)

    def get(self, address):
        return struct.unpack('<I', self.uc.mem_read(address, 4))[0]

    def put(self, address, value):
        self.uc.mem_write(address, struct.pack('<I', value))

    def allocate(self, size):
        if not 0 < size <= 4096 or self.next_address+size > self.HEAP+65536:
            raise ValueError('Emulator allocation outside bounded private arena')
        address = self.next_address
        self.next_address += (size+15)&~15
        self.allocations[address] = size
        self.uc.mem_write(address, bytes([0xcd])*size)
        return address

    def on_code(self, _uc, address, size, _context):
        if address in (0x7e566f, 0x7e2120):
            esp = self.uc.reg_read(self.reg.UC_X86_REG_ESP)
            arg = self.get(esp+4)
            if address == 0x7e566f:
                self.uc.reg_write(self.reg.UC_X86_REG_EAX, self.allocate(arg))
            elif arg and arg not in self.allocations:
                raise ValueError('Unexpected emulator free target')
            self.uc.reg_write(self.reg.UC_X86_REG_EIP, self.get(esp))
            self.uc.reg_write(self.reg.UC_X86_REG_ESP, esp+4)
            return
        if not any(start <= address and address+size <= end for start, end in RANGES):
            raise ValueError(f'Unreviewed native instruction destination: {address:#x}')

    def call(self, address, obj, *arguments):
        esp = self.STACK+0x8000
        self.uc.mem_write(esp, struct.pack('<'+'I'*(len(arguments)+1), self.STOP, *arguments))
        self.uc.reg_write(self.reg.UC_X86_REG_ESP, esp)
        self.uc.reg_write(self.reg.UC_X86_REG_ECX, obj)
        self.uc.emu_start(address, self.STOP, timeout=1_000_000, count=20000)
        if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != self.STOP:
            raise ValueError('Native oracle instruction/time budget exhausted')
        if self.uc.reg_read(self.reg.UC_X86_REG_ESP) != esp+4+4*len(arguments):
            raise ValueError('Native oracle calling convention mismatch')

    def inspect_record(self, raw, slot_id):
        if type(slot_id) is not int or not 0 <= slot_id < 500:
            raise ValueError('Native item slot outside 1.12 capacity')
        layout = decode_record(raw)
        # A fresh arena for every item. Input ends exactly at an unmapped page.
        self.allocations.clear()
        self.next_address = self.HEAP
        obj = self.allocate(0x68)
        measure = self.allocate(4)
        source = self.INPUT+4096-len(raw)
        self.uc.mem_write(source, raw)
        self.call(CONSTRUCTORS[layout['kind']], obj, slot_id)
        self.put(measure, 500)
        self.call(self.get(self.get(obj)+8), obj, measure, source+8)
        if self.get(obj+4) != layout['kind'] or self.get(obj+8) != slot_id:
            raise ValueError('Native constructor kind/slot mismatch')
        for member, expected in layout['members'].items():
            if self.get(obj+int(member, 16)) != expected['value_raw']:
                raise ValueError('Independent parser/native descriptor member mismatch')
        for record_offset, member in ((8, 0x24), (28, 0x2c), (48, 0x34)):
            expected = raw[record_offset:record_offset+20]
            pointer = self.get(obj+member)
            if (expected[0] == 0 and pointer != 0) or (expected[0] != 0 and
                    bytes(self.uc.mem_read(pointer, 20)) != expected):
                raise ValueError('Native model/icon name copy mismatch')
        for action in layout['actions']:
            pointer = self.get(obj+0x48+4*action['channel'])
            if action['selector'] == 0:
                if pointer != 0:
                    raise ValueError('Absent native action unexpectedly allocated')
            elif sha(bytes(self.uc.mem_read(pointer+4, action['native_copied_size']))) != action['native_copied_sha256']:
                raise ValueError('Native action payload copy mismatch')
        # Type-specific readers leave measure at the measured BASE size.
        expected_base = layout['derived_offset']-8
        if self.get(measure) != expected_base:
            raise ValueError('Native descriptor base size mismatch')
        self.put(measure, 0)
        self.call(self.get(self.get(obj)+4), obj, measure, source+8)
        if self.get(measure) != layout['descriptor_serialized_size']:
            raise ValueError('Native descriptor serializer size mismatch')
        if bytes(self.uc.mem_read(source, len(raw))) != raw:
            raise ValueError('Read-only item input changed')
        return {**layout, 'slot': slot_id, 'native_decode_matches': True,
                'native_descriptor_measure_matches': True,
                'game_started': False, 'saved_game_serialization_qualified': False}

    def fpv_cell(self, group_id, state_id, channel_ordinal):
        expected = fpv_loaded_cell(group_id, state_id, channel_ordinal)
        stack = self.STACK+0x8000
        self.uc.reg_write(self.reg.UC_X86_REG_ESP, stack)
        self.uc.reg_write(self.reg.UC_X86_REG_EAX, group_id)
        self.uc.reg_write(self.reg.UC_X86_REG_EDI, channel_ordinal)
        self.put(stack+0x10, state_id)
        self.put(stack+0x1c, self.HEAP)
        # End before file/string-reader calls. Both arithmetic paths execute
        # their actual pinned instructions; no OS or resource loader runs.
        for start, end in ((0x490ea3, 0x490eb5), (0x490f58, 0x490f68),
                           (0x491072, 0x49108c)):
            self.uc.emu_start(start, end, count=32, timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != end:
                raise ValueError('FPV indexing instruction budget exhausted')
        name = self.uc.reg_read(self.reg.UC_X86_REG_EDX)-self.HEAP
        self.uc.emu_start(0x491096, 0x4910a6, count=32, timeout=1_000_000)
        value = self.uc.reg_read(self.reg.UC_X86_REG_EAX)-self.HEAP
        if (self.uc.reg_read(self.reg.UC_X86_REG_EIP) != 0x4910a6 or
                name != expected['name_member_offset'] or value != expected['value_member_offset']):
            raise ValueError('Native FPV index math differs from independent decoder')
        return {**expected, 'native_index_math_matches': True,
                'fpv_consumer_qualified': False}

    def fpv_capacity(self):
        stages = ((0x49078a, 0x4907a9, 0xa0, 624, 500),
                  (0x4907e1, 0x4907f2, 0, 48, 13),
                  (0x490803, 0x490815, 0x10, 4, 4))
        for start, end, member, stride, count in stages:
            stack = self.STACK+0x8000
            for register in (self.reg.UC_X86_REG_ECX, self.reg.UC_X86_REG_ESI):
                self.uc.reg_write(register, self.HEAP)
            self.uc.reg_write(self.reg.UC_X86_REG_ESP, stack)
            self.uc.reg_write(self.reg.UC_X86_REG_EBX, 0)
            self.uc.emu_start(start, end, count=32, timeout=1_000_000)
            pointer = self.uc.reg_read(self.reg.UC_X86_REG_ESP)
            observed = tuple(self.get(pointer+4*n) for n in range(3))
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != end or observed != (self.HEAP+member, stride, count):
                raise ValueError('Unexpected FPV constructor array layout')
        return {'item_slots': 500, 'slot_stride': 624, 'states_per_slot': 13,
                'state_stride': 48, 'channels_per_state': 4,
                'array_member_offset': 0xa0, 'array_end_member_offset': 0x4c360,
                'native_constructor_arguments_match': True,
                'constructors_not_executed': True}

    def fpv_binding(self, slot_id, state_index):
        if (type(slot_id) is not int or not 0<=slot_id<500
                or type(state_index) is not int or not 0<=state_index<13):
            raise ValueError('Native FPV binding outside reviewed slot/state domain')
        cell=fpv_loaded_cell(slot_id+100, state_index+2000, 0)
        # Execute only the reviewed data-flow blocks, stopping BEFORE any
        # scene/model call. Objects and model pointers are synthetic sentinels.
        stack=self.STACK+0x8000
        instance=self.HEAP+0x8000
        descriptor=self.HEAP+0x9000
        for register,value in ((self.reg.UC_X86_REG_EAX,slot_id),
                               (self.reg.UC_X86_REG_ECX,descriptor),
                               (self.reg.UC_X86_REG_ESI,instance)):
            self.uc.reg_write(register,value)
        self.uc.emu_start(0x7d3ebd,0x7d3ec5,count=16)
        self.put(descriptor+0x64,0x12345678)
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,stack)
        self.uc.reg_write(self.reg.UC_X86_REG_EDI,instance)
        self.uc.reg_write(self.reg.UC_X86_REG_ESI,self.FPV)
        self.uc.reg_write(self.reg.UC_X86_REG_EAX,0x23456789)
        self.uc.emu_start(0x4923f8,0x492406,count=16)
        if tuple(self.get(stack-12+4*n) for n in range(3)) != (0x23456789,0x12345678,slot_id):
            raise ValueError('Weapon instance slot not passed as FPV selector argument')
        # Mimic only the stack frame of the observed three-argument setter.
        self.uc.reg_write(self.reg.UC_X86_REG_EBP,stack-20)
        self.uc.emu_start(0x49121d,0x491231,count=16)
        if self.get(self.FPV+0x54)!=slot_id:
            raise ValueError('Native FPV selector differs from item instance slot')
        self.put(stack+8,state_index)
        self.uc.reg_write(self.reg.UC_X86_REG_EBP,stack)
        self.uc.emu_start(0x492e21,0x492e3a,count=16)
        if self.uc.reg_read(self.reg.UC_X86_REG_EDX)-self.FPV != cell['value_member_offset']:
            raise ValueError('FPV consumer selects a different cell from the loader')
        return {'slot':slot_id,'state_index':state_index,'group_id':slot_id+100,
                'native_instance_to_consumer_binding_matches':True,
                'scene_or_model_calls_executed':False,'live_animation_qualified':False}

    def fpv_threshold_choice(self, slot_id, state_index, thresholds, draw):
        self.fpv_binding(slot_id,state_index)
        if (len(thresholds)!=4 or any(type(t) is not int or not 0<=t<=100 for t in thresholds)
                or type(draw) is not int or not 0<=draw<=100):
            raise ValueError('Synthetic FPV thresholds/draw outside 0..100')
        cell=fpv_loaded_cell(slot_id+100,state_index+2000,0)
        for index,value in enumerate(thresholds):
            self.put(self.FPV+cell['value_member_offset']+4*index,value)
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,self.STACK+0x8000)
        self.uc.reg_write(self.reg.UC_X86_REG_EAX,draw)
        # RandFloat and float conversion are not executed. The draw is an
        # explicit input; selection uses native signed cumulative thresholds.
        self.uc.emu_start(0x492e79,0x492eab,count=96)
        end=self.uc.reg_read(self.reg.UC_X86_REG_EIP)
        if end != 0x492eab:
            raise ValueError('Native FPV threshold selection left its reviewed block')
        chosen=self.uc.reg_read(self.reg.UC_X86_REG_EDI)
        expected=next((i for i,t in enumerate(thresholds) if draw<=t),4)
        if chosen!=expected:
            raise ValueError('Native FPV threshold selection mismatch')
        return None if chosen==4 else chosen


def main(argv=None):
    from benelli_table_audit import read_tables
    from items_sav import parse
    from fpv_table import parse as parse_fpv
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', required=True, type=Path)
    parser.add_argument('--image', type=Path, default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--archives-only', action='store_true')
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():
            raise ValueError('Report exists; use a fresh path')
        if sha((args.game/'HD2_SabreSquadron.exe').read_bytes()) != SOURCE_SHA:
            raise ValueError('Unreviewed packed client')
        machine = Oracle(args.image.read_bytes())
        capacity = machine.fpv_capacity()
        bindings = [machine.fpv_binding(slot,state) for slot in (9,10,23,359,499) for state in range(13)]
        fpv_cells = [machine.fpv_cell(group, state, channel)
                     for group in (100, 109, 110, 359, 459, 599)
                     for state in range(2000, 2013) for channel in range(4)]
        tables, excluded = read_tables(args.game, archives_only=args.archives_only)
        layers = {}
        projections = {}
        for (archive, name), raw in tables.items():
            if name == 'tables/fpvanims.sav':
                projection=fpv_native_projection(parse_fpv(raw))
                projections[archive]={k:v for k,v in projection.items() if k!='cells'}
            if name != 'tables/items.sav':
                continue
            parsed = parse(raw)
            items = [machine.inspect_record(raw[s['offset']:s['offset']+s['size']], s['slot'])
                     for s in parsed['slots'] if s['present']]
            layers[archive] = {'table_sha256': sha(raw), 'records_checked': len(items), 'records': items}
            print(f'{archive}: {len(items)} native descriptors checked', flush=True)
        report = {'schema_version': 1, 'scope': 'offline_native_item_descriptor_oracle',
                  'source_sha256': SOURCE_SHA, 'private_image_sha256': IMAGE_SHA,
                  'layers': layers, 'excluded_loose_overrides': excluded,
                  'fpv_cells_checked': len(fpv_cells),
                  'fpv_capacity': capacity,
                  'fpv_bindings_checked':len(bindings),
                  'fpv_table_projections':projections,
                  'fpv_loader_index_math_qualified': True,
                  'fpv_instance_slot_binding_qualified': True,
                  'live_animation_qualified': False,
                  'game_started': False, 'game_files_modified': False,
                  'saved_game_serialization_qualified': False,
                  'item_slot_allocated': False}
        rendered = json.dumps(report, ensure_ascii=False, indent=2)+'\n'
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            with args.json_output.open('x', encoding='utf-8') as stream:
                stream.write(rendered)
        print(json.dumps({k:v for k,v in report.items() if k != 'layers'}, indent=2))
        print('Native descriptors checked: '+str(sum(l['records_checked'] for l in layers.values())))
        return 0
    except (OSError, ValueError, ImportError) as error:
        print('Native item contract refused: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
