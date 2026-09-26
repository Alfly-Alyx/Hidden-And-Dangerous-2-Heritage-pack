from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from item_instance_state import (COMMON, STATE, CHILDREN, ENVELOPE, WEAPON_MEMBERS,
                                 encode_leaf, decode_leaf, children, chunk, scalar_chunk)
from item_state_oracle import StateOracle, inspect_tables
from item_native_layout import decode_record
from test_item_native_layout import invented_record
from test_items_sav import table as item_table

PLACEMENT={1:0xffffffff,2:0x3f800000,3:0xbf800000}
COMMON_VALUES={100:0x12345678,101:0x90abcdef,102:0,103:0xffffffff,104:1}
WEAPON_VALUES={k:(1 if k==209 else 0x40000000+k) for k in WEAPON_MEMBERS}


def paired_records(ammo_slot=179,quantity=7.0):
    gun=bytearray(invented_record(1,(4,5)))
    ammo=bytearray(invented_record(0,(0,0)))
    struct.pack_into('<I',gun,decode_record(gun)['members']['0x54']['record_offset'],ammo_slot)
    struct.pack_into('<f',ammo,decode_record(ammo)['members']['0x54']['record_offset'],quantity)
    return bytes(gun),bytes(ammo)


class LeafItemCodecTests(unittest.TestCase):
    def test_slot_and_raw_scalars_roundtrip_without_truncation(self):
        for slot in (0,9,254,255,256,359,499):
            for gun in (None,WEAPON_VALUES):
                raw=encode_leaf(slot,PLACEMENT,COMMON_VALUES,gun)
                self.assertEqual(len(raw),114 if gun is None else 224)
                parsed=decode_leaf(raw,weapon=gun is not None)
                self.assertEqual(parsed,{'slot':slot,'placement':PLACEMENT,'common':COMMON_VALUES,
                                         'weapon':gun,'whole_saved_game_qualified':False})

    def test_domain_types_and_boolean_values_fail_closed(self):
        for slot in (-1,500,True,1.0):
            with self.assertRaises(ValueError):encode_leaf(slot,PLACEMENT,COMMON_VALUES)
        for field,value in ((100,-1),(101,2**32),(102,True),(104,2)):
            with self.assertRaises(ValueError):encode_leaf(359,PLACEMENT,{**COMMON_VALUES,field:value})
        with self.assertRaises(ValueError):encode_leaf(359,PLACEMENT,COMMON_VALUES,{**WEAPON_VALUES,209:2})
        for values in ({},{**COMMON_VALUES,999:0}):
            with self.assertRaises(ValueError):encode_leaf(359,PLACEMENT,values)

    def test_truncated_sizes_duplicate_unknown_and_nested_fields_refused(self):
        raw=encode_leaf(359,PLACEMENT,COMMON_VALUES,WEAPON_VALUES)
        for length in range(len(raw)):
            with self.subTest(length=length),self.assertRaises(ValueError):decode_leaf(raw[:length],weapon=True)
        for malformed in (raw+b'\0',raw+raw,chunk(ENVELOPE,raw[6:]+scalar_chunk(0,359)),
                          chunk(ENVELOPE,raw[6:]+scalar_chunk(999,1))):
            with self.assertRaises(ValueError):decode_leaf(malformed,weapon=True)
        fields=dict(children(raw[6:]))
        for tag,body in ((0,struct.pack('<I',500)),(0,b'\0'),(CHILDREN,scalar_chunk(1,1)),
                         (STATE,fields[STATE]+scalar_chunk(200,0))):
            modified=chunk(ENVELOPE,b''.join(chunk(k,body if k==tag else v) for k,v in fields.items()))
            with self.assertRaises(ValueError):decode_leaf(modified,weapon=True)
        reverse_root=chunk(ENVELOPE,b''.join(chunk(k,v) for k,v in reversed(list(fields.items()))))
        state_children=children(fields[STATE])
        shifted_state=b''.join(chunk(k,v) for k,v in state_children[1:]+state_children[:1])
        reverse_state=chunk(ENVELOPE,b''.join(chunk(k,shifted_state if k==STATE else v) for k,v in fields.items()))
        for reordered in (reverse_root,reverse_state):
            with self.assertRaises(ValueError):decode_leaf(reordered,weapon=True)

    def test_explicit_kind_cannot_hide_extra_state_or_omit_weapon_state(self):
        for gun in (None,WEAPON_VALUES):
            with self.assertRaises(ValueError):
                decode_leaf(encode_leaf(359,PLACEMENT,COMMON_VALUES,gun),weapon=gun is None)
        with self.assertRaises(ValueError):decode_leaf(b'',weapon=1)

    def test_noncanonical_saved_booleans_are_rejected_without_rewriting(self):
        raw=encode_leaf(359,PLACEMENT,COMMON_VALUES,WEAPON_VALUES)
        for tag in (104,209):
            bad=raw.replace(scalar_chunk(tag,1),scalar_chunk(tag,2))
            self.assertNotEqual(raw,bad)
            with self.assertRaises(ValueError):decode_leaf(bad,weapon=True)

    def test_table_audit_separates_typed_absent_and_unqualified_ammo_references(self):
        from unittest.mock import Mock
        gun,ammo=paired_records()
        def readable(raw):
            out=bytearray(raw);out[88:108]=b'Invented'.ljust(20,b'\0')
            struct.pack_into('<f',out,112,2.0)
            return bytes(out)
        slots=[None]*500
        slots[23]=readable(gun);slots[179]=readable(ammo)
        slots[102]=readable(invented_record(2,(0,0)))
        slots[270]=readable(paired_records(102)[0])
        slots[56]=readable(paired_records(0xffffffff)[0])
        machine=Mock();machine.ammo_binding.return_value={'native_ammo_binding_matches':True}
        result=inspect_tables(machine,{('fixture','tables/items.sav'):item_table(slots)})['fixture']
        self.assertEqual(len(result['typed_associations_checked']),1)
        self.assertEqual(result['no_ammo_reference_slots'],[56])
        self.assertEqual(result['unqualified_reference_slots'],[{'weapon_slot':270,'referenced_slot':102,'referenced_kind':2}])
        self.assertFalse(result['synthetic_benelli_ammo_probe']['commercial_benelli_weapon_record'])
        self.assertFalse(result['synthetic_benelli_ammo_probe']['item_slot_allocated'])


