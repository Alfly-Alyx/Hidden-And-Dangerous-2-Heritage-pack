"""Invented editor fields only; no commercial records or archives needed."""
import copy
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import item_shoot_projection as shoot


def fields():
    return {2:'TEST',3:7,4:1.25,6:900.0,8:'123',10:'-1',12:42,24:2.5,26:700.0,
            28:9.0,30:2.25,38:.125,40:.5,42:.38,46:1.4,58:1,77:0xffffffff,79:7}


def payload(values):
    data=bytearray(b'\xcc'*128)
    for span in shoot.projection(values):
        data[span['offset']:span['offset']+len(span['raw'])]=span['raw']
    return bytes(data)


class ShootProjectionTests(unittest.TestCase):
    def test_eighteen_columns_and_three_constants_leave_padding_unqualified(self):
        spans=shoot.projection(fields())
        self.assertEqual(len(spans),21)
        self.assertEqual({s['column'] for s in spans if s['column'] is not None},set(fields()))
        covered={i for s in spans for i in range(s['offset'],s['offset']+len(s['raw']))}
        self.assertEqual(set(range(88))-covered,{29,30,31,81,82,83})
        self.assertEqual(shoot.UNLINKED_COLUMNS,(1,81,84,86,88,92,94,98))

    def test_conversions_have_exact_reviewed_offsets_and_explicit_units_only(self):
        data=payload(fields())
        self.assertEqual(struct.unpack_from('<I',data,16)[0],123)
        self.assertEqual(struct.unpack_from('<I',data,40)[0],0xffffffff)
        self.assertEqual(struct.unpack_from('<f',data,20)[0],125)
        self.assertEqual(struct.unpack_from('<f',data,44)[0],2500)
        self.assertEqual(data[76:81],b'TEST\0')
        self.assertEqual(data[28],1)
        self.assertTrue(shoot.compare(fields(),data)['all_reviewed_fields_match'])

    def test_single_precision_percent_constant_avoids_one_ulp_regression(self):
        projected=shoot.encode_field(.38,'times_f32_percent')
        source=struct.unpack('<f',struct.pack('<f',.38))[0]
        self.assertEqual(projected.hex(),'6b09793b')
        self.assertEqual(struct.pack('<f',source*.01).hex(),'6c09793b')
        self.assertNotEqual(projected,struct.pack('<f',source*.01))

    def test_padding_string_suffix_and_editor_tail_are_not_misread_as_live_fields(self):
        data=bytearray(payload(fields()))
        for offset in (29,30,31,81,82,83,*range(88,128)):data[offset]=0x55
        result=shoot.compare(fields(),bytes(data))
        self.assertTrue(result['all_reviewed_fields_match'])
        self.assertFalse(result['padding_and_stale_suffix_compared'])
        self.assertFalse(result['gameplay_semantics_qualified'])

    def test_one_changed_column_and_one_constant_are_reported_separately(self):
        data=bytearray(payload(fields()))
        struct.pack_into('<f',data,52,8)
        struct.pack_into('<I',data,4,4)
        result=shoot.compare(fields(),bytes(data))
        self.assertEqual(result['different_columns'],[28,None])
        self.assertFalse(result['all_reviewed_fields_match'])

    def test_symbolic_references_are_refused_or_explicitly_omitted_never_zeroed(self):
        value=fields();value[8]='SYMBOL_F';value[10]='SYMBOL_R'
        with self.assertRaises(ValueError):shoot.projection(value)
        spans=shoot.projection(value,omit_symbolic=True)
        self.assertEqual(len(spans),19)
        self.assertNotIn(8,{s['column'] for s in spans})
        self.assertNotIn(10,{s['column'] for s in spans})
        for bad in ('../path','12;13',' 2','02','123x','',None):
            value=fields();value[8]=bad
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                shoot.projection(value,omit_symbolic=True)

    def test_invalid_values_and_missing_columns_fail_closed(self):
        invalid=((2,'TOO_LONG'),(2,'A\0B'),(2,'\u2603'),(3,-1),(3,True),(3,2**32),
                 (4,float('nan')),(4,float('inf')),(4,True),(4,1e50),
                 (8,'4294967296'),(58,True),(58,2))
        for key,value in invalid:
            mapping=fields();mapping[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):shoot.projection(mapping)
        mapping=fields();mapping.pop(46)
        with self.assertRaises(ValueError):shoot.projection(mapping)

    def test_wrong_payload_size_or_mutable_record_is_refused_and_source_unchanged(self):
        values=fields();before=copy.deepcopy(values);raw=payload(values)
        for bad in (raw[:88],raw+b'\0',bytearray(raw)):
            with self.subTest(length=len(bad)),self.assertRaises(ValueError):shoot.compare(values,bad)
        shoot.compare(values,raw)
        self.assertEqual(values,before)
        self.assertEqual(raw,payload(values))


if __name__=='__main__':unittest.main()

