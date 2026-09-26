import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_benelli_descriptor_lab as lab
from item_weapon_descriptor import build_weapon
from item_native_layout import decode_record
from fpv_table import parse as parse_fpv
from test_item_weapon_descriptor import fixture as weapon_spec
from test_benelli_table_audit import benelli_table
from test_items_sav import invented_slot,table as item_table
from test_sound_definition import chunk,string,bank
from sound_definition import VARIANT_FIELDS


def sound_entry(label,filename):
    variant=chunk(1300,string(1400,filename)+b''.join(chunk(k,bytes(4)) for k in VARIANT_FIELDS[1:]))
    return chunk(1200,string(1210,label)+chunk(1310,b'\0')+variant)


def sound_fixture():
    empty=chunk(1200,string(1210,'')+chunk(1310,b'\0'))
    return chunk(1000,bank('First',b'')+bank('Second',b'')
                 +bank('Weapon Shooting',empty*36+sound_entry('I Benelli M4','f_bene_a.wav'))
                 +bank('Weapon Manipulation',empty*54+sound_entry('I Benelli M4 Reload','bene_r.wav')))


def baseline():
    raw=bytearray(build_weapon(weapon_spec()));raw[88:108]=b'Side by Side'.ljust(20,b'\0')
    return bytes(raw)


def fixture():
    slots=[None]*500
    slots[23]=baseline()
    slots[179]=invented_slot(name='AMMO Beneli',text_id=1179,kind=0)
    raw=item_table(slots)
    return {('SabreSquadron.dta','tables/items.sav'):raw,
            ('PatchX01.dta','tables/items.sav'):raw,
            ('others.DTA','tables/item_shoot.tbl'):b'invented shoot source',
            ('SabreSquadron.dta','tables/fpvanims.sav'):benelli_table()}


class Machine:
    def inspect_record(self,raw,slot):return {**decode_record(raw),'slot':slot,'synthetic_test_double':True}
    def ammo_binding(self,raw,ammo,**kwargs):return {'synthetic_test_double':True,**kwargs}
    def fpv_binding(self,slot,state):return {'synthetic_test_double':True,'slot':slot,'state':state}


