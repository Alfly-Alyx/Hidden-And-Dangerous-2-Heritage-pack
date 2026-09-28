"""Invented byte buffers only; native executions are separate private audits."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_arm_pose_commit as commit
import build_native_arm_pose_commit as builder
import rigid_hand_transition_audit as transitions


class NativeArmPoseCommitTests(unittest.TestCase):
    def inputs(self):
        arena=bytearray(b'Z'*0x10000);offsets=[i*0x200 for i in range(6)]
        before=[[0,0,0,1] for _ in offsets];after=[[0,0,1,0] for _ in offsets];flags=[0x11c]*6
        for at,q in zip(offsets,before):
            struct.pack_into('<I',arena,at+0xf8,10);struct.pack_into('<I',arena,at+0xe0,0x11c)
            struct.pack_into('<4f',arena,at+0xc0,*q)
        return bytes(arena),offsets,before,after,flags

    def test_commit_changes_only_six_quaternions_and_their_dirty_flags(self):
        values=self.inputs();saved=deepcopy(values);result,status=commit.reference_commit(*values)
        self.assertEqual(status,0);allowed=set()
        for at in values[1]:
            self.assertEqual(struct.unpack_from('<4f',result,at+0xc0),(0,0,1,0))
            self.assertEqual(struct.unpack_from('<I',result,at+0xe0)[0],0x40000008)
            allowed.update(range(at+0xc0,at+0xd0));allowed.update(range(at+0xe0,at+0xe4))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(values[0],result))))
        self.assertEqual(values,saved)

    def test_last_snapshot_failure_keeps_every_earlier_record_unchanged(self):
        arena,at,old,new,flags=self.inputs();old[-1]=[0,0,0,-1]
        result,status=commit.reference_commit(arena,at,old,new,flags)
        self.assertEqual(status,5);self.assertEqual(result,arena)
        old[-1]=[0,0,0,1];flags[-1]|=1
        self.assertEqual(commit.reference_commit(arena,at,old,new,flags),(arena,3))

    def test_nonfinite_nonunit_and_callback_inputs_refused_without_changes(self):
        for q in ([0,0,0,0],[float('nan'),0,0,1],[0,0,float('inf'),1],[0,0,0,2]):
            arena,at,old,new,flags=self.inputs();new[-1]=q
            self.assertEqual(commit.reference_commit(arena,at,old,new,flags),(arena,4))
        arena,at,old,new,flags=self.inputs();data=bytearray(arena);flags[-1]|=0x200
        struct.pack_into('<I',data,at[-1]+0xe0,flags[-1]);arena=bytes(data)
        self.assertEqual(commit.reference_commit(arena,at,old,new,flags),(arena,3))

    def test_overlapping_unaligned_and_out_of_range_nodes_refused(self):
        for last in (0,0x10,0x201,0xfffffff0,0x10000-0x160):
            arena,at,old,new,flags=self.inputs();at[-1]=last
            self.assertEqual(commit.reference_commit(arena,at,old,new,flags),(arena,2))

    def test_refresh_propagates_to_descendants_not_unrelated_sibling(self):
        arena=bytearray(0x10000);parents=[-1,0,1,0]
        for i in range(4):
            struct.pack_into('<I',arena,i*0x200+0xe0,0x11c)
            struct.pack_into('<I',arena,i*0x200+0x164,0x18)
            struct.pack_into('<I',arena,i*0x200+0x104,7)
        struct.pack_into('<I',arena,0x200+0xe0,0x40000008)
        struct.pack_into('<I',arena,0xf000+0xe0,0x11c)
        struct.pack_into('<I',arena,0xf000+0x1d0,0x60000)
        result=commit.reference_refresh(bytes(arena),parents)
        read=lambda at:struct.unpack_from('<I',result,at)[0]
        self.assertEqual(read(0x200+0x164),0);self.assertEqual(read(0x400+0x164),0)
        self.assertEqual(read(0x600+0x164),0x18)
        self.assertEqual(read(0x200+0x104),8);self.assertEqual(read(0x400+0x104),8)
        self.assertEqual(read(0x600+0x104),7);self.assertEqual(read(0xf000+0x218),1)
        self.assertEqual(read(0xf000+0x1d0),0);self.assertEqual(read(0xf000+0xe0),0x4000001c)

    def test_image_and_code_guards_reject_unknown_startup_and_deferred_queue(self):
        with self.assertRaisesRegex(ValueError,'commit image'):commit.PersistentArmCommitOracle(b'',b'MZ')
        machine=object.__new__(commit.PersistentArmCommitOracle);machine.phase='arm_commit'
        machine.on_code(None,commit.ENTRY,1,None)
        for address in (commit.BASE+0x1000,commit.CODE_END,0x10020150):
            with self.assertRaises(ValueError):machine.on_code(None,address,1,None)
        machine.phase='joint_refresh';machine.on_code(None,commit.REFRESH,1,None)
        for address in (0x1001e750,0x100566d0,0x1008d41c):
            with self.assertRaises(ValueError):machine.on_code(None,address,1,None)

    def test_build_never_executes_for_existing_output_bad_library_or_missing_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as process:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root,b'')
                with self.assertRaisesRegex(ValueError,'LS3DF'):builder.build(root/'new',b'')
                with patch.object(builder,'verify_library'),patch.object(builder,'COMPILER',root/'absent.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'new',b'')
                process.assert_not_called();self.assertFalse((root/'new').exists())

    def test_transition_commit_requires_native_and_compiled_solver_before_reading_sources(self):
        with patch.object(transitions,'read_hands') as read:
            for native,solver in ((False,None),(True,None),(False,Path('missing'))):
                with self.assertRaisesRegex(ValueError,'requires native'):
                    transitions.audit(Path('game'),Path('banks'),'HandFPV_v10',{},native=native,
                                      compiled_solver=solver,compiled_commit=Path('missing'))
            read.assert_not_called()


if __name__=='__main__':unittest.main()
