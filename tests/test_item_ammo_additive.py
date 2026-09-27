"""Invented 500-slot buffers exercise dual additions in both physical orders."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import item_ammo_additive as tx
from item_ammo_descriptor import build_ammunition
from item_weapon_descriptor import build_weapon
from items_sav import parse
from fpv_table import parse as parse_fpv
from test_item_ammo_descriptor import fixture as ammo_spec
from test_item_weapon_descriptor import fixture as weapon_spec
from test_items_sav import invented_slot,table
from test_item_table_additive import group
from test_fpv_table import table as fpv_table


def fixture(weapon_slot=364,ammo_slot=365):
    slots=[None]*500
    for index in (9,400):
        raw=bytearray(invented_slot(name='Existing'+str(index),text_id=1000+index,kind=2));struct.pack_into('<II',raw,136,0,0)
        slots[index]=bytes(raw)
    spec=weapon_spec();spec['text_id']=21503;spec['weapon_members_raw'][0x54]=ammo_slot
    return table(slots),fpv_table(group(109)),build_weapon(spec),fpv_table(group(weapon_slot+100)),build_ammunition(ammo_spec())


class ModernAmmoAdditionTests(unittest.TestCase):
    def test_ammo_alone_preserves_all_records_and_round_trips_exactly(self):
        for slot in (0,1,255,256,365,499):
            items,_,_,_,ammo=fixture();before=parse(items)
            current,proof=tx.build(items,ammo,slot=slot);after=parse(current)
            self.assertEqual(len(current),len(items));self.assertEqual(after['serialized_size'],before['serialized_size']+504)
            for a,b in zip(before['slots'],after['slots']):
                if a['slot']!=slot:self.assertEqual(a['sha256'],b['sha256'])
            self.assertEqual(tx.restore(current,json.loads(json.dumps(proof))),items)
            self.assertFalse(proof['installation_allowed']);self.assertFalse(proof['global_slot_reservation'])

    def test_two_additions_in_either_slot_order_preserve_every_old_object_and_group(self):
        for weapon_slot,ammo_slot in ((364,365),(365,364),(0,499),(499,0)):
            inputs=fixture(weapon_slot,ammo_slot);before=deepcopy(inputs)
            current,proof=tx.build_pair(*inputs,weapon_slot=weapon_slot,ammo_slot=ammo_slot)
            self.assertEqual(inputs,before);self.assertEqual(parse(current['items'])['present_slots'],4)
            self.assertEqual(parse(current['items'])['allocation_tail_size'],parse(inputs[0])['allocation_tail_size']-1008)
            self.assertEqual([g['id'] for g in parse_fpv(current['fpv'])['groups']],[109,weapon_slot+100])
            for a,b in zip(parse(inputs[0])['slots'],parse(current['items'])['slots']):
                if a['slot'] not in (weapon_slot,ammo_slot):self.assertEqual(a['sha256'],b['sha256'])
            self.assertEqual(tx.restore_pair(current,json.loads(json.dumps(proof))),{'items':inputs[0],'fpv':inputs[1]})
            self.assertFalse(proof['ammo_has_fpv_group']);self.assertFalse(proof['installation_allowed'])

    def test_occupied_or_out_of_domain_slots_never_replaced(self):
        items,fpv,gun,fragment,ammo=fixture()
        for slot in (9,400,True,-1,500,365.0):
            with self.assertRaises(ValueError):tx.build(items,ammo,slot=slot)
        for a,b in ((364,364),(365,364)):
            with self.assertRaises(ValueError):tx.build_pair(items,fpv,gun,fragment,ammo,weapon_slot=a,ammo_slot=b)
        with self.assertRaises(ValueError):tx.build(table([None]*255),ammo,slot=365)

    def test_wrong_class_actions_quantity_or_identity_are_rejected(self):
        items,_,gun,_,ammo=fixture()
        for offset,value in ((4,struct.pack('<I',1)),(136,struct.pack('<I',5)),(108,b'\xff'*4),
            (88,b'NotModern'.ljust(20,b'\0')),(176,struct.pack('<f',0)),(176,struct.pack('<f',float('nan')))):
            raw=bytearray(ammo);raw[offset:offset+len(value)]=value
            with self.assertRaises(ValueError):tx.build(items,bytes(raw),slot=365)
        with self.assertRaises(ValueError):tx.build(items,gun,slot=365)

    def test_name_or_text_collision_refused_including_between_new_records(self):
        inputs=fixture();items=inputs[0];ammo=inputs[-1]
        first,_=tx.build(items,ammo,slot=366)
        with self.assertRaisesRegex(ValueError,'collision'):tx.build(first,ammo,slot=365)
        spec=ammo_spec();spec['text_id']=21503
        with self.assertRaisesRegex(ValueError,'text ID'):
            tx.build_pair(*inputs[:-1],build_ammunition(spec),weapon_slot=364,ammo_slot=365)

    def test_later_edits_and_metadata_type_changes_refuse_rollback(self):
        current,proof=tx.build_pair(*fixture(),weapon_slot=364,ammo_slot=365)
        for key in ('items','fpv'):
            changed=dict(current);changed[key]+=b'changed'
            with self.assertRaises(ValueError):tx.restore_pair(changed,proof)
        for mutate in (lambda p:p['ammo'].update(slot=365.0),lambda p:p['ammo'].update(item_offset=True),
            lambda p:p.update(allocation_bytes_consumed=1008.0),lambda p:p.update(ammo_has_fpv_group=0),
            lambda p:p['weapon'].update(slot=365),lambda p:p.update(extra='unknown')):
            bad=deepcopy(proof);mutate(bad)
            with self.assertRaises(ValueError):tx.restore_pair(current,bad)

    def test_two_insertions_refuse_insufficient_tail_without_mutating_input(self):
        _,fpv,gun,fragment,ammo=fixture();slots=[None]*500
        ids=[n for n in range(500) if n not in (364,365)][:495]
        for n in ids:slots[n]=invented_slot(name='Old'+str(n),text_id=1000+n,kind=2)
        items=table(slots);before=bytes(items)
        with self.assertRaisesRegex(ValueError,'tail'):tx.build_pair(items,fpv,gun,fragment,ammo,weapon_slot=364,ammo_slot=365)
        self.assertEqual(items,before)

    def test_personal_overlays_and_exact_snapshot_reversal(self):
        items,fpv,gun,fragment,ammo=fixture();changed=bytearray(items);slot=parse(items)['slots'][9]
        struct.pack_into('<f',changed,slot['offset']+112,4.5);overlay={'items':bytes(changed)}
        result,proof=tx.compose({'items':items,'fpv':fpv},overlay,gun,fragment,ammo,weapon_slot=364,ammo_slot=365)
        self.assertEqual(tx.restore_pair(result,proof['transaction']),{'items':overlay['items'],'fpv':fpv})
        self.assertTrue(proof['all_preexisting_central_table_changes_preserved'])
        self.assertEqual([r['slot'] for r in proof['preexisting_changes']['items']],[9])
        occupied,_=tx.build(items,ammo,slot=365)
        with self.assertRaisesRegex(ValueError,'occupied'):
            tx.compose({'items':items,'fpv':fpv},{'items':occupied},gun,fragment,ammo,weapon_slot=364,ammo_slot=365)
        with self.assertRaisesRegex(ValueError,'archive'):
            tx.compose({'items':occupied,'fpv':fpv},{},gun,fragment,ammo,weapon_slot=364,ammo_slot=365)


if __name__=='__main__':unittest.main()
