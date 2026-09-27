"""Invented tables/audio definitions and mock native receipts only."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_fg42_descriptor_lab as lab
import build_modern_audio_lab as audio
from build_modern_inventory_text_lab import CATALOGUE
from item_weapon_descriptor import build_weapon
from item_native_layout import decode_record
from test_item_weapon_descriptor import fixture as weapon_spec
from test_items_sav import invented_slot,table as item_table
from test_modern_audio_lab import definition,Machine as AudioMachine
from test_mg34_descriptor_lab import SoundMachine
from test_benelli_table_lab import Machine as StateMachine


def baseline():
    raw=bytearray(build_weapon(weapon_spec()));raw[88:108]=b'MP 44'.ljust(20,b'\0');return bytes(raw)


def ammunition():
    raw=bytearray(invented_slot(name='AMMO FG 42',kind=0))
    struct.pack_into('<II',raw,136,0,0)
    struct.pack_into('<f',raw,decode_record(raw)['members']['0x54']['record_offset'],20.0);return bytes(raw)


def tables():
    helmet=bytearray(invented_slot(name='Existing helmet',kind=2));struct.pack_into('<II',helmet,136,0,0)
    slots=[None]*500;slots[26]=baseline();slots[27]=bytes(helmet);slots[196]=ammunition()
    raw=item_table(slots)
    return {('SabreSquadron.dta','tables/items.sav'):raw,('PatchX01.dta','tables/items.sav'):raw,
            ('others.DTA','tables/item_shoot.tbl'):b'invented shoot table'}


class Machine(StateMachine):
    def ammo_binding(self,raw,ammo,**kwargs):
        return {'synthetic_test_double':True,'native_ammo_binding_matches':True,'initial_quantity':20.0,**kwargs}
    def fpv_binding(self,slot,state):return {'slot':slot,'state':state,'synthetic_test_double':True}


def inventory():
    return {'catalogue':json.loads(CATALOGUE.read_text(encoding='utf-8')),
        'sources':{'Text/french/TEXTY_DD.txt':b'1 "Existing"\n'},
        'occupied_item_text_ids':{1026,1196},'mission_range':(22000,65000)}


def audio_bundle():
    raw=definition();recipes={case:json.loads(path.read_text(encoding='utf-8')) for case,path in audio.RECIPES.items()}
    with patch.object(audio,'PIN',('Patch.dta',len(raw),lab.digest(raw))):return audio.prepare(raw,recipes,AudioMachine())


class FG42DescriptorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.audio=audio_bundle()

    def prepare(self,*,mutate_tables=None,mutate_audio=None,inv=None,state=None,sound=None):
        data=tables();bundle=deepcopy(self.audio)
        if mutate_tables:mutate_tables(data)
        if mutate_audio:mutate_audio(*bundle)
        fields=weapon_spec()['primary']['editor_fields'];fields[8]='FG42_F';fields[10]='FG42_R'
        before=deepcopy(fields)
        with patch.object(lab,'BASELINE_SHA',lab.digest(baseline())),patch.object(lab,'AMMO_SHA',lab.digest(ammunition())),\
             patch.object(lab,'require_row',return_value={'fields':fields,'sha256':lab.SHOOT_ROW_SHA}),\
             patch.object(lab,'prepare_audio',return_value=bundle),\
             patch.object(lab,'FPV_PIN',lab.digest(b'invented modern FPV')),\
             patch.object(lab,'world_assets',return_value=(b'invented world',b'invented icon',{'synthetic_test_double':True})),\
             patch.object(lab,'prepare_resources',return_value=({'PROTOTYPE_FG4_HandFPV.4ds.disabled':b'invented modern FPV',
                'PROTOTYPE_FG4PH.fpvgroup.disabled':b'invented group'},{'synthetic_test_double':True})) as resource:
            result=lab.prepare(data,b'invented',{},b'invented hand',Path('unused'),{},'H',state or Machine(),
                sound or SoundMachine(),None,None,inventory=inventory() if inv is None else inv)
        self.assertEqual(fields,before);self.assertEqual(resource.call_args.args[:2],('FG42','H'));return result

    def test_modern_category_does_not_copy_weapon_identity_or_ammo(self):
        raw=baseline()
        with patch.object(lab,'BASELINE_SHA',lab.digest(raw)):spec=lab.specification(weapon_spec()['primary']['editor_fields'],raw)
        self.assertEqual(spec['weapon_members_raw'][0x54],196)
        self.assertEqual(spec['base_members_raw'],weapon_spec()['base_members_raw'])
        self.assertEqual(spec['names']['internal'],'MODERN_FG42');self.assertEqual(spec['names']['icon'],'MOD_FG42_ICON')
        self.assertTrue(all(len(s)<=19 for s in spec['names'].values()));self.assertNotEqual(build_weapon(spec),raw)
        with self.assertRaisesRegex(ValueError,'baseline'):lab.specification(weapon_spec()['primary']['editor_fields'],raw)

    def test_complete_bundle_identifies_modern_sound_substitution_without_resolving_symbols(self):
        files,report=self.prepare();self.assertTrue(all(n.endswith('.disabled') for n in files))
        raw=files['PROTOTYPE_FG42.item.disabled'];self.assertEqual(len(raw),508)
        self.assertEqual(struct.unpack_from('<I',raw,108)[0],21502)
        self.assertEqual(decode_record(raw)['members']['0x54']['value_raw'],196)
        self.assertEqual(files['PROTOTYPE_FG4FPV.4ds.disabled'],b'invented modern FPV')
        self.assertNotIn('PROTOTYPE_FG4_HandFPV.4ds.disabled',files)
        self.assertEqual([r['modern_index'] for r in report['modern_sound_choices']],[1,3])
        self.assertEqual([r['historical_symbol'] for r in report['modern_sound_choices']],['FG42_F','FG42_R'])
        self.assertTrue(report['helmet_slot_27_untouched']);self.assertEqual(len(report['native_fpv_binding_checks']),13)
        self.assertEqual([r['initial_quantity'] for r in report['native_ammunition_checks']],[20,20])
        for flag in ('historical_shoot_sound_symbols_resolved','historical_shoot_table_changed','commercial_audio_exported',
                     'commercial_hand_model_exported','installation_allowed','game_modified','game_started','playable_weapon'):
            self.assertFalse(report[flag])

    def test_only_the_two_explicit_sound_fields_change(self):
        fields=weapon_spec()['primary']['editor_fields'];fields.update({8:'FG42_F',10:'FG42_R'});before=deepcopy(fields)
        result,choices,refs=lab.modern_sound_fields(fields,*deepcopy(self.audio))
        self.assertEqual(fields,before);self.assertEqual({k for k in fields if result[k]!=fields[k]},{8,10})
        self.assertTrue(all(r['resolved'] for r in refs));self.assertTrue(all(not c['historical_symbol_resolved'] for c in choices))
        fields[8]='OTHER'
        with self.assertRaises(ValueError):lab.modern_sound_fields(fields,*self.audio)

    def test_changed_audio_or_receipt_cannot_be_bound(self):
        for mutate in (lambda f,r:f.update({'Sounds/MOD_FG42_F.wav.disabled':b'changed'}),
                       lambda f,r:r['transaction']['additions'][0].update(index=100),
                       lambda f,r:r.update(scope='unreviewed')):
            with self.assertRaises(ValueError):self.prepare(mutate_audio=mutate)

    def test_ammo_owner_or_source_change_in_either_layer_refused(self):
        for layer in ('SabreSquadron.dta','PatchX01.dta'):
            def mutate(data):
                key=(layer,'tables/items.sav');data[key]=data[key].replace(b'AMMO FG 42\0',b'AMMO Wrong\0')
            with self.assertRaisesRegex(ValueError,'ammunition'):self.prepare(mutate_tables=mutate)

    def test_incomplete_native_descriptor_ammo_and_sound_receipts_refused(self):
        with self.assertRaisesRegex(ValueError,'descriptor receipt'):self.prepare(state=Machine(False))
        machine=Machine()
        with patch.object(machine,'ammo_binding',return_value={'initial_quantity':20.0}):
            with self.assertRaisesRegex(ValueError,'ammunition receipt'):self.prepare(state=machine)
        fake=SimpleNamespace(selection=lambda *args:{'native_argument_flow_matches':True,
            'shoot':{'bank':2,'index':0},'reload':{'bank':3,'index':3}})
        with self.assertRaisesRegex(ValueError,'sound flow'):self.prepare(sound=fake)

    def test_inventory_is_required_and_collisions_are_refused(self):
        with self.assertRaisesRegex(ValueError,'inventory snapshot'):self.prepare(inv={})
        inv=inventory();inv['occupied_item_text_ids'].add(21502)
        with self.assertRaisesRegex(ValueError,'referenced'):self.prepare(inv=inv)
        inv=inventory();inv['catalogue']['labels']=[r for r in inv['catalogue']['labels'] if r['key']!='fg42']
        with self.assertRaisesRegex(ValueError,'modern FG42 label'):self.prepare(inv=inv)

    def test_modern_world_and_icon_are_rebuilt_without_game_files(self):
        raw,icon,report=lab.world_assets();self.assertEqual((len(raw),lab.digest(raw)),lab.WORLD_PIN)
        self.assertEqual(icon[:2],b'BM');self.assertEqual(report['sha256'],lab.digest(icon))


if __name__=='__main__':unittest.main()
