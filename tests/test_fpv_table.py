from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fpv_table import parse


def chunk(kind,data=b''):return struct.pack('<HI',kind,len(data)+6)+data
def variant(name='invented.I3D',value=100):return chunk(1000,name.encode()+b'\0')+struct.pack('<I',value)
def state(kind=2000,variants=None):
    return chunk(kind,chunk(3000,variant() if variants is None else variants)+b''.join(chunk(i) for i in (3001,3002,3003)))
def table(groups=None):return chunk(12345,groups if groups is not None else chunk(109,state()))


class FpvTableTests(unittest.TestCase):
    def test_nested_groups_preserve_numeric_channels_and_auxiliary_values(self):
        p=parse(table(chunk(109,state(2000,variant('a.I3D',70)+variant('b.I3D',30))+state(2001))))
        channels=p['groups'][0]['states'][0]['channels']
        self.assertEqual(channels[0]['variants'],[{'name':'a.I3D','value_raw':70},{'name':'b.I3D','value_raw':30}])
        self.assertFalse(p['event_semantics_qualified']);self.assertFalse(p['weapon_binding_qualified'])
        self.assertEqual(channels[-1]['variants'],[])

    def test_empty_groups_allowed_but_duplicate_owners_refused(self):
        self.assertEqual(parse(table(chunk(109)))['groups'][0]['states'],[])
        for raw in (table(chunk(109)+chunk(109)),table(chunk(109,state()+state())),
                    table(chunk(109,chunk(2000,b''.join(chunk(3000) for _ in range(4)))))):
            with self.assertRaisesRegex(ValueError,'Duplicate'):parse(raw)

    def test_malformed_roots_bounds_names_and_variant_tail_refused(self):
        good=table()
        for raw in (b'',good[:-1],good+b'\0',chunk(1,good[6:]),
                    table(chunk(109,state(2000,variant()[:-1]))),
                    table(chunk(109,state(2000,variant('a\0b.I3D')))),
                    table(chunk(109,chunk(2000,chunk(3000))))):
            with self.subTest(size=len(raw)),self.assertRaises(ValueError):parse(raw)


if __name__=='__main__':unittest.main()
