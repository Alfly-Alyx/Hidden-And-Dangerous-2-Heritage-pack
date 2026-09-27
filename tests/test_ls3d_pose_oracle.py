"""Invented pose references only; unit tests never read a commercial library."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ls3d_pose_oracle as pose
from ls3d_pose_audit import slot,quaternion,cases,audit


class PoseReferenceTests(unittest.TestCase):
    def setUp(self):self.initial={'position':[4,3,2],'rotation':[0,0,0,-1],'scale':[2,3,4]}

    def test_no_channels_preserve_current_pose_not_identity_or_implicit_rest(self):
        result=pose.reference(self.initial,[])
        self.assertEqual(result['pose'],self.initial);self.assertEqual(result['flags'],8)
        self.assertEqual(result['accumulation_counts'],dict.fromkeys(self.initial,0))

    def test_first_positive_slot_copies_even_with_small_weight(self):
        result=pose.reference(self.initial,[slot(('position',),weight=.0001,time=0)])
        self.assertEqual(result['pose']['position'],[0,0,0])
        self.assertEqual(result['pose']['rotation'],self.initial['rotation'])
        self.assertEqual(result['pose']['scale'],self.initial['scale'])

    def test_zero_weight_and_inactive_slots_are_skipped(self):
        self.assertEqual(pose.reference(self.initial,[slot(weight=0),slot(active=False)])['pose'],self.initial)

    def test_later_weights_blend_in_order_or_replace(self):
        first=slot(('position',),time=0);second=slot(('position',),weight=.25,time=80)
        forward=pose.reference(self.initial,[first,second])['pose']['position']
        self.assertEqual(forward,[.25,.5,.75])
        self.assertEqual(pose.reference(self.initial,[second,first])['pose']['position'],[0,0,0])
        second['weight']=2
        self.assertEqual(pose.reference(self.initial,[first,second])['pose']['position'],[1,2,3])

    def test_locked_position_remains_unchanged_without_preventing_other_channels(self):
        result=pose.reference(self.initial,[slot(time=0)],0x88)
        self.assertEqual(result['pose']['position'],self.initial['position'])
        self.assertEqual(result['pose']['scale'],[1,1,1]);self.assertEqual(result['flags'],0x40000088)

    def test_rotation_is_normalized_and_canonicalized_only_when_written(self):
        one=slot(('rotation',),time=120,angle=.028)
        result=pose.reference(self.initial,[one])
        self.assertLess(abs(sum(v*v for v in result['pose']['rotation'])-1),1e-7)
        self.assertGreater(result['pose']['rotation'][3],0)
        one['channels']['rotation']={'frames':[0],'values':[[0,0,0,-1]]}
        self.assertEqual(pose.reference(self.initial,[one])['pose']['rotation'],[0,0,0,1])

    def test_rotation_replacement_resets_accumulator_count_but_vectors_count_all(self):
        result=pose.reference(self.initial,[slot(weight=.5),slot(weight=.5),slot(weight=1)])
        self.assertEqual(result['accumulation_counts'],{'position':3,'rotation':1,'scale':3})

    def test_serialized_inputs_are_not_mutated(self):
        slots=[slot(),slot(weight=.25)];before=deepcopy((self.initial,slots))
        pose.reference(self.initial,slots)
        self.assertEqual((self.initial,slots),before)

    def test_unreviewed_flags_slots_keys_weights_and_shapes_are_refused(self):
        for flags in (0,True,0x108,0xffffffff):
            with self.assertRaises(ValueError):pose.reference(self.initial,[],flags)
        with self.assertRaises(ValueError):pose.reference(self.initial,[slot()]*9)
        for field,value in (('weight',-1),('weight',3),('active',1),('time',-1),('channels',{'event':{}})):
            item=slot();item[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):pose.reference(self.initial,[item])
        item=slot();item['channels']['rotation']={'frames':[0,1,2,3],'values':[[0,0,0,1]]*4}
        with self.assertRaises(ValueError):pose.reference(self.initial,[item])
        with self.assertRaises(ValueError):pose.normalize([0,0,0,0])

    def test_pose_allowlist_rejects_callbacks_extra_pose_and_matrix_fallback(self):
        machine=object.__new__(pose.PoseOracle);machine.phase='pose';machine.visited=set()
        machine.on_code(None,pose.POSE_START,1,None)
        for address in (pose.POSE_STOP,0x1001f446,0x1002f220,0x1001fc10,0x100305f8):
            with self.assertRaises(ValueError):machine.on_code(None,address,1,None)


class PoseAuditTests(unittest.TestCase):
    def test_synthetic_corpus_covers_all_eight_slots_and_boundaries(self):
        rows=list(cases())
        self.assertEqual(len(rows),586)
        self.assertTrue(any(len(slots)==8 for _,_,slots,_ in rows))
        self.assertEqual({flags for _,_,_,flags in rows},{8,0x88})
        for _,initial,slots,flags in rows:pose.reference(initial,slots,flags)

    def test_incomplete_or_engine_claiming_proof_is_rejected(self):
        class Incomplete:
            def apply(self,*args):return {'native_synthetic_pose_match':True,'game_started':True}
        with self.assertRaisesRegex(ValueError,'Incomplete'):audit(Incomplete())


if __name__=='__main__':unittest.main()
