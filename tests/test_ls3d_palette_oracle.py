"""Invented hierarchy/matrix fixtures, without commercial native code."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_palette_oracle import reference,product,local_matrix,PaletteOracle,START,STOP,PALETTE
from ls3d_palette_audit import pose,cases,audit,check_receipt
from ls3d_skin_audit import IDENTITY
from benelli_palette_audit import rest_poses,scenarios,audit as hands_audit
from benelli_fpv_rig_audit import HAND_PINS
from four_ds_skin import read_reviewed
from test_four_ds_skin import fixture


class PaletteTests(unittest.TestCase):
    def test_row_matrix_product_order_is_not_commutative(self):
        translation=IDENTITY.copy();translation[12]=2
        rotation=[0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1]
        self.assertEqual(product(translation,rotation)[12:15],[0,2,0])
        self.assertEqual(product(rotation,translation)[12:15],[2,0,0])

    def test_native_quaternion_direction_scale_and_position(self):
        matrix=local_matrix(pose(position=(1,2,3),rotation=(0,0,math.sqrt(.5),math.sqrt(.5)),scale=(2,.5,1)))
        self.assertAlmostEqual(matrix[1],-2,places=6);self.assertAlmostEqual(matrix[4],.5,places=6)
        self.assertEqual(matrix[12:16],[1,2,3,1])

    def test_native_identity_shortcut_does_not_normalize_quaternion(self):
        self.assertEqual(local_matrix(pose(rotation=(.001,0,0,1))),IDENTITY)

    def test_child_before_parent_and_parent_before_child_have_correct_world(self):
        forward=[pose(position=(1,0,0)),pose(0,position=(0,2,0))]
        reverse=[pose(1,position=(0,2,0)),pose(position=(1,0,0))]
        a=reference(forward,[IDENTITY]*2);b=reference(reverse,[IDENTITY]*2)
        self.assertEqual(a['world_matrices'][1][12:15],[1,2,0])
        self.assertEqual(a['world_matrices'],b['world_matrices'][::-1])

    def test_independent_roots_do_not_inherit_each_other(self):
        rows=reference([pose(position=(1,0,0)),pose(position=(0,2,0))],[IDENTITY]*2)['palette']
        self.assertEqual(rows[0][12:15],[1,0,0]);self.assertEqual(rows[1][12:15],[0,2,0])

    def test_inverse_bind_precedes_current_joint_world(self):
        inverse=IDENTITY.copy();inverse[12]=-1
        result=reference([pose(position=(1,0,0))],[inverse])
        self.assertEqual(result['palette'],[IDENTITY])

    def test_cycles_parent_bounds_shapes_scales_and_nonfinite_are_refused(self):
        for poses in ([],[pose(0)],[pose(1),pose(0)],[pose(True)],[pose(2)],
                      [pose(scale=(0,1,1))],[pose(scale=(-1,1,1))],[pose(position=(math.nan,0,0))],
                      [pose(rotation=(0,0,0,0))],[pose()]*65):
            with self.subTest(poses=poses),self.assertRaises(ValueError):reference(poses,[IDENTITY]*len(poses))
        with self.assertRaises(ValueError):reference([pose()],[])
        with self.assertRaises(ValueError):reference([pose(position=(10,0,0)),pose(0,position=(1,0,0))],[IDENTITY]*2)
        inverse=IDENTITY.copy();inverse[3]=1
        with self.assertRaises(ValueError):reference([pose()],[inverse])

    def test_reference_preserves_inputs(self):
        args=([pose(),pose(0)],[IDENTITY,IDENTITY]);before=deepcopy(args)
        reference(*args);self.assertEqual(args,before)

    def test_gpu_loader_missing_bone_and_matrix_recovery_paths_are_denied(self):
        machine=object.__new__(PaletteOracle);machine.phase='palette';machine.calls={}
        machine.on_code(None,START,4,None)
        for address,size in ((STOP,1),(0x10053385,1),(0x10053900,1),(0x1002c600,1),
                             (0x1002f220,1),(0x1002d9af,2)):
            with self.assertRaises(ValueError):machine.on_code(None,address,size,None)

    def test_only_exact_matrix_fields_flags_and_palette_can_be_written(self):
        machine=object.__new__(PaletteOracle);machine.phase='palette';machine.joints=2
        for address,size in ((PALETTE,4),(PALETTE+124,4),(machine.NODES+0x80,4),
                             (machine.NODES+0x364,4),(machine.STACK,4)):
            machine.on_write(None,None,address,size,0,None)
        for address,size in ((PALETTE+128,4),(machine.NODES+0xb0,4),(machine.NODES+0xc0,4),
                             (machine.NODES+0x400,4),(machine.NODES+0x8b,2),(machine.SOURCE,4)):
            with self.assertRaises(ValueError):machine.on_write(None,None,address,size,0,None)

    def test_synthetic_corpus_covers_64_joints_and_both_orders(self):
        rows=list(cases());self.assertEqual(len(rows),46)
        self.assertEqual(sum(len(p) for p,_ in rows),748)
        for row in rows:reference(*row)

    def test_receipts_reject_missing_nonfinite_and_wrong_matrices(self):
        class Invalid:
            def assemble(self,*args):return {'native_palette_match':True}
        with self.assertRaisesRegex(ValueError,'receipt'):audit(Invalid())
        row={**reference([pose()],[IDENTITY]),'joints':1,'native_palette_match':True,
             'inputs_preserved':True,'joint_only_palette_assembly_qualified':True,
             'loaded_scene_qualified':False,'animation_pose_selection_qualified':False,
             'gpu_called':False,'library_loaded':False,'game_started':False,
             'local_rotations_built':1,'matrix_products':1,'cached_ancestor_reuses':0,
             'max_errors':{'local_matrices':0,'world_matrices':0,'palette':0}}
        check_receipt(row,1)
        for key,value in (('joints',True),('palette',[]),('gpu_called',True),
                          ('max_errors',{'local_matrices':0,'world_matrices':0,'palette':math.nan})):
            with self.assertRaises(ValueError):check_receipt({**row,key:value},1)

    def test_private_hand_reader_maps_by_bone_id_and_diagnostics_do_not_change_rest(self):
        raw=fixture();skin=read_reviewed(raw);poses=rest_poses(raw,skin)
        self.assertEqual([p['parent'] for p in poses],[1,-1])
        result=reference(poses,skin['inverse_binds'])
        for matrix in result['palette']:
            self.assertLess(max(abs(a-b) for a,b in zip(matrix,IDENTITY)),1e-6)
        before=deepcopy(poses);rows=list(scenarios(raw,skin))
        self.assertEqual(len(rows),3);self.assertEqual(rows[0][1],before)

    def test_changed_or_missing_commercial_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Incomplete pinned'):hands_audit({},None,None)
        with self.assertRaisesRegex(ValueError,'Changed pinned'):hands_audit(dict.fromkeys(HAND_PINS,b''),None,None)


if __name__=='__main__':unittest.main()
