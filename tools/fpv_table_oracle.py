"""Native FPV group/state/channel traversal with memory-only file doubles.

The root is independently validated and seeded as an already opened scope.
Native nested-header readers, scope closure, strings and cell writes execute.
No scene, model, animation, file-opening, Windows API or live game executes.
"""
from __future__ import annotations
from collections import Counter
import struct

from fpv_table import parse
from item_native_contract import Oracle,sha
from item_native_layout import fpv_native_projection,fpv_loaded_cell

FPV_RANGES=((0x490e00,0x4910ef),(0x415c90,0x415cfa),(0x415d00,0x415db6),
            (0x415dfb,0x415e2a),(0x4476c0,0x447700),(0x405180,0x4051f6),
            (0x405890,0x4058a4),(0x405902,0x405937),(0x405940,0x4059b0))
MAX_SOURCE=1048576
EMPTY_VALUE=0x5a5a5a5a # Deliberate oracle sentinel, NOT a native default.


def validated_fpv(raw):
    if len(raw)>MAX_SOURCE:raise ValueError('FPV source exceeds bounded oracle buffer')
    parsed=parse(raw);projection=fpv_native_projection(parsed)
    for cell in projection['cells']:
        resource=cell['resource']
        # The native string reader copies at most 999 bytes including NUL.
        if resource and len(resource['name'].encode('cp1252'))>998:
            raise ValueError('FPV name would be truncated by the native string reader')
    return parsed,projection


