"""Synthetic pair transactions; no commercial table bytes are fixtures."""
import copy
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_mg34_descriptor_lab as lab
from build_rigid_weapon_resource_lab import group
from item_table_additive import restore,fingerprint
from items_sav import parse as parse_items
from test_mg34_descriptor_lab import tables as descriptor_tables
from test_item_weapon_descriptor import fixture as weapon_spec
from item_weapon_descriptor import build_weapon
from test_item_table_additive import group as old_group
from test_fpv_table import table as fpv_table
from test_item_table_oracle import SyntheticMachine
from test_benelli_table_lab import Machine as StateMachine
from test_fpv_table_oracle import Machine as FpvMachine
from test_fpv_resource_oracle import ResourceMachine


class Both(ResourceMachine,FpvMachine):
    def inspect_table(self,raw):
        ResourceMachine.inspect_table(self,raw);return FpvMachine().inspect_table(raw)


def fixture(variant='H'):
    tables=descriptor_tables()
    for key,raw in list(tables.items()):
        if key[1]!='tables/items.sav':continue
        raw=bytearray(raw)
        for slot in parse_items(raw)['slots']:
            if slot['present']:struct.pack_into('<II',raw,slot['offset']+136,0,0)
        tables[key]=bytes(raw)
    tables['SabreSquadron.dta','tables/fpvanims.sav']=fpv_table(old_group(109))
    spec=weapon_spec();spec['text_id']=21501;spec['names']['internal']='MODERN_MG34';spec['weapon_members_raw'][0x54]=201
    files={'PROTOTYPE_MG34.item.disabled':build_weapon(spec),
           f'PROTOTYPE_MG3P{variant}.fpvgroup.disabled':group('MG34',variant)[0],
           'Text/french/TEXTY_DD.txt.disabled':b'21501 "MG 34 [MODERNE]"\n'}
    report={'scope':'private_disabled_portable_mg34_descriptor','inventory_texts':{'synthetic_test_double':True},
        'synthetic_slot':363,'hand_variant':variant,'files':{n:fingerprint(r) for n,r in files.items()},
        'pending_requirements':['additive_central_table_transaction','network_and_live_gameplay']}
    return tables,files,report


class MG34TableTests(unittest.TestCase):
    def prepare(self,*,variant='H',layer='PatchX01.dta',mutate=None,**kwargs):
        tables,files,report=fixture(variant);pins={k:(len(r),lab.digest(r)) for k,r in tables.items()}
        if mutate:mutate(tables,files,report)
        with patch.object(lab,'TABLE_PINS',pins):
            return lab.full_tables(tables,files,report,item_layer=layer,state_machine=kwargs.pop('state_machine',StateMachine()),
                table_machine=kwargs.pop('table_machine',SyntheticMachine()),fpv_machine=kwargs.pop('fpv_machine',Both()),**kwargs)

    def test_all_four_layer_hand_combinations_preserve_every_existing_slot_and_reverse(self):
        for variant in ('H','R'):
            for layer in ('SabreSquadron.dta','PatchX01.dta'):
                tables,source,_=fixture(variant);before=copy.deepcopy(tables)
                files,report=self.prepare(variant=variant,layer=layer)
                pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']}
                self.assertEqual(restore(pair,report['transaction']),{'items':tables[layer,'tables/items.sav'],
                    'fpv':tables['SabreSquadron.dta','tables/fpvanims.sav']})
                self.assertEqual(len(pair['items']),252000);self.assertEqual(tables,before)
                self.assertEqual(report['native_descriptor_slots_checked'],[32,33,48,201,211,363])
                self.assertEqual(len(report['native_animation_resource_requests']),39)
                self.assertNotIn('additive_central_table_transaction',report['pending_requirements'])
                self.assertIn('network_and_live_gameplay',report['pending_requirements'])
                self.assertEqual({n:files[n] for n in source},source)
                for flag in ('installation_allowed','game_started','game_modified','playable_weapon','item_slot_allocated_in_game'):
                    self.assertFalse(report[flag])

    def test_native_descriptor_or_table_receipts_cannot_be_waived(self):
        for kwargs in ({'state_machine':StateMachine(False)},
            {'table_machine':SyntheticMachine(lambda r:r.update(native_loaded_descriptors_match=False))},
            {'fpv_machine':FpvMachine(lambda r:r.update(unpopulated_cells_unchanged=False))}):
            with self.assertRaisesRegex(ValueError,'Incomplete native'):self.prepare(**kwargs)

    def test_wrong_layer_or_unresolved_inventory_or_changed_bundle_are_refused(self):
        for layer in ('others.DTA','Patch.dta',None):
            with self.assertRaises(ValueError):self.prepare(layer=layer)
        for mutate in (lambda t,f,r:r.update(inventory_texts=None),lambda t,f,r:r.update(synthetic_slot=32),
            lambda t,f,r:f.update({'PROTOTYPE_MG34.item.disabled':b'changed'}),
            lambda t,f,r:f.pop('Text/french/TEXTY_DD.txt.disabled')):
            with self.assertRaises(ValueError):self.prepare(mutate=mutate)

    def test_changed_selected_archives_are_refused_before_insertion(self):
        with self.assertRaisesRegex(ValueError,'central table source'):
            self.prepare(mutate=lambda t,f,r:t.update({('PatchX01.dta','tables/items.sav'):b'changed'}))

    def test_personal_central_record_changes_are_preserved_and_restored_exactly(self):
        tables,_,_=fixture();raw=bytearray(tables['PatchX01.dta','tables/items.sav'])
        slot=parse_items(raw)['slots'][32];struct.pack_into('<f',raw,slot['offset']+112,4.25)
        overlay={'items':bytes(raw)};files,report=self.prepare(overlays=overlay)
        pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']}
        self.assertEqual(restore(pair,report['transaction'])['items'],overlay['items'])
        self.assertTrue(report['central_table_overlay_composition']['all_preexisting_central_table_changes_preserved'])
        self.assertFalse(report['installation_allowed'])

    def test_changed_portable_ammo_override_is_refused_not_replaced(self):
        tables,_,_=fixture();raw=bytearray(tables['PatchX01.dta','tables/items.sav'])
        slot=parse_items(raw)['slots'][201];struct.pack_into('<f',raw,slot['offset']+112,4.25)
        with self.assertRaisesRegex(ValueError,'ammunition differs'):self.prepare(overlays={'items':bytes(raw)})

    def test_later_edit_refuses_pair_rollback(self):
        files,report=self.prepare();pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']+b'new'}
        with self.assertRaises(ValueError):restore(pair,report['transaction'])


if __name__=='__main__':unittest.main()
