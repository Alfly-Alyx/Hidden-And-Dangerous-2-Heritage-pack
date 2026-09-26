import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from item_editor_table import MAGIC, parse, require_row


def fixture():
    columns=((1,0,3),(2,1,6),(4,9,4),(5,13,5),(6,17,18),(7,21,7))
    stride=37
    head=struct.pack('<6I',MAGIC,7,0xcccc003d,len(columns),2*stride,0)
    schema=b''.join(struct.pack('<HIHHH',field,offset,2,stride,kind) for field,offset,kind in columns)
    rows=b''.join(struct.pack('<B8sIfI16s',index,b'Invented',0xffffffff,1.25,3,b'private\0garbage')
                  for index in (0,1))
    # Use a seven-character name so the fixed eight-byte field is terminated.
    rows=rows.replace(b'Invented',b'Fixture\0')
    return head+schema+rows


class EditorTableTests(unittest.TestCase):
    def test_header_schema_owns_boundaries_and_typed_columns(self):
        parsed=parse(fixture())
        self.assertEqual(parsed['data_offset'],96)
        self.assertEqual(parsed['row_stride'],37)
        self.assertEqual(parsed['rows'][1]['offset'],133)
        self.assertEqual(parsed['rows'][1]['fields'],{1:1,2:'Fixture',4:0xffffffff,5:1.25,6:3,7:'private'})
        self.assertFalse(parsed['gameplay_field_names_qualified'])

    def test_changed_header_truncation_and_tail_fail_closed(self):
        good=fixture()
        for length in range(len(good)):
            with self.subTest(length=length),self.assertRaises(ValueError):parse(good[:length])
        for offset,value in ((0,0),(4,8),(12,0),(12,513),(16,73),(20,1)):
            bad=bytearray(good);struct.pack_into('<I',bad,offset,value)
            with self.subTest(offset=offset),self.assertRaises(ValueError):parse(bad)
        with self.assertRaises(ValueError):parse(good+b'\0')

    def test_duplicate_overlap_gap_unknown_type_and_mixed_shape_refused(self):
        good=fixture()
        for offset,fmt,value in ((36,'H',1),(38,'I',0),(38,'I',2),(46,'H',99),
                                 (42,'H',1),(44,'H',74),(44,'H',0),(42,'H',0)):
            bad=bytearray(good);struct.pack_into('<'+fmt,bad,offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):parse(bad)

    def test_invalid_boolean_float_or_name_does_not_leak_to_metadata(self):
        good=fixture()
        for offset,value in ((96,b'\2'),(97,b'x'*8),(97,b'\1abc\0'),(97,b'\x81\0'),
                             (109,struct.pack('<f',float('nan'))),(109,struct.pack('<f',float('inf')))):
            bad=bytearray(good);bad[offset:offset+len(value)]=value
            with self.subTest(offset=offset),self.assertRaises(ValueError):parse(bad)

    def test_row_owner_and_capacity_are_explicit(self):
        raw=fixture()
        row=require_row(raw,1,stride=37,name_column=2,name='Fixture')
        self.assertEqual(row['offset'],133)
        for index,stride,name in ((True,37,'Fixture'),(2,37,'Fixture'),(1,135,'Fixture'),(1,37,'Other')):
            with self.assertRaises(ValueError):require_row(raw,index,stride=stride,name_column=2,name=name)


if __name__=='__main__':unittest.main()
