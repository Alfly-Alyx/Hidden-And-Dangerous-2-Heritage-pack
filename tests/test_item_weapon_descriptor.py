"""Fully invented descriptors; no game assets, client or allocation required."""
import copy
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from item_native_layout import decode_record
from item_weapon_descriptor import build_weapon,secondary_action
from items_sav import parse as parse_items


def fixture():
    return {'provenance':'ASSEMBLAGE_MODERNE','status':'prototype_disabled','native_class':1,
            'names':{'internal':'MODERN_Test','fpv':'PROTOTYPE_TestFPV','icon':'test_icon','world':'PROTOTYPE_Test'},
            'text_id':0xffffffff,'weight':2.5,
            'base_members_raw':{0x0c:0,0x1c:2,0x38:6,0x3c:0,0x40:40,0x44:2},
            'weapon_members_raw':{0x58:3,0x5c:3,0x60:0,0x54:179},
            'primary':{'selector':4,'editor_fields':{2:'TEST',3:7,4:1.25,6:900.0,8:'123',10:'-1',12:42,
                24:2.5,26:700.0,28:9.0,30:2.25,38:.125,40:.5,42:.38,46:1.4,58:1,77:0xffffffff,79:7}},
            'secondary':{'selector':5,'mode_raw':5,'scalar':1.0}}


class WeaponDescriptorTests(unittest.TestCase):
    def test_complete_508_bytes_with_native_selectors_and_derived_members(self):
        raw=build_weapon(fixture());layout=decode_record(raw)
        self.assertIsInstance(raw,bytes);self.assertEqual(len(raw),508)
        self.assertEqual(layout['kind'],1);self.assertEqual(layout['derived_offset'],320)
        self.assertEqual([a['selector'] for a in layout['actions']],[4,5])
        self.assertEqual([a['serialized_size'] for a in layout['actions']],[128,16])
        self.assertEqual(layout['members']['0x54']['value_raw'],179)
        self.assertEqual(struct.unpack_from('<4I',raw,320),(3,3,0,179))
        self.assertEqual(raw[272:288],struct.pack('<IIIf',0,4,5,1.0))
        self.assertEqual(raw[156:160],struct.pack('<I',123))

    def test_descriptor_parses_inside_synthetic_table_without_allocating_real_slot(self):
        raw=build_weapon(fixture());buffer=raw+bytes(4)+b'\xcd'*(1008-512)
        parsed=parse_items(buffer,capacity=2)
        self.assertEqual(parsed['slots'][0]['internal_name'],'MODERN_Test')
        self.assertEqual(parsed['slots'][0]['fpv_model'],'PROTOTYPE_TestFPV')
        self.assertEqual(parsed['slots'][0]['text_id'],0xffffffff)
        self.assertEqual(parsed['slots'][0]['weight_raw'],2.5)
        self.assertFalse(parsed['slots'][1]['present'])

    def test_secondary_absence_changes_derived_offset_without_leaking_stale_payload(self):
        spec=fixture();spec['secondary']={'selector':0};raw=build_weapon(spec)
        layout=decode_record(raw)
        self.assertEqual(layout['derived_offset'],304)
        self.assertEqual(layout['actions'][1]['serialized_size'],0)
        self.assertEqual(struct.unpack_from('<4I',raw,304),(3,3,0,179))
        self.assertEqual(raw[320:],bytes(188))

    def test_modern_zero_fill_policy_is_explicit_and_deterministic(self):
        spec=fixture();before=copy.deepcopy(spec);raw=build_weapon(spec)
        self.assertEqual(raw,build_weapon(spec));self.assertEqual(spec,before)
        for start,end in ((72,88),(169,172),(221,224),(228,268),(288,320),(336,508)):
            self.assertEqual(raw[start:end],bytes(end-start))

    def test_no_implicit_defaults_unknown_keys_or_class_inference(self):
        for key,value in (('provenance','ORIGINAL'),('status','active'),('native_class',2),('native_class',True)):
            spec=fixture();spec[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):build_weapon(spec)
        for key in fixture():
            spec=fixture();spec.pop(key)
            with self.subTest(missing=key),self.assertRaises(ValueError):build_weapon(spec)
        spec=fixture();spec['allocate_slot']=359
        with self.assertRaises(ValueError):build_weapon(spec)
        for group,key in (('base_members_raw',0x44),('weapon_members_raw',0x54)):
            spec=fixture();spec[group].pop(key)
            with self.assertRaises(ValueError):build_weapon(spec)

    def test_invalid_or_unresolved_resources_are_not_silently_truncated_or_zeroed(self):
        for name,value in (('fpv','x'*20),('world','../unsafe'),('icon','NUL'),('internal','not_modern'),('fpv',None)):
            spec=fixture();spec['names'][name]=value
            with self.subTest(name=name,value=value),self.assertRaises(ValueError):build_weapon(spec)
        spec=fixture();spec['primary']['editor_fields'][8]='UNRESOLVED'
        with self.assertRaises(ValueError):build_weapon(spec)
        spec=fixture();spec['names']['icon']=''
        self.assertEqual(build_weapon(spec)[28:48],bytes(20))
        spec['names']['icon']='wi_test-icon'
        self.assertEqual(build_weapon(spec)[28:41],b'wi_test-icon\0')
        spec['names']['world']='model-hyphen'
        with self.assertRaises(ValueError):build_weapon(spec)

    def test_bad_selector_numeric_fields_and_secondary_values_are_refused(self):
        for selector in (True,3,5,'4'):
            spec=fixture();spec['primary']['selector']=selector
            with self.assertRaises(ValueError):build_weapon(spec)
        for secondary in ({'selector':True},{'selector':9},{'selector':0,'scalar':1},{'selector':5}):
            spec=fixture();spec['secondary']=secondary
            with self.assertRaises(ValueError):build_weapon(spec)
        for key,value in (('weight',-1),('weight',float('inf')),('text_id',-1),('text_id',True)):
            spec=fixture();spec[key]=value
            with self.assertRaises(ValueError):build_weapon(spec)
        for mode,value in ((-1,1),(True,1),(5,0),(5,float('nan')),(5,True)):
            with self.assertRaises(ValueError):secondary_action(mode,value)

    def test_zero_padding_does_not_claim_editor_only_fields_are_reconstructed(self):
        spec=fixture();raw=build_weapon(spec)
        spec['primary']['editor_fields'][98]=12345
        self.assertEqual(build_weapon(spec),raw)
        self.assertFalse(decode_record(raw)['saved_game_serialization_qualified'])


if __name__=='__main__':unittest.main()
