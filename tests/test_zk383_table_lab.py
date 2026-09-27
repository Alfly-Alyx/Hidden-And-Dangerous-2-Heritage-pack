"""Synthetic dual-item tables; no commercial bytes in test inputs."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_zk383_descriptor_lab as lab
from build_rigid_weapon_resource_lab import group
from item_ammo_additive import restore_pair
from item_table_additive import fingerprint
from item_weapon_descriptor import build_weapon
from item_ammo_descriptor import build_ammunition
from items_sav import parse
from fpv_table import parse as parse_fpv
from test_zk383_descriptor_lab import tables
from test_fg42_descriptor_lab import audio_bundle
from test_item_weapon_descriptor import fixture as weapon_spec
from test_item_ammo_descriptor import fixture as ammo_spec
from test_item_table_oracle import SyntheticMachine
from test_benelli_table_lab import Machine as StateMachine
from test_fpv_table_oracle import Machine as FpvMachine
from test_mg34_table_lab import Both


class ZK383TableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.audio=audio_bundle()

    def fixture(self,variant='H'):
        data=tables();spec=weapon_spec();spec['text_id']=21503;spec['weapon_members_raw'][0x54]=365
        files,audio=deepcopy(self.audio);files.update({'PROTOTYPE_ZK383.item.disabled':build_weapon(spec),
            'PROTOTYPE_ZK3MAG.item.disabled':build_ammunition(ammo_spec()),
            f'PROTOTYPE_ZK3P{variant}.fpvgroup.disabled':group('ZK383',variant)[0]})
        report={'scope':'private_disabled_zk383_and_ammunition','synthetic_slot':364,'synthetic_ammo_slot':365,
            'hand_variant':variant,'inventory_texts':{'synthetic_test_double':True},'audio_lab':audio,
            'files':{n:fingerprint(r) for n,r in files.items()},
            'pending_requirements':['additive_weapon_and_ammunition_tables','network_and_live_gameplay']}
        return data,files,report

    def prepare(self,*,variant='H',layer='PatchX01.dta',mutation=None,**kwargs):
        data,files,report=self.fixture(variant);pins={k:(len(v),lab.digest(v)) for k,v in data.items()}
        if mutation:mutation(data,files,report)
        with patch.object(lab,'TABLE_PINS',pins):
            return lab.full_tables(data,files,report,item_layer=layer,state_machine=kwargs.pop('state_machine',StateMachine()),
                table_machine=kwargs.pop('table_machine',SyntheticMachine()),fpv_machine=kwargs.pop('fpv_machine',Both()),**kwargs)

    def test_four_layer_hand_pairs_preserve_old_tables_and_have_no_ammo_fpv_group(self):
        for variant in ('H','R'):
            for layer in ('SabreSquadron.dta','PatchX01.dta'):
                data,source,_=self.fixture(variant);files,report=self.prepare(variant=variant,layer=layer)
                pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']}
                self.assertEqual(restore_pair(pair,report['transaction']),{'items':data[layer,'tables/items.sav'],
                    'fpv':data['SabreSquadron.dta','tables/fpvanims.sav']})
                self.assertEqual(report['native_descriptor_slots_checked'],[9,18,187,364,365])
                self.assertEqual(len(report['native_animation_resource_requests']),39)
                self.assertEqual([g['id'] for g in parse_fpv(pair['fpv'])['groups']],[109,464])
                self.assertEqual({n:files[n] for n in source},source)
                self.assertNotIn('additive_weapon_and_ammunition_tables',report['pending_requirements'])
                for flag in ('installation_allowed','game_started','game_modified','playable_weapon','global_slots_reserved'):
                    self.assertFalse(report[flag])

    def test_incomplete_native_receipts_fail_closed(self):
        for kwargs in ({'state_machine':StateMachine(False)},
            {'table_machine':SyntheticMachine(lambda r:r.update(native_loaded_descriptors_match=False))},
            {'fpv_machine':FpvMachine(lambda r:r.update(unpopulated_cells_unchanged=False))}):
            with self.assertRaisesRegex(ValueError,'Incomplete native'):self.prepare(**kwargs)

    def test_wrong_layer_incomplete_bundle_or_changed_sources_refused(self):
        for layer in ('others.DTA','Patch.dta',None):
            with self.assertRaises(ValueError):self.prepare(layer=layer)
        for mutation in (lambda t,f,r:r.update(inventory_texts=None),lambda t,f,r:r.update(synthetic_ammo_slot=187),
            lambda t,f,r:f.pop('PROTOTYPE_ZK3MAG.item.disabled'),lambda t,f,r:f.update({'PROTOTYPE_ZK383.item.disabled':b'changed'}),
            lambda t,f,r:t.update({('PatchX01.dta','tables/items.sav'):b'changed'})):
            with self.assertRaises(ValueError):self.prepare(mutation=mutation)

    def test_personal_old_ammunition_edits_are_preserved_because_new_ammo_is_independent(self):
        data,_,_=self.fixture();raw=bytearray(data['PatchX01.dta','tables/items.sav']);slot=parse(raw)['slots'][187]
        struct.pack_into('<f',raw,slot['offset']+176,19.0);overlay={'items':bytes(raw)}
        files,report=self.prepare(overlays=overlay)
        pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']}
        self.assertEqual(restore_pair(pair,report['transaction'])['items'],overlay['items'])
        self.assertTrue(report['central_table_overlay_composition']['all_preexisting_central_table_changes_preserved'])

    def test_changed_output_refuses_dual_rollback(self):
        files,report=self.prepare();pair={'items':files['Tables/items.sav.disabled'],'fpv':files['Tables/FpvAnims.sav.disabled']+b'new'}
        with self.assertRaises(ValueError):restore_pair(pair,report['transaction'])


if __name__=='__main__':unittest.main()
