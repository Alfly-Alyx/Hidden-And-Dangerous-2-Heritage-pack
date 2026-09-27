#!/usr/bin/env python3
"""Pinned, offline resource-request argument paths. No resource loader runs.

Hand selection starts with an explicitly supplied item, NOT an actor inventory.
Animation requests start from names actually loaded by FpvTableOracle. Random
draws and empty caches are explicit synthetic inputs, not gameplay evidence.
"""
from __future__ import annotations
import struct

from fpv_table_oracle import FpvTableOracle,validated_fpv
from item_native_contract import Oracle,sha
from item_native_layout import fpv_loaded_cell

HAND_RANGES=((0x492338,0x4923c0),(0x7e5ea0,0x7e5f20),(0x7e5b30,0x7e5b57))
REQUEST_RANGES=((0x492e21,0x492e61),(0x492e79,0x492eab),(0x492ecd,0x492f15))


def hand_name(source):
    """Independent byte-string model of the reviewed 20-byte descriptor field."""
    if source is None:return 'FPV_hands'
    if not isinstance(source,str):raise ValueError('Hand model name must be text or absent')
    try:raw=source.encode('cp1252')
    except UnicodeEncodeError as error:raise ValueError('Hand model name is not cp1252') from error
    if len(raw)>19 or any(b<32 or b==127 for b in raw):
        raise ValueError('Hand model name exceeds bounded descriptor string domain')
    if 'w_default' in source:return 'FPV_hands'
    return source.rsplit('.',1)[0] if '.' in source else source


def signed(raw):return raw if raw<2**31 else raw-2**32


def request_plan(projection,slot,state,draw):
    fpv_loaded_cell(slot+100 if type(slot) is int else None,
                    state+2000 if type(state) is int else None,0)
    if type(draw) is not int or not 0<=draw<=100:raise ValueError('Synthetic draw outside 0..100')
    cells=[c for c in projection['cells'] if c['slot_index']==slot and c['state_index']==state]
    if len(cells)!=4 or [c['channel_ordinal'] for c in cells]!=[0,1,2,3]:
        raise ValueError('Requested state has not been loaded in reviewed channel order')
    if not any(c['resource'] and c['resource']['name'] and signed(c['resource']['value_raw'])>0 for c in cells):
        raise ValueError('No populated positive-valued native animation candidate')
    for cell in cells:
        resource=cell['resource']
        # Empty cells retain an ORACLE sentinel. Do not let its value masquerade
        # as the actual runtime constructor's default or select an empty name.
        if resource is None:raise ValueError('Selection would depend on an unqualified empty-cell value')
        if draw<=signed(resource['value_raw']):
            if not resource['name']:raise ValueError('Selected animation resource name is empty')
            return cell
    raise ValueError('Draw is not covered by a populated native channel')


def run_block(machine,start,end):
    machine.uc.emu_start(start,end,count=5000,timeout=1_000_000)
    if machine.uc.reg_read(machine.reg.UC_X86_REG_EIP)!=end:
        raise ValueError('Resource argument path exceeded instruction/time budget')


class HandsNameOracle(Oracle):
    def __init__(self,image):super().__init__(image);self.hand_active=False

    def on_code(self,uc,address,size,context):
        if self.hand_active:
            if not any(a<=address and address+size<=b for a,b in HAND_RANGES):
                raise ValueError('Hand resource loader or unreviewed instruction refused')
            return
        super().on_code(uc,address,size,context)

    def inspect_name(self,source):
        expected=hand_name(source)
        source_raw=(source or '').encode('cp1252').ljust(20,b'\0')
        pointer=self.INPUT+4096-20;instance=self.HEAP+0x8000;descriptor=self.HEAP+0x9000
        self.uc.mem_write(pointer,source_raw)
        self.put(instance+4,descriptor);self.put(descriptor+0x24,pointer)
        before=bytes(self.uc.mem_read(self.FPV,0x4d000))
        if bytes(self.uc.mem_read(0x867a90,1))!=b'\0':raise ValueError('Changed native empty suffix')
        stack=self.STACK+0x8000;self.uc.mem_write(stack,bytes(0x100))
        for register,value in ((self.reg.UC_X86_REG_ESP,stack),(self.reg.UC_X86_REG_ESI,self.FPV),
                               (self.reg.UC_X86_REG_EAX,instance),(self.reg.UC_X86_REG_EFLAGS,2)):
            self.uc.reg_write(register,value)
        self.hand_active=True
        try:
            run_block(self,0x4923a8 if source is None else 0x492338,0x4923c0)
            result=bytes(self.uc.mem_read(stack+12,20)).split(b'\0',1)[0].decode('cp1252')
            if (result!=expected or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-4
                    or self.get(stack-4)!=stack+12 or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=self.FPV
                    or self.get(instance+4)!=descriptor or self.get(descriptor+0x24)!=pointer
                    or bytes(self.uc.mem_read(pointer,20))!=source_raw
                    or bytes(self.uc.mem_read(self.FPV,len(before)))!=before):
                raise ValueError('Native hands name or loader argument differs from independent rule')
            return {'source_name':source,'requested_name':result,'native_name_argument_matches':True,
                    'source_read_only_unchanged':True,'stopped_before_loader':True,
                    'inventory_item_selection_qualified':False,'model_loader_executed':False,
                    'game_started':False,'game_modified':False}
        finally:self.hand_active=False


