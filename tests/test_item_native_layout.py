from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from item_native_layout import ACTION_SIZES, decode_record, fpv_loaded_cell, fpv_native_projection
from item_native_contract import Oracle, verify_image


def invented_record(kind=1, selectors=(4,5)):
    data=bytearray([0xcd]*508)
    struct.pack_into('<II',data,0,1,kind)
    for offset,value in ((8,b'fixture_fpv'),(28,b'fixture_icon'),(48,b'fixture_world')):
        data[offset:offset+20]=value.ljust(20,b'\0')
    for index,offset in enumerate((68,108,112,116,120,124,128,132)):
        struct.pack_into('<I',data,offset,index+1024)
    at=136
    for selector in selectors:
        struct.pack_into('<I',data,at,selector)
        size=ACTION_SIZES[selector]
        data[at+4:at+4+size]=bytes((index*7+13)%256 for index in range(size))
        at+=4+size
    for index in range({0:1,1:4,2:5}[kind]):
        struct.pack_into('<I',data,at+32+index*4,2000+index)
    return bytes(data)


class NativeLayoutTests(unittest.TestCase):
    def test_variable_actions_preserve_opaque_gap_and_derived_order(self):
        result=decode_record(invented_record())
        self.assertEqual(result['derived_offset'],320)
        self.assertEqual(result['opaque_gap_offset'],288)
        self.assertEqual(result['members']['0x54'],{'record_offset':332,'value_raw':2003})
        self.assertEqual(result['descriptor_serialized_size'],328)
        self.assertEqual(result['actions'][0]['native_copied_size'],88)
        self.assertFalse(result['saved_game_serialization_qualified'])

    def test_all_selectors_and_kinds_have_bounded_layouts(self):
        for kind in range(3):
            for first in range(11):
                for second in range(11):
                    with self.subTest(kind=kind,selectors=(first,second)):
                        result=decode_record(invented_record(kind,(first,second)))
                        self.assertEqual(result['derived_offset'],176+ACTION_SIZES[first]+ACTION_SIZES[second])
                        self.assertLessEqual(result['descriptor_serialized_size'],500)

    def test_invalid_presence_kind_selector_and_length_refused(self):
        data=invented_record()
        for offset,value in ((0,0),(0,2),(4,3),(136,11),(268,0xffffffff)):
            bad=bytearray(data);struct.pack_into('<I',bad,offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):decode_record(bad)
        for raw in (b'',data[:-1],data+b'\0'):
            with self.assertRaises(ValueError):decode_record(raw)

    def test_fpv_group_not_equal_to_slot_and_value_array_follows_names(self):
        cell=fpv_loaded_cell(459,2012,3)
        self.assertEqual(cell['slot_index'],359)
        self.assertEqual(cell['name_member_offset'],0xb0+(359*13+12)*48+12)
        self.assertEqual(cell['value_member_offset']-cell['name_member_offset'],16)
        self.assertEqual(fpv_loaded_cell(109,2000,0)['slot_index'],9)

    def test_fpv_domain_rejects_boolean_negative_and_excess_ids(self):
        for args in ((99,2000,0),(600,2000,0),(100,1999,0),(100,2013,0),(100,2000,4),
                     (True,2000,0),(100,2000,True),(100,False,0)):
            with self.subTest(args=args),self.assertRaises(ValueError):fpv_loaded_cell(*args)

    def test_unreviewed_native_image_refused_before_emulation(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed'):verify_image(b'not a client')

    def test_native_projection_requires_full_states_ordered_channels_and_one_variant(self):
        import copy
        group={'id':459,'states':[{'id':state,'channels':[{'id':channel,'variants':[]}
                for channel in range(3000,3004)]} for state in range(2000,2013)]}
        self.assertEqual(fpv_native_projection({'groups':[group]})['cell_count'],52)
        for alteration in ('short','order','multiple','domain'):
            changed=copy.deepcopy(group)
            if alteration=='short':changed['states'].pop()
            elif alteration=='order':changed['states'][0]['channels'].reverse()
            elif alteration=='domain':changed['id']=600
            else:changed['states'][0]['channels'][0]['variants']=[{},{}]
            with self.subTest(alteration=alteration),self.assertRaises(ValueError):
                fpv_native_projection({'groups':[changed]})


@unittest.skipUnless((ROOT/'tmp/stock-menu-analysis.bin').is_file(), 'Private owned-client image is not distributed')
class PrivateNativeOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.machine=Oracle((ROOT/'tmp/stock-menu-analysis.bin').read_bytes())

    def test_all_ten_action_reader_pairs_and_three_item_kinds(self):
        for kind in range(3):
            for selector in range(11):
                with self.subTest(kind=kind,selector=selector):
                    report=self.machine.inspect_record(invented_record(kind,(selector,10-selector)),359)
                    self.assertTrue(report['native_decode_matches'])
                    self.assertFalse(report['saved_game_serialization_qualified'])

    def test_empty_names_are_freed_without_changing_the_input(self):
        raw=bytearray(invented_record(0,(0,0)))
        raw[8:68]=bytes(60)
        self.assertTrue(self.machine.inspect_record(bytes(raw),179)['native_decode_matches'])

    def test_real_native_index_arithmetic_for_candidate_and_compass(self):
        for group in (100,109,359,459,599):
            for state in (2000,2006,2012):
                for channel in range(4):
                    with self.subTest(group=group,state=state,channel=channel):
                        self.assertTrue(self.machine.fpv_cell(group,state,channel)['native_index_math_matches'])

    def test_native_constructor_arguments_match_the_complete_array(self):
        capacity=self.machine.fpv_capacity()
        self.assertEqual(capacity['item_slots'],500)
        self.assertEqual(capacity['array_end_member_offset'],0xa0+500*13*48)
        self.assertTrue(capacity['constructors_not_executed'])

    def test_native_instance_binding_reaches_the_same_consumer_cell(self):
        for slot in (9,23,359,499):
            for state in (0,6,12):
                report=self.machine.fpv_binding(slot,state)
                self.assertTrue(report['native_instance_to_consumer_binding_matches'])
                self.assertEqual(report['group_id'],slot+100)
                self.assertFalse(report['scene_or_model_calls_executed'])

    def test_native_thresholds_are_ordered_cutoffs_not_independent_weights(self):
        for thresholds in ((100,0,0,0),(25,50,75,100),(0,0,0,100),(10,90,20,100),(0,0,0,0)):
            for draw in (0,1,25,26,50,75,99,100):
                expected=next((i for i,t in enumerate(thresholds) if draw<=t),None)
                with self.subTest(thresholds=thresholds,draw=draw):
                    self.assertEqual(self.machine.fpv_threshold_choice(359,6,thresholds,draw),expected)

    def test_native_destination_and_allocation_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed native'):
            self.machine.on_code(None,0x401000,1,None)
        for size in (-1,0,4097):
            with self.assertRaises(ValueError):self.machine.allocate(size)
        for slot in (-1,500,True):
            with self.assertRaises(ValueError):self.machine.inspect_record(invented_record(),slot)
            with self.assertRaises(ValueError):self.machine.fpv_binding(slot,0)
        for state in (-1,13,True):
            with self.assertRaises(ValueError):self.machine.fpv_binding(359,state)


if __name__=='__main__':unittest.main()
