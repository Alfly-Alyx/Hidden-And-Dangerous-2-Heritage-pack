"""Synthetic base fields only, independent from commercial item tables."""
import copy
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import item_base_projection as base
from item_native_layout import ACTION_SIZES,decode_record


def fields():
    return {1:1,2:'TEST OBJECT',4:1200,5:3,6:'test_fpv',8:'test_icon',10:'test_world',
            11:0,12:2.5,14:2,16:4,18:91,20:5,22:7,24:179,26:7.0,
            39:4,40:0,44:6,46:0,48:40,50:2}


def record(values,kind):
    # Independent layout assembly. The projector under test never fills this.
    raw=bytearray(b'\xcc'*508);struct.pack_into('<II',raw,0,1,kind)
    for column,offset in ((2,88),(6,8),(8,28),(10,48)):
        text=values[column].encode('cp1252')+b'\0';raw[offset:offset+len(text)]=text
    for column,offset in ((11,68),(4,108),(14,116),(44,120),(46,124),(48,128),(50,132)):
        struct.pack_into('<I',raw,offset,values[column])
    struct.pack_into('<f',raw,112,values[12])
    offset=136
    for column in (16,20):
        struct.pack_into('<I',raw,offset,values[column]);offset+=4+ACTION_SIZES[values[column]]
    offset+=32
    for column in {0:(26,),1:(5,39,40,24),2:(5,39,40)}[kind]:
        struct.pack_into('<f' if kind==0 else '<I',raw,offset,values[column]);offset+=4
    return bytes(raw)


class BaseProjectionTests(unittest.TestCase):
    def test_weapon_fields_and_variable_action_offsets(self):
        for selectors in ((4,5),(0,0),(3,5),(1,2),(10,9)):
            values=fields();values[16],values[20]=selectors;raw=record(values,1)
            result=base.compare(values,raw)
            self.assertTrue(result['all_reviewed_fields_match'])
            self.assertEqual(len(result['checks']),19)
            layout=decode_record(raw)
            self.assertEqual(next(c['offset'] for c in result['checks'] if c['column']==24),layout['derived_offset']+12)
            self.assertFalse(result['native_class_inferred_from_editor'])

    def test_class_must_be_explicit_and_is_not_an_editor_enum(self):
        for kind in (None,True,3,-1,'1'):
            with self.subTest(kind=kind),self.assertRaises(ValueError):base.projection(fields(),kind=kind)
        for kind,count in ((0,16),(1,19),(2,18)):
            result=base.compare(fields(),record(fields(),kind))
            self.assertTrue(result['all_reviewed_fields_match'])
            self.assertEqual(len(result['checks']),count)

    def test_empty_slot_does_not_project_stale_editor_fields(self):
        values={1:0,2:'STALE',16:999,24:123}
        spans=base.projection(values,kind=None)
        self.assertEqual(spans,[{'column':1,'offset':0,'raw':bytes(4),'conversion':'presence'}])
        self.assertEqual(base.compare(values,bytes(4))['different_columns'],[])
        with self.assertRaises(ValueError):base.projection(values,kind=1)
        with self.assertRaises(ValueError):base.compare(fields(),bytes(4))
        with self.assertRaises(ValueError):base.compare(values,record(fields(),1))

    def test_sentinels_are_differences_not_automatic_zero_conversions(self):
        for kind,column,delta,value in ((1,24,12,0xffffffff),(0,26,0,0xbf800000)):
            values=fields();values[column]=0;raw=bytearray(record(values,kind))
            offset=decode_record(raw)['derived_offset']+delta
            struct.pack_into('<I',raw,offset,value)
            result=base.compare(values,bytes(raw))
            self.assertEqual(result['different_columns'],[column])
            self.assertFalse(result['all_reviewed_fields_match'])

    def test_suffixes_gaps_action_payloads_and_generic_tail_remain_opaque(self):
        values=fields();raw=bytearray(record(values,2));layout=decode_record(raw)
        for start,end in ((8+len(values[6])+1,28),(72,88),
                          (140,140+128),(layout['opaque_gap_offset'],layout['derived_offset']),
                          (layout['derived_offset']+12,508)):
            raw[start:end]=b'\x55'*(end-start)
        result=base.compare(values,bytes(raw))
        self.assertTrue(result['all_reviewed_fields_match'])
        self.assertFalse(result['generic_members_0x60_0x64_qualified'])
        self.assertFalse(result['opaque_bytes_compared'])
        self.assertFalse(result['complete_descriptor_built'])

    def test_action_rows_are_not_claimed_as_native_offsets_or_resolved(self):
        result=base.compare(fields(),record(fields(),1))
        self.assertEqual(result['action_rows_not_resolved'],{'18':91,'22':7})
        self.assertFalse({18,22}&{c['column'] for c in result['checks']})

    def test_shape_difference_is_not_compared_at_wrong_offsets(self):
        values=fields();raw=record(values,1);values[16]=3
        with self.assertRaisesRegex(ValueError,'Action shape'):base.compare(values,raw)

    def test_invalid_fields_and_missing_columns_are_refused(self):
        for column,value in ((1,True),(1,2),(2,'x'*16),(6,'x\0y'),(8,'\u2603'),
                             (12,-1),(12,float('nan')),(12,True),(14,-1),(24,2**32),
                             (16,11),(20,True),(39,None)):
            values=fields();values[column]=value
            with self.subTest(column=column,value=value),self.assertRaises(ValueError):base.projection(values,kind=1)
        values=fields();values.pop(39)
        with self.assertRaises(ValueError):base.projection(values,kind=1)

    def test_source_is_immutable_and_changed_column_is_reported(self):
        values=fields();before=copy.deepcopy(values);raw=record(values,1)
        for bad in (raw[:-1],raw+b'\0',bytearray(raw),b'\1\0\0\0'):
            with self.assertRaises(ValueError):base.compare(values,bad)
        changed=bytearray(raw);struct.pack_into('<I',changed,120,5)
        self.assertEqual(base.compare(values,bytes(changed))['different_columns'],[44])
        self.assertEqual(values,before)
        self.assertEqual(raw,record(values,1))


if __name__=='__main__':unittest.main()
