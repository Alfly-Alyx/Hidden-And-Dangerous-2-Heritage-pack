"""Registered scatter bridge guards; no commercial inputs or native loading."""
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_scatter_hook as native
import native_scattered_hand_relay as relay
import native_hand_relay as dense
import build_native_hand_scatter_hook as builder
from ls3d_attach_oracle import AttachOracle


class NativeScatterHookTests(unittest.TestCase):
    def test_binary_pin_and_extended_export_contract(self):
        for raw in (None,b'',b'MZ'+bytes(native.BINARY_SIZE-2),bytearray(native.BINARY_SIZE)):
            with self.assertRaisesRegex(ValueError,'scatter image'):native.HandScatterHookOracle(raw)
        self.assertEqual(native.ENTRY+41,native.CODE_END)
        self.assertIn(b'Hd2ConfigureHandHook',native.EXPORTS)
        self.assertIn(b'Hd2CorrectScatteredHandPose',native.EXPORTS)

    def test_scatter_patch_only_accepts_its_own_compiled_entry(self):
        data=relay.scatter_relay_patch(dense.HOOK_ORIGINAL)
        self.assertEqual(len(data),6);self.assertEqual(data[-1],0x90)
        self.assertEqual(dense.HOOK_SITE+5+struct.unpack_from('<i',data,1)[0],native.ENTRY)
        with self.assertRaises(ValueError):relay.scatter_relay_patch(dense.HOOK_ORIGINAL,target=dense.ENTRY)
        with self.assertRaises(ValueError):relay.scatter_relay_patch(b'changed')

    def test_reseed_refuses_live_registered_pointer(self):
        m=object.__new__(native.HandScatterHookOracle);m.mode=None;m.uc=Mock();m.uc.mem_read.return_value=b'\1\0\0\0'
        with self.assertRaisesRegex(ValueError,'Unregister'):m.seed(None,None,None,None)
        m.uc.mem_write.assert_not_called()

    def test_invalid_or_nested_adapter_invocation_is_rejected(self):
        m=object.__new__(native.HandScatterHookOracle);m.mode=None;m.active=False;m.count=11
        for kwargs in ({'registered':1},{'other_model':1},{'control':True},{'control':0}):
            with self.assertRaises(ValueError):m.invoke_adapter(**kwargs)
        m.active=True
        with self.assertRaises(ValueError):m.invoke_adapter()
        m.active=False;m.count=0
        with self.assertRaises(ValueError):m.invoke_adapter()

    def test_configuration_write_guard_excludes_nodes_work_and_overflow(self):
        m=object.__new__(native.HandScatterHookOracle);m.mode='configure';m.phase_writes=[(native.ACTIVE,native.ACTIVE+4)]
        m.on_write(None,None,native.ACTIVE,4,0,None)
        for at,size in ((native.ACTIVE+3,2),(m.WORK,4),(m.NODES+0xc0,4),(m.INPUT,4)):
            with self.assertRaisesRegex(ValueError,'phase'):m.on_write(None,None,at,size,0,None)

    def test_separate_pages_are_not_in_logical_or_index_order(self):
        m=object.__new__(relay.ScatteredHandRelayOracle);m.adapter=SimpleNamespace(NODES=0x4000000)
        addresses=m.node_addresses([i*512 for i in range(128)])
        self.assertEqual(len(set(addresses)),128)
        self.assertTrue(all(at%16==4 for at in addresses))
        self.assertNotEqual(addresses,sorted(addresses))

    def test_external_page_guards_detect_prefix_suffix_and_owner_changes(self):
        m=object.__new__(relay.ScatteredHandRelayOracle);m.uc=Mock();seed=b'Z'*4096
        m.adapter=SimpleNamespace(pages=[0x4000000],blocks=[seed]);m.owner_seed=seed
        m.uc.mem_read.side_effect=[seed,seed[0x240:]];m.check_external_guards()
        for at in (0,0x174,4095):
            changed=bytearray(seed);changed[at]=0;m.uc.mem_read.side_effect=[bytes(changed)]
            with self.assertRaisesRegex(ValueError,'node page'):m.check_external_guards()
        m.uc.mem_read.side_effect=[seed,bytes(4096-0x240)]
        with self.assertRaisesRegex(ValueError,'owning-visual'):m.check_external_guards()

    def test_snapshot_reader_must_be_callable_before_state_access(self):
        m=object.__new__(AttachOracle)
        with self.assertRaisesRegex(ValueError,'snapshot reader'):
            m.check_state(None,None,None,None,None,None,node_flag_reader=1)

    def test_build_refuses_existing_output_or_unavailable_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                run.assert_not_called();self.assertFalse((root/'fresh').exists())

    def test_native_console_requires_exact_success_and_no_stderr(self):
        path=Path(builder.PROBE_NAME)
        for stdout,stderr in (('PASS: partial',''),('', ''),(builder.PROBE_MESSAGE,'error')):
            with patch.object(builder.subprocess,'run',return_value=SimpleNamespace(stdout=stdout,stderr=stderr,returncode=0)) as run:
                with self.assertRaisesRegex(ValueError,'confirm success'):builder.run_probe(path)
                self.assertEqual(run.call_args.kwargs['timeout'],30)
        with patch.object(builder.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'Unreviewed'):builder.run_probe(Path('unknown.exe'))
            run.assert_not_called()


if __name__=='__main__':unittest.main()
