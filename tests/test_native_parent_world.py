"""Invented affine forests and conservative native receipts, no game files."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_palette_oracle import local_matrix,product
import native_parent_world as world
import audit_native_parent_world as audit


def matrix(angle=0,scale=1,position=None):
    return local_matrix({'rotation':[0,0,math.sin(angle/2),math.cos(angle/2)],'scale':[scale]*3,'position':position or [0,0,0]})


def receipts():
    result=[]
    for case in audit.CASES:
        for turned in (False,True):
            for patched in (False,True):
                for flags in (1,3):
                    changed=case!='same_parent';calls=dict(audit.EXPECTED_CALLS[case])
                    result.append({'case':case,'turned':turned,'patched':patched,'flags':flags,'changed':changed,
                        'all_world_transforms_preserved':True,'unrelated_bytes_and_membership_unchanged':True,
                        'native_image_fully_restored':True,'native_immediate_refresh_executed':False,'scene_notifications_executed':False,
                        'native_allocator_or_destructor_executed':False,'game_started':False,'game_modified':False,'hand_correction_executed':False,
                        'live_model_lifetime_qualified':False,'moved_quaternion_left_stale_by_native_matrix_path':changed,
                        'fourth_scale_slot_is_nonsemantic_copied_padding':changed,'parent_prologue_checks':int(patched),
                        'compiled_parent_notifications':int(patched),'native_calls':calls,'native_world_cache_objects':calls.get('world_cache',0),
                        'max_errors':{k:0 for k in audit.ERRORS}})
    return result


class NativeParentWorldTests(unittest.TestCase):
    def test_inverse_uniform_rotation_scale_and_translation(self):
        source=matrix(.3,1.125,[.25,-.1,.5]);identity=product(source,world.inverse_uniform(source))
        self.assertLess(max(abs(a-b) for a,b in zip(identity,matrix())),1e-6)

    def test_nonuniform_reflected_sheared_and_nonfinite_matrices_refused(self):
        for offset,value in ((0,2),(0,-1),(1,.2),(5,float('nan')),(15,0),(0,True)):
            source=matrix();source[offset]=value
            with self.assertRaises(ValueError):world.inverse_uniform(source)
        with self.assertRaises(ValueError):world.inverse_uniform([0]*16)

    def test_world_target_preserves_entire_moved_subtree(self):
        tree={0x1000:{'parent':0,'children':[0x2000],'flags':8},0x2000:{'parent':0x1000,'children':[0x3000],'flags':8},
              0x3000:{'parent':0x2000,'children':[],'flags':8},0x4000:{'parent':0,'children':[],'flags':8}}
        locals={p:matrix(.05*i,1+.05*i,[.02*i,0,0]) for i,p in enumerate(tree)}
        old=deepcopy(locals);updated,target,before=world.world_target(tree,locals,0x2000,0x4000)
        self.assertEqual(locals,old);locals[0x2000]=target;after=world.world_matrices(updated,locals)
        self.assertLess(max(abs(a-b) for p in tree for a,b in zip(before[p],after[p])),1e-6)

    def test_empty_mismatched_and_cyclic_forests_refused(self):
        with self.assertRaises(ValueError):world.world_matrices({}, {})
        with self.assertRaises(ValueError):world.world_matrices({0x1000:{}},{})
        tree={0x1000:{'parent':0x1000,'children':[0x1000],'flags':8}}
        with self.assertRaises(ValueError):world.world_matrices(tree,{0x1000:matrix()})

    def test_complete_receipts_distinguish_native_work_guard_and_noop(self):
        result=audit.summarize(receipts())
        self.assertEqual((result['scenarios'],result['changed_operations'],result['no_op_operations'],result['guarded_operations']),(32,24,8,16))
        self.assertEqual(result['native_calls']['world_cache'],104);self.assertEqual(result['native_calls']['inverse_matrix'],16)

    def test_duplicate_missing_or_untyped_receipts_refused(self):
        rows=receipts()
        with self.assertRaises(ValueError):audit.summarize(rows[:-1])
        rows[-1]=deepcopy(rows[0])
        with self.assertRaises(ValueError):audit.summarize(rows)
        for key,value in (('patched',1),('flags',True),('parent_prologue_checks',False),('native_world_cache_objects',True)):
            rows=receipts();rows[0][key]=value
            with self.assertRaises(ValueError):audit.summarize(rows)

    def test_overclaims_nonfinite_errors_and_wrong_native_counts_refused(self):
        for key,value in (('game_started',True),('live_model_lifetime_qualified',True),('native_image_fully_restored',False),
                          ('compiled_parent_notifications',1),('fourth_scale_slot_is_nonsemantic_copied_padding',False)):
            rows=receipts();rows[0][key]=value
            with self.assertRaises(ValueError):audit.summarize(rows)
        for value in (float('nan'),True,-1,.1):
            rows=receipts();rows[0]['max_errors']['preserved_world']=value
            with self.assertRaises(ValueError):audit.summarize(rows)
        rows=receipts();rows[0]['native_calls']['inverse_matrix']=0
        with self.assertRaises(ValueError):audit.summarize(rows)

    def test_parent_world_flags_refused_before_memory(self):
        m=object.__new__(world.NativeParentWorldOracle);m.phase=None;m.uc=Mock()
        for flags in (0,2,True,5):
            with self.assertRaises(ValueError):m.world_reparent(0x1000,0,flags)
        m.uc.mem_write.assert_not_called()

    def test_existing_destination_refused_before_private_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            source=Mock()
            with self.assertRaisesRegex(ValueError,'already exists'):audit.audit(Path(directory),source,source,source,source,source)
            source.read_bytes.assert_not_called()


if __name__=='__main__':unittest.main()
