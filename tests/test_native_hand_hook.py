"""Invented adapter contracts; native builds and execution stay in private audits."""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_hook as native
import build_native_hand_hook as builder


class NativeHandHookTests(unittest.TestCase):
    def test_unreviewed_image_refused_before_parser_or_emulator(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'hand hook image'):native.HandHookOracle(raw)

    def test_entry_arguments_and_recursive_invocation_refused_before_memory_access(self):
        machine=object.__new__(native.HandHookOracle);machine.mode=None
        for entry,args,mode,kwargs in ((native.ENTRY,[],'unknown',{}),(native.ENTRY,[],'hook',{'control':True}),
                (native.BASE+0x1000,[],'hook',{}),(native.ENTRY,[1],'hook',{}),
                (native.BASE+native.EXPORTS[b'Hd2ConfigureHandHook'],[False],'configure',{}),
                (native.ENTRY,[],'hook',{'model':1234})):
            with self.assertRaises(ValueError):machine.invoke(entry,args,mode,**kwargs)
        machine.mode='hook'
        with self.assertRaises(ValueError):machine.invoke(native.ENTRY,[],'hook')

    def test_reseed_refuses_a_still_registered_context(self):
        machine=object.__new__(native.HandHookOracle);machine.mode=None;machine.uc=Mock()
        machine.uc.mem_read.return_value=b'\x01\0\0\0'
        with self.assertRaisesRegex(ValueError,'Unregister'):machine.seed(None,None,None,None)
        machine.uc.mem_write.assert_not_called()

    def test_unseeded_operations_and_boolean_policy_are_rejected(self):
        machine=object.__new__(native.HandHookOracle);machine.count=0
        for action in (lambda:machine.configure(),lambda:machine.frame(),lambda:machine.configure(1),lambda:machine.frame(other_model=1)):
            with self.assertRaises(ValueError):action()

    def test_instruction_guard_excludes_startup_and_external_code(self):
        machine=object.__new__(native.HandHookOracle);machine.mode='hook';machine.calls={}
        machine.on_code(None,native.CALLBACK,1,None);self.assertEqual(machine.calls,{'Hd2OnModelHandPose':1})
        for at,size in ((native.BASE+0x1000,1),(native.CODE_END,1),(native.CODE_END-1,2),(machine.INPUT,1)):
            with self.assertRaises(ValueError):machine.on_code(None,at,size,None)
        machine.mode=None
        with self.assertRaises(ValueError):machine.on_code(None,native.ENTRY,1,None)
        machine.mode='fpu_init';machine.on_code(None,machine.FPU_INIT,2,None)
        with self.assertRaises(ValueError):machine.on_code(None,machine.FPU_INIT+5,2,None)

    def test_phase_write_guard_excludes_immutable_buffers_and_boundary_overflow(self):
        machine=object.__new__(native.HandHookOracle);machine.mode='configure';machine.allowed=[(native.ACTIVE,native.ACTIVE+4)]
        machine.on_write(None,None,native.ACTIVE,4,0,None)
        machine.on_write(None,None,machine.STACK,65536,0,None)
        for at,size in ((native.ACTIVE+3,2),(machine.INPUT,4),(machine.ARENA,4),(machine.POSES,4)):
            with self.assertRaises(ValueError):machine.on_write(None,None,at,size,0,None)
        machine.mode=None
        with self.assertRaises(ValueError):machine.on_write(None,None,machine.STACK,4,0,None)

    def test_only_independently_observed_emulator_metadata_limitations_are_allowed(self):
        machine=object.__new__(native.HandHookOracle)
        machine.expected_fpu={'FIP':1,'FDP':2,'FPSW':3,'FP0':(4,5)}
        machine.emulator_restore_limitations=['FIP','FDP']
        with patch.object(machine,'fpu_state',return_value={'FIP':7,'FDP':8,'FPSW':3,'FP0':(4,5)}):
            self.assertEqual(machine.check_fpu(),['FIP','FDP'])
            machine.emulator_restore_limitations=[]
            with self.assertRaises(ValueError):machine.check_fpu()
        machine.emulator_restore_limitations=['FIP','FDP']
        for actual in ({'FIP':7,'FDP':8,'FPSW':0,'FP0':(4,5)},{'FIP':7,'FDP':8,'FPSW':3,'FP0':(9,5)}):
            with patch.object(machine,'fpu_state',return_value=actual):
                with self.assertRaises(ValueError):machine.check_fpu()

    def test_independent_restore_probe_never_waives_numerical_state_corruption(self):
        reg=SimpleNamespace(UC_X86_REG_FPCW=1,UC_X86_REG_FPSW=2,UC_X86_REG_FPTAG=3,UC_X86_REG_EIP=4)
        for changed,expected in (([],[]),([12],['FIP']),([12,20],['FIP','FDP']),([4],None),([28],None)):
            after=bytearray(108)
            for i in changed:after[i]=1
            machine=Mock();machine.mem_read.side_effect=[bytes(108),bytes(after)]
            machine.emu_start.side_effect=lambda start,end,**kwargs:setattr(machine,'end_address',end)
            machine.reg_read.side_effect=lambda reg:machine.end_address
            uni=SimpleNamespace(Uc=Mock(return_value=machine),UC_ARCH_X86=1,UC_MODE_32=2)
            if expected is None:
                with self.assertRaisesRegex(ValueError,'numerical'):native.emulator_restore_probe(uni,reg)
            else:self.assertEqual(native.emulator_restore_probe(uni,reg),expected)

    def test_existing_output_and_missing_compiler_refused_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as process:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                process.assert_not_called();self.assertFalse((root/'fresh').exists())

    def test_native_probe_requires_exact_confirmation_and_no_error_output(self):
        path=Path('hand-fpu-probe.exe')
        for stdout,stderr in (('PASS: partial',''),('', ''),(builder.PROBE_MESSAGES[path.name],'error')):
            process=SimpleNamespace(stdout=stdout,stderr=stderr,returncode=0)
            with patch.object(builder.subprocess,'run',return_value=process) as run:
                with self.assertRaisesRegex(ValueError,'confirm success'):builder.run_console_probe(path)
                self.assertEqual(run.call_args.kwargs['timeout'],30)
        with patch.object(builder.subprocess,'run') as run:
            with self.assertRaisesRegex(ValueError,'Unreviewed'):builder.run_console_probe(Path('other.exe'))
            run.assert_not_called()


if __name__=='__main__':unittest.main()
