"""Invented skin data only; native execution is a separate private audit."""
from copy import deepcopy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_skin_oracle import reference,SkinOracle,START,END
from ls3d_skin_audit import IDENTITY,cases,audit,check_receipt
from benelli_skin_audit import rest_palette,palettes,audit as hands_audit
from four_ds_skin import read_reviewed,audit_rest
from test_four_ds_skin import fixture
from benelli_fpv_rig_audit import HAND_PINS


class SkinTests(unittest.TestCase):
    def setUp(self):
        self.vertex=[1,2,3,1,0,0,.25,.75]
        self.translation=IDENTITY.copy();self.translation[12:15]=[4,-2,1]

    def test_zero_weight_is_rigid_and_one_based_last_bone_is_valid(self):
        self.assertEqual(reference([self.vertex],[[2,0]],[IDENTITY,self.translation],[0,1]),[[5,0,4,1,0,0]])

    def test_weight_255_still_has_one_256th_of_the_selected_bone(self):
        value=reference([self.vertex],[[1,255]],[self.translation],[0])[0]
        self.assertEqual(value[:3],[1+4/256,2-2/256,3+1/256])

    def test_parent_matrix_is_selected_from_current_bone_parent_byte(self):
        value=reference([self.vertex],[[2,128]],[self.translation,IDENTITY],[0,1])[0]
        self.assertEqual(value[:3],[3,1,3.5])

    def test_parent_zero_uses_original_vertex_without_recursion(self):
        value=reference([self.vertex],[[1,128]],[self.translation],[0])[0]
        self.assertEqual(value[:3],[3,1,3.5])

    def test_normals_have_no_translation_or_renormalization(self):
        matrix=self.translation.copy();matrix[0]=2
        value=reference([self.vertex],[[1,128]],[matrix],[0])[0]
        self.assertEqual(value[3:],[1.5,0,0])

    def test_normal_rotation_uses_same_basis_not_inverse_transpose(self):
        matrix=[0,2,0,0,-.5,0,0,0,0,0,1,0,0,0,0,1]
        value=reference([self.vertex],[[1,0]],[matrix],[0])[0]
        self.assertEqual(value,[ -1,2,3,0,2,0])

    def test_empty_input_and_unmodified_inputs(self):
        self.assertEqual(reference([],[],[IDENTITY],[0]),[])
        args=([self.vertex],[[1,128]],[self.translation],[0]);before=deepcopy(args)
        reference(*args);self.assertEqual(args,before)

    def test_invalid_bone_parent_byte_counts_and_values_refused(self):
        base=([self.vertex],[[1,0]],[IDENTITY],[0])
        for pair in ([0,0],[2,0],[1,256],[1,-1],[True,0],[1,False]):
            with self.subTest(pair=pair),self.assertRaises(ValueError):reference(base[0],[pair],base[2],base[3])
        for parents in ([],[2],[True]):
            with self.assertRaises(ValueError):reference(*base[:3],parents)
        with self.assertRaises(ValueError):reference([self.vertex]*2049,[[1,0]]*2049,[IDENTITY],[0])
        for at,value in ((0,math.nan),(1,math.inf),(2,11)):
            vertex=self.vertex.copy();vertex[at]=value
            with self.assertRaises(ValueError):reference([vertex],*base[1:])
        matrix=IDENTITY.copy();matrix[3]=1
        with self.assertRaises(ValueError):reference(*base[:2],[matrix],[0])
        with self.assertRaises(ValueError):reference(*base[:2],[IDENTITY]*65,[0]*65)

    def test_only_kernel_instructions_are_allowed(self):
        machine=object.__new__(SkinOracle);machine.phase='skin';machine.hits={}
        machine.on_code(None,START,1,None)
        for address,size in ((START-1,1),(END,1),(END-1,2),(0x10053900,1),(0x1002d830,1)):
            with self.assertRaises(ValueError):machine.on_code(None,address,size,None)

    def test_only_position_normal_and_stack_writes_are_allowed(self):
        machine=object.__new__(SkinOracle);machine.phase='skin';machine.vertex_count=2
        for at,size in ((machine.TARGET,4),(machine.TARGET+20,4),(machine.TARGET+32,4),(machine.STACK,4)):
            machine.on_write(None,None,at,size,0,None)
        for at,size in ((machine.SOURCE,4),(machine.TARGET-1,1),(machine.TARGET+24,4),
                        (machine.TARGET+23,2),(machine.TARGET+64,4),(machine.STACK+65535,2)):
            with self.assertRaises(ValueError):machine.on_write(None,None,at,size,0,None)

    def test_corpus_includes_all_blend_bytes_and_limits(self):
        rows=list(cases());self.assertEqual(len(rows),150)
        self.assertEqual(sum(len(r[0]) for r in rows),4376)
        self.assertEqual({p[1] for r in rows for p in r[1]},set(range(256)))
        for row in rows:reference(*row)

    def test_incomplete_nonfinite_or_bad_shape_receipts_refused(self):
        class Invalid:
            def deform(self,*args):return {'native_skin_kernel_match':True}
        with self.assertRaisesRegex(ValueError,'receipt'):audit(Invalid())
        row=dict(native_skin_kernel_match=True,inputs_preserved=True,uv_output_untouched=True,
            bone_index_base=1,blend_byte_divisor=256,normals_renormalized=False,
            matrix_palette_assembly_qualified=False,scene_loaded=False,library_loaded=False,
            game_started=False,engine_validated=False,max_error=0,vertices=1,values=[[0]*6],
            branches={'rigid':1,'parent_matrix':0,'parent_identity':0})
        check_receipt(row,1)
        for key,value in (('max_error',math.nan),('max_error',True),('values',[[0]*5]),
                          ('vertices',True),('values',[[0,0,math.nan,0,0,0]]),('branches',{})):
            with self.assertRaises(ValueError):check_receipt({**row,key:value},1)

    def test_reviewed_reader_exposes_one_based_pairs_and_keeps_report_private(self):
        data=read_reviewed(fixture());self.assertEqual(data['pairs'],[[1,0],[2,128],[1,255]])
        self.assertEqual(data['joint_node_indices'],[3,2])
        self.assertEqual(data['report'],audit_rest(fixture()))
        self.assertIsInstance(data['report']['vertices'],int)
        self.assertEqual(data['report']['vertex_bone_index_base'],1)
        self.assertNotIn('inverse_binds',data['report'])
        matrices=rest_palette(data)
        for matrix in matrices:
            self.assertLess(max(abs(a-b) for a,b in zip(matrix,IDENTITY)),1e-6)
        self.assertEqual(len(list(palettes(data))),5)

    def test_hands_audit_rejects_unpinned_sources_before_emulation(self):
        with self.assertRaisesRegex(ValueError,'Incomplete pinned'):hands_audit({},None)
        with self.assertRaisesRegex(ValueError,'Changed pinned'):hands_audit(dict.fromkeys(HAND_PINS,b''),None)


if __name__=='__main__':unittest.main()
