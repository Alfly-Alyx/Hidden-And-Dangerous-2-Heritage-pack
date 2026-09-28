"""Contract checks use invented records only, never the game or native emulator."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_pipeline as native
import build_native_hand_pipeline as builder
from build_native_hand_targets import reference_inputs
from build_native_hand_constraints import reference_arm
from native_arm_pose_commit import reference_commit
from ls3d_math_oracle import f32


class NativeHandPipelineTests(unittest.TestCase):
    def receipt(self):
        return {'status':0,'compiled_sha256':native.BINARY_SHA,'compiled_calls':dict(native.EXPECTED_CALLS),
            'inputs_unchanged':True,'unrelated_arena_unchanged':True,'failed_arena_unchanged':True,
            'workspace_guard_unchanged':True,'native_cdecl_preserved':True,'shared_animation_arena':True,
            'client_hook_implemented':False,'game_started':False,'max_input_error':0}

    def test_unreviewed_image_refused_before_reading_parent_or_importing_emulator(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'pipeline image'):native.HandPipelineOracle(raw,parent=object())

    def test_invalid_abi_and_recursive_entry_refused_before_memory_access(self):
        machine=object.__new__(native.HandPipelineOracle);machine.active=False
        for mutate,kwargs in ((lambda d,a,o,r:(None,a,o,r),{}),
                (lambda d,a,o,r:(d,a[:-1],o,r),{}),(lambda d,a,o,r:(d,a,o[:-1],r),{}),
                (lambda d,a,o,r:(d,a,o,[True]*11),{}),(lambda d,a,o,r:(d,a,o,r),{'work_bytes':True}),
                (lambda d,a,o,r:(d,a,o,r),{'role_count':12})):
            args=mutate(*builder.invented_case())
            with self.assertRaises(ValueError):machine.correct(*args,**kwargs)
        machine.active=True
        with self.assertRaises(ValueError):machine.correct(*builder.invented_case())

    def test_instruction_and_write_guards_reject_startup_and_unrelated_memory(self):
        machine=object.__new__(native.HandPipelineOracle);machine.active=True;machine.calls={}
        machine.allowed=[(machine.ARENA+0xc0,machine.ARENA+0xd0)]
        machine.on_code(None,native.BASE+native.EXPORTS[b'Hd2CorrectHandPose'],1,None)
        self.assertEqual(machine.calls,{'Hd2CorrectHandPose':1})
        for at,size in ((native.BASE+0x1000,1),(native.BASE+0x1000+native.CODE_SIZE,1),(machine.INPUT,1)):
            with self.assertRaises(ValueError):machine.on_code(None,at,size,None)
        for at,size in ((machine.WORK,native.WORK_SIZE),(machine.STACK,65536),(machine.ARENA+0xc0,16)):
            machine.on_write(None,None,at,size,0,None)
        for at,size in ((machine.WORK+native.WORK_SIZE-1,2),(machine.ARENA,1),(machine.ARENA+0xcf,2),(machine.INPUT,1)):
            with self.assertRaises(ValueError):machine.on_write(None,None,at,size,0,None)

    def test_receipt_requires_all_four_compiled_stages_and_shared_memory(self):
        good=self.receipt();self.assertEqual(native.validate_receipt(good),0)
        for key,value in (('status',True),('status',34),('compiled_sha256','0'*64),('shared_animation_arena',False),
                ('inputs_unchanged',False),('failed_arena_unchanged',False),('workspace_guard_unchanged',False),
                ('client_hook_implemented',True),('game_started',True),('max_input_error',float('nan')),
                ('compiled_calls',{**native.EXPECTED_CALLS,'Hd2SolveArm':1}),
                ('compiled_calls',{**native.EXPECTED_CALLS,'Hd2CommitArms':True})):
            with self.assertRaises(ValueError):native.validate_receipt({**good,key:value})

    def test_invented_buffers_include_both_chains_and_maximum_count(self):
        for count in (11,128):
            data,arena,offsets,roles=builder.invented_case(count,True)
            self.assertEqual(len(arena),65536);self.assertEqual(len(data['poses']),count)
            self.assertEqual(roles[3],roles[6]);self.assertEqual(roles[4],roles[9])
            for i,at in enumerate(offsets):
                self.assertEqual(list(struct.unpack_from('<3f',arena,at+0xb0)),[f32(v) for v in data['poses'][i][:3]])
            with self.assertRaises(ValueError):builder.invented_case(10)

    def test_independent_reference_detects_pose_bias_and_unrelated_changes(self):
        for turned in (False,True):
            data,arena,offsets,roles=builder.invented_case(11,turned);saved=deepcopy(data);inputs=reference_inputs(data)
            quats=[q for s in range(2) for q in reference_arm(inputs[s*60:(s+1)*60],1 if s==0 else -1)]
            quats=[[f32(v if q[3]>=0 else -v) for v in q] for q in quats]
            arms=[offsets[i] for i in roles[5:]];before=[data['poses'][i][3:7] for i in roles[5:]]
            after,status=reference_commit(arena,arms,before,quats,[8]*6);self.assertEqual(status,0)
            self.assertLessEqual(builder.compare(data,arena,after,offsets,roles),2e-6);self.assertEqual(data,saved)
            bad=bytearray(after);bad[0]=1
            with self.assertRaises(ValueError):builder.compare(data,arena,bytes(bad),offsets,roles)
            bad=bytearray(after);struct.pack_into('<4f',bad,arms[-1]+0xc0,0,0,1,0)
            with self.assertRaises(ValueError):builder.compare(data,arena,bytes(bad),offsets,roles)

    def test_builder_refuses_existing_output_or_missing_compiler_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as process:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                process.assert_not_called();self.assertFalse((root/'fresh').exists())

    def test_shared_correction_refuses_detached_memory(self):
        machine=type('Detached',(),{'parent':None})()
        with self.assertRaisesRegex(ValueError,'share its arena'):native.correct_pipeline(None,None,None,None,machine)


if __name__=='__main__':unittest.main()