class BenelliDescriptorLabTests(unittest.TestCase):
    def prepare(self,tables=None,*,changed_model=False,changed_sound=False,inventory=None):
        models={'PROTOTYPE_BenFPV':b'invented fpv','PROTOTYPE_BenM4':b'invented world'}
        pins={name:(len(raw),lab.sha(raw)) for name,raw in models.items()}
        if changed_model:models['PROTOTYPE_BenFPV']+=b'changed'
        fields=weapon_spec()['primary']['editor_fields'];fields[8]='36';fields[10]='54'
        sounds=sound_fixture()
        if changed_sound:sounds=sounds.replace(b'f_bene_a.wav',b'x_bene_a.wav')
        with patch('item_editor_table.require_row',return_value={'fields':fields,'sha256':'synthetic'}),\
             patch('benelli_fpv_static.derive',return_value=(b'invented derived',{})),\
             patch('build_benelli_fpv_lab.native_assets',return_value=(models,{'synthetic_test_double':True})),\
             patch.object(lab,'MODEL_PINS',pins):
            return lab.prepare(fixture() if tables is None else tables,
                               {'models/#fpvbeneliaim.4ds':b'invented model','maps/wi_it-benelli.bmp':b'invented icon',
                                'tables/ingamesounds.def':sounds,'sounds/f_bene_a.wav':b'invented sound',
                                'sounds/bene_r.wav':b'invented sound'},Machine(),inventory=inventory)

    def inventory(self):
        from build_modern_inventory_text_lab import CATALOGUE
        return {'catalogue':json.loads(CATALOGUE.read_text(encoding='utf-8')),
                'sources':{'Text/english/TEXTY_DD.txt':b'1 "Existing"\n','Text/french/TEXTY_DD.txt':b'1 "Existant"\n'},
                'occupied_item_text_ids':{1009,1179},'mission_range':(22000,65000)}

    def test_baseline_is_individual_explicit_attributes_not_whole_record(self):
        raw=baseline();fields=weapon_spec()['primary']['editor_fields']
        spec=lab.specification(fields,raw);built=build_weapon(spec)
        self.assertEqual(spec['names']['internal'],'MODERN_Benelli')
        self.assertEqual(spec['names']['icon'],'wi_it-benelli')
        self.assertEqual(spec['text_id'],0xffffffff)
        self.assertEqual(spec['weapon_members_raw'][0x54],179)
        self.assertEqual(spec['base_members_raw'],weapon_spec()['base_members_raw'])
        self.assertNotEqual(built,raw)
        self.assertEqual(fields,weapon_spec()['primary']['editor_fields'])

    def test_changed_baseline_owner_kind_or_secondary_contract_is_refused(self):
        good=baseline()
        for offset,blob in ((4,struct.pack('<I',2)),(88,b'Other'),(136,struct.pack('<I',3)),
                            (272,struct.pack('<I',1)),(276,struct.pack('<I',5)),(280,struct.pack('<I',6))):
            bad=bytearray(good);bad[offset:offset+len(blob)]=blob
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                lab.specification(weapon_spec()['primary']['editor_fields'],bytes(bad))

    def test_fpv_fragment_changes_only_group_owner_not_commercial_source(self):
        source=benelli_table();before=bytes(source);result=lab.isolated_fpv_group(source)
        group=parse_fpv(result)['groups'][0]
        original=next(g for g in parse_fpv(source)['groups'] if g['id']==109)
        self.assertEqual(group['id'],459)
        self.assertEqual(group['states'],original['states'])
        self.assertEqual(result[8:],source[original['offset']+2:original['offset']+original['size']])
        self.assertEqual(source,before)

    def test_bundle_has_only_disabled_fragments_and_explicit_remaining_work(self):
        tables=fixture();before=copy.deepcopy(tables);files,report=self.prepare(tables)
        self.assertEqual(len(files),4)
        self.assertTrue(all(name.endswith('.disabled') for name in files))
        self.assertFalse(any(name.casefold().endswith('.sav') for name in files))
        self.assertEqual(len(report['native_fpv_binding_checks']),13)
        self.assertEqual(len(report['native_ammunition_checks']),2)
        for key in ('item_slot_allocated','central_tables_modified','game_modified','game_started','playable_weapon','full_save_compatibility_qualified'):
            self.assertFalse(report[key])
        self.assertTrue(report['complete_binary_descriptor_built'])
        self.assertFalse(report['modern_design_decisions']['text_id_allocated'])
        self.assertIn('inventory_text_allocation',report['pending_requirements'])
        self.assertEqual(tables,before)
        self.assertEqual([r['index'] for r in report['sound_references']],[36,54])
        self.assertFalse(report['native_sound_argument_audit_included'])

    def test_changed_sound_reference_is_refused(self):
        with self.assertRaisesRegex(ValueError,'Changed Benelli sound reference'):self.prepare(changed_sound=True)

    def test_inventory_labels_replace_only_the_unresolved_text_member(self):
        original,_=self.prepare();files,report=self.prepare(inventory=self.inventory())
        before=original['PROTOTYPE_Benelli.item.disabled'];after=files['PROTOTYPE_Benelli.item.disabled']
        self.assertEqual(struct.unpack_from('<I',after,108)[0],21500)
        self.assertEqual(before[:108]+before[112:],after[:108]+after[112:])
        self.assertEqual(len(files),6)
        self.assertTrue(report['modern_design_decisions']['text_id_allocated'])
        self.assertEqual(report['modern_design_decisions']['text_id_allocation_scope'],'disabled_laboratory_only')
        self.assertNotIn('inventory_text_allocation',report['pending_requirements'])
        self.assertIn('inventory_text_rendering_and_font_tests',report['pending_requirements'])
        self.assertFalse(report['inventory_texts']['native_text_loader_qualified'])
        self.assertFalse(report['game_modified']);self.assertFalse(report['item_slot_allocated'])

    def test_inventory_snapshot_collisions_fail_before_a_descriptor_bundle_is_returned(self):
        inventory=self.inventory();inventory['occupied_item_text_ids'].add(21500)
        with self.assertRaisesRegex(ValueError,'referenced by an item'):self.prepare(inventory=inventory)
        inventory=self.inventory();inventory['sources']['Text/french/TEXTY_DD.txt']=b'21500 "Other owner"\n'
        with self.assertRaisesRegex(ValueError,'already present'):self.prepare(inventory=inventory)

    def test_missing_inventory_contract_or_wrong_label_owner_is_refused(self):
        with self.assertRaisesRegex(ValueError,'Incomplete inventory'):self.prepare(inventory={})
        inventory=self.inventory();inventory['catalogue']['labels'][0]['key']='different_owner'
        with self.assertRaisesRegex(ValueError,'Missing modern Benelli'):self.prepare(inventory=inventory)

    def test_occupied_candidate_fails_in_either_layer(self):
        for archive in ('SabreSquadron.dta','PatchX01.dta'):
            tables=fixture();slots=[None]*500
            slots[23]=baseline();slots[179]=invented_slot(name='AMMO Beneli',kind=0)
            slots[359]=invented_slot(name='Existing owner',kind=2)
            tables[archive,'tables/items.sav']=item_table(slots)
            with self.subTest(archive=archive),self.assertRaisesRegex(ValueError,'candidate'):
                self.prepare(tables)

    def test_changed_model_is_not_bundled(self):
        with self.assertRaisesRegex(ValueError,'Changed prepared model'):self.prepare(changed_model=True)

    def test_output_stays_in_private_fresh_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);output=lab.output_directory('Fixture_v1',root)
            self.assertEqual(output,root/'.analysis/item-descriptor-labs/Fixture_v1')
            self.assertFalse(output.exists())
            output.mkdir(parents=True)
            with self.assertRaises(ValueError):lab.output_directory('Fixture_v1',root)
            for name in ('../escape','',None,'NUL','COM1','a/b','a\\b','x'*65):
                with self.subTest(name=name),self.assertRaises(ValueError):lab.output_directory(name,root)

    def test_linked_output_is_refused_before_creation(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(Path,'is_symlink',return_value=True):
            with self.assertRaisesRegex(ValueError,'Linked'):lab.output_directory('Fixture',Path(temp))


if __name__=='__main__':unittest.main()
