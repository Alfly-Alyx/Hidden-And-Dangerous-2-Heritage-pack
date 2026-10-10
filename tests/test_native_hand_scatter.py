"""Synthetic scatter ABI/guard contracts, independent of commercial files."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_scatter as native
import build_native_hand_scatter as builder


class NativeHandScatterTests(unittest.TestCase):
    def test_unreviewed_binary_rejected_before_parsing_or_emulation(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'scatter image'):native.HandScatterOracle(raw)

    def test_layout_workspace_size_and_six_arm_selection(self):
        self.assertEqual(native.WORK_SIZE,128*0x170+128*10*4+4*128*4+942*8)
        for count in (11,128):
            data,arena,offsets,roles=builder.invented_case(count)
            self.assertEqual(len({((i*37)%128) for i in range(count)}),count)
            self.assertEqual(len(set(roles[5:])),6)

    def test_invalid_or_nested_entries_and_argument_scalars_refused(self):
        m=object.__new__(native.HandScatterOracle);m.active=False
        entry=native.BASE+native.EXPORTS[b'Hd2CorrectScatteredHandPose']
        for address,args in ((native.BASE+0x1000,[]),(entry,[]),(entry,[True]*10),(entry,[-1]*10),(entry,[0x100000000]*10)):
            with self.assertRaises(ValueError):m.invoke(address,args)
        m.active=True
        with self.assertRaisesRegex(ValueError,'nested'):m.invoke(entry,[0]*10)

    def test_instruction_guard_excludes_startup_padding_and_unmapped_code(self):
        m=object.__new__(native.HandScatterOracle);m.active=True;m.calls={};m.return_to_scatter=None;m.late_mutation=None
        m.on_code(None,native.BASE+native.EXPORTS[b'Hd2SolveArm'],1,None)
        self.assertEqual(m.calls,{'Hd2SolveArm':1})
        for at,size in ((native.BASE+0x1000,1),(native.CODE_END,1),(native.CODE_END-1,2),(m.INPUT,1)):
            with self.assertRaises(ValueError):m.on_code(None,at,size,None)
        m.active=False
        with self.assertRaises(ValueError):m.on_code(None,native.BASE+native.EXPORTS[b'Hd2SolveArm'],1,None)

    def test_write_guard_counts_native_writes_and_rejects_gap_or_workspace_overflow(self):
        m=object.__new__(native.HandScatterOracle);m.active=True;m.native_writes=0;m.allowed=[(m.NODES+0xc0,m.NODES+0xd0)]
        m.on_write(None,None,m.WORK,native.WORK_SIZE,0,None)
        self.assertEqual(m.native_writes,0)
        m.on_write(None,None,m.NODES+0xc0,4,0,None);self.assertEqual(m.native_writes,1)
        for at,size in ((m.WORK+native.WORK_SIZE-1,2),(m.NODES+0xcf,2),(m.NODES+0x1000,1),(m.INPUT,4)):
            with self.assertRaises(ValueError):m.on_write(None,None,at,size,0,None)

    def test_unreviewed_diagnostic_switches_refused_before_memory(self):
        m=object.__new__(native.HandScatterOracle);m.active=False
        for kwargs in ({'alignment':True},{'alignment':1},{'case':'anything'}):
            with self.assertRaisesRegex(ValueError,'switch'):m.correct(None,None,None,None,**kwargs)

    def test_late_fault_occurs_once_only_at_pipeline_return(self):
        m=object.__new__(native.HandScatterOracle);m.active=True;m.calls={}
        at=native.BASE+0x5100;m.return_to_scatter=at;m.late_mutation=(0x40000,b'abcd');m.pages=[0x40000]
        m.injected=False;m.uc=Mock();m.uc.mem_read.return_value=b'page'
        m.on_code(m.uc,at-1,1,None);m.uc.mem_write.assert_not_called()
        m.on_code(m.uc,at,1,None);m.on_code(m.uc,at,1,None)
        m.uc.mem_write.assert_called_once_with(0x40000,b'abcd');self.assertTrue(m.injected)
        self.assertIsNone(m.late_mutation);self.assertEqual(m.after_fault,[b'page'])

    def test_build_refuses_existing_output_or_unavailable_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                run.assert_not_called();self.assertFalse((root/'fresh').exists())


if __name__=='__main__':unittest.main()