class FpvResourceOracle(FpvTableOracle):
    def __init__(self,image):
        super().__init__(image);self.request_active=False;self.loaded_projection=None

    def on_code(self,uc,address,size,context):
        if self.request_active:
            if not any(a<=address and address+size<=b for a,b in REQUEST_RANGES):
                raise ValueError('Animation resource loader or unreviewed instruction refused')
            return
        super().on_code(uc,address,size,context)

    def inspect_table(self,raw):
        self.loaded_projection=None
        _,projection=validated_fpv(raw)
        receipt=super().inspect_table(raw)
        self.loaded_projection=projection
        return receipt

    def inspect_request(self,slot,state,draw):
        if self.loaded_projection is None:raise ValueError('No successfully loaded FPV table')
        cell=request_plan(self.loaded_projection,slot,state,draw)
        before=bytes(self.uc.mem_read(self.FPV,0x4d000))
        cache=self.FPV+cell['name_member_offset']-16
        first_cache=cache-4*cell['channel_ordinal']
        string_pointer=self.get(self.FPV+cell['name_member_offset'])
        expected_name=cell['resource']['name'].encode('cp1252')
        if (self.allocations.get(string_pointer)!=len(expected_name)+9 or self.get(string_pointer)!=1
                or self.get(string_pointer+4)!=len(expected_name)
                or bytes(self.uc.mem_read(string_pointer+8,len(expected_name)+1))!=expected_name+b'\0'):
            raise ValueError('Loaded animation string no longer matches verified table')
        strings_before=bytes(self.uc.mem_read(self.STRINGS,self.next_address-self.STRINGS))
        self.put(self.FPV+0x54,slot);self.uc.mem_write(first_cache,bytes(16))
        seeded=bytes(self.uc.mem_read(self.FPV,len(before)))
        stack=self.STACK+0x8000;frame=stack+0x100
        self.uc.mem_write(stack,bytes(0x200));self.put(frame+8,state)
        for register,value in ((self.reg.UC_X86_REG_ESP,stack),(self.reg.UC_X86_REG_EBP,frame),
                               (self.reg.UC_X86_REG_ESI,self.FPV),(self.reg.UC_X86_REG_EFLAGS,2)):
            self.uc.reg_write(register,value)
        self.request_active=True
        try:
            run_block(self,0x492e21,0x492e69) # Stop before RNG; use an explicit draw.
            self.uc.reg_write(self.reg.UC_X86_REG_EAX,draw)
            run_block(self,0x492e79,0x492eab)
            if self.uc.reg_read(self.reg.UC_X86_REG_EDI)!=cell['channel_ordinal']:
                raise ValueError('Native animation channel differs from independent selection')
            run_block(self,0x492ecd,0x492f15) # Stop BEFORE the four-argument resource loader.
            if (self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-16
                    or tuple(self.get(stack-16+4*n) for n in range(4))!=(string_pointer+8,cache,0,0)
                    or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=0x8aed28
                    or bytes(self.uc.mem_read(self.FPV,len(before)))!=seeded
                    or bytes(self.uc.mem_read(self.STRINGS,len(strings_before)))!=strings_before):
                raise ValueError('Native animation request arguments or immutable memory mismatch')
            return {'slot':slot,'state_index':state,'synthetic_draw':draw,'channel':cell['channel_ordinal'],
                'requested_name':cell['resource']['name'],'cache_member_offset':cache-self.FPV,
                'native_request_arguments_match':True,'loaded_names_and_values_unchanged':True,
                'cache_seeded_empty':True,'random_generator_executed':False,'resource_loader_executed':False,
                'game_started':False,'game_modified':False,'live_animation_qualified':False}
        finally:
            self.request_active=False
            self.uc.mem_write(self.FPV,before)


