"""Invented fixtures only; no commercial table/model/sound bytes committed."""
from contextlib import ExitStack
import copy
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import wave

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_mg34_descriptor_lab as lab
from item_weapon_descriptor import build_weapon
from item_native_layout import decode_record
from test_item_weapon_descriptor import fixture as weapon_spec
from test_items_sav import invented_slot,table as item_table
from test_benelli_descriptor_lab import sound_entry,Machine
from test_sound_definition import chunk,string,bank


def baseline():
    raw=bytearray(build_weapon(weapon_spec()));raw[88:108]=b'MG 42'.ljust(20,b'\0');return bytes(raw)


def sources():
    empty=chunk(1200,string(1210,'')+chunk(1310,b'\0'))
    sounds=chunk(1000,bank('First',b'')+bank('Second',b'')
        +bank('Weapon Shooting',empty*34+sound_entry('G MG34','f_mg34_a.wav'))
        +bank('Weapon Manipulation',empty*38+sound_entry('G MG34 Reload','mg34_r.wav')))
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as wav:
        wav.setnchannels(1);wav.setsampwidth(2);wav.setframerate(22050);wav.writeframes(bytes(20))
    return {'tables/ingamesounds.def':sounds,'maps/wi_ge-mg34.bmp':b'invented icon',
            'sounds/f_mg34_a.wav':buffer.getvalue(),'sounds/mg34_r.wav':buffer.getvalue()}


def tables():
    rows=[None]*500;rows[33]=baseline();rows[32]=invented_slot(name='Existing helmet',kind=2)
    rows[48]=invented_slot(name='Existing tank',kind=1)
    rows[201]=invented_slot(name='AMMO MG 34',kind=0);rows[211]=invented_slot(name='AMMO Tank MG 34',kind=0)
    raw=item_table(rows)
    return {('SabreSquadron.dta','tables/items.sav'):raw,('PatchX01.dta','tables/items.sav'):raw,
            ('others.DTA','tables/item_shoot.tbl'):b'invented shoot table'}


class SoundMachine:
    def selection(self,raw,slot):
        action=decode_record(raw)['actions'][0]['payload_offset']
        return {'slot':slot,'shoot':{'bank':2,'index':struct.unpack_from('<I',raw,action+16)[0]},
            'reload':{'bank':3,'index':struct.unpack_from('<I',raw,action+40)[0]},'native_argument_flow_matches':True,
            'synthetic_test_double':True}


