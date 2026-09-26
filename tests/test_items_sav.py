from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from items_sav import parse,candidate_status,PAYLOAD_SIZE,model_name_field


def invented_slot(name='Invented',text_id=1200,kind=1):
    raw=bytearray([0xcd]*508)
    struct.pack_into('<II',raw,0,1,kind)
    for offset,value in ((8,'fixture_fpv'),(28,'fixture_icon'),(48,'fixture_world'),(88,name)):
        raw[offset:offset+len(value)+1]=value.encode()+b'\0'
    struct.pack_into('<If',raw,108,text_id,2.5)
    return bytes(raw)


def table(slots):
    body=b''.join(slot if slot is not None else bytes(4) for slot in slots)
    size=len(slots)*PAYLOAD_SIZE
    if len(body)>=size: raise ValueError('Fixture needs at least one empty slot')
    return body+bytes([0xcd])*(size-len(body))


class ItemsSavTests(unittest.TestCase):
    def test_model_names_fit_exactly_without_truncating_or_accepting_paths(self):
        self.assertEqual(model_name_field('A'*19),b'A'*19+b'\0')
        self.assertEqual(model_name_field('PROTOTYPE_BenFPV').split(b'\0')[0],b'PROTOTYPE_BenFPV')
        for name in ('A'*20,'../x','dir/model','C:foo','test.4ds','CON','com9','écran','',None):
            with self.subTest(name=name),self.assertRaises(ValueError):model_name_field(name)

    def test_empty_words_preserve_slot_ids_and_text_id_is_not_the_slot(self):
        p=parse(table([invented_slot(text_id=1099),None,None,invented_slot(text_id=1385),None]))
        self.assertEqual(p['capacity'],5);self.assertEqual(p['present_slots'],2)
        self.assertEqual(p['slots'][3]['slot'],3);self.assertEqual(p['slots'][3]['text_id'],1385)
        self.assertEqual(p['slots'][3]['offset'],516)
        self.assertEqual(p['serialized_size'],1028)
        self.assertFalse(p['runtime_semantics_qualified'])

    def test_candidate_never_allocated_on_empty_slot_alone(self):
        p=parse(table([invented_slot(),None,None]))
        self.assertEqual(candidate_status(p,0)['status'],'occupied')
        self.assertEqual(candidate_status(p,1)['status'],'serialized_empty')
        self.assertEqual(candidate_status(p,3)['status'],'outside_serialized_capacity')
        for n in range(4):self.assertFalse(candidate_status(p,n)['allocation_allowed'])
        for n in (True,-1,1.5):
            with self.assertRaises(ValueError):candidate_status(p,n)

    def test_capacity_header_and_noncanonical_tail_refused(self):
        data=table([invented_slot(),None,None])
        for raw in (b'',data[:-1],data+b'\0',data[:-1]+b'\0',b'\2'+data[1:]):
            with self.assertRaises(ValueError):parse(raw)
        for cap in (True,0,4,65537):
            with self.assertRaises(ValueError):parse(data,capacity=cap)

    def test_absent_slot_does_not_consume_next_slots_kind(self):
        p=parse(table([None,None,invented_slot(kind=0),None,invented_slot(kind=2)]))
        self.assertEqual([s.get('kind') for s in p['slots']],[None,None,0,None,2])
        self.assertEqual(p['kind_counts'],{0:1,2:1})

    def test_invalid_fields_or_truncated_present_record_refused(self):
        for offset,raw in ((4,struct.pack('<I',3)),(8,b'x'*20),(88,b'\1'+b'x'*18+b'\0'),
                           (112,struct.pack('<f',float('nan'))),(112,struct.pack('<f',-1))):
            slot=bytearray(invented_slot());slot[offset:offset+len(raw)]=raw
            with self.subTest(offset=offset),self.assertRaises(ValueError):parse(table([bytes(slot),None]))
        with self.assertRaisesRegex(ValueError,'Truncated'):parse(invented_slot()[:504],capacity=1)


if __name__=='__main__':unittest.main()
