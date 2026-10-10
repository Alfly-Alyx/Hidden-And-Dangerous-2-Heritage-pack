"""Bounded collection contracts without game resources or native execution."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_model_collect as native
import native_hand_model_binding as binding
import build_native_hand_model_collect as builder
from native_collected_hand_relay import CollectedHandRelayOracle
from hand_relay_audit import audit


class NativeHandModelCollectionTests(unittest.TestCase):
    def test_pinned_collection_rejects_other_images_before_imports(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'binding image'):native.HandModelCollectionOracle(raw)
        self.assertNotEqual(native.BINARY_SHA,binding.BINARY_SHA)

    def test_workspace_contains_private_pending_result_and_binding_workspace(self):
        self.assertEqual(native.WORK_SIZE,128*16+binding.OUTPUT_SIZE+binding.WORK_SIZE+2*128*4)
        self.assertLess(native.WORK_SIZE,native.HandModelCollectionOracle.WORK_MAP_SIZE)
        self.assertEqual(native.HandModelCollectionOracle.WORK_MAP_SIZE,0x3000)

    def test_all_vector_permutations_are_bijections(self):
        for count in (11,128):
            for order in builder.ORDERS:
                values=builder.permutation(count,order)
                self.assertEqual(sorted(values),list(range(count)))
        with self.assertRaises(ValueError):builder.permutation(11,'unknown')

    def test_invocation_requires_ten_args_and_excludes_standalone_binder(self):
        m=object.__new__(native.HandModelCollectionOracle);m.active=False
        entry=native.BASE+native.EXPORTS[b'Hd2CollectHandModelBinding']
        for at,args in ((entry,[0]*9),(entry,[True]*10),(entry,[-1]*10),
                        (native.BASE+native.EXPORTS[b'Hd2BuildHandModelBinding'],[0]*7)):
            with self.assertRaises(ValueError):m.invoke(at,args)
        with self.assertRaisesRegex(ValueError,'explicit owned'):m.bind(None,None)

    def test_write_guard_allows_full_workspace_but_no_native_model_or_vector(self):
        m=object.__new__(native.HandModelCollectionOracle);m.active=True;m.output_writes=0
        m.on_write(None,None,m.WORK+native.WORK_SIZE-4,4,0,None)
        for at,size in ((m.MODEL,4),(m.VECTOR,4),(m.NODES,4),(m.INPUT,4),
                        (m.WORK+native.WORK_SIZE-1,2),(m.OUTPUT+binding.OUTPUT_SIZE-1,2)):
            with self.assertRaises(ValueError):m.on_write(None,None,at,size,0,None)

    def test_late_vector_fault_runs_only_at_final_outer_recheck(self):
        m=object.__new__(native.HandModelCollectionOracle);m.active=True;m.calls={};m.injected=False
        m.late_fault=(m.VECTOR,0);uc=Mock()
        m.on_code(uc,native.BASE+0x1bd3,1,None);uc.mem_write.assert_not_called()
        m.on_code(uc,native.SNAPSHOT_CHECK,1,None);m.on_code(uc,native.SNAPSHOT_CHECK,1,None)
        uc.mem_write.assert_called_once_with(m.VECTOR,bytes(4));self.assertTrue(m.injected)

    def test_collector_fixture_guard_precedes_memory_access(self):
        m=object.__new__(native.HandModelCollectionOracle);m.active=False;m.uc=Mock()
        for args in ((0,0x170,m.VECTOR,44,[{}]*11),(m.MODEL,-1,m.VECTOR,44,[{}]*11),
                     (m.MODEL,0x170,True,44,[{}]*11),(m.MODEL,0x170,m.VECTOR,44,[{}]*10)):
            with self.assertRaisesRegex(ValueError,'fixture'):m.collect(*args)
        m.uc.mem_read.assert_not_called();m.uc.mem_write.assert_not_called()

    def test_relay_supplies_known_model_and_vector_extents(self):
        m=object.__new__(CollectedHandRelayOracle)
        m.binding=SimpleNamespace(collect=Mock(return_value=('result','order','receipt')))
        records=[object() for _ in range(11)]
        self.assertEqual(m.build_binding(records),('result','order','receipt'))
        m.binding.collect.assert_called_once_with(m.STATE+0x100,0x170,m.SOURCE+0x400,44,records)

    def test_audit_refuses_conflicting_modes_before_native_access(self):
        for options in ({'compiled_collection':b'x'},
                        {'compiled_collection':b'x','compiled_binding':b'y','scattered':True}):
            with self.assertRaisesRegex(ValueError,'requires the scattered'):audit(None,None,**options)

    def test_builder_refuses_existing_output_or_missing_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                run.assert_not_called();self.assertFalse((root/'fresh').exists())


if __name__=='__main__':unittest.main()