def inspect_loaded_requests(machine,raw,slot):
    _,projection=validated_fpv(raw);cases=[]
    for state in range(13):
        for draw in (0,50,100):
            expected=request_plan(projection,slot,state,draw);receipt=machine.inspect_request(slot,state,draw)
            if (receipt.get('requested_name')!=expected['resource']['name']
                    or any(type(receipt.get(key)) is not int or receipt[key]!=value for key,value in
                           (('slot',slot),('state_index',state),('synthetic_draw',draw),
                            ('channel',expected['channel_ordinal']),('cache_member_offset',expected['name_member_offset']-16)))
                    or receipt.get('native_request_arguments_match') is not True
                    or receipt.get('loaded_names_and_values_unchanged') is not True
                    or receipt.get('resource_loader_executed') is not False):raise ValueError('Incomplete animation request receipt')
            cases.append(receipt)
    return cases


def audit(tables,hands_machine,fpv_machine):
    from benelli_table_audit import TABLE_PINS
    from build_benelli_descriptor_lab import isolated_fpv_group
    from items_sav import parse as parse_items
    hand_cases={};references={}
    for archive in ('others.DTA','Patch.dta','SabreSquadron.dta','PatchX01.dta'):
        key=(archive,'tables/items.sav')
        if key not in tables or (len(tables[key]),sha(tables[key]))!=TABLE_PINS[key]:
            raise ValueError('Changed or missing reviewed item source')
        refs=[s for s in parse_items(tables[key])['slots'] if s.get('fpv_model','').casefold() in ('fpv_hands','fpv_hands_r')]
        references[archive]=[{'slot':s['slot'],'kind':s['kind'],'source_name':s['fpv_model']} for s in refs]
        for slot in refs:hand_cases[slot['fpv_model']]=None
    synthetic=(None,'','w_default','xw_default.4ds','W_DEFAULT.4ds','fpv_hands.4ds',
               'FPV_hands_r.4ds','a.b.c','.4ds','A'*19,'manche_é.4ds')
    for name in dict.fromkeys([*hand_cases,*synthetic]):
        receipt=hands_machine.inspect_name(name)
        if (receipt.get('requested_name')!=hand_name(name) or receipt.get('native_name_argument_matches') is not True
                or receipt.get('source_read_only_unchanged') is not True or receipt.get('stopped_before_loader') is not True
                or receipt.get('model_loader_executed') is not False):raise ValueError('Incomplete hands request receipt')
        hand_cases[name]=receipt
    sources={}
    for archive in ('others.DTA','SabreSquadron.dta'):
        key=(archive,'tables/fpvanims.sav')
        if key not in tables or (len(tables[key]),sha(tables[key]))!=TABLE_PINS[key]:
            raise ValueError('Changed or missing reviewed FPV source')
        sources[archive]=(tables[key],9)
    source=sources['SabreSquadron.dta'][0];fragment=isolated_fpv_group(source)
    added=struct.pack('<HI',12345,len(source)+len(fragment)-6)+source[6:]+fragment[6:]
    sources.update(isolated_modern_group_459=(fragment,359),disabled_sabre_plus_group_459=(added,359))
    requests={}
    for name,(raw,slot) in sources.items():
        loaded=fpv_machine.inspect_table(raw)
        if (loaded.get('table_sha256')!=sha(raw) or loaded.get('native_nested_traversal_matches') is not True
                or loaded.get('native_strings_and_values_match') is not True):raise ValueError('Incomplete loaded FPV receipt')
        requests[name]={'native_table_load':loaded,'requests':inspect_loaded_requests(fpv_machine,raw,slot)}
    return {'schema_version':1,'scope':'private_native_fpv_resource_arguments',
            'commercial_hand_references':references,'hands_name_cases':list(hand_cases.values()),'animation_cases':requests,
            'inventory_item_selection_qualified':False,'model_or_animation_loading_qualified':False,
            'native_joint_name_binding_qualified':False,'game_started':False,'game_modified':False,
            'playable_weapon':False}


def main(argv=None):
    import argparse,json,sys
    from pathlib import Path
    from benelli_table_audit import read_tables
    from item_native_contract import ROOT,SOURCE_SHA,IMAGE_SHA
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh path')
        if sha((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        tables,excluded=read_tables(args.game,archives_only=args.archives_only);image=args.image.read_bytes()
        report=audit(tables,HandsNameOracle(image),FpvResourceOracle(image))
        report.update(source_executable_sha256=SOURCE_SHA,private_image_sha256=IMAGE_SHA,excluded_loose_overrides=excluded)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({'hands_name_cases':len(report['hands_name_cases']),
            'commercial_hand_references':{k:len(v) for k,v in report['commercial_hand_references'].items()},
            'animation_requests':{k:len(v['requests']) for k,v in report['animation_cases'].items()},
            'game_started':False,'resource_loaders_executed':False},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native FPV resource arguments refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
