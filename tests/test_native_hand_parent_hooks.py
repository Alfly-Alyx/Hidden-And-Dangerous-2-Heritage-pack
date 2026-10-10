"""Invented forests and refusal contracts; no commercial binaries or game."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_parent_hooks as native
import build_native_hand_parent_hooks as builder


def fixture():
    return {0x1000:{'parent':0,'children':[0x2000,0x3000],'flags':0x11c},
            0x2000:{'parent':0x1000,'children':[0x4000],'flags':0x11c},
            0x3000:{'parent':0x1000,'children':[],'flags':0x11c},
            0x4000:{'parent':0x2000,'children':[],'flags':0x11c},
            0x5000:{'parent':0,'children':[],'flags':0x11c}}


class ParentReferenceTests(unittest.TestCase):
    def test_move_removes_non_head_and_prepends_destination_without_input_write(self):
        source=fixture();before=deepcopy(source)
        actual=native.reference_parent(source,0x3000,0x2000,0)
        self.assertEqual(source,before);self.assertEqual(actual[0x1000]['children'],[0x2000])
        self.assertEqual(actual[0x2000]['children'],[0x3000,0x4000]);self.assertEqual(actual[0x3000]['parent'],0x2000)
        self.assertEqual(actual[0x3000]['flags'],0x4000001c)

    def test_null_parent_detaches_and_clears_old_list(self):
        actual=native.reference_parent(fixture(),0x4000,0,0)
        self.assertEqual(actual[0x2000]['children'],[]);self.assertEqual(actual[0x4000]['parent'],0)
        self.assertEqual(actual[0x1000]['flags'],0x11c)

    def test_flag_two_invalidates_ancestors_without_moving_descendants(self):
        actual=native.reference_parent(fixture(),0x4000,0x5000,2)
        self.assertEqual(actual[0x1000]['flags'],0x1c);self.assertEqual(actual[0x2000]['flags'],0x1c)
        self.assertEqual(actual[0x5000]['flags'],0x1c);self.assertEqual(actual[0x3000]['flags'],0x11c)

    def test_same_parent_is_byte_state_noop(self):
        source=fixture();self.assertEqual(native.reference_parent(source,0x2000,0x1000,2),source)

    def test_move_with_children_preserves_subtree(self):
        actual=native.reference_parent(fixture(),0x2000,0x5000,0)
        self.assertEqual(actual[0x2000]['children'],[0x4000]);self.assertEqual(actual[0x4000],fixture()[0x4000])

    def test_new_cycles_unknown_flags_and_noninteger_arguments_refused(self):
        for frame,parent,flags in ((0x1000,0x4000,0),(0x2000,0x2000,0),(0x4000,0,1),(0x4000,0,4),
                                   (0x4000,0,True),(True,0,0),(0x4000,True,0),(0x4000,0x6000,0)):
            with self.assertRaises(ValueError):native.reference_parent(fixture(),frame,parent,flags)

    def test_malformed_backlinks_cycles_and_scene_flags_refused(self):
        mutations=[lambda t:t[0x2000].update(children=[]),lambda t:t[0x1000].update(children=[0x2000,0x2000]),
            lambda t:t[0x2000].update(children=[[]]),lambda t:t[0x2000].update(flags=-1),
            lambda t:t[0x2000].update(flags=0x40000),lambda t:t.update({0x2000:None}),
            lambda t:(t[0x1000].update(parent=0x4000),t[0x4000].update(children=[0x1000]))]
        for mutate in mutations:
            tree=fixture();mutate(tree)
            with self.assertRaises(ValueError):native.reference_parent(tree,0x3000,0,0)


class ParentNativeContractsTests(unittest.TestCase):
    def test_patch_replaces_six_complete_prologue_bytes(self):
        self.assertEqual(native.ORIGINAL,bytes.fromhex('558bec83e4f0'))
        self.assertEqual(len(native.PATCH),6);self.assertEqual(native.PATCH[-1],0x90)
        self.assertEqual(native.PARENT+5+struct.unpack_from('<i',native.PATCH,1)[0],native.ENTRY)

    def test_unknown_binary_refused_before_other_reads(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'parent interception image'):
                native.NativeHandParentHooksOracle(None,None,None,None,raw)

    def test_active_patch_and_setup_refused_before_cpu(self):
        m=object.__new__(native.NativeHandParentHooksOracle);m.phase='membership';m.parent_setup=False;m.setup_active=False;m.uc=Mock()
        with self.assertRaisesRegex(ValueError,'Active'):m.set_parent_patch(True)
        with self.assertRaisesRegex(ValueError,'setup'):m.setup_parent(b'Hd2ParentHookEntry',[])
        m.uc.mem_write.assert_not_called();m.uc.emu_start.assert_not_called()

    def test_native_world_preservation_and_scene_callback_ranges_are_excluded(self):
        m=object.__new__(native.NativeHandParentHooksOracle);m.parent_running=True;m.parent_executing=False
        m.collector=None;m.adapter=None
        for at in (0x1001d6b2,0x1001d7c3,0x1001d970,0x1001d988):
            with self.assertRaisesRegex(ValueError,'Unreviewed parent instruction'):m.on_code(None,at,1,None)

    def test_parent_trap_with_sentinel_size_never_forwards(self):
        m=object.__new__(native.NativeHandParentHooksOracle);m.parent_running=True;m.parent_saved={}
        m.collector=None;m.adapter=None
        cpu=Mock();cpu.mem_read.return_value=b'\x0f\x0b'
        with self.assertRaises(native.LifecycleRefusal):m.on_code(cpu,native.TRAP,0xffffffff,None)
        m.parent_saved=None
        with self.assertRaisesRegex(ValueError,'Unexpected'):m.on_code(cpu,native.TRAP,0xffffffff,None)

    def test_existing_output_and_missing_compiler_refused_before_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=Mock()
            with patch.object(builder.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root,source,source,source,source)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh',source,source,source,source)
                source.read_bytes.assert_not_called();run.assert_not_called()


if __name__=='__main__':unittest.main()
