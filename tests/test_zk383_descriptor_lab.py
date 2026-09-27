"""Invented category tables and native test doubles; no commercial fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_zk383_descriptor_lab as lab
from item_weapon_descriptor import build_weapon
from item_ammo_descriptor import build_ammunition
from item_native_layout import decode_record
from test_item_weapon_descriptor import fixture as weapon_spec
from test_item_ammo_descriptor import fixture as ammo_spec
from test_items_sav import invented_slot,table
from test_fg42_descriptor_lab import inventory,audio_bundle
from test_mg34_descriptor_lab import SoundMachine
from test_benelli_table_lab import Machine as StateMachine
from test_item_table_additive import group
from test_fpv_table import table as fpv_table


def baselines():
    gun=bytearray(build_weapon(weapon_spec()));gun[88:108]=b'MP 40 '.ljust(20,b'\0')
    spec=ammo_spec();spec['text_id']=1187;spec['quantity']=32;ammo=bytearray(build_ammunition(spec));ammo[88:108]=b'AMMO MP 40'.ljust(20,b'\0')
    return bytes(gun),bytes(ammo)


def recipe():
    r=json.loads(lab.RECIPE.read_text(encoding='utf-8'));gun,ammo=baselines()
    r['category_weapon_sha256']=lab.digest(gun);r['category_ammo_sha256']=lab.digest(ammo);return r


def tables():
    gun,ammo=baselines();rows=[None]*500;rows[18]=gun;rows[187]=ammo
    existing=bytearray(invented_slot(name='Old helmet',text_id=1009,kind=2));struct.pack_into('<II',existing,136,0,0);rows[9]=bytes(existing)
    raw=table(rows)
    return {('SabreSquadron.dta','tables/items.sav'):raw,('PatchX01.dta','tables/items.sav'):raw,
        ('SabreSquadron.dta','tables/fpvanims.sav'):fpv_table(group(109))}


class Machine(StateMachine):
    def ammo_binding(self,gun,ammo,**kwargs):return {'native_ammo_binding_matches':True,'initial_quantity':30.0,**kwargs}
    def fpv_binding(self,slot,state):return {'slot':slot,'state':state,'synthetic_test_double':True}


class ZK383DescriptorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.audio=audio_bundle()

    def prepare(self,*,mutation=None,state=None,sound=None,inv=None):
        data=tables();r=recipe();bundle=deepcopy(self.audio);pins={k:(len(raw),lab.digest(raw)) for k,raw in data.items()}
        if mutation:mutation(data,r,bundle)
        gun,ammo=baselines()
        with patch.object(lab,'WEAPON_BASE_SHA',lab.digest(gun)),patch.object(lab,'AMMO_BASE_SHA',lab.digest(ammo)),\
             patch.object(lab,'TABLE_PINS',pins),patch.object(lab,'prepare_audio',return_value=bundle),\
             patch.object(lab,'FPV_PIN',lab.digest(b'invented FPV')),\
             patch.object(lab,'model_assets',return_value=({'PROTOTYPE_ZK383.4ds.disabled':b'world',
                'PROTOTYPE_ZK3MAG.4ds.disabled':b'magazine','Maps/MOD_ZK383_ICON.bmp.disabled':b'icon',
                'Maps/MOD_ZK3MAG_ICON.bmp.disabled':b'magazine icon'},{'synthetic_test_double':True})),\
             patch.object(lab,'prepare_resources',return_value=({'PROTOTYPE_ZK3_HandFPV.4ds.disabled':b'invented FPV',
                'PROTOTYPE_ZK3PH.fpvgroup.disabled':b'invented group'},{'synthetic_test_double':True})) as resource:
            before=deepcopy((data,r));result=lab.prepare(data,b'definition',{},r,b'hand',Path('unused'),{},'H',
                state or Machine(),sound or SoundMachine(),None,None,inventory=inventory() if inv is None else inv)
            self.assertEqual((data,r),before)
        self.assertEqual(resource.call_args.args[:2],('ZK383','H'));return result

    def test_complete_modern_weapon_and_magazine_have_distinct_new_identities(self):
        files,report=self.prepare();gun=files['PROTOTYPE_ZK383.item.disabled'];ammo=files['PROTOTYPE_ZK3MAG.item.disabled']
        self.assertEqual(len(gun),508);self.assertEqual(len(ammo),508)
        self.assertEqual(decode_record(gun)['members']['0x54']['value_raw'],365)
        self.assertEqual(decode_record(ammo)['kind'],0);self.assertEqual(struct.unpack_from('<f',ammo,176)[0],30)
        self.assertEqual(struct.unpack_from('<I',gun,108)[0],21503);self.assertEqual(struct.unpack_from('<I',ammo,108)[0],21504)
        self.assertEqual(ammo[8:28],bytes(20));self.assertTrue(all(n.endswith('.disabled') for n in files))
        self.assertEqual(files['PROTOTYPE_ZK3FPV.4ds.disabled'],b'invented FPV')
        self.assertNotIn('PROTOTYPE_ZK3_HandFPV.4ds.disabled',files)
        self.assertEqual(report['native_sound_arguments']['shoot'],{'bank':2,'index':2})
        self.assertEqual(report['native_sound_arguments']['reload'],{'bank':3,'index':4})
        self.assertEqual(len(report['native_fpv_bindings']),13)
        self.assertTrue(report['existing_mp40_and_ammunition_187_unchanged'])
        for flag in ('installation_allowed','game_started','game_modified','playable_weapon','commercial_audio_exported','commercial_hand_model_exported'):
            self.assertFalse(report[flag])
        self.assertFalse(report['modern_design_decisions']['historical_zk383_data_recovered'])

    def test_recipe_requires_explicit_modern_identity_complete_fields_and_distinct_slots(self):
        original=json.loads(lab.RECIPE.read_text(encoding='utf-8'));fields=lab.checked_recipe(original)
        self.assertEqual(fields[2],'ZK 383');self.assertEqual(fields[8],'MOD_ZK383_F')
        for key,value in (('status','active'),('case','FG42'),('schema_version',True),('ammo_slot',187),
            ('weapon_slot',18),('ammo_quantity',True),('ammo_quantity',0),('ammo_quantity',10001)):
            changed=deepcopy(original);changed[key]=value
            with self.assertRaises(ValueError):lab.checked_recipe(changed)
        for mutation in (lambda r:r['shoot_fields'].pop('6'),lambda r:r['shoot_fields'].update({'8':'0'}),
            lambda r:r.update(extra='unexpected')):
            changed=deepcopy(original);mutation(changed)
            with self.assertRaises(ValueError):lab.checked_recipe(changed)

    def test_changed_baseline_archives_and_audio_are_refused(self):
        def source(data,r,bundle):data['PatchX01.dta','tables/items.sav']+=b'changed'
        def audio(data,r,bundle):bundle[0]['Sounds/MOD_ZK383_F.wav.disabled']=b'changed'
        def receipt(data,r,bundle):bundle[1]['transaction']['additions'][2]['index']=100
        for mutation in (source,audio,receipt):
            with self.assertRaises(ValueError):self.prepare(mutation=mutation)

    def test_incomplete_native_descriptor_ammo_and_sound_receipts_refused(self):
        with self.assertRaisesRegex(ValueError,'weapon receipt'):self.prepare(state=Machine(False))
        state=Machine()
        with patch.object(state,'ammo_binding',return_value={'native_ammo_binding_matches':True,'initial_quantity':32.0}):
            with self.assertRaisesRegex(ValueError,'ammunition binding'):self.prepare(state=state)
        sound=SimpleNamespace(selection=lambda *args:{'native_argument_flow_matches':True,'shoot':{'bank':2,'index':0},'reload':{'bank':3,'index':4}})
        with self.assertRaisesRegex(ValueError,'sound flow'):self.prepare(sound=sound)

    def test_inventory_requires_both_labels_and_no_collision(self):
        with self.assertRaisesRegex(ValueError,'inventory snapshot'):self.prepare(inv={})
        for number in (21503,21504):
            inv=inventory();inv['occupied_item_text_ids'].add(number)
            with self.assertRaises(ValueError):self.prepare(inv=inv)
        inv=inventory();inv['catalogue']['labels']=[r for r in inv['catalogue']['labels'] if r['key']!='zk383_magazine']
        with self.assertRaisesRegex(ValueError,'inventory labels'):self.prepare(inv=inv)

    def test_modern_geometry_and_icons_rebuild_without_commercial_assets(self):
        files,report=lab.model_assets()
        self.assertEqual((len(files['PROTOTYPE_ZK383.4ds.disabled']),lab.digest(files['PROTOTYPE_ZK383.4ds.disabled'])),lab.MODEL_PINS['world'])
        self.assertEqual((len(files['PROTOTYPE_ZK3MAG.4ds.disabled']),lab.digest(files['PROTOTYPE_ZK3MAG.4ds.disabled'])),lab.MODEL_PINS['magazine'])
        self.assertEqual(report['magazine']['pieces'],2);self.assertEqual(report['magazine']['triangles_per_lod'],[24,24])
        for role in ('world','magazine'):
            self.assertFalse(report[role]['commercial_model_or_icon_used']);self.assertFalse(report[role]['engine_loaded'])

    def test_availability_refuses_either_occupied_slot_or_fpv_owner(self):
        for occupied in (364,365):
            data=tables();rows=[None]*500;rows[18],rows[187]=baselines();rows[occupied]=invented_slot(name='Occupied',kind=2)
            data['PatchX01.dta','tables/items.sav']=table(rows)
            with patch.object(lab,'TABLE_PINS',{k:(len(v),lab.digest(v)) for k,v in data.items()}),\
                 patch.object(lab,'WEAPON_BASE_SHA',lab.digest(baselines()[0])),patch.object(lab,'AMMO_BASE_SHA',lab.digest(baselines()[1])):
                with self.assertRaisesRegex(ValueError,'occupied'):lab.availability(data)
        for owner in (464,465):
            data=tables();data['SabreSquadron.dta','tables/fpvanims.sav']=fpv_table(group(owner))
            with patch.object(lab,'TABLE_PINS',{k:(len(v),lab.digest(v)) for k,v in data.items()}),\
                 patch.object(lab,'WEAPON_BASE_SHA',lab.digest(baselines()[0])),patch.object(lab,'AMMO_BASE_SHA',lab.digest(baselines()[1])):
                with self.assertRaisesRegex(ValueError,'FPV owner'):lab.availability(data)


if __name__=='__main__':unittest.main()