class FpvTableOracle(Oracle):
    HANDLE=0x3456
    STRINGS=0x3800000
    STRINGS_SIZE=0x100000

    def __init__(self,image):
        super().__init__(image)
        self.fpv_active=False;self.buffer=b'';self.position=0
        self.io_counts=Counter();self.group_ids=[]
        self.uc.mem_map(self.STRINGS,self.STRINGS_SIZE,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)

    def allocate(self,size):
        if not self.fpv_active:return super().allocate(size)
        if (type(size) is not int or not 0<size<=4096 or self.next_address<self.STRINGS
                or self.next_address+((size+15)&~15)>self.STRINGS+self.STRINGS_SIZE):
            raise ValueError('FPV string allocation outside bounded private arena')
        pointer=self.next_address;self.next_address+=(size+15)&~15
        self.allocations[pointer]=size;self.uc.mem_write(pointer,b'\xcd'*size)
        return pointer

    def return_io(self,result):
        stack=self.uc.reg_read(self.reg.UC_X86_REG_ESP)
        self.uc.reg_write(self.reg.UC_X86_REG_EAX,result&0xffffffff)
        self.uc.reg_write(self.reg.UC_X86_REG_EIP,self.get(stack))
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,stack+16)

    def on_code(self,uc,address,size,context):
        if self.fpv_active:
            if address in (0x7e5392,0x7e5398,0x7e539e):
                if address==0x7e5392:raise ValueError('Writes forbidden in FPV input oracle')
                stack=self.uc.reg_read(self.reg.UC_X86_REG_ESP)
                handle,arg2,arg3=(self.get(stack+4*n) for n in (1,2,3))
                if handle!=self.HANDLE:raise ValueError('Unexpected FPV memory handle')
                if address==0x7e5398:
                    if arg3 not in (0,1,2):raise ValueError('Invalid FPV seek origin')
                    displacement=arg2 if arg2<2**31 else arg2-2**32
                    target=(0,self.position,len(self.buffer))[arg3]+displacement
                    if not 0<=target<=len(self.buffer):raise ValueError('FPV seek outside owned input')
                    self.position=target;self.io_counts['seek']+=1;self.return_io(target)
                else:
                    if (arg3>1024 or self.position+arg3>len(self.buffer)
                            or not any(base<=arg2 and arg2+arg3<=base+extent
                                       for base,extent in ((self.STACK,65536),(self.FPV,0x4d000)))):
                        raise ValueError('FPV read outside input or allowed output arenas')
                    self.uc.mem_write(arg2,self.buffer[self.position:self.position+arg3])
                    self.position+=arg3;self.io_counts['read']+=1;self.io_counts['read_bytes']+=arg3
                    self.return_io(arg3)
                return
            if any(start<=address and address+size<=end for start,end in FPV_RANGES):
                if address==0x490ea3:
                    owner=self.uc.reg_read(self.reg.UC_X86_REG_EAX)&0xffff
                    index=len(self.group_ids)
                    if index>=len(self.expected_groups) or owner!=self.expected_groups[index]:
                        raise ValueError('Native FPV group iteration differs from independent parser')
                    self.group_ids.append(owner)
                return
        super().on_code(uc,address,size,context)

    def inspect_table(self,raw):
        parsed,projection=validated_fpv(raw)
        self.buffer=bytes(raw);self.position=6;self.io_counts=Counter();self.group_ids=[]
        self.expected_groups=[g['id'] for g in parsed['groups']]
        self.allocations.clear();self.next_address=self.STRINGS
        initial=bytearray(b'\xcd'*0x4d000)
        for slot in range(500):
            for state in range(13):
                for channel in range(4):
                    cell=fpv_loaded_cell(slot+100,state+2000,channel)
                    struct.pack_into('<I',initial,cell['name_member_offset'],0)
                    struct.pack_into('<I',initial,cell['value_member_offset'],EMPTY_VALUE)
        self.uc.mem_write(self.FPV,bytes(initial))
        stack=self.STACK+0x8000;stream=stack+0x3c
        self.uc.mem_write(stack,bytes(0x600))
        self.put(stack+0x1c,self.FPV)
        self.uc.mem_write(stream,b'\1');self.put(stream+4,self.HANDLE)
        self.put(stream+0x410,1);self.put(stream+0x10,len(raw))
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,stack)
        self.fpv_active=True
        try:
            self.uc.emu_start(0x490e00,0x4910ef,count=5_000_000,timeout=30_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=0x4910ef:
                raise ValueError('Native FPV traversal exceeded instruction/time budget')
            if (self.position!=len(raw) or self.get(stream+0x410)!=1
                    or self.group_ids!=self.expected_groups
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack):
                raise ValueError('Native FPV cursor, scope depth, groups or stack mismatch')
            populated=0;pointers=set()
            for cell in projection['cells']:
                resource=cell['resource']
                if resource is None:continue
                offset=cell['name_member_offset'];pointer=self.get(self.FPV+offset)
                name=resource['name'].encode('cp1252')
                if (pointer not in self.allocations or pointer in pointers
                        or self.allocations[pointer]!=len(name)+9
                        or self.get(pointer)!=1 or self.get(pointer+4)!=len(name)
                        or bytes(self.uc.mem_read(pointer+8,len(name)+1))!=name+b'\0'):
                    raise ValueError('Native FPV reference-counted name differs from source')
                if self.get(self.FPV+cell['value_member_offset'])!=resource['value_raw']:
                    raise ValueError('Native FPV raw channel value differs from source')
                pointers.add(pointer);populated+=1
                struct.pack_into('<I',initial,offset,pointer)
                struct.pack_into('<I',initial,cell['value_member_offset'],resource['value_raw'])
            if bytes(self.uc.mem_read(self.FPV,len(initial)))!=bytes(initial):
                raise ValueError('Native FPV traversal changed an unexpected or empty cell')
            if self.buffer!=raw:raise ValueError('FPV input changed')
            return {'schema_version':1,'scope':'offline_native_fpv_nested_traversal',
                'table_size':len(raw),'table_sha256':sha(raw),'groups_visited':len(self.group_ids),
                'state_containers':len(self.group_ids)*13,'channel_containers':len(projection['cells']),
                'populated_channels_checked':populated,'entire_array_cells_checked':26000,
                'untouched_cells_checked':26000-populated,'final_cursor':self.position,
                'final_scope_depth':self.get(stream+0x410),'io_doubles':dict(self.io_counts),
                'string_allocations':len(self.allocations),'private_string_bytes':self.next_address-self.STRINGS,
                'empty_value_sentinel':EMPTY_VALUE,'sentinel_is_native_default':False,
                'native_nested_traversal_matches':True,'native_strings_and_values_match':True,
                'unpopulated_cells_unchanged':True,'source_read_only_unchanged':True,
                'root_scope_seeded_after_independent_validation':True,
                'native_root_opening_or_file_io_executed':False,'scene_or_animation_calls_executed':False,
                'game_started':False,'game_modified':False,'live_animation_qualified':False}
        finally:self.fpv_active=False


def audit(tables,machine):
    from benelli_table_audit import TABLE_PINS
    from build_benelli_descriptor_lab import isolated_fpv_group
    sources={}
    for archive in ('others.DTA','SabreSquadron.dta'):
        key=(archive,'tables/fpvanims.sav')
        if key not in tables or (len(tables[key]),sha(tables[key]))!=TABLE_PINS[key]:
            raise ValueError('Changed or missing reviewed FPV source')
        sources[archive]=tables[key]
    fragment=isolated_fpv_group(sources['SabreSquadron.dta'])
    source=sources['SabreSquadron.dta']
    added=struct.pack('<HI',12345,len(source)+len(fragment)-6)+source[6:]+fragment[6:]
    sources.update(isolated_modern_group_459=fragment,disabled_sabre_plus_group_459=added)
    cases={}
    for name,raw in sources.items():
        parsed,projection=validated_fpv(raw);result=machine.inspect_table(raw)
        if (result.get('table_sha256')!=sha(raw) or result.get('native_nested_traversal_matches') is not True
                or result.get('native_strings_and_values_match') is not True
                or result.get('unpopulated_cells_unchanged') is not True
                or result.get('source_read_only_unchanged') is not True
                or type(result.get('groups_visited')) is not int or result['groups_visited']!=len(parsed['groups'])
                or type(result.get('populated_channels_checked')) is not int
                or result['populated_channels_checked']!=sum(c['resource'] is not None for c in projection['cells'])):
            raise ValueError('Incomplete native FPV traversal receipt')
        cases[name]=result
    return {'schema_version':1,'scope':'private_native_fpv_table_traversal_audit','cases':cases,
            'commercial_tables_modified':False,'game_started':False,'game_modified':False,
            'native_root_opening_or_file_io_executed':False,'live_animation_qualified':False}


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
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        report=audit(tables,FpvTableOracle(args.image.read_bytes()))
        report.update(source_executable_sha256=SOURCE_SHA,private_image_sha256=IMAGE_SHA,excluded_loose_overrides=excluded)
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps(report,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native FPV table traversal refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
