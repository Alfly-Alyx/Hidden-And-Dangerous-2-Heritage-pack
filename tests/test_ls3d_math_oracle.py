"""Invented numerical and safety fixtures; no commercial DLL in this suite."""
import math
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import ls3d_math_oracle as native
import ls3d_math_audit as audit
from modern_animation import slerp as modern_slerp


class MathReferenceTests(unittest.TestCase):
    def test_native_basis_uses_opposite_active_quarter_turn(self):
        matrix=native.basis([0,0,math.sqrt(.5),math.sqrt(.5)])
        self.assertAlmostEqual(matrix[0][0],0,places=6)
        self.assertAlmostEqual(matrix[1][0],-1,places=6)
        self.assertAlmostEqual(matrix[0][1],1,places=6)

    def test_float32_identity_shortcut_is_not_silently_normalized(self):
        q=[0,0,math.sin(.00005),math.cos(.00005)]
        self.assertEqual(native.unit(q)[3],1)
        self.assertEqual(native.basis(q),[[1,0,0],[0,1,0],[0,0,1]])

    def test_linear_branch_preserves_nonunit_output_unlike_modern_preview(self):
        left=[0,0,0,1];right=[0,0,math.sin(.014),math.cos(.014)]
        result=native.interpolation(left,right,.5)
        self.assertEqual(result['branch'],'linear');self.assertFalse(result['result_normalized'])
        self.assertGreater(abs(sum(v*v for v in result['value'])-1),4e-5)
        self.assertAlmostEqual(sum(v*v for v in modern_slerp(left,right,.5)),1)

    def test_threshold_spherical_path_and_antipodes_are_explicit(self):
        left=[0,0,0,1]
        for angle,branch in ((.028,'linear'),(.029,'spherical'),(1,'spherical')):
            right=[0,0,math.sin(angle/2),math.cos(angle/2)]
            direct=native.interpolation(left,right,.25)
            opposite=native.interpolation(left,[-v for v in right],.25)
            self.assertEqual(direct['value'],opposite['value'])
            self.assertEqual(direct['branch'],branch)
            self.assertFalse(direct['right_antipode_selected']);self.assertTrue(opposite['right_antipode_selected'])

    def test_nonnumeric_nonfinite_nonunit_and_unbounded_inputs_are_refused(self):
        for bad in (True,math.nan,math.inf,1e100,10**400,'1'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):native.f32(bad)
        for bad in ([0,0,0],[0,0,0,0],[0,0,0,2],[0,False,0,1],[0,0,math.nan,1]):
            with self.subTest(bad=bad),self.assertRaises(ValueError):native.unit(bad)
        for amount in (-.001,1.001,True,math.nan):
            with self.assertRaises(ValueError):native.interpolation([0,0,0,1],[0,0,1,0],amount)

    def test_unreviewed_library_is_refused_before_dependency_or_engine_loading(self):
        for raw in (b'MZ invented',b'\0'*native.DLL_SIZE,None):
            with self.assertRaisesRegex(ValueError,'Unreviewed LS3DF'):native.MathOracle(raw)

    def test_commercial_key_rounding_domain_preserves_nonunit_values(self):
        value=[0,0,0,math.sqrt(1+1.1e-5)]
        result=native.unit(value)
        self.assertGreater(result[3],1);self.assertEqual(result[3],native.f32(value[3]))
        with self.assertRaises(ValueError):native.unit([0,0,0,math.sqrt(1+3e-5)])


class MathBoundaryTests(unittest.TestCase):
    def machine(self,phase='rotation'):
        machine=object.__new__(native.MathOracle)
        machine.phase=phase;machine.visited=set();machine.writes=((machine.OUTPUT,machine.OUTPUT+64),)
        return machine

    def test_instruction_edges_cross_phase_and_import_calls_fail_closed(self):
        machine=self.machine();machine.on_code(None,0x1002d260,4,None)
        self.assertIn(0x1002d260,machine.visited)
        for address,size in ((0x1002d28e,2),(0x1002ea40,1),(0x10090407,1),(0x70000000,1)):
            with self.subTest(address=address),self.assertRaisesRegex(ValueError,'Unreviewed math'):
                machine.on_code(None,address,size,None)
        machine.phase=None
        with self.assertRaises(ValueError):machine.on_code(None,0x1002d260,1,None)

    def test_only_current_output_and_stack_are_writable(self):
        machine=self.machine()
        machine.on_write(None,0,machine.OUTPUT+60,4,0,None)
        machine.on_write(None,0,machine.STACK,4,0,None)
        for address,size in ((machine.OUTPUT+63,2),(machine.INPUT,4),(native.BASE,4),(machine.STACK-1,2)):
            with self.subTest(address=address),self.assertRaisesRegex(ValueError,'bounded output'):
                machine.on_write(None,0,address,size,0,None)

    def test_nested_phase_and_invalid_flag_are_rejected_before_execution(self):
        machine=self.machine()
        with self.assertRaisesRegex(ValueError,'nested'):machine.run('rotation',[],[])
        with self.assertRaisesRegex(ValueError,'boolean'):machine.slerp([0,0,0,1],[0,0,0,1],.5,1)

    def test_budget_failure_clears_phase_and_write_permissions(self):
        machine=self.machine(None);machine.uc=Mock();machine.reg=Mock()
        machine.uc.reg_read.return_value=0
        with self.assertRaisesRegex(ValueError,'budget'):machine.run('rotation',[machine.OUTPUT,machine.INPUT],machine.writes)
        self.assertIsNone(machine.phase);self.assertEqual(machine.writes,())


