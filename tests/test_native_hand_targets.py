"""Invented buffers only; no native DLL, game data or emulator required."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_targets as native
import build_native_hand_targets as builder
import unified_hand_pose_audit as audit


class NativeHandTargetsTests(unittest.TestCase):
    def receipt(self):
        return {'status':0,'compiled_sha256':native.BINARY_SHA,'input_unchanged':True,
            'output_and_scratch_guards_unchanged':True,'failed_output_unchanged':True,
            'native_cdecl_preserved':True,'game_started':False,'client_hook_implemented':False}

    def test_encoding_sizes_offsets_and_source_preservation(self):
        for count in (5,9,64,128):
            data=builder.invented_data(count,True);saved=deepcopy(data);n,raw=native.encode_inputs(data)
            self.assertEqual(n,count);self.assertEqual(len(raw),0x3000);self.assertEqual(data,saved)
            self.assertEqual(list(struct.unpack_from('<'+'i'*n,raw,0x1800)),data['parents'])
            self.assertEqual(list(struct.unpack_from('<5I',raw,0x1b00)),data['roles'])
            self.assertEqual(list(struct.unpack_from('<90d',raw,0x1c00)),data['rest'])
            self.assertEqual(list(struct.unpack_from('<30d',raw,0x2000)),data['grips'])
            self.assertEqual(raw[n*40:0x1800],bytes(0x1800-n*40))

    def test_invalid_shapes_types_and_overflow_are_rejected_before_memory_access(self):
        for mutate in (lambda d:d.update(extra=0),lambda d:d.update(poses=d['poses'][:4]),
                lambda d:d['poses'][0].append(0),lambda d:d['poses'][0].__setitem__(0,True),
                lambda d:d['poses'][0].__setitem__(0,1e300),lambda d:d['parents'].__setitem__(0,False),
                lambda d:d['roles'].__setitem__(0,-1),lambda d:d['rest'].pop(),
                lambda d:d['grips'].__setitem__(0,'1')):
            data=builder.invented_data();mutate(data)
            with self.assertRaises(ValueError):native.encode_inputs(data)

    def test_unreviewed_binary_rejected_before_parser_import(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'preparation image'):native.TargetPreparationOracle(raw)

    def test_machine_guards_exclude_startup_input_and_buffer_tails(self):
        machine=object.__new__(native.TargetPreparationOracle);machine.active=True;machine.work_size=5*48
        machine.on_code(None,native.ENTRY,1,None)
        for at,size in ((native.BASE+0x1000,1),(native.CODE_END,1),(native.CODE_END-1,2),(machine.INPUT,1)):
            with self.assertRaises(ValueError):machine.on_code(None,at,size,None)
        for at,size in ((machine.STACK,65536),(machine.WORK,240),(machine.OUTPUT,960)):
            machine.on_write(None,None,at,size,0,None)
        for at,size in ((machine.WORK+239,2),(machine.OUTPUT+959,2),(machine.INPUT,4),(native.BASE,1)):
            with self.assertRaises(ValueError):machine.on_write(None,None,at,size,0,None)
        machine.active=False
        with self.assertRaises(ValueError):machine.on_code(None,native.ENTRY,1,None)

    def test_checked_preparation_returns_compiled_values_not_reference(self):
        actual=[1e-8]*120;reference=[0]*120;data=builder.invented_data()
        machine=Mock();machine.prepare.return_value=(actual,self.receipt())
        result,receipt=native.checked_prepare(machine,data,reference)
        self.assertIs(result,actual);self.assertEqual(receipt['max_input_error'],1e-8)
        machine.prepare.assert_called_once_with(data);self.assertEqual(reference,[0]*120)

    def test_checked_preparation_rejects_partial_nonfinite_or_biased_inputs(self):
        for actual in (None,[],[0]*119,[0]*121,[True]*120,[float('nan')]*120,[float('inf')]*120,[3e-6]*120):
            machine=Mock();machine.prepare.return_value=(actual,self.receipt())
            with self.assertRaises(ValueError):native.checked_prepare(machine,{},[0]*120)

    def test_receipts_require_success_safety_and_honest_runtime_scope(self):
        good={**self.receipt(),'max_input_error':0};self.assertEqual(native.validate_receipt(good),0)
        for key,value in (('status',True),('status',1),('compiled_sha256','0'*64),('input_unchanged',False),
                ('failed_output_unchanged',False),('native_cdecl_preserved',False),('client_hook_implemented',True),
                ('game_started',True),('max_input_error',float('nan')),('max_input_error',True),('max_input_error',3e-6)):
            bad={**good,key:value}
            with self.assertRaises(ValueError):native.validate_receipt(bad)
        with self.assertRaises(ValueError):native.validate_receipt(None)

    def test_reference_preserves_rest_inputs_for_both_sides(self):
        for count in (5,9,64,128):
            for turned in (False,True):
                data=builder.invented_data(count,turned);saved=deepcopy(data);result=builder.reference_inputs(data)
                self.assertEqual(len(result),120);self.assertEqual(result[:45],data['rest'][:45])
                self.assertEqual(result[60:105],data['rest'][45:]);self.assertEqual(data,saved)

    def test_builder_refuses_existing_output_or_missing_compiler_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as process:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                process.assert_not_called();self.assertFalse((root/'fresh').exists())


if __name__=='__main__':unittest.main()
