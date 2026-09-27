"""Game-only invented magazine parameters, no commercial descriptors."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from item_ammo_descriptor import build_ammunition
from item_native_layout import decode_record


def fixture():
    return {'provenance':'ASSEMBLAGE_MODERNE','status':'prototype_disabled','native_class':0,
        'names':{'internal':'MODERN_TestAmmo','fpv':'','world':'PROTOTYPE_TestMag','icon':'MOD_TestMagIcon'},
        'text_id':21504,'weight':.2,'base_members_raw':{0x0c:1,0x1c:0,0x38:9,0x3c:0,0x40:0,0x44:1},'quantity':30}


class ModernAmmoDescriptorTests(unittest.TestCase):
    def test_explicit_class_quantity_names_zero_fill_and_reproducibility(self):
        spec=fixture();before=deepcopy(spec);raw=build_ammunition(spec);layout=decode_record(raw)
        self.assertEqual(len(raw),508);self.assertEqual(raw,build_ammunition(spec));self.assertEqual(spec,before)
        self.assertEqual(layout['kind'],0);self.assertEqual(layout['derived_offset'],176)
        self.assertEqual([a['selector'] for a in layout['actions']],[0,0])
        self.assertEqual(struct.unpack_from('<f',raw,176)[0],30);self.assertEqual(raw[180:],bytes(328))
        self.assertEqual(raw[136:176],bytes(40));self.assertEqual(raw[8:28],bytes(20))
        self.assertEqual(struct.unpack_from('<I',raw,108)[0],21504)

    def test_status_class_quantity_text_and_weight_must_be_explicit(self):
        for key,values in {'status':['active'],'provenance':['ORIGINAL'],'native_class':[True,1],
            'quantity':[True,0,-1,10001,3.5,float('nan')],'text_id':[True,-1,0xffffffff],
            'weight':[-1,float('inf'),float('nan')]}.items():
            for value in values:
                spec=fixture();spec[key]=value
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):build_ammunition(spec)

    def test_no_missing_keys_or_implicit_resource_choices(self):
        for key in fixture():
            spec=fixture();spec.pop(key)
            with self.assertRaises(ValueError):build_ammunition(spec)
        for key,value in (('world',''),('icon',''),('fpv','unexpected'),('internal','Original'),('world','../bad'),('icon','too_long_'*4)):
            spec=fixture();spec['names'][key]=value
            with self.assertRaises(ValueError):build_ammunition(spec)
        spec=fixture();spec['base_members_raw'][0x54]=30
        with self.assertRaises(ValueError):build_ammunition(spec)


if __name__=='__main__':unittest.main()
