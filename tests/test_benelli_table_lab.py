import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_benelli_table_lab as lab
from items_sav import parse as parse_items
from test_item_table_additive import fixture


class Machine:
    def __init__(self,valid=True):self.checked=[];self.valid=valid
    def inspect_record(self,raw,slot):
        self.checked.append((slot,lab.sha(raw)))
        return {'native_decode_matches':self.valid,'native_descriptor_measure_matches':self.valid}


def bundle(descriptor,fragment):
    files={'PROTOTYPE_Benelli.item.disabled':descriptor,'PROTOTYPE_Benelli.fpvgroup.disabled':fragment,
           'Text/french/TEXTY_DD.txt.disabled':b'21500 "Invented [MODERNE]"\n'}
    report={'modern_design_decisions':{'text_id_allocated':True},
            'pending_requirements':['additive_table_transaction','complete_saved_game_compatibility','fpv_camera_hands_and_events']}
    return files,report


class BenelliFullTableLabTests(unittest.TestCase):
    def prepare(self,*,layer='PatchX01.dta',mutation=None,inventory=None,machine=None,changed_source=False,**kwargs):
        items,fpv,descriptor,fragment=fixture()
        tables={('SabreSquadron.dta','tables/items.sav'):items,
                ('PatchX01.dta','tables/items.sav'):items,lab.FPV_SOURCE:fpv}
        pins={key:(len(raw),lab.sha(raw)) for key,raw in tables.items()}
        files,report=bundle(descriptor,fragment)
        if mutation:mutation(tables,files,report)
        if changed_source:tables[lab.FPV_SOURCE]+=b'changed'
        with patch.object(lab,'TABLE_PINS',pins),\
             patch.object(lab.descriptor_lab,'prepare',return_value=(files,report)):
            return lab.prepare(tables,{},machine or Machine(),inventory={} if inventory is None else inventory,item_layer=layer,**kwargs)

    def test_optional_native_oracles_must_verify_both_exact_tables(self):
        from test_item_table_oracle import SyntheticMachine
        from test_fpv_table_oracle import Machine as FpvMachine
        files,report=self.prepare(table_machine=SyntheticMachine(),fpv_machine=FpvMachine())
        self.assertEqual(report['native_table_traversal']['items']['table_sha256'],lab.sha(files['Tables/items.sav.disabled']))
        self.assertEqual(report['native_table_traversal']['fpv']['table_sha256'],lab.sha(files['Tables/FpvAnims.sav.disabled']))
        for kwargs in ({'table_machine':SyntheticMachine()},{'fpv_machine':FpvMachine()}):
            with self.assertRaisesRegex(ValueError,'required together'):self.prepare(**kwargs)
        for table_machine,fpv_machine in (
                (SyntheticMachine(lambda report:report.update(native_loaded_descriptors_match=False)),FpvMachine()),
                (SyntheticMachine(),FpvMachine(lambda report:report.update(unpopulated_cells_unchanged=False)))):
            with self.assertRaisesRegex(ValueError,'traversal verification incomplete'):
                self.prepare(table_machine=table_machine,fpv_machine=fpv_machine)

    def test_both_archive_variants_prepare_full_disabled_tables_without_claiming_installation(self):
        for layer in lab.ITEM_LAYERS:
            with self.subTest(layer=layer):
                files,report=self.prepare(layer=layer)
                self.assertIn('Tables/items.sav.disabled',files)
                self.assertIn('Tables/FpvAnims.sav.disabled',files)
                self.assertTrue(all(name.endswith('.disabled') for name in files))
                self.assertEqual(report['native_descriptor_records_checked'],5)
                self.assertEqual(report['native_descriptor_slots_checked'],[9,23,179,359,400])
                self.assertEqual(parse_items(files['Tables/items.sav.disabled'])['present_slots'],5)
                self.assertEqual(report['item_source'],layer+'::tables/items.sav')
                self.assertTrue(report['reverse_verified_in_memory'])
                for key in ('game_modified','game_started','playable_weapon','item_slot_allocated_in_game',
                            'global_slot_reservation','installation_allowed','full_save_compatibility_qualified',
                            'native_whole_table_loader_executed','loose_overrides_merged'):
                    self.assertFalse(report[key])
                self.assertNotIn('additive_table_transaction',report['pending_requirements'])
                self.assertIn('isolated_deployment_transaction_and_override_merge',report['pending_requirements'])
                self.assertIn('complete_saved_game_compatibility',report['pending_requirements'])

    def test_every_present_record_is_verified_not_just_the_new_descriptor(self):
        machine=Machine();files,report=self.prepare(machine=machine)
        parsed=parse_items(files['Tables/items.sav.disabled'])
        self.assertEqual(machine.checked,[(s['slot'],s['sha256']) for s in parsed['slots'] if s['present']])
        with self.assertRaisesRegex(ValueError,'verification incomplete'):self.prepare(machine=Machine(False))

    def test_unknown_missing_and_changed_archive_bases_are_refused(self):
        for layer in ('others.DTA','Patch.dta','unknown',None):
            with self.subTest(layer=layer),self.assertRaisesRegex(ValueError,'Unreviewed'):self.prepare(layer=layer)
        with self.assertRaisesRegex(ValueError,'Changed selected'):self.prepare(changed_source=True)
        with self.assertRaisesRegex(ValueError,'Missing explicitly'):
            self.prepare(mutation=lambda tables,_files,_report:tables.pop(('PatchX01.dta','tables/items.sav')))

    def test_inventory_is_mandatory_and_unresolved_state_cannot_be_waived(self):
        with self.assertRaisesRegex(ValueError,'inventory texts'):
            lab.prepare({}, {},Machine(),inventory=None,item_layer='PatchX01.dta')
        with self.assertRaisesRegex(ValueError,'remains unresolved'):
            self.prepare(mutation=lambda _tables,_files,report:report['modern_design_decisions'].update(text_id_allocated=False))

    def test_private_output_is_fresh_safe_and_link_free(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);output=lab.output_directory('Fixture_v1',root)
            self.assertEqual(output,root/'.analysis/item-table-labs/Fixture_v1')
            for name in ('../escape','x/y','x\\y','NUL','COM1','',None,'x'*65):
                with self.subTest(name=name),self.assertRaises(ValueError):lab.output_directory(name,root)
            with patch.object(Path,'is_symlink',return_value=True),self.assertRaisesRegex(ValueError,'Linked'):
                lab.output_directory('Linked',root)
            output.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'already exists'):lab.output_directory('Fixture_v1',root)

    def test_writer_emits_only_disabled_payloads_and_never_overwrites_an_existing_lab(self):
        files,report=self.prepare();before=copy.deepcopy(files)
        with tempfile.TemporaryDirectory() as temp:
            output=lab.output_directory('Fixture',Path(temp));lab.write_lab(output,files,report)
            for name,raw in files.items():self.assertEqual((output/name).read_bytes(),raw)
            self.assertEqual(len([p for p in output.rglob('*') if p.is_file()]),len(files)+2)
            with self.assertRaises(FileExistsError):lab.write_lab(output,files,report)
        self.assertEqual(files,before)

    def test_writer_refuses_active_or_traversing_names_before_creating_any_output(self):
        for name in ('Tables/items.sav','../escaped.disabled','/absolute.disabled','C:evil.disabled',
                     'a\\evil.disabled','a/../evil.disabled','./evil.disabled'):
            with self.subTest(name=name),tempfile.TemporaryDirectory() as temp:
                output=Path(temp)/'uncreated'
                with self.assertRaises(ValueError):lab.write_lab(output,{name:b'invented'}, {})
                self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
