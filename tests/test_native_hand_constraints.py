"""Invented buffers and mocked skeletons only; actual C runs in private audits."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_constraints as native
import build_native_hand_constraints as builder


class NativeHandConstraintTests(unittest.TestCase):
    def test_unreviewed_image_rejected_before_parsing_or_mapping(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'compiled arm image'):
                native.ArmSolverOracle(raw)

    def skin(self):
        identity=[[1,0,0],[0,1,0],[0,0,1]]
        nodes=[{'name':n,'index':i+1,'parent_id':i} for i,n in enumerate(
            ('a','Bip01 L Clavicle','Bip01 L UpperArm','Bip01 L Forearm','Bip01 L Hand'))]
        skin={'nodes':nodes,'rest_world':{i+1:(deepcopy(identity),p) for i,p in
            enumerate(([0,0,0],[0,0,0],[0,0,0],[.3,0,0],[.55,0,0]))}}
        target={'position':[.4,.1,.1],'rotation':deepcopy(identity),'pole':[0,.3,0]}
        return skin,target

    def test_input_layout_preserves_source_and_encodes_clavicle_parent_basis(self):
        skin,target=self.skin();before=deepcopy((skin,target));values=native.arm_input(skin,'L',target)
        self.assertEqual(len(values),60);self.assertEqual(values[9:12],[0,0,0])
        self.assertEqual(values[21:24],[.3,0,0]);self.assertEqual(values[33:36],[.55,0,0])
        self.assertEqual(values[45:48],target['position']);self.assertEqual(values[57:60],target['pole'])
        self.assertEqual((skin,target),before)

    def test_unreviewed_hierarchy_target_fields_or_orientation_are_rejected(self):
        for mutate in (lambda s,t:s['nodes'][2].update(parent_id=1),lambda s,t:s['nodes'][3].update(parent_id=1),
                       lambda s,t:t.update(extra=0),lambda s,t:t.update(position=[0,float('nan'),0]),
                       lambda s,t:t.update(rotation=[[-1,0,0],[0,1,0],[0,0,1]])):
            skin,target=self.skin();mutate(skin,target)
            with self.assertRaises(ValueError):native.arm_input(skin,'L',target)

    def test_invalid_abi_values_rejected_before_memory_access(self):
        machine=object.__new__(native.ArmSolverOracle);machine.active=False
        for values,side,kwargs in [([],1,{}),([0]*59,1,{}),([True]*60,1,{}),([0]*60,True,{}),
                                  ([0]*60,3,{}),([0]*60,1,{'count':True}),([0]*60,1,{'capacity':17})]:
            with self.assertRaises(ValueError):machine.solve(values,side,**kwargs)
        machine.active=True
        with self.assertRaises(ValueError):machine.solve([0]*60,1)

    def test_instruction_and_write_guards_exclude_startup_imports_input_and_output_tail(self):
        machine=object.__new__(native.ArmSolverOracle);machine.active=True;machine.visited=set()
        machine.on_code(None,machine.BASE+native.ENTRY_RVA,1,None)
        for address,size in ((machine.BASE+0x1000,1),(machine.BASE+0x1000+native.CODE_SIZE,1),
                             (machine.BASE+0x3000,1),(machine.INPUT,1)):
            with self.assertRaises(ValueError):machine.on_code(None,address,size,None)
        for address,size in ((machine.OUTPUT,96),(machine.STACK,65536)):
            machine.on_write(None,None,address,size,0,None)
        for address,size in ((machine.INPUT,8),(machine.OUTPUT+95,2),(machine.STACK-1,1),(machine.BASE,1)):
            with self.assertRaises(ValueError):machine.on_write(None,None,address,size,0,None)

    def test_comparison_accepts_quaternion_sign_but_refuses_drift_or_unrelated_changes(self):
        pose={'position':[0,0,0],'rotation':[0,0,0,1],'scale':[1,1,1]}
        original={n:deepcopy(pose) for n in [*native.ARM_NAMES,'invented_other']};result=deepcopy(original)
        for name in native.ARM_NAMES:result[name]['rotation']=[0,0,0,-1]
        machine=type('InventedSolver',(),{'raw_sha':'a'*64})()
        checker=native.ComparedCorrector(machine)
        with patch.object(native,'correct_compiled',return_value=(result,{})), \
             patch.object(native,'correct_reference',return_value=(original,{})):
            actual,_=checker(None,None,original,{})
            self.assertEqual(actual,result);self.assertEqual(checker.report()['compiled_arm_calls'],2)
            result[next(iter(native.ARM_NAMES))]['rotation']=[0,0,1,0]
            with self.assertRaisesRegex(ValueError,'rotations differ'):checker(None,None,original,{})
            result=deepcopy(original)
        with patch.object(native,'correct_compiled',return_value=(result,{})), \
             patch.object(native,'correct_reference',return_value=(original,{})):
            result['invented_other']['position'][0]=1
            with self.assertRaisesRegex(ValueError,'unrelated'):checker(None,None,original,{})

    def test_build_refuses_existing_output_or_unreviewed_compiler_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as process:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                process.assert_not_called();self.assertFalse((root/'fresh').exists())

    def test_independent_invented_reference_covers_rotated_parents_both_sides_and_unit_outputs(self):
        for turned in (False,True):
            for target in ((.35,.1,.1),(.12,.3,-.08),(-.25,.2,.1)):
                values=builder.invented_values(turned=turned,target=target);saved=values[:]
                for side in (1,-1):
                    result=builder.reference_arm(values,side);self.assertEqual(len(result),3)
                    for q in result:self.assertAlmostEqual(sum(v*v for v in q),1,places=12)
                self.assertEqual(values,saved)


if __name__=='__main__':unittest.main()
