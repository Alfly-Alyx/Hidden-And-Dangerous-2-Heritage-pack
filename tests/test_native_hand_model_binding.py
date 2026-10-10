"""Original binding contracts without commercial assets or native libraries."""
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import native_hand_model_binding as native
import build_native_hand_model_binding as builder
from native_bound_hand_relay import BoundHandRelayOracle
from native_scattered_hand_relay import ScatteredHandRelayOracle
from hand_relay_audit import audit


def records():
    pointers=[0x5300004+i*0x2000 for i in range(11)];model=0x5700000
    return model,[{'pointer':p,'bytes':0x170,'name':native.NAMES[i],
                   'parent':model if native.PARENTS[i]<0 else pointers[native.PARENTS[i]]} for i,p in enumerate(pointers)]


class NativeHandModelBindingTests(unittest.TestCase):
    def test_unreviewed_image_rejected_before_importing_parser(self):
        for raw in (None,b'',bytearray(native.BINARY_SIZE),b'MZ'+bytes(native.BINARY_SIZE-2)):
            with self.assertRaisesRegex(ValueError,'binding image'):native.HandModelBindingOracle(raw)

    def test_output_and_workspace_layouts_are_explicit(self):
        self.assertEqual(native.OUTPUT_SIZE,8+128*8+128*4+11*4)
        self.assertEqual(native.WORK_SIZE,native.OUTPUT_SIZE+4*128*4)

    def test_reference_reorders_forests_but_preserves_role_identity(self):
        model,rows=records()
        for inputs in (rows,list(reversed(rows)),rows[5:]+rows[:5]):
            raw,order=native.reference_binding(model,inputs)
            self.assertEqual(struct.unpack_from('<II',raw),(model,11))
            parents=struct.unpack_from('<11i',raw,0x408);roles=struct.unpack_from('<11I',raw,0x608)
            self.assertTrue(all(-1<=p<i for i,p in enumerate(parents)))
            self.assertEqual([inputs[order[i]]['name'] for i in roles],[native.NAMES[i] for i in native.ROLES])
            self.assertEqual(raw[8+11*8:0x408],bytes((128-11)*8))
            self.assertEqual(raw[0x408+11*4:0x608],bytes((128-11)*4))

    def test_reference_refuses_cycle_and_unknown_parent(self):
        for parent in (0xdeadbeef,0x5300004+4*0x2000):
            model,rows=records();rows[3]['parent']=parent
            with self.assertRaisesRegex(ValueError,'hierarchy'):native.reference_binding(model,rows)

    def test_invocation_guard_excludes_startup_bad_scalars_and_nested_calls(self):
        m=object.__new__(native.HandModelBindingOracle);m.active=False
        entry=native.BASE+native.EXPORTS[b'Hd2BuildHandModelBinding']
        for address,args in ((native.BASE+0x1000,[]),(entry,[]),(entry,[True]*7),(entry,[-1]*7)):
            with self.assertRaises(ValueError):m.invoke(address,args)
        m.active=True
        with self.assertRaises(ValueError):m.invoke(entry,[0]*7)

    def test_binding_write_guard_never_accepts_a_native_record(self):
        m=object.__new__(native.HandModelBindingOracle);m.active=True;m.output_writes=0
        m.on_write(None,None,m.OUTPUT,1,0,None);self.assertEqual(m.output_writes,1)
        for at,size in ((m.NODES,4),(m.INPUT,4),(m.OUTPUT+native.OUTPUT_SIZE-1,2),(m.WORK+native.WORK_SIZE-1,2)):
            with self.assertRaises(ValueError):m.on_write(None,None,at,size,0,None)

    def test_late_metadata_fault_only_occurs_at_snapshot_revalidation(self):
        m=object.__new__(native.HandModelBindingOracle);m.active=True;m.calls={};m.injected=False;m.late_fault=(0x530010c,0)
        uc=Mock();m.on_code(uc,native.SNAPSHOT_CHECK-1,1,None);uc.mem_write.assert_not_called()
        m.on_code(uc,native.SNAPSHOT_CHECK,1,None);m.on_code(uc,native.SNAPSHOT_CHECK,1,None)
        uc.mem_write.assert_called_once_with(0x530010c,bytes(4));self.assertTrue(m.injected)

    def test_bound_context_points_at_readonly_c_output(self):
        m=object.__new__(BoundHandRelayOracle);m.uc=Mock();model,rows=records();pointers=[r['pointer'] for r in rows]
        m.adapter=SimpleNamespace(pointers=pointers,CONTEXT=0x4600000)
        m.binding=SimpleNamespace(OUTPUT=0x5100000,bind=Mock(return_value=(b'result',list(reversed(range(11))),{'status':0})))
        def read(pointer,size):
            if pointer in pointers:
                i=pointers.index(pointer);node=bytearray(0x170)
                struct.pack_into('<I',node,0xe8,m.SOURCE+0x1000+i*64);struct.pack_into('<I',node,0x108,rows[i]['parent'])
                return bytes(node)
            i=(pointer-m.SOURCE-0x1000)//64;name=native.NAMES[i].encode()+b'\0';return name+bytes(64-len(name))
        m.uc.mem_read.side_effect=read
        with patch.object(ScatteredHandRelayOracle,'seed_adapter'):
            m.seed_adapter(None,None,None,None)
        for offset,pointer in ((4,0x5100008),(12,0x5100408),(16,0x5100608)):
            m.uc.mem_write.assert_any_call(0x4600000+offset,struct.pack('<I',pointer))
        self.assertEqual(m.binding_source_indices,list(range(11)))
        self.assertEqual([r['pointer'] for r in m.binding.bind.call_args.args[1]],list(reversed(pointers)))

    def test_binding_requires_scattered_relay_before_any_native_image_access(self):
        with self.assertRaisesRegex(ValueError,'requires the scattered'):audit(None,None,compiled_binding=b'x')

    def test_build_refuses_existing_output_or_missing_compiler(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch.object(builder.subprocess,'run') as run:
                with self.assertRaisesRegex(ValueError,'already exists'):builder.build(root)
                with patch.object(builder,'COMPILER',root/'missing.exe'):
                    with self.assertRaisesRegex(ValueError,'compiler required'):builder.build(root/'fresh')
                run.assert_not_called();self.assertFalse((root/'fresh').exists())


if __name__=='__main__':unittest.main()
