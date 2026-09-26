"""Bounded, memory-only oracle for native item state and ammo consumers.

All file I/O is replaced with one <=32 KiB bytearray. Object creation,
registration and owner lookup are explicit synthetic doubles; no saved game
or Windows process is opened or written. This is not live-game validation.
"""
from __future__ import annotations
from collections import Counter
import math
import struct

from item_native_contract import Oracle, ROOT, SOURCE_SHA, IMAGE_SHA, sha
from item_native_layout import decode_record
from item_instance_state import (COMMON, COMMON_MEMBERS, COMMON_READER_MEMBERS,
                                 WEAPON_MEMBERS, chunk, scalar_chunk, decode_leaf, encode_leaf)

STATE_RANGES=((0x405820,0x4059e2),(0x415c90,0x415cfa),(0x4476c0,0x447700),
              (0x53b1d0,0x53b2b3),(0x7d3fb0,0x7d44fa),
              (0x7d5950,0x7d5eab),(0x7de840,0x7df18a),(0x7df190,0x7df1ab),
              (0x7e0990,0x7e0994),(0x7d4bee,0x7d4c57),
              (0x7e0970,0x7e0974),(0x7e0870,0x7e0874),(0x7d4ab0,0x7d4ad1))


class StateOracle(Oracle):
    HANDLE=0x1234
    STREAM=Oracle.HEAP+0x6000
    MANAGER=Oracle.HEAP+0x6800
    INSTANCE=Oracle.HEAP+0x8000
    DESCRIPTOR=Oracle.HEAP+0x9000
    OWNER=Oracle.HEAP+0xa000

    def __init__(self,image):
        super().__init__(image)
        self.buffer=bytearray();self.position=0;self.writing=False
        self.io_counts=Counter();self.factories=[];self.registered=[];self.owners={}
        self.registered_slot=None

    def return_call(self,result,argc):
        esp=self.uc.reg_read(self.reg.UC_X86_REG_ESP)
        self.uc.reg_write(self.reg.UC_X86_REG_EAX,result&0xffffffff)
        self.uc.reg_write(self.reg.UC_X86_REG_EIP,self.get(esp))
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,esp+4+argc*4)

    def on_code(self,uc,address,size,context):
        if address in (0x7e5392,0x7e5398,0x7e539e):
            esp=self.uc.reg_read(self.reg.UC_X86_REG_ESP)
            handle,arg2,arg3=(self.get(esp+4*n) for n in (1,2,3))
            if handle!=self.HANDLE:raise ValueError('Unexpected emulated file handle')
            if address==0x7e5398:
                self.io_counts['seek']+=1
                displacement=arg2 if arg2<2**31 else arg2-2**32
                if arg3 not in (0,1,2):raise ValueError('Invalid emulated seek origin')
                position=(0,self.position,len(self.buffer))[arg3]+displacement
                if not 0<=position<=len(self.buffer):raise ValueError('Emulated seek outside owned buffer')
                self.position=position;result=position
            else:
                if arg3>32768 or not any(base<=arg2 and arg2+arg3<=base+65536 for base in (self.STACK,self.HEAP)):
                    raise ValueError('Emulated I/O pointer outside synthetic data arenas')
                end=self.position+arg3
                if address==0x7e5392:
                    if not self.writing or end>32768:raise ValueError('Emulated write forbidden or too large')
                    self.io_counts['write']+=1
                    if end>len(self.buffer):self.buffer.extend(bytes(end-len(self.buffer)))
                    self.buffer[self.position:end]=self.uc.mem_read(arg2,arg3)
                    result=arg3
                else:
                    if self.writing:raise ValueError('Emulated read in write-only stream')
                    self.io_counts['read']+=1
                    result=min(arg3,len(self.buffer)-self.position)
                    if result:self.uc.mem_write(arg2,bytes(self.buffer[self.position:self.position+result]))
                self.position+=result
            self.return_call(result,3);return
        if address in (0x7dd9c0,0x7dd950):
            esp=self.uc.reg_read(self.reg.UC_X86_REG_ESP);slot=self.get(esp+4)
            if slot!=self.registered_slot:raise ValueError('Unexpected emulated instance factory slot')
            self.factories.append({'slot':slot,'kind':'weapon' if address==0x7dd9c0 else 'generic'})
            self.put(self.INSTANCE+4,self.DESCRIPTOR);self.put(self.INSTANCE+0xc,slot)
            self.put(self.INSTANCE,0x817018 if address==0x7dd9c0 else 0x816f78)
            self.return_call(self.INSTANCE,1);return
        if address==0x7dcb40:
            esp=self.uc.reg_read(self.reg.UC_X86_REG_ESP);obj=self.get(esp+4)
            if obj!=self.INSTANCE:raise ValueError('Unexpected emulated registration target')
            self.registered.append(obj);self.return_call(0,1);return
        if address==0x475dd0:
            esp=self.uc.reg_read(self.reg.UC_X86_REG_ESP);owner=self.get(esp+4)
            if owner not in self.owners:raise ValueError('Unknown owner in synthetic lookup')
            self.return_call(self.owners[owner],1);return
        if any(start<=address and address+size<=end for start,end in STATE_RANGES):return
        super().on_code(uc,address,size,context)

    def stream(self,raw=None):
        self.uc.mem_write(self.STREAM,bytes(0x414))
        self.put(self.STREAM,1);self.put(self.STREAM+4,self.HANDLE)
        self.writing=raw is None
        self.put(self.STREAM+8,int(self.writing))
        self.buffer=bytearray(raw or b'');self.position=0
        self.io_counts=Counter()

    def seed_instance(self,slot,common,weapon):
        self.uc.mem_write(self.INSTANCE,bytes(0xb0))
        self.uc.mem_write(self.DESCRIPTOR,bytes(0x68))
        self.put(self.INSTANCE,0x817018 if weapon is not None else 0x816f78)
        self.put(self.INSTANCE+4,self.DESCRIPTOR);self.put(self.INSTANCE+0xc,slot)
        self.put(self.DESCRIPTOR,0x817408 if weapon is not None else 0x81742c)
        self.put(self.DESCRIPTOR+4,1 if weapon is not None else 2)
        # A firearm descriptor, not the special type-6 grenade post-load path.
        self.put(self.DESCRIPTOR+0x5c,4)
        self.owners={}
        for tag,member in COMMON_MEMBERS.items():
            value=common[tag]
            if tag==103:
                if value!=0xffffffff:
                    self.put(self.OWNER+0x10,value);self.owners[value]=self.OWNER
                value=0 if value==0xffffffff else self.OWNER
            if tag==104:self.uc.mem_write(self.INSTANCE+member,bytes([value]))
            else:self.put(self.INSTANCE+member,value)
        if weapon is not None:
            for tag,member in WEAPON_MEMBERS.items():
                if tag==209:self.uc.mem_write(self.INSTANCE+member,bytes([weapon[tag]]))
                else:self.put(self.INSTANCE+member,weapon[tag])

    def roundtrip_leaf(self,slot,placement,common,weapon=None,*,definition_present=True):
        expected=encode_leaf(slot,placement,common,weapon)
        self.seed_instance(slot,common,weapon)
        self.stream()
        self.call(0x7de840,self.MANAGER,self.INSTANCE,placement[1],placement[2],placement[3],self.STREAM)
        written=bytes(self.buffer)
        if written!=expected or self.get(self.STREAM+0x410)!=0:
            raise ValueError('Native item-instance serialization differs from original codec')
        write_counts=dict(self.io_counts)
        # Retain only fake descriptor and owner lookup; clear mutable state.
        self.uc.mem_write(self.INSTANCE,bytes(0xb0))
        self.uc.mem_write(self.MANAGER,bytes(0x800))
        self.registered_slot=slot;self.factories=[];self.registered=[]
        if definition_present:self.put(self.MANAGER+0x10+slot*4,self.DESCRIPTOR)
        self.stream(written)
        destinations=[self.HEAP+0xb000+4*n for n in range(3)]
        self.call(0x7deb60,self.MANAGER,*destinations,self.STREAM,0)
        loaded=self.uc.reg_read(self.reg.UC_X86_REG_EAX)
        if not definition_present:
            if loaded!=0 or self.factories or self.registered:
                raise ValueError('Missing descriptor unexpectedly recreated an item')
            return {'slot':slot,'bytes':len(written),'native_roundtrip':False,
                    'missing_definition_rejected':True,'whole_saved_game_qualified':False}
        if loaded!=self.INSTANCE or len(self.factories)!=1 or self.registered!=[self.INSTANCE]:
            raise ValueError('Native item-instance reconstruction did not reach the expected object')
        if self.get(self.INSTANCE+0xc)!=slot:
            raise ValueError('Native item slot truncated during restoration')
        if tuple(self.get(p) for p in destinations)!=tuple(placement[k] for k in (1,2,3)):
            raise ValueError('Native item placement fields differ')
        for mapping,values in ((COMMON_MEMBERS,common),(WEAPON_MEMBERS,weapon)):
            if values is None:continue
            for tag,member in mapping.items():
                actual=self.uc.mem_read(self.INSTANCE+member,1)[0] if tag in (104,209) else self.get(self.INSTANCE+member)
                wanted=values[tag]
                # Writer tags 102/103 are ignored by this native reader.
                # The factory double initializes both corresponding fields to 0.
                if tag in (102,103):wanted=0
                if actual!=wanted:raise ValueError(f'Native restored instance field differs: {tag}')
        if self.position!=len(written) or self.get(self.STREAM+0x410)!=0:
            raise ValueError('Native item reader did not consume/close the exact envelope')
        decode_leaf(written,weapon=weapon is not None)
        lossless=common[102]==0 and common[103]==0xffffffff
        return {'slot':slot,'bytes':len(written),'native_roundtrip':lossless,
                'native_writer_matches':True,'native_reader_matches':True,
                'item_slot_restored':True,'weapon_state_restored':weapon is not None,
                'common_writer_tags_ignored_by_reader':[102,103],
                'complete_common_state_restored':lossless,
                'writer_io':write_counts,'reader_io':dict(self.io_counts),
                'factory_and_owner_lookup':'synthetic_doubles',
                'whole_saved_game_qualified':False,'game_started':False}

    def common_reader_probe(self,fields):
        """Exercise reviewed common tags, including writer/reader asymmetry.

        This builds a synthetic common chunk, not a patched player save.
        Missing members retain explicit zero-initialized test-double defaults.
        """
        if (not set(fields)<=set(COMMON_MEMBERS)|set(COMMON_READER_MEMBERS)
                or any(type(v) is not int or not 0<=v<=0xffffffff for v in fields.values())):
            raise ValueError('Unreviewed common-reader probe field')
        raw=chunk(COMMON,b''.join(scalar_chunk(k,v) for k,v in fields.items()))
        self.uc.mem_write(self.INSTANCE,bytes(0xb0));self.owners={}
        owner=fields.get(203,0xffffffff)
        if owner!=0xffffffff:
            self.owners[owner]=self.OWNER;self.put(self.OWNER+0x10,owner)
        self.stream(raw)
        self.call(0x7d41f0,self.INSTANCE,self.STREAM)
        expected={member:0 for member in COMMON_READER_MEMBERS.values()}
        for tag,member in COMMON_READER_MEMBERS.items():
            if tag not in fields:continue
            value=fields[tag]
            if tag==104:value=int(value!=0)
            if tag==203:value=0 if value==0xffffffff else self.OWNER
            expected[member]=value
        for member,value in expected.items():
            actual=self.uc.mem_read(self.INSTANCE+member,1)[0] if member==0x1c else self.get(self.INSTANCE+member)
            if actual!=value:raise ValueError('Native common-reader dispatch mismatch')
        if self.position!=len(raw) or self.get(self.STREAM+0x410)!=0:
            raise ValueError('Native common reader left its synthetic chunk open')
        return {'reader_tags':list(COMMON_READER_MEMBERS),'writer_only_tags_ignored':[102,103],
                'native_reader_dispatch_matches':True,'save_migration_performed':False}

    def consume_quantity(self,current,amount):
        if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1e6 for v in (current,amount)):
            raise ValueError('Synthetic ammunition quantity outside reviewed finite domain')
        self.uc.mem_write(self.INSTANCE+0x50,struct.pack('<f',current))
        argument=struct.unpack('<I',struct.pack('<f',amount))[0]
        self.call(0x7d4ab0,self.INSTANCE,argument)
        observed=struct.unpack('<f',self.uc.mem_read(self.INSTANCE+0x50,4))[0]
        f32=lambda n:struct.unpack('<f',struct.pack('<f',n))[0]
        expected=max(0.0,f32(f32(current)-f32(amount)))
        if observed!=expected:raise ValueError('Native ammunition decrement differs')
        return observed

    def ammo_binding(self,weapon_raw,ammo_raw,*,weapon_slot,ammo_slot):
        weapon=decode_record(weapon_raw);ammo=decode_record(ammo_raw)
        if (weapon['kind']!=1 or ammo['kind']!=0 or type(ammo_slot) is not int or not 0<=ammo_slot<500
                or weapon['members']['0x54']['value_raw']!=ammo_slot):
            raise ValueError('Weapon and ammo descriptors do not form the requested typed association')
        quantity=struct.unpack('<f',struct.pack('<I',ammo['members']['0x54']['value_raw']))[0]
        if not math.isfinite(quantity) or quantity<0:raise ValueError('Invalid initial ammo quantity')
        self.inspect_record(weapon_raw,weapon_slot)
        gun_bytes=bytes(self.uc.mem_read(self.HEAP,0x68))
        self.inspect_record(ammo_raw,ammo_slot)
        ammo_bytes=bytes(self.uc.mem_read(self.HEAP,0x68))
        self.uc.mem_write(self.DESCRIPTOR,gun_bytes)
        self.uc.mem_write(self.OWNER,ammo_bytes)
        self.uc.mem_write(self.INSTANCE,bytes(0xb0))
        self.put(self.INSTANCE+4,self.DESCRIPTOR)
        global_slot=0x98b030+4*ammo_slot
        previous=self.get(global_slot)
        try:
            # Synthetic table pointer in EMULATED global DATA only. No code,
            # source file or actual running process is patched.
            self.put(global_slot,self.OWNER)
            self.uc.reg_write(self.reg.UC_X86_REG_ESI,self.INSTANCE)
            self.uc.reg_write(self.reg.UC_X86_REG_ESP,self.STACK+0x8000)
            self.uc.emu_start(0x7d4bee,0x7d4c57,count=200,timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=0x7d4c57:
                raise ValueError('Native ammo binding did not reach quantity initialization')
            expected=ammo['members']['0x54']['value_raw']
            if any(self.get(self.INSTANCE+m)!=expected for m in (0x50,0x54)):
                raise ValueError('Native loaded/max quantity differs from referenced ammo descriptor')
        finally:self.put(global_slot,previous)
        return {'weapon_slot':weapon_slot,'ammo_slot':ammo_slot,'initial_quantity':quantity,
                'native_ammo_binding_matches':True,'live_reload_qualified':False}


def inspect_tables(machine,tables):
    """Cross-check every typed commercial weapon/ammo pair, never alter tables."""
    from items_sav import parse
    layers={}
    for (archive,name),raw in tables.items():
        if name!='tables/items.sav':continue
        parsed=parse(raw)
        records={s['slot']:raw[s['offset']:s['offset']+s['size']] for s in parsed['slots'] if s['present']}
        layouts={slot:decode_record(record) for slot,record in records.items()}
        checked=[];without_ammo=[];untyped=[]
        for slot,layout in layouts.items():
            if layout['kind']!=1:continue
            reference=layout['members']['0x54']['value_raw']
            if reference==0xffffffff:
                without_ammo.append(slot);continue
            if reference not in layouts or layouts[reference]['kind']!=0:
                untyped.append({'weapon_slot':slot,'referenced_slot':reference,
                                'referenced_kind':layouts.get(reference,{}).get('kind')})
                continue
            checked.append(machine.ammo_binding(records[slot],records[reference],
                                                 weapon_slot=slot,ammo_slot=reference))
        # A one-field synthetic association, NOT a restored commercial Benelli
        # entry or an allocation. The donor's mechanics remain unqualified.
        donor=bytearray(records[23])
        member=layouts[23]['members']['0x54']['record_offset']
        struct.pack_into('<I',donor,member,179)
        candidate=machine.ammo_binding(bytes(donor),records[179],weapon_slot=359,ammo_slot=179)
        layers[archive]={'table_sha256':sha(raw),'typed_associations_checked':checked,
                         'no_ammo_reference_slots':without_ammo,'unqualified_reference_slots':untyped,
                         'synthetic_benelli_ammo_probe':{**candidate,'donor_slot':23,
                             'donor_sha256':sha(records[23]),'only_changed_record_member':member,
                             'commercial_benelli_weapon_record':False,'item_slot_allocated':False}}
    return layers


def main(argv=None):
    import argparse
    import json
    from pathlib import Path
    import sys
    from benelli_table_audit import read_tables
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',required=True,type=Path)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin')
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh path')
        if sha((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed packed client')
        machine=StateOracle(args.image.read_bytes())
        tables,excluded=read_tables(args.game,archives_only=args.archives_only)
        layers=inspect_tables(machine,tables)
        common={100:17,101:18,102:0,103:0xffffffff,104:1}
        placement={1:1,2:0x3f800000,3:0xbf800000}
        gun={k:0 for k in WEAPON_MEMBERS}
        gun.update({200:0x40c00000,201:0x40e00000,209:1})  # 6 of 7, synthetic.
        leaves=[machine.roundtrip_leaf(slot,placement,common,weapon)
                for slot in (9,255,256,359,499) for weapon in (None,gun)]
        asymmetry=machine.roundtrip_leaf(359,placement,{**common,102:42,103:77},gun)
        tags=machine.common_reader_probe({100:17,101:18,102:42,103:77,104:1,202:99,203:88})
        missing=machine.roundtrip_leaf(359,placement,common,gun,definition_present=False)
        report={'schema_version':1,'scope':'memory_only_item_leaf_state_and_ammo',
                'source_sha256':SOURCE_SHA,'private_image_sha256':IMAGE_SHA,
                'layers':layers,'excluded_loose_overrides':excluded,'leaf_envelopes':leaves,
                'common_writer_reader_asymmetry':asymmetry,'common_reader_tag_probe':tags,
                'missing_definition_probe':missing,
                'quantity_decrement':[{'current':n,'amount':1,'remaining':machine.consume_quantity(n,1)}
                                      for n in (7,2,1,0)],
                'whole_saved_game_qualified':False,'player_saves_opened':False,
                'native_factories_executed':False,'live_reload_qualified':False,
                'game_started':False,'game_files_modified':False,'item_slot_allocated':False}
        rendered=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:stream.write(rendered)
        print(json.dumps({'layers':{name:{'checked':len(layer['typed_associations_checked']),
                    'without_ammo':len(layer['no_ammo_reference_slots']),
                    'unqualified':layer['unqualified_reference_slots'],
                    'synthetic_benelli_quantity':layer['synthetic_benelli_ammo_probe']['initial_quantity']}
                    for name,layer in layers.items()},'native_leaf_envelopes_checked':len(leaves),
                    'common_writer_only_tags_ignored':[102,103],'whole_saved_game_qualified':False},indent=2))
        return 0
    except (OSError,ValueError,ImportError) as error:
        print('Item state oracle refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
