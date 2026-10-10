"""Model membership and caller-reference contracts, no commercial inputs."""
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_model_membership as native


def empty(count=11):
    return {'models':[{'slots':[None]*128,'count':0} for _ in range(2)],'owners':[None]*count,'refs':[1]*count}


class NativeModelMembershipTests(unittest.TestCase):
    def test_library_pin_precedes_mapping_and_compiled_image(self):
        with self.assertRaisesRegex(ValueError,'LS3DF'):native.ModelMembershipOracle(b'not a library',None)

    def test_add_keeps_input_and_increments_only_membership_reference(self):
        state=empty();saved=deepcopy(state);result,status=native.reference_operation(state,'add',0,3)
        self.assertIsNone(status);self.assertEqual(state,saved)
        self.assertEqual(result['models'][0]['slots'][0],3);self.assertEqual(result['refs'][3],2)
        self.assertEqual(result['owners'][3],0)

    def test_remove_fills_gap_from_last_and_preserves_stale_tail(self):
        state=empty()
        for node in (2,5,8):state,_=native.reference_operation(state,'add',0,node)
        result,status=native.reference_operation(state,'remove',0,2)
        self.assertEqual(status,0);self.assertEqual(result['models'][0]['count'],2)
        self.assertEqual(result['models'][0]['slots'][:3],[8,5,8])
        self.assertEqual(result['refs'][2],1);self.assertIsNone(result['owners'][2])

    def test_cross_model_transfer_preserves_caller_reference_and_removes_old_owner(self):
        state,_=native.reference_operation(empty(),'add',0,3)
        state,_=native.reference_operation(state,'add',1,3)
        self.assertEqual(state['models'][0]['count'],0);self.assertEqual(state['models'][1]['slots'][0],3)
        self.assertEqual(state['refs'][3],2);self.assertEqual(state['owners'][3],1)

    def test_readding_same_model_at_full_capacity_is_bounded_reorder(self):
        state=empty(128)
        for i in range(128):state,_=native.reference_operation(state,'add',0,i)
        state,_=native.reference_operation(state,'add',0,64)
        self.assertEqual(state['models'][0]['count'],128)
        self.assertEqual(state['models'][0]['slots'][64],127);self.assertEqual(state['models'][0]['slots'][127],64)
        self.assertEqual(state['refs'],[2]*128)

    def test_absent_remove_is_unchanged_and_reports_native_error(self):
        state=empty();result,status=native.reference_operation(state,'remove',0,0)
        self.assertEqual(status,native.NOT_FOUND);self.assertEqual(result,state)

    def test_unreviewed_scalars_capacity_and_reference_overflow_refused(self):
        for args in (('add',True,0),('add',0,True),('add',0,-1),('add',2,0),('clear',0,0)):
            with self.assertRaises(ValueError):native.reference_operation(empty(),*args)
        state=empty(129)
        for i in range(128):state,_=native.reference_operation(state,'add',0,i)
        with self.assertRaisesRegex(ValueError,'allocation'):native.reference_operation(state,'add',0,128)
        state=empty();state['refs'][0]=32767
        with self.assertRaisesRegex(ValueError,'reference'):native.reference_operation(state,'add',0,0)

    def test_final_release_is_rejected_before_emulated_memory_access(self):
        m=object.__new__(native.ModelMembershipOracle);m.phase=None;m.collector=SimpleNamespace(active=False)
        m.state=empty();m.state['models'][0]['slots'][0]=0;m.state['models'][0]['count']=1;m.state['owners'][0]=0
        m.check_pages=Mock()
        with self.assertRaisesRegex(ValueError,'Final native release'):m.operation('remove',0,0)
        m.check_pages.assert_not_called()

    def test_instruction_guard_excludes_allocator_destructor_and_zero_reference_branch(self):
        m=object.__new__(native.ModelMembershipOracle);m.collector=None;m.phase='membership';m.calls={}
        m.on_code(None,native.ADD,1,None);self.assertEqual(m.calls,{'add':1})
        for address in (0x100341e6,0x1008d41c,0x10019dc0,0x1001c38f):
            with self.assertRaisesRegex(ValueError,'instruction'):m.on_code(None,address,1,None)

    def test_write_guard_cannot_change_parent_link_or_name(self):
        m=object.__new__(native.ModelMembershipOracle);m.collector=None;m.phase='membership'
        m.writes=((0x5300104,0x5300108),(0x53000e8,0x53000ea))
        m.on_write(None,None,0x5300104,4,0,None)
        for address in (0x530010c,0x53000ec,0x5300107):
            with self.assertRaisesRegex(ValueError,'write'):m.on_write(None,None,address,4,0,None)


if __name__=='__main__':unittest.main()
