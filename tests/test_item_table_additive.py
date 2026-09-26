"""Invented buffers only; no commercial table or executable is required."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import item_table_additive as transaction
from item_weapon_descriptor import build_weapon
from items_sav import parse as parse_items
from fpv_table import parse as parse_fpv
from test_item_weapon_descriptor import fixture as weapon_spec
from test_items_sav import invented_slot,table as item_table
from test_fpv_table import chunk,variant,state,table as fpv_table


def group(owner):
    return chunk(owner,b''.join(state(2000+i,variant('Invented'+str(i)+'.I3D')) for i in range(13)))


def fixture(slot=359):
    slots=[None]*500
    for number,kind,name in ((9,2,'KOMPAS'),(23,1,'Existing weapon'),(179,0,'Existing ammo'),(400,2,'Late object')):
        slots[number]=invented_slot(name=name,text_id=1000+number,kind=kind)
    spec=weapon_spec();spec['text_id']=21500
    return item_table(slots),fpv_table(group(109)+group(123)),build_weapon(spec),fpv_table(group(slot+100))


class AdditiveTableTests(unittest.TestCase):
    def test_pair_preserves_every_other_item_group_and_allocated_capacity(self):
        inputs=fixture();before=copy.deepcopy(inputs)
        result,proof=transaction.build(*inputs,slot=359)
        original=parse_items(inputs[0]);changed=parse_items(result['items'])
        self.assertEqual(len(result['items']),252000)
        self.assertEqual(changed['serialized_size'],original['serialized_size']+504)
        self.assertEqual(changed['allocation_tail_size'],original['allocation_tail_size']-504)
        self.assertEqual(changed['present_slots'],original['present_slots']+1)
        for old,new in zip(original['slots'],changed['slots']):
            if old['slot']==359:
                self.assertEqual(new['sha256'],transaction.sha(inputs[2]));continue
            self.assertEqual(old['sha256'],new['sha256'])
            self.assertEqual(new['offset'],old['offset']+(504 if old['slot']>359 else 0))
        self.assertEqual(result['fpv'][6:len(inputs[1])],inputs[1][6:])
        self.assertEqual(parse_fpv(result['fpv'])['groups'][:-1],parse_fpv(inputs[1])['groups'])
        self.assertEqual(proof['existing_item_slots_preserved'],499)
        self.assertEqual(proof['existing_present_items_preserved'],4)
        self.assertFalse(proof['global_slot_reservation']);self.assertFalse(proof['installation_allowed'])
        self.assertFalse(proof['saved_game_compatibility_qualified'])
        self.assertEqual(inputs,before)

    def test_round_trip_is_exact_including_tail_and_empty_boundary_slots(self):
        for slot in (0,1,255,256,359,499):
            with self.subTest(slot=slot):
                original=fixture(slot)
                current,proof=transaction.build(*original,slot=slot)
                self.assertEqual(transaction.restore(current,json.loads(json.dumps(proof))),
                                 {'items':original[0],'fpv':original[1]})
                repeated,receipt=transaction.build(*original,slot=slot)
                self.assertEqual((current,proof),(repeated,receipt))

    def test_occupied_slot_never_overwritten_and_base_capacity_never_extended(self):
        raw,fpv,descriptor,fragment=fixture()
        for slot in (9,23,179,400):
            with self.subTest(slot=slot),self.assertRaisesRegex(ValueError,'occupied'):
                transaction.build(raw,fpv,descriptor,fragment,slot=slot)
        with self.assertRaisesRegex(ValueError,'capacity'):
            transaction.build(item_table([None]*255),fpv,descriptor,fragment,slot=359)
        for slot in (True,-1,500,359.0,'359'):
            with self.subTest(slot=slot),self.assertRaises(ValueError):transaction.build(*fixture(),slot=slot)

    def test_tail_exhaustion_is_refused_and_last_safe_insertion_reverses(self):
        _,fpv,descriptor,fragment=fixture()
        for count in (495,496):
            slots=[None]*500
            ids=[n for n in range(500) if n!=359][:count]
            for n in ids:slots[n]=invented_slot(name='Existing',kind=0 if n==179 else 2,text_id=1000+n)
            raw=item_table(slots)
            if count==496:
                with self.assertRaisesRegex(ValueError,'tail'):transaction.build(raw,fpv,descriptor,fragment,slot=359)
            else:
                current,proof=transaction.build(raw,fpv,descriptor,fragment,slot=359)
                self.assertEqual(parse_items(current['items'])['allocation_tail_size'],16)
                self.assertEqual(transaction.restore(current,proof)['items'],raw)

    def test_existing_fpv_owner_or_wrong_fragment_is_refused(self):
        items,fpv,descriptor,fragment=fixture()
        with self.assertRaisesRegex(ValueError,'already present'):
            transaction.build(items,fpv_table(group(459)),descriptor,fragment,slot=359)
        for bad in (fpv_table(b''),fpv_table(group(359)),fpv_table(group(459)+group(460))):
            with self.subTest(size=len(bad)),self.assertRaisesRegex(ValueError,'exactly'):
                transaction.build(items,fpv,descriptor,bad,slot=359)

    def test_native_fpv_shape_errors_are_not_silently_normalized(self):
        items,fpv,descriptor,fragment=fixture()
        incomplete=fpv_table(chunk(109,state(2000,variant('Invented.I3D'))))
        with self.assertRaisesRegex(ValueError,'thirteen'):
            transaction.build(items,incomplete,descriptor,fragment,slot=359)
        incomplete=fpv_table(chunk(459,state(2000,variant('Invented.I3D'))))
        with self.assertRaisesRegex(ValueError,'thirteen'):
            transaction.build(items,fpv,descriptor,incomplete,slot=359)

    def test_nonmodern_unresolved_kind_and_duplicate_identity_are_refused(self):
        items,fpv,descriptor,fragment=fixture()
        for at,blob in ((4,struct.pack('<I',2)),(88,b'Other'.ljust(20,b'\0')),(108,b'\xff'*4)):
            changed=bytearray(descriptor);changed[at:at+len(blob)]=blob
            with self.subTest(at=at),self.assertRaisesRegex(ValueError,'modern Weapon'):
                transaction.build(items,fpv,bytes(changed),fragment,slot=359)
        for name,text_id,expected in (('modern_test',1400,'internal name'),('Unrelated',21500,'text ID')):
            slots=[None]*500;slots[179]=invented_slot(kind=0,text_id=1179)
            slots[400]=invented_slot(name=name,text_id=text_id)
            with self.assertRaisesRegex(ValueError,expected):
                transaction.build(item_table(slots),fpv,descriptor,fragment,slot=359)

    def test_missing_out_of_range_or_wrong_class_ammunition_is_refused(self):
        items,fpv,_,fragment=fixture()
        for ammo in (359,9,23,500,0xffffffff):
            spec=weapon_spec();spec['text_id']=21500;spec['weapon_members_raw'][0x54]=ammo
            with self.subTest(ammo=ammo),self.assertRaisesRegex(ValueError,'ammunition'):
                transaction.build(items,fpv,build_weapon(spec),fragment,slot=359)

    def test_later_edit_in_either_table_refuses_whole_pair_rollback(self):
        current,proof=transaction.build(*fixture(),slot=359);before=copy.deepcopy(current)
        for name in ('items','fpv'):
            bad=dict(current);bad[name]=bad[name][:-1]+bytes([bad[name][-1]^1])
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'result changed'):
                transaction.restore(bad,proof)
        with self.assertRaises(ValueError):transaction.restore({'items':current['items']},proof)
        self.assertEqual(current,before)

    def test_receipt_tampering_is_refused_even_for_python_numeric_aliases(self):
        current,proof=transaction.build(*fixture(),slot=359)
        for key,value in (('slot',359.0),('capacity',500.0),('group_id',False),('item_offset',-1),
                          ('original_tail_size',True),('original_serialized_size',0),
                          ('existing_item_slots_preserved',498),('installation_allowed',True)):
            bad=copy.deepcopy(proof);bad[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):transaction.restore(current,bad)
        for section in ('sources','results','descriptor','fragment'):
            bad=copy.deepcopy(proof);bad[section]={}
            with self.subTest(section=section),self.assertRaises(ValueError):transaction.restore(current,bad)
        bad=copy.deepcopy(proof);bad['extra']='not accepted'
        with self.assertRaises(ValueError):transaction.restore(current,bad)

    def test_reapplying_same_insertion_is_not_mistaken_for_idempotent_success(self):
        originals=fixture();current,_=transaction.build(*originals,slot=359)
        with self.assertRaisesRegex(ValueError,'occupied'):
            transaction.build(current['items'],current['fpv'],originals[2],originals[3],slot=359)


if __name__=='__main__':unittest.main()
