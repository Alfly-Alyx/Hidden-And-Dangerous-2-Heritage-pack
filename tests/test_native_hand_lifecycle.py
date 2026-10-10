"""Explicit lifecycle retirement contracts, no game or native input required."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_lifecycle as native
import build_native_hand_lifecycle as builder


class NativeHandLifecycleTests(unittest.TestCase):
    def test_unreviewed_guard_image_rejected_before_registry_or_parser(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'lifecycle image'):native.HandLifecycleOracle(None,raw)

    def test_state_has_two_pointers_and_three_monotonic_metadata_fields(self):
        self.assertEqual(native.STATE_SIZE,2*4+3*4)
        self.assertEqual(native.ARGUMENTS,{b'Hd2WatchHandContext':4,b'Hd2BeforeHandModelChange':5,b'Hd2HandLifecycleSize':0})

    def test_invalid_invocation_cannot_start_cpu(self):
        m=object.__new__(native.HandLifecycleOracle);m.mode=None;m.active=False;m.uc=Mock()
        for name,args in ((b'unknown',[]),(b'Hd2WatchHandContext',[]),(b'Hd2BeforeHandModelChange',[True]*5),
                          (b'Hd2BeforeHandModelChange',[-1]*5)):
            with self.assertRaisesRegex(ValueError,'invocation'):m.invoke_guard(name,args)
        m.mode='hook'
        with self.assertRaises(ValueError):m.invoke_guard(b'Hd2HandLifecycleSize',[])
        m.uc.emu_start.assert_not_called()

    def test_instruction_guard_excludes_startup_correction_callback_and_solver(self):
        m=object.__new__(native.HandLifecycleOracle);m.mode='lifecycle';m.calls={}
        m.on_code(None,native.BASE+native.EXPORTS[b'Hd2BeforeHandModelChange'],1,None)
        m.on_code(None,native.CONFIGURE,1,None)
        self.assertEqual(m.calls,{'Hd2BeforeHandModelChange':1,'Hd2ConfigureHandHook':1})
        for at in (native.BASE+0x1000,native.CODE_END,native.HOOK_BASE+0x54b1,native.HOOK_BASE+0x10ab):
            with self.assertRaisesRegex(ValueError,'instruction'):m.on_code(None,at,1,None)

    def test_write_guard_never_accepts_native_objects_or_context_identity(self):
        m=object.__new__(native.HandLifecycleOracle);m.mode='lifecycle'
        for at,size in ((m.STATE,native.STATE_SIZE),(native.ACTIVE,4),(m.CONTEXT+44,8)):
            m.on_write(None,None,at,size,0,None)
        for at,size in ((m.NODES+0xe4,2),(m.MODEL+0x128,4),(m.CONTEXT,4),(m.INPUT,4),(m.STATE+19,2)):
            with self.assertRaisesRegex(ValueError,'write'):m.on_write(None,None,at,size,0,None)

    def test_probe_rejects_active_state_before_restricting_memory(self):
        m=object.__new__(native.HandLifecycleOracle);m.state=Mock(return_value=(1,2,3,4,5));m.uc=Mock()
        with self.assertRaisesRegex(ValueError,'retired'):m.retired_callback_probe()
        m.uc.mem_protect.assert_not_called()

    def test_probe_restores_permissions_even_if_inactive_callback_fails(self):
        m=object.__new__(native.HandLifecycleOracle);m.state=Mock(return_value=(0,0,1,3,1));m.uc=Mock()
        m.uc.mem_read.return_value=bytes(4);m.pages=[0x4000000,0x4002000]
        m.uni=Mock(UC_PROT_READ=1,UC_PROT_WRITE=2);m.invoke_adapter=Mock(side_effect=ValueError('probe failed'))
        with self.assertRaisesRegex(ValueError,'probe failed'):m.retired_callback_probe()
        for page,permission in ((m.CONTEXT,3),(m.INPUT,1),(0x4000000,3),(0x4002000,3)):
            m.uc.mem_protect.assert_any_call(page,4096,0);m.uc.mem_protect.assert_any_call(page,4096,permission)

    def test_explicit_events_use_owned_state_and_the_pinned_configuration_entry(self):
        m=object.__new__(native.HandLifecycleOracle);m.invoke_guard=Mock(return_value=0)
        m.watch();m.invoke_guard.assert_called_with(b'Hd2WatchHandContext',[m.STATE,20,m.CONTEXT,native.CONFIGURE])
        m.event(0xdeadbeec,0,3)
        m.invoke_guard.assert_called_with(b'Hd2BeforeHandModelChange',[m.STATE,20,0xdeadbeec,0,3])

    def test_builder_refuses_existing_output_or_missing_compiler_before_reading_hook(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);hook=Mock()
            with patch.object(builder.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root,hook)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh',hook)
                hook.read_bytes.assert_not_called();run.assert_not_called();self.assertFalse((root/'fresh').exists())


if __name__=='__main__':unittest.main()
