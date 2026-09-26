"""Fabricated sparse tables: no commercial records, models or audio."""
import hashlib
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from item_editor_table import MAGIC
from asset_presence_audit import benelli_shoot_evidence,benelli_compass_evidence
from orphan_weapon_evidence_audit import table_boundaries
from flamethrower_evidence_audit import weapon_table_evidence,ammo_record_evidence
from test_items_sav import invented_slot,table as items_table

SHOOT_FIELDS=((1,3),(2,6),(3,18),(4,5),(6,5),(8,7),(10,7),(12,4),(24,5),
              (26,5),(28,5),(30,5),(38,5),(40,5),(42,5),(46,5),(58,3),(77,4),
              (79,4),(81,3),(84,5),(86,5),(88,7),(92,5),(94,5),(98,4))
ITEM_FIELDS=((1,3),(2,7),(4,4),(5,18),(6,7),(8,7),(10,7),(11,18),(12,5),(14,18),
             (16,18),(18,4),(20,18),(22,4),(24,4),(26,5),(39,18),(40,18),(44,4),(46,4),(48,4),(50,18))


def editor_table(fields,count,values):
    sizes={3:1,4:4,5:4,6:8,7:16,18:4}
    stride=sum(sizes[k] for _,k in fields)
    schema=bytearray();offset=0
    for field,kind in fields:
        schema+=struct.pack('<HIHHH',field,offset,count,stride,kind);offset+=sizes[kind]
    rows=bytearray(count*stride)
    for index,contents in values.items():
        offset=index*stride
        for field,kind in fields:
            if field in contents:
                value=contents[field]
                raw=(struct.pack('<f',value) if kind==5 else struct.pack('<I',value) if kind in (4,18)
                     else bytes([value]) if kind==3 else value.encode().ljust(sizes[kind],b'\0'))
                if len(raw)!=sizes[kind]:raise ValueError('Bad invented field width')
                rows[offset:offset+sizes[kind]]=raw
            offset+=sizes[kind]
    return struct.pack('<6I',MAGIC,7,0,len(fields),len(rows),0)+schema+rows


class WeaponEvidenceBoundaryTests(unittest.TestCase):
    def test_benelli_row_does_not_include_previous_rows_last_word(self):
        raw=editor_table(SHOOT_FIELDS,255,{8:{98:0x12345678},9:{1:1,2:'Benelli',3:2,4:.3,6:1500}})
        proof=benelli_shoot_evidence(raw)
        self.assertEqual((proof['offset_start'],proof['offset_end']),(1551,1686))
        self.assertEqual(proof['sha256'],hashlib.sha256(raw[1551:1686]).hexdigest().upper())
        self.assertTrue(proof['header_ok']);self.assertFalse(proof['record_type_header_present'])
        self.assertNotIn('record_type',proof)
        self.assertNotEqual(proof['sha256'],hashlib.sha256(raw[1547:1682]).hexdigest().upper())

    def test_compass_row_is_133_bytes_without_the_next_item_marker(self):
        raw=editor_table(ITEM_FIELDS,500,{9:{1:1,2:'KOMPAS'},10:{1:1,2:'Neighbour'}})
        proof=benelli_compass_evidence(raw)
        self.assertEqual((proof['offset_start'],proof['offset_end'],proof['size']),(1485,1618,133))
        self.assertEqual(proof['sha256'],hashlib.sha256(raw[1485:1618]).hexdigest().upper())

    def test_editor_proofs_require_correct_row_name_not_a_neighbour_fragment(self):
        wrong=editor_table(SHOOT_FIELDS,255,{8:{1:1,2:'Benelli'},9:{2:'Other'}})
        with self.assertRaisesRegex(ValueError,'owner'):benelli_shoot_evidence(wrong)
        wrong=editor_table(ITEM_FIELDS,500,{44:{2:'Other'},45:{2:'Flak TMP'}})
        with self.assertRaisesRegex(ValueError,'owner'):weapon_table_evidence(wrong)

    def test_flame_editor_rows_have_distinct_schema_owned_slots(self):
        raw=editor_table(ITEM_FIELDS,500,{44:{2:'Flammewerfer'},45:{1:1,2:'Flak TMP'}})
        proof=weapon_table_evidence(raw)
        self.assertEqual(proof['german_record']['offset_start'],6140)
        self.assertEqual(proof['german_record']['size'],133)
        self.assertEqual(proof['british_reused_record']['offset_start'],6273)
        self.assertEqual(proof['british_reused_record']['live_fpv_reference'],'')

    def test_ammo_proof_uses_the_native_slot_parser_and_refuses_shifted_windows(self):
        record=bytearray(invented_slot(name='Invented ammo',text_id=1207,kind=0))
        record[48:68]=b'w_ammo'.ljust(20,b'\0')
        struct.pack_into('<fI',record,112,5.0,2)
        slots=[None]*210;slots[207]=bytes(record)
        raw=items_table(slots);start=207*4
        definition={'slot':207,'sha256':hashlib.sha256(record).hexdigest().upper(),
                    'icon':'fixture_icon','internal_name':'Invented ammo','text_id':1207}
        self.assertTrue(ammo_record_evidence(raw,start,definition)['expected'])
        for bad in (start-28,start-16,start+4):
            with self.assertRaises(ValueError):ammo_record_evidence(raw,bad,definition)

    def test_orphan_audit_only_accepts_exact_present_slots_or_editor_rows(self):
        raw=items_table([None,invented_slot(),None])
        bounds=table_boundaries(raw,'TABLES/items.sav')
        self.assertEqual(bounds,{(4,512):1})
        self.assertNotIn((0,508),bounds)
        raw=editor_table(SHOOT_FIELDS,255,{9:{2:'Fixture'}})
        bounds=table_boundaries(raw,'TABLES/item_shoot.tbl')
        self.assertEqual(bounds[(1551,1686)],9)
        self.assertNotIn((1547,1682),bounds)
        with self.assertRaises(ValueError):table_boundaries(raw,'something.bin')


if __name__=='__main__':unittest.main()
