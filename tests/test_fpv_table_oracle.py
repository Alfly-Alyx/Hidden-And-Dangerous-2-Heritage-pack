"""Invented FPV containers and bounded memory-I/O doubles only."""
from collections import Counter
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import fpv_table_oracle as oracle
from fpv_table import parse
from item_native_layout import fpv_native_projection
from test_fpv_table import chunk,variant,state,table
from test_item_table_additive import group
from benelli_table_audit import EXPECTED_STATES


def benelli_table():
    return table(chunk(109,b''.join(state(2000+i,variant('#FPVBeneli'+name+'.I3D'))
                                   for i,name in enumerate(EXPECTED_STATES))))


class Machine:
    def __init__(self,mutation=None):self.inputs=[];self.mutation=mutation
    def inspect_table(self,raw):
        parsed,projected=oracle.validated_fpv(raw);self.inputs.append(raw)
        result={'table_sha256':oracle.sha(raw),'native_nested_traversal_matches':True,
                'native_strings_and_values_match':True,'unpopulated_cells_unchanged':True,
                'source_read_only_unchanged':True,'groups_visited':len(parsed['groups']),
                'populated_channels_checked':sum(c['resource'] is not None for c in projected['cells'])}
        if self.mutation:self.mutation(result)
        return result


class FpvOracleSafetyTests(unittest.TestCase):
    def test_validation_retains_native_shape_and_rejects_string_truncation(self):
        raw=table(group(459));parsed,projected=oracle.validated_fpv(raw)
        self.assertEqual(len(projected['cells']),52);self.assertEqual(parsed['groups'][0]['id'],459)
        for name,valid in (('A'*998,True),('A'*999,False)):
            raw=table(chunk(459,b''.join(state(2000+i,variant(name)) for i in range(13))))
            if valid:oracle.validated_fpv(raw)
            else:
                with self.assertRaisesRegex(ValueError,'truncated'):oracle.validated_fpv(raw)
        with self.assertRaisesRegex(ValueError,'bounded'):oracle.validated_fpv(b'x'*(oracle.MAX_SOURCE+1))
        with self.assertRaisesRegex(ValueError,'thirteen'):oracle.validated_fpv(table(chunk(459,state())))

    def test_duplicate_groups_and_multiple_variants_are_not_normalized(self):
        with self.assertRaises(ValueError):oracle.validated_fpv(table(group(459)+group(459)))
        raw=table(chunk(459,b''.join(state(2000+i,variant('a')+variant('b')) for i in range(13))))
        with self.assertRaisesRegex(ValueError,'first variant'):oracle.validated_fpv(raw)

    def test_unpinned_image_cannot_reach_native_execution(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed decompressed'):oracle.FpvTableOracle(b'invented')

    def io_machine(self,args):
        machine=object.__new__(oracle.FpvTableOracle)
        machine.fpv_active=True;machine.buffer=b'0123456789';machine.position=2;machine.io_counts=Counter()
        machine.reg=SimpleNamespace(UC_X86_REG_ESP=1)
        stack=machine.STACK+0x8000
        machine.uc=Mock();machine.uc.reg_read.return_value=stack
        frame={stack+4*n:arg for n,arg in enumerate(args,1)}
        machine.get=lambda address:frame[address]
        machine.return_io=Mock()
        return machine

    def test_read_double_copies_only_requested_bytes_to_allowed_private_memory(self):
        machine=self.io_machine((oracle.FpvTableOracle.HANDLE,oracle.FpvTableOracle.FPV+0xc0,4))
        machine.on_code(None,0x7e539e,1,None)
        machine.uc.mem_write.assert_called_once_with(machine.FPV+0xc0,b'2345')
        self.assertEqual(machine.position,6);self.assertEqual(machine.buffer,b'0123456789')
        machine.return_io.assert_called_once_with(4)

    def test_reads_refuse_handles_foreign_pointers_oversized_and_truncated_requests(self):
        cls=oracle.FpvTableOracle
        for args in ((0,cls.STACK,4),(cls.HANDLE,0x401000,4),(cls.HANDLE,cls.STACK+65535,4),
                     (cls.HANDLE,cls.STACK,1025),(cls.HANDLE,cls.STACK,9)):
            machine=self.io_machine(args)
            with self.subTest(args=args),self.assertRaises(ValueError):machine.on_code(None,0x7e539e,1,None)
            machine.uc.mem_write.assert_not_called()
        with self.assertRaisesRegex(ValueError,'Writes forbidden'):
            self.io_machine((cls.HANDLE,cls.STACK,4)).on_code(None,0x7e5392,1,None)

    def test_seek_supports_signed_relative_motion_but_never_leaves_owned_input(self):
        cls=oracle.FpvTableOracle
        for offset,origin,expected in ((3,0,3),(0xffffffff,1,1),(0xfffffffe,2,8)):
            machine=self.io_machine((cls.HANDLE,offset,origin));machine.on_code(None,0x7e5398,1,None)
            self.assertEqual(machine.position,expected);machine.return_io.assert_called_once_with(expected)
        for offset,origin in ((11,0),(0xffffffff,0),(1,2),(0,3)):
            with self.subTest(offset=offset,origin=origin),self.assertRaises(ValueError):
                self.io_machine((cls.HANDLE,offset,origin)).on_code(None,0x7e5398,1,None)

    def test_reference_counted_string_arena_is_bounded_and_aligned(self):
        machine=object.__new__(oracle.FpvTableOracle);machine.fpv_active=True
        machine.next_address=machine.STRINGS;machine.allocations={};machine.uc=Mock()
        first=machine.allocate(33);self.assertEqual(machine.next_address,first+48)
        machine.uc.mem_write.assert_called_once_with(first,b'\xcd'*33)
        for size in (0,-1,True,1.0,4097):
            with self.assertRaises(ValueError):machine.allocate(size)
        machine.next_address=machine.STRINGS+machine.STRINGS_SIZE-8
        with self.assertRaisesRegex(ValueError,'bounded'):machine.allocate(8)

    def test_group_trace_refuses_extra_or_reordered_native_groups(self):
        machine=object.__new__(oracle.FpvTableOracle);machine.fpv_active=True
        machine.expected_groups=[109,459];machine.group_ids=[]
        machine.reg=SimpleNamespace(UC_X86_REG_EAX=1);machine.uc=Mock();machine.uc.reg_read.return_value=109
        machine.on_code(None,0x490ea3,5,None);self.assertEqual(machine.group_ids,[109])
        with self.assertRaisesRegex(ValueError,'iteration'):machine.on_code(None,0x490ea3,5,None)
        machine.uc.reg_read.return_value=459;machine.on_code(None,0x490ea3,5,None)
        with self.assertRaisesRegex(ValueError,'iteration'):machine.on_code(None,0x490ea3,5,None)


class FpvTraversalAuditTests(unittest.TestCase):
    def run_audit(self,machine=None,changed=False):
        raw=benelli_table();tables={(name,'tables/fpvanims.sav'):raw for name in ('others.DTA','SabreSquadron.dta')}
        pins={key:(len(value),oracle.sha(value)) for key,value in tables.items()}
        if changed:tables['others.DTA','tables/fpvanims.sav']+=b'changed'
        with patch('benelli_table_audit.TABLE_PINS',pins):return oracle.audit(tables,machine or Machine())

    def test_two_sources_fragment_and_full_addition_are_checked_without_activation(self):
        machine=Machine();report=self.run_audit(machine)
        self.assertEqual(len(machine.inputs),4)
        added=machine.inputs[-1];source=machine.inputs[1]
        self.assertEqual(added[6:len(source)],source[6:])
        self.assertEqual([g['id'] for g in parse(added)['groups']],[109,459])
        for key in ('commercial_tables_modified','game_started','game_modified',
                    'native_root_opening_or_file_io_executed','live_animation_qualified'):
            self.assertFalse(report[key])

    def test_changed_sources_and_incomplete_native_receipts_are_refused(self):
        with self.assertRaisesRegex(ValueError,'reviewed FPV'):self.run_audit(changed=True)
        for key,value in (('table_sha256','unrelated'),('native_nested_traversal_matches',False),
                          ('native_strings_and_values_match',1),('groups_visited',1.0),
                          ('populated_channels_checked',0),('unpopulated_cells_unchanged',False)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Incomplete'):
                self.run_audit(Machine(lambda result:result.update({key:value})))


if __name__=='__main__':unittest.main()
