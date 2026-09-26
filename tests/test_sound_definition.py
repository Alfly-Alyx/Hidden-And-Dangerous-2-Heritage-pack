import copy
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from sound_definition import parse,resolve,VARIANT_FIELDS
from item_sound_audit import editor_references,reference
from item_sound_oracle import SoundOracle


def chunk(kind,payload):return struct.pack('<HI',kind,len(payload)+6)+payload
def string(kind,name):return chunk(kind,name.encode('cp1252')+b'\0')
def variant(name='fixture.wav'):
    return chunk(1300,string(1400,name)+b''.join(chunk(k,struct.pack('<I',k)) for k in VARIANT_FIELDS[1:]))
def entry(name='Invented',variants=1):
    return chunk(1200,string(1210,name)+chunk(1310,b'\0')+variant()*variants)
def bank(name='Bank',entries=None):return chunk(1100,string(1110,name)+(entry() if entries is None else entries))
def fixture():
    return chunk(1000,bank('First',entry('Absent',0)+entry('First sound',2))
                 +bank('Empty',b'')+bank('Weapon Shooting',entry('Shoot'))
                 +bank('Weapon Manipulation',entry('Reload'))
                 +chunk(1050,struct.pack('<II',123,456)))


class SoundDefinitionTests(unittest.TestCase):
    def test_ordinals_include_empty_entries_and_banks(self):
        parsed=parse(fixture())
        self.assertEqual(len(parsed['banks']),4)
        self.assertEqual(parsed['entry_count'],4);self.assertEqual(parsed['variant_count'],4)
        self.assertEqual(resolve(parsed,0,0)['variants'],[])
        self.assertEqual(resolve(parsed,0,1)['label'],'First sound')
        self.assertEqual(len(resolve(parsed,0,1)['variants']),2)
        self.assertEqual(parsed['banks'][1]['entries'],[])
        self.assertEqual(resolve(parsed,2,0)['label'],'Shoot')

    def test_parameters_and_lookup_are_opaque_not_gameplay_claims(self):
        parsed=parse(fixture());v=resolve(parsed,0,1)['variants'][0]
        self.assertEqual(v['parameters_raw'],{str(k):k for k in VARIANT_FIELDS[1:]})
        self.assertEqual(parsed['opaque_lookup']['pair_count'],1)
        self.assertFalse(parsed['opaque_lookup']['semantics_qualified'])
        self.assertFalse(parsed['playback_qualified'])

    def test_all_truncations_bad_bounds_root_and_mutability_are_refused(self):
        raw=fixture()
        for length in range(len(raw)):
            with self.subTest(length=length),self.assertRaises(ValueError):parse(raw[:length])
        for bad in (raw+b'\0',bytearray(raw),chunk(999,raw[6:]),chunk(1000,struct.pack('<HI',1100,5))):
            with self.assertRaises(ValueError):parse(bad)

    def test_bank_entry_and_variant_order_are_not_repaired(self):
        bad_entries=(chunk(1200,chunk(1310,b'\0')+string(1210,'Bad')),
                     chunk(1200,string(1210,'Bad')+chunk(1310,b'\2')),
                     chunk(1200,string(1210,'Bad')+chunk(1310,b'\0\0')),
                     chunk(1200,string(1210,'Bad')+chunk(1310,b'\0')+chunk(1300,string(1400,'a.wav'))))
        for raw in bad_entries:
            with self.assertRaises(ValueError):parse(chunk(1000,bank(entries=raw)))
        with self.assertRaises(ValueError):parse(chunk(1000,chunk(1100,entry()+string(1110,'Late label'))))
        with self.assertRaises(ValueError):parse(chunk(1000,chunk(999,b'')))

    def test_text_terminators_controls_encoding_and_empty_filename_are_checked(self):
        for text in (b'unterminated',b'bad\0tail\0',b'\1bad\0',b'\x81\0'):
            with self.assertRaises(ValueError):parse(chunk(1000,chunk(1100,chunk(1110,text))))
        raw=fixture().replace(b'fixture.wav\0',b'\0'*12,1)
        with self.assertRaises(ValueError):parse(raw)
        parsed=parse(chunk(1000,bank('',entry('',0))))
        self.assertEqual(parsed['banks'][0]['label'],'')

    def test_lookup_tail_is_not_mistaken_for_another_bank(self):
        for tail in (chunk(1050,b'x'),chunk(1050,b'')+chunk(1050,b''),chunk(1050,b'')+bank()):
            with self.assertRaises(ValueError):parse(chunk(1000,bank()+tail))

    def test_sentinel_bounds_and_symbolic_ids_never_alias_zero(self):
        parsed=parse(fixture())
        self.assertIsNone(resolve(parsed,2,0xffffffff))
        for bank_id,index in ((True,0),(2,True),(-1,0),(4,0),(2,-1),(2,1),(1,0),(2,2**32)):
            with self.subTest(bank=bank_id,index=index),self.assertRaises(ValueError):resolve(parsed,bank_id,index)
        result=editor_references({8:'TEST_F',10:'TEST_R'},parsed)
        self.assertEqual(result,[{'column':8,'bank':2,'symbol':'TEST_F','resolved':False},
                                 {'column':10,'bank':3,'symbol':'TEST_R','resolved':False}])
        for bad in (' 0','00','../bad','',None):
            with self.assertRaises(ValueError):editor_references({8:bad,10:'0'},parsed)

    def test_editor_columns_select_distinct_banks_and_leave_source_unchanged(self):
        parsed=parse(fixture());before=copy.deepcopy(parsed)
        refs=editor_references({8:'0',10:'0'},parsed)
        self.assertEqual([r['label'] for r in refs],['Shoot','Reload'])
        self.assertTrue(all(r['resolved'] for r in refs))
        self.assertTrue(reference(parsed,2,0xffffffff)['absent_sentinel'])
        self.assertFalse(refs[0]['audio_playback_qualified'])
        self.assertEqual(parsed,before)

    def test_native_oracle_refuses_unpinned_image_and_invalid_lookup_domain(self):
        with self.assertRaises(ValueError):SoundOracle(bytes(1024))
        oracle=SoundOracle.__new__(SoundOracle)
        for bank_id,index,counts in ((True,0,[1]),(0,-1,[1]),(0,0,[]),(0,0,[257]),(0,0,[True]),(0,0,[1]*17)):
            with self.assertRaises(ValueError):oracle.lookup(bank_id,index,counts)


if __name__=='__main__':unittest.main()