class MG34DescriptorTests(unittest.TestCase):
    def prepare(self,*,source_change=None,table_change=None,inventory=None,sound_machine=None):
        data=sources();pins={n:(lab.SOURCE_PINS[n][0],len(raw),lab.digest(raw)) for n,raw in data.items()}
        items=tables()
        if source_change:source_change(data)
        if table_change:table_change(items)
        fields=weapon_spec()['primary']['editor_fields'];fields[8]='34';fields[10]='38'
        with patch.object(lab,'SOURCE_PINS',pins),patch.object(lab,'BASELINE_SHA',lab.digest(baseline())),\
             patch.object(lab,'require_row',return_value={'fields':fields,'sha256':lab.SHOOT_ROW_SHA}),\
             patch.object(lab,'FPV_PIN',lab.digest(b'invented modern FPV')),\
             patch.object(lab,'world_model',return_value=b'invented modern world'),\
             patch.object(lab,'prepare_resources',return_value=({'PROTOTYPE_MG3_HandFPV.4ds.disabled':b'invented modern FPV',
                 'PROTOTYPE_MG3PH.fpvgroup.disabled':b'invented group'},{'synthetic_test_double':True})) as resource:
            files,report=lab.prepare(items,data,b'invented hand',Path('unused'),{},'H',Machine(),
                                    sound_machine or SoundMachine(),None,None,inventory=inventory)
            self.assertEqual(resource.call_args.args[:2],('MG34','H'))
            return files,report,items

    def inventory(self):
        from build_modern_inventory_text_lab import CATALOGUE
        return {'catalogue':json.loads(CATALOGUE.read_text(encoding='utf-8')),
            'sources':{'Text/french/TEXTY_DD.txt':b'1 "Existing"\n'},
            'occupied_item_text_ids':{1033,1201,1211},'mission_range':(22000,65000)}

    def test_modern_baseline_is_explicit_individual_attributes_with_portable_ammo(self):
        raw=baseline();fields=weapon_spec()['primary']['editor_fields']
        with patch.object(lab,'BASELINE_SHA',lab.digest(raw)):spec=lab.specification(fields,raw)
        self.assertEqual(spec['weapon_members_raw'][0x54],201)
        self.assertEqual(spec['names']['internal'],'MODERN_MG34')
        self.assertEqual(spec['names']['icon'],'wi_ge-mg34')
        self.assertEqual(spec['text_id'],0xffffffff)
        self.assertEqual(spec['base_members_raw'],weapon_spec()['base_members_raw'])
        self.assertTrue(all(len(v)<=19 for v in spec['names'].values()))
        self.assertNotEqual(build_weapon(spec),raw)

    def test_changed_baseline_and_secondary_constants_are_refused(self):
        fields=weapon_spec()['primary']['editor_fields'];raw=baseline()
        with self.assertRaises(ValueError):lab.specification(fields,raw)
        for offset,value in ((88,b'TANK MG34'),(272,struct.pack('<I',1)),(276,struct.pack('<I',5))):
            bad=bytearray(raw);bad[offset:offset+len(value)]=value;bad=bytes(bad)
            with patch.object(lab,'BASELINE_SHA',lab.digest(bad)),self.assertRaises(ValueError):lab.specification(fields,bad)

    def test_complete_disabled_descriptor_preserves_original_tables_and_separates_provenance(self):
        before=tables();files,report,after=self.prepare()
        self.assertEqual(before,after);self.assertTrue(all(n.endswith('.disabled') for n in files))
        self.assertEqual(len(files['PROTOTYPE_MG34.item.disabled']),508)
        self.assertEqual(files['PROTOTYPE_MG3FPV.4ds.disabled'],b'invented modern FPV')
        self.assertNotIn('PROTOTYPE_MG3_HandFPV.4ds.disabled',files)
        self.assertEqual([r['ammo_slot'] for r in report['native_ammunition_checks']],[201,201])
        self.assertEqual(len(report['native_fpv_binding_checks']),13)
        self.assertEqual([r['index'] for r in report['sound_references']],[34,38])
        self.assertEqual(report['audio_metadata']['sounds/mg34_r.wav']['sample_frames'],10)
        self.assertTrue(report['tank_mg34_and_ammo_211_untouched']);self.assertTrue(report['helmet_slot_32_untouched'])
        self.assertFalse(report['modern_design_decisions']['whole_donor_record_copied'])
        for name in ('central_tables_emitted','item_slot_allocated_in_game','game_modified','game_started',
                     'playable_weapon','installation_allowed','audio_or_icon_exported','commercial_hand_model_exported'):
            self.assertFalse(report[name])

    def test_changed_or_missing_resource_is_rejected_before_assembly(self):
        with self.assertRaisesRegex(ValueError,'Changed pinned'):self.prepare(source_change=lambda s:s.update({'sounds/mg34_r.wav':b'changed'}))
        with self.assertRaisesRegex(ValueError,'Incomplete MG34'):self.prepare(source_change=lambda s:s.pop('maps/wi_ge-mg34.bmp'))

    def test_portable_ammo_owner_must_not_be_the_tank_owner(self):
        def change(data):
            key=('PatchX01.dta','tables/items.sav')
            data[key]=data[key].replace(b'AMMO MG 34\0',b'AMMO Wrong\0')
        with self.assertRaises(ValueError):self.prepare(table_change=change)

    def test_inventory_label_changes_only_text_member_of_descriptor(self):
        old,_,_=self.prepare();files,report,_=self.prepare(inventory=self.inventory())
        a=old['PROTOTYPE_MG34.item.disabled'];b=files['PROTOTYPE_MG34.item.disabled']
        self.assertEqual(a[:108]+a[112:],b[:108]+b[112:]);self.assertEqual(struct.unpack_from('<I',b,108)[0],21501)
        self.assertNotIn('inventory_text_allocation',report['pending_requirements'])
        self.assertIn(b'21501\t"MG 34 [MODERNE]"',files['Text/french/TEXTY_DD.txt.disabled'])
        inventory=self.inventory();inventory['occupied_item_text_ids'].add(21501)
        with self.assertRaises(ValueError):self.prepare(inventory=inventory)

    def test_native_sound_flow_must_match_both_historical_references(self):
        fake=SimpleNamespace(selection=lambda *args:{'native_argument_flow_matches':True,
            'shoot':{'bank':2,'index':0},'reload':{'bank':3,'index':38}})
        with self.assertRaisesRegex(ValueError,'native MG34 sound'):self.prepare(sound_machine=fake)

    def test_pinned_modern_world_is_reproducible(self):
        raw=lab.world_model();self.assertEqual((len(raw),lab.digest(raw)),lab.WORLD_PIN)

    def test_reader_detects_shadowing_duplicates_missing_sources_and_loose_overrides(self):
        payloads=sources();pins={n:(lab.SOURCE_PINS[n][0],len(r),lab.digest(r)) for n,r in payloads.items()}
        class Archive:
            def __init__(self,path):
                self.entries=[SimpleNamespace(name=n) for n,p in pins.items() if p[0]==path.name]
                self.path=path
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,entry):return payloads[entry.name]
        with tempfile.TemporaryDirectory() as directory,patch.object(lab,'SOURCE_PINS',pins),patch.object(lab,'DtaArchive',Archive):
            root=Path(directory);actual,excluded=lab.read_sources(root);self.assertEqual(actual,payloads);self.assertEqual(excluded,{})
            loose=root/'sounds/mg34_r.wav';loose.parent.mkdir();loose.write_bytes(b'invented override')
            with self.assertRaisesRegex(ValueError,'Loose'):lab.read_sources(root)
            actual,excluded=lab.read_sources(root,archives_only=True);self.assertEqual(actual,payloads)
            self.assertEqual(excluded['sounds/mg34_r.wav']['sha256'],lab.digest(b'invented override'))
            class Shadow(Archive):
                def __init__(self,path):
                    super().__init__(path)
                    if path.name=='SabreSquadron.dta':self.entries.append(SimpleNamespace(name='sounds/mg34_r.wav'))
            with patch.object(lab,'DtaArchive',Shadow),self.assertRaisesRegex(ValueError,'shadowed'):lab.read_sources(root,archives_only=True)
            class Duplicate(Archive):
                def __init__(self,path):super().__init__(path);self.entries*=2
            with patch.object(lab,'DtaArchive',Duplicate),self.assertRaisesRegex(ValueError,'Ambiguous'):lab.read_sources(root,archives_only=True)
            class Missing(Archive):
                def __init__(self,path):super().__init__(path);self.entries=[]
            with patch.object(lab,'DtaArchive',Missing),self.assertRaisesRegex(ValueError,'Missing'):lab.read_sources(root,archives_only=True)


if __name__=='__main__':unittest.main()
