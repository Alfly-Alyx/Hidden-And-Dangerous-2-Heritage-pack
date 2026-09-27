"""Invented central tables and real original audio recipes; no game fixtures."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_fg42_descriptor_lab as lab
from build_rigid_weapon_resource_lab import group
from item_table_additive import restore,fingerprint
from items_sav import parse as parse_items
from item_weapon_descriptor import build_weapon
from test_fg42_descriptor_lab import tables as descriptor_tables,audio_bundle
from test_item_weapon_descriptor import fixture as weapon_spec
from test_item_table_additive import group as old_group
from test_fpv_table import table as fpv_table
from test_item_table_oracle import SyntheticMachine
from test_benelli_table_lab import Machine as StateMachine
from test_fpv_table_oracle import Machine as FpvMachine
from test_mg34_table_lab import Both


class FG42TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.audio=audio_bundle()

    def fixture(self,variant='H'):
        tables=descriptor_tables();tables['SabreSquadron.dta','tables/fpvanims.sav']=fpv_table(old_group(109))
        spec=weapon_spec();spec['text_id']=21502;spec['names']['internal']='MODERN_FG42';spec['weapon_members_raw'][0x54]=196
        files,proof=deepcopy(self.audio)
        files.update({'PROTOTYPE_FG42.item.disabled':build_weapon(spec),
            f'PROTOTYPE_FG4P{variant}.fpvgroup.disabled':group('FG42',variant)[0],
            'Text/french/TEXTY_DD.txt.disabled':b'21502 "FG 42 [MODERNE]"\n'})
        report={'scope':'private_disabled_fg42_descriptor','inventory_texts':{'synthetic_test_double':True},
            'audio_lab':proof,'synthetic_slot':362,'hand_variant':variant,'files':{n:fingerprint(r) for n,r in files.items()},
            'pending_requirements':['additive_central_table_transaction','network_and_live_gameplay']}
        return tables,files,report

    def prepare(self,*,variant='H',layer='PatchX01.dta',mutate=None,**kwargs):
        tables,files,report=self.fixture(variant);pins={k:(len(r),lab.digest(r)) for k,r in tables.items()}
        if mutate:mutate(tables,files,report)
        with patch.object(lab,'TABLE_PINS',pins):
            return lab.full_tables(tables,files,report,item_layer=layer,state_machine=kwargs.pop('state_machine',StateMachine()),
                table_machine=kwargs.pop('table_machine',SyntheticMachine()),fpv_machine=kwargs.pop('fpv_machine',Both()),**kwargs)

    def test_four_layer_hand_combinations_reverse_without_changing_previous_entries(self):
        for variant in ('H','R'):
            for layer in ('SabreSquadron.dta','PatchX01.dta'):
                tables,source,_=self.fixture(variant);files,report=self.prepare(variant=variant,layer=layer)
                pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']}
                self.assertEqual(restore(pair,report['transaction']),{'items':tables[layer,'tables/items.sav'],
                    'fpv':tables['SabreSquadron.dta','tables/fpvanims.sav']})
                self.assertEqual(report['native_descriptor_slots_checked'],[26,27,196,362])
                self.assertEqual(len(report['native_animation_resource_requests']),39)
                self.assertEqual({n:files[n] for n in source},source)
                self.assertNotIn('additive_central_table_transaction',report['pending_requirements'])
                self.assertTrue(report['sound_definition_reversal_verified'])
                for flag in ('installation_allowed','game_started','game_modified','playable_weapon','item_slot_allocated_in_game'):
                    self.assertFalse(report[flag])

    def test_native_receipts_cannot_be_waived(self):
        for kwargs in ({'state_machine':StateMachine(False)},
            {'table_machine':SyntheticMachine(lambda r:r.update(native_loaded_descriptors_match=False))},
            {'fpv_machine':FpvMachine(lambda r:r.update(unpopulated_cells_unchanged=False))}):
            with self.assertRaisesRegex(ValueError,'Incomplete native'):self.prepare(**kwargs)

    def test_wrong_layer_or_changed_bundle_refused(self):
        for layer in ('others.DTA','Patch.dta',None):
            with self.assertRaises(ValueError):self.prepare(layer=layer)
        for mutate in (lambda t,f,r:r.update(inventory_texts=None),lambda t,f,r:r.update(audio_lab=None),
            lambda t,f,r:r.update(synthetic_slot=27),lambda t,f,r:f.update({'PROTOTYPE_FG42.item.disabled':b'changed'}),
            lambda t,f,r:f.pop('Sounds/MOD_FG42_F.wav.disabled')):
            with self.assertRaises(ValueError):self.prepare(mutate=mutate)

    def test_changed_archive_refused_before_insertion(self):
        with self.assertRaisesRegex(ValueError,'central table source'):
            self.prepare(mutate=lambda t,f,r:t.update({('PatchX01.dta','tables/items.sav'):b'changed'}))

    def test_personal_helmet_edit_preserved_and_reversed(self):
        tables,_,_=self.fixture();raw=bytearray(tables['PatchX01.dta','tables/items.sav']);slot=parse_items(raw)['slots'][27]
        struct.pack_into('<f',raw,slot['offset']+112,4.25);overlay={'items':bytes(raw)}
        files,report=self.prepare(overlays=overlay)
        pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']}
        self.assertEqual(restore(pair,report['transaction'])['items'],overlay['items'])
        self.assertTrue(report['central_table_overlay_composition']['all_preexisting_central_table_changes_preserved'])

    def test_changed_ammunition_override_refused_not_replaced(self):
        tables,_,_=self.fixture();raw=bytearray(tables['PatchX01.dta','tables/items.sav']);slot=parse_items(raw)['slots'][196]
        struct.pack_into('<f',raw,slot['offset']+112,4.25)
        with self.assertRaisesRegex(ValueError,'ammunition differs'):self.prepare(overlays={'items':bytes(raw)})

    def test_later_edit_prevents_rollback(self):
        files,report=self.prepare();pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']+b'new'}
        with self.assertRaises(ValueError):restore(pair,report['transaction'])


if __name__=='__main__':unittest.main()