@unittest.skipUnless((ROOT/'tmp/stock-menu-analysis.bin').is_file(),'Private owned-client image is not distributed')
class PrivateItemStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.machine=StateOracle((ROOT/'tmp/stock-menu-analysis.bin').read_bytes())

    def test_native_envelopes_restore_item_slots_and_all_weapon_fields(self):
        for slot in (0,9,255,256,359,499):
            for gun in (None,WEAPON_VALUES):
                with self.subTest(slot=slot,weapon=gun is not None):
                    report=self.machine.roundtrip_leaf(slot,PLACEMENT,COMMON_VALUES,gun)
                    self.assertTrue(report['native_roundtrip'])
                    self.assertTrue(report['native_writer_matches'])
                    self.assertFalse(report['whole_saved_game_qualified'])

    def test_missing_descriptor_does_not_recreate_the_saved_weapon(self):
        report=self.machine.roundtrip_leaf(359,PLACEMENT,COMMON_VALUES,WEAPON_VALUES,definition_present=False)
        self.assertTrue(report['missing_definition_rejected'])
        self.assertFalse(report['native_roundtrip'])

    def test_native_common_writer_reader_asymmetry_is_not_hidden(self):
        for common in ({**COMMON_VALUES,102:42},{**COMMON_VALUES,103:77},
                       {**COMMON_VALUES,102:0xdeadbeef,103:0}):
            report=self.machine.roundtrip_leaf(359,PLACEMENT,common,WEAPON_VALUES)
            self.assertFalse(report['native_roundtrip'])
            self.assertFalse(report['complete_common_state_restored'])
            self.assertTrue(report['weapon_state_restored'])
            self.assertEqual(report['common_writer_tags_ignored_by_reader'],[102,103])

    def test_common_reader_accepts_202_203_only_inside_common_container(self):
        for fields in ({102:42,103:77},{202:42,203:77},
                       {100:3,101:4,104:2,202:5,203:0xffffffff},{}):
            self.assertTrue(self.machine.common_reader_probe(fields)['native_reader_dispatch_matches'])
        with self.assertRaises(ValueError):self.machine.common_reader_probe({999:1})

    def test_native_ammo_binding_initializes_current_and_maximum(self):
        for slot,quantity in ((179,7.0),(192,2.0),(499,0.0),(0,1.5)):
            gun,ammo=paired_records(slot,quantity)
            report=self.machine.ammo_binding(gun,ammo,weapon_slot=359,ammo_slot=slot)
            self.assertEqual(report['initial_quantity'],quantity)
            self.assertTrue(report['native_ammo_binding_matches'])
            self.assertFalse(report['live_reload_qualified'])

    def test_ammo_type_and_reference_mismatch_are_not_emulated(self):
        gun,ammo=paired_records()
        for first,second,slot in ((gun,ammo,180),(gun,gun,179),(ammo,ammo,179)):
            with self.assertRaises(ValueError):self.machine.ammo_binding(first,second,weapon_slot=359,ammo_slot=slot)
        for quantity in (-1.0,float('inf'),float('nan')):
            gun,ammo=paired_records(quantity=quantity)
            with self.assertRaises(ValueError):self.machine.ammo_binding(gun,ammo,weapon_slot=359,ammo_slot=179)

    def test_native_quantity_decrement_clamps_without_a_projectile_or_shot(self):
        for current,amount,expected in ((7,1,6),(1,1,0),(0,1,0),(2,7,0),(1.5,.25,1.25),(7,0,7)):
            self.assertEqual(self.machine.consume_quantity(current,amount),expected)
        for invalid in (-1,float('nan'),float('inf'),True,1e7):
            with self.assertRaises(ValueError):self.machine.consume_quantity(invalid,1)

    def test_file_doubles_reject_unexpected_handle_pointer_mode_and_seek(self):
        machine=self.machine
        for address,args,pattern in ((0x7e539e,(1,machine.HEAP,4),'handle'),
                    (0x7e539e,(machine.HANDLE,machine.INPUT,4),'pointer'),
                    (0x7e539e,(machine.HANDLE,machine.HEAP,4),'write-only'),
                    (0x7e5398,(machine.HANDLE,1,0),'outside'),
                    (0x7e5398,(machine.HANDLE,0,3),'origin')):
            machine.stream()
            with self.subTest(address=address,args=args),self.assertRaisesRegex(ValueError,pattern):
                machine.call(address,machine.STREAM,*args)
        machine.stream(b'')
        with self.assertRaisesRegex(ValueError,'write forbidden'):
            machine.call(0x7e5392,machine.STREAM,machine.HANDLE,machine.HEAP,4)


if __name__=='__main__':unittest.main()
