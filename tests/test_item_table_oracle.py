"""Synthetic safety/audit tests; the commercial loop is checked privately."""
import copy
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from item_table_oracle import TableOracle,validated_table
import item_table_traversal_audit as audit
from items_sav import parse as parse_items
from test_item_table_additive import fixture
from test_items_sav import table as item_table


def valid_records():
    items=bytearray(fixture()[0])
    for slot in parse_items(items)['slots']:
        if slot['present']:struct.pack_into('<II',items,slot['offset']+136,0,0)
    return bytes(items)


class SyntheticMachine:
    def __init__(self,mutation=None):self.inputs=[];self.mutation=mutation
    def inspect_table(self,raw):
        self.inputs.append(raw)
        result={'table_sha256':audit.sha(raw),'native_slot_loop_matches':True,
                'native_loaded_descriptors_match':True,'source_read_only_unchanged':True,'slots_visited':500}
        if self.mutation:self.mutation(result)
        return result


class NativeTableSafetyTests(unittest.TestCase):
    def test_full_table_and_every_action_selector_are_validated_before_execution(self):
        good=valid_records();self.assertEqual(validated_table(good)['present_slots'],4)
        with self.assertRaises(ValueError):validated_table(item_table([None]*255))
        bad=bytearray(good);at=parse_items(good)['slots'][400]['offset']
        struct.pack_into('<I',bad,at+136,99)
        with self.assertRaisesRegex(ValueError,'action selector'):validated_table(bytes(bad))
        with self.assertRaises(ValueError):validated_table(good[:-1]+b'\0')

    def test_unpinned_image_is_rejected_before_any_native_emulation(self):
        for image in (b'',b'not a commercial client'):
            with self.assertRaisesRegex(ValueError,'Unreviewed decompressed'):TableOracle(image)

    def test_private_arena_alignment_and_limits_are_explicit(self):
        machine=object.__new__(TableOracle)
        machine.table_active=True;machine.next_address=machine.TABLE_ARENA
        machine.allocations={};machine.uc=Mock()
        first=machine.allocate(20);second=machine.allocate(104)
        self.assertEqual(first,machine.TABLE_ARENA);self.assertEqual(second,first+32)
        self.assertEqual(machine.next_address,second+112)
        machine.uc.mem_write.assert_any_call(first,b'\xcd'*20)
        for size in (0,-1,4097,True,1.0):
            with self.subTest(size=size),self.assertRaises(ValueError):machine.allocate(size)
        machine.next_address=machine.TABLE_ARENA+machine.TABLE_ARENA_SIZE-8
        with self.assertRaisesRegex(ValueError,'bounded'):machine.allocate(8)
        machine.next_address=machine.TABLE_ARENA-16
        with self.assertRaisesRegex(ValueError,'bounded'):machine.allocate(8)

    def test_slot_hook_rejects_wrong_cursor_destination_bound_and_iteration(self):
        machine=object.__new__(TableOracle);machine.table_active=True
        machine.table_source=0x3601000;machine.table_slots=[{'offset':0},{'offset':4}];machine.visited=[]
        machine.reg=SimpleNamespace(UC_X86_REG_EBX=1,UC_X86_REG_EBP=2,UC_X86_REG_ESI=3,UC_X86_REG_EDI=4)
        good={1:0,2:machine.table_source,3:machine.TABLE_MANAGER+0x10,4:500}
        registers=dict(good);machine.uc=SimpleNamespace(reg_read=lambda key:registers[key])
        machine.on_code(None,0x7dca46,3,None);self.assertEqual(machine.visited,[0])
        for key,value in ((1,1),(2,machine.table_source+4),(3,machine.TABLE_MANAGER+0x14),(4,499)):
            machine.visited=[];registers.clear();registers.update(good);registers[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):machine.on_code(None,0x7dca46,3,None)
        machine.visited=list(range(500));registers[1]=500
        with self.assertRaisesRegex(ValueError,'exceeded'):machine.on_code(None,0x7dca46,3,None)

    def test_synthetic_mapping_extents_do_not_overlap_existing_arenas(self):
        self.assertGreaterEqual(TableOracle.TABLE_MANAGER,TableOracle.FPV+0x4d000)
        self.assertGreaterEqual(TableOracle.TABLE_INPUT,TableOracle.TABLE_MANAGER+4096)
        self.assertGreaterEqual(TableOracle.TABLE_ARENA,TableOracle.TABLE_INPUT+TableOracle.TABLE_INPUT_SIZE)
        self.assertGreaterEqual(TableOracle.TABLE_INPUT_SIZE,252000)
        self.assertLessEqual(TableOracle.TABLE_ARENA_SIZE,262144)


class NativeTableAuditTests(unittest.TestCase):
    def run_audit(self,*,mutation=None,machine=None):
        items,fpv,descriptor,fragment=fixture()
        tables={('SabreSquadron.dta','tables/items.sav'):items,
                ('PatchX01.dta','tables/items.sav'):items,('SabreSquadron.dta','tables/fpvanims.sav'):fpv}
        pins={key:(len(raw),audit.sha(raw)) for key,raw in tables.items()}
        if mutation:mutation(tables)
        with patch.object(audit,'TABLE_PINS',pins):
            return audit.audit(tables,descriptor,fragment,machine or SyntheticMachine())

    def test_each_layer_is_traversed_before_and_after_addition_with_exact_reversal(self):
        machine=SyntheticMachine();report=self.run_audit(machine=machine)
        self.assertEqual(len(machine.inputs),4)
        for layer in report['layers'].values():
            self.assertEqual(layer['original']['slots_visited'],500)
            self.assertEqual(layer['disabled_addition']['slots_visited'],500)
            self.assertTrue(layer['reverse_verified_in_memory'])
        for key in ('base_255_slot_tables_executed','native_file_io_executed','native_fpv_table_loader_executed',
                    'game_started','game_modified','global_slot_reservation','full_save_compatibility_qualified'):
            self.assertFalse(report[key])

    def test_patchx_is_optional_but_sabre_and_pins_are_required(self):
        report=self.run_audit(mutation=lambda tables:tables.pop(('PatchX01.dta','tables/items.sav')))
        self.assertEqual(list(report['layers']),['SabreSquadron.dta'])
        with self.assertRaisesRegex(ValueError,'Missing reviewed'):
            self.run_audit(mutation=lambda tables:tables.pop(('SabreSquadron.dta','tables/items.sav')))
        with self.assertRaisesRegex(ValueError,'Changed or missing'):
            self.run_audit(mutation=lambda tables:tables.update({('SabreSquadron.dta','tables/fpvanims.sav'):b'changed'}))

    def test_incomplete_or_unrelated_native_receipt_cannot_be_called_success(self):
        for key,value in (('table_sha256','unrelated'),('native_slot_loop_matches',False),
                          ('native_loaded_descriptors_match',1),('source_read_only_unchanged',False),
                          ('slots_visited',499),('slots_visited',500.0)):
            with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'incomplete'):
                self.run_audit(machine=SyntheticMachine(lambda report:report.update({key:value})))


if __name__=='__main__':unittest.main()