class RotationSamplingTests(unittest.TestCase):
    def setUp(self):
        self.frames=[2,4,10];self.values=[[0,0,0,1],[0,0,math.sin(.5),math.cos(.5)],[0,0,1,0]]

    def test_integer_key_selection_holds_endpoints_and_selects_sparse_intervals(self):
        for time,indices,branch in ((0,[0],'held_first'),(79,[0],'held_first'),
                                    (80,[0,1],'spherical'),(159,[0,1],'spherical'),
                                    (160,[1,2],'spherical'),(399,[1,2],'spherical'),
                                    (400,[2],'held_last'),(401,[2],'held_last')):
            result=native.rotation_sample(self.frames,self.values,time)
            self.assertEqual(result['key_indices'],indices);self.assertEqual(result['branch'],branch)
            self.assertEqual(result['frame_index'],time//40)

    def test_fraction_uses_stored_float32_factor_not_exact_division_by_forty(self):
        result=native.rotation_sample(self.frames,self.values,80)
        self.assertGreater(result['fraction'],0)
        self.assertEqual(result['fraction'],native.f32((80*native.TIME_FACTOR-2)/2))
        self.assertNotEqual(result['value'],self.values[0])

    def test_single_key_maximum_time_and_long_curve_are_bounded(self):
        result=native.rotation_sample([2],[[0,0,0,1]],65535*40+39)
        self.assertEqual(result['value'],[0,0,0,1]);self.assertEqual(result['frame_index'],65535)
        result=native.rotation_sample(list(range(180)),[[0,0,0,1]]*180,178*40+20)
        self.assertEqual(result['key_indices'],[178,179]);self.assertEqual(result['branch'],'linear')

    def test_wraparound_unsorted_duplicate_or_oversized_channels_are_refused(self):
        for time in (-1,True,65536*40,.5):
            with self.assertRaises(ValueError):native.rotation_sample(self.frames,self.values,time)
        for frames,values in (([],[]),([0,0],self.values[:2]),([2,1],self.values[:2]),
                              ([0],self.values),([True],[self.values[0]]),
                              (list(range(181)),[self.values[0]]*181)):
            with self.assertRaises(ValueError):native.rotation_sample(frames,values,0)

    def test_track_stop_is_before_blending_and_unreviewed_helpers(self):
        machine=object.__new__(native.MathOracle);machine.phase='rotation_track';machine.visited=set()
        machine.on_code(None,0x1001f0fa,3,None)
        with self.assertRaises(ValueError):machine.on_code(None,native.TRACK_STOP,1,None)
        with self.assertRaises(ValueError):machine.on_code(None,0x10090407,1,None)


class VectorSamplingTests(unittest.TestCase):
    def test_sparse_vectors_hold_and_interpolate_without_normalization(self):
        frames=[2,4,10];values=[[1,2,3],[3,4,5],[-2,1,0]]
        self.assertEqual(native.vector_sample(frames,values,79)['value'],values[0])
        self.assertEqual(native.vector_sample(frames,values,400)['value'],values[-1])
        result=native.vector_sample(frames,values,120)
        self.assertEqual(result['key_indices'],[0,1]);self.assertEqual(result['branch'],'linear')
        for actual,expected in zip(result['value'],[2,3,4]):self.assertAlmostEqual(actual,expected,places=6)

    def test_fraction_remains_unstored_until_output_components(self):
        result=native.vector_sample([0,3],[[0,0,0],[1,2,3]],1)
        self.assertNotEqual(result['fraction'],native.f32(result['fraction']))
        self.assertEqual(result['fraction'],native.TIME_FACTOR/3)

    def test_single_key_and_even_dense_curve_remain_bounded(self):
        self.assertEqual(native.vector_sample([1],[[1,1,1]],65535*40+39)['value'],[1,1,1])
        self.assertEqual(native.vector_sample(list(range(180)),[[1,1,1]]*180,7179)['key_indices'],[179])

    def test_vector_shape_range_kind_and_key_domain_fail_closed(self):
        for value in ([1,2],[0,0,11],[0,0,math.nan],[False,1,1]):
            with self.assertRaises(ValueError):native.vector_sample([0],[value],0)
        with self.assertRaises(ValueError):native.vector_sample([1,0],[[1,1,1]]*2,0)
        with self.assertRaises(ValueError):native.vector_sample([0],[[1,1,1]],65536*40)
        machine=object.__new__(native.MathOracle)
        with self.assertRaises(ValueError):machine.sample_vector('unknown',[0],[[1,1,1]],0)

    def test_vector_instruction_ranges_cannot_enter_blending_or_rotation(self):
        for kind,(start,stop,_,_) in native.VECTOR_TRACKS.items():
            machine=object.__new__(native.MathOracle);machine.phase=kind+'_track';machine.visited=set()
            machine.on_code(None,start,3,None)
            for address in (stop,0x100302e0):
                with self.assertRaises(ValueError):machine.on_code(None,address,1,None)


if __name__=='__main__':unittest.main()
