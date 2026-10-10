"""Pinned emulator entry shims and mutation-stop contracts, no game files."""
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_lifecycle_hooks as native
import build_native_hand_lifecycle_hooks as builder


class NativeHandLifecycleHooksTests(unittest.TestCase):
    def test_three_exact_whole_instruction_entry_patches(self):
        for site,(original,target,_) in native.SITES.items():
            raw=native.patch_bytes(site,original)
            self.assertEqual(len(raw),len(original));self.assertEqual(raw[0],0xe8)
            self.assertEqual(site+5+struct.unpack_from('<i',raw,1)[0],target)
            self.assertEqual(raw[5:],b'\x90'*(len(original)-5))

    def test_unreviewed_entry_or_mutable_original_refused(self):
        for site,original in ((True,b'x'),(native.ADD+1,native.SITES[native.ADD][0]),
                              (native.ADD,b'x'),(native.ADD,bytearray(native.SITES[native.ADD][0]))):
            with self.assertRaisesRegex(ValueError,'entry'):native.patch_bytes(site,original)

    def test_unknown_guard_image_refused_before_native_inputs(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'delivery image'):native.NativeHandLifecycleHooksOracle(None,None,None,raw)

    def test_patch_change_refuses_active_operation_before_memory(self):
        m=object.__new__(native.NativeHandLifecycleHooksOracle);m.phase='membership';m.setup_active=False;m.entries=[];m.uc=Mock()
        with self.assertRaisesRegex(ValueError,'Active'):m.set_patches(True)
        m.uc.mem_write.assert_not_called()

    def test_setup_argument_guard_precedes_cpu(self):
        m=object.__new__(native.NativeHandLifecycleHooksOracle);m.setup_active=False;m.phase=None;m.uc=Mock()
        for name,args in ((b'unknown',[]),(b'Hd2ConfigureLifecycleHooks',[0]),(b'Hd2ConfigureLifecycleHooks',[True,0])):
            with self.assertRaisesRegex(ValueError,'setup'):m.setup_call(name,args)
        m.uc.emu_start.assert_not_called()

    def test_trap_with_sentinel_instruction_size_stops_before_original_code(self):
        m=object.__new__(native.NativeHandLifecycleHooksOracle);m.collector=None;m.adapter=None
        m.phase='membership';m.entries=[{}];uc=Mock();uc.mem_read.return_value=b'\x0f\x0b'
        with self.assertRaises(native.LifecycleRefusal):m.on_code(uc,native.SITES[native.REMOVE][2],0xffffffff,None)
        m.entries=[]
        with self.assertRaisesRegex(ValueError,'Unexpected'):m.on_code(uc,native.SITES[native.REMOVE][2],0xffffffff,None)

    def test_guard_cannot_write_original_native_records(self):
        m=object.__new__(native.NativeHandLifecycleHooksOracle);m.collector=None;m.adapter=SimpleNamespace(mode=None,CONTEXT=0x4600000)
        m.guard_executing=True;m.setup_active=False
        m.on_write(None,None,m.STATE,20,0,None)
        for at,size in ((0x53000e8,2),(0x5700128,4),(m.STATE+19,2)):
            with self.assertRaisesRegex(ValueError,'outside'):m.on_write(None,None,at,size,0,None)

    def test_final_reference_and_nested_release_refused_before_cpu(self):
        m=object.__new__(native.NativeHandLifecycleHooksOracle);m.phase=None;m.pointers=[0x5300004];m.state={'refs':[1]};m.uc=Mock()
        for node in (0,True,-1):
            with self.assertRaisesRegex(ValueError,'release'):m.release_retained(node)
        m.uc.emu_start.assert_not_called()

    def test_builder_refuses_existing_output_or_missing_compiler_before_native_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=Mock()
            with patch.object(builder.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root,source,source,source)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh',source,source,source)
                source.read_bytes.assert_not_called();run.assert_not_called()


if __name__=='__main__':unittest.main()
