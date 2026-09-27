"""Invented names/5DS and reference double; no commercial engine input."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_binding_oracle import BindingOracle,select_name,name_bytes,NAME_START,NAME_STOPS,DESCRIPTOR_STOP
from animation_binding_audit import audit_bank,audit_name_controls
from five_ds import parse_5ds
from test_five_ds import invented_clip


class ReferenceDouble:
    def __init__(self,mutate=None):self.mutate=mutate
    def finish(self,result):
        result.update({'inputs_preserved':True,'allocation_or_binding_called':False,'scene_loaded':False,
                       'game_started':False,'library_loaded':False})
        if self.mutate:self.mutate(result)
        return result
    def select(self,names,query,kind):
        return self.finish({'native_name_selection_match':True,'selected_index':select_name(names,query),
                            'model_kind':kind,'exact_case_sensitive':True})
    def describe(self,raw,index,slot):
        channels=parse_5ds(raw)['tracks'][index]['channels']
        return self.finish({'native_transform_descriptor_match':True,'slot':slot,
                            'channels':{k:len(v['frames']) for k,v in channels.items()},'event_channels_evaluated':False})


class NameReferenceTests(unittest.TestCase):
    def test_exact_case_and_first_duplicate_match(self):
        names=['A','BC','def','def']
        self.assertEqual(select_name(names,'def'),2)
        self.assertIsNone(select_name(names,'Def'));self.assertIsNone(select_name(names,'de'))
        self.assertIsNone(select_name([],'A'))

    def test_ascii_cp1252_and_long_names_remain_bounded(self):
        self.assertEqual(name_bytes('é'),b'\xe9\0');self.assertEqual(len(name_bytes('A'*63)),64)
        for name in ('','A'*64,'a\0b','a\nb','😀',None):
            with self.assertRaises(ValueError):name_bytes(name)
        with self.assertRaises(ValueError):select_name(['A']*129,'A')

    def test_name_allowlist_stops_before_binding_and_refuses_allocator(self):
        class FakeCpu:
            def __init__(self):self.stopped=False
            def emu_stop(self):self.stopped=True
        machine=object.__new__(BindingOracle);machine.phase='name';machine.visited=set();cpu=FakeCpu()
        machine.on_code(cpu,NAME_START,2,None)
        for address in NAME_STOPS:
            machine.on_code(cpu,address,5,None);self.assertTrue(cpu.stopped);self.assertEqual(machine.stopped,address)
        with self.assertRaises(ValueError):machine.on_code(cpu,0x10020740,1,None)

    def test_descriptor_stops_before_outer_loop(self):
        class FakeCpu:
            def emu_stop(self):pass
        machine=object.__new__(BindingOracle);machine.phase='descriptor';machine.visited=set()
        machine.on_code(FakeCpu(),DESCRIPTOR_STOP,1,None)
        self.assertEqual(machine.stopped,DESCRIPTOR_STOP)
        with self.assertRaises(ValueError):machine.on_code(FakeCpu(),DESCRIPTOR_STOP+1,1,None)


class BindingAuditTests(unittest.TestCase):
    def clips(self):return {'invented':invented_clip([('Root',{'position':([0,10],[(0,0,0),(1,2,3)])})])}

    def test_bank_checks_both_containers_and_all_eight_slots(self):
        report=audit_bank(ReferenceDouble(),['Root','Other'],self.clips())
        self.assertEqual(report['native_name_selections'],2);self.assertEqual(report['native_channel_descriptors'],8)
        self.assertFalse(report['actual_model_attachment_qualified']);self.assertFalse(report['commercial_geometry_or_keys_exported'])

    def test_synthetic_control_corpus_includes_missing_case_and_boundary_names(self):
        report=audit_name_controls(ReferenceDouble())
        self.assertEqual(report['cases'],22);self.assertEqual(report['maximum_target_count'],128)
        with self.assertRaisesRegex(ValueError,'receipt'):
            audit_name_controls(ReferenceDouble(lambda row:row.update({'scene_loaded':True})))

    def test_missing_or_duplicate_target_and_empty_bank_fail_closed(self):
        for names,clips in ((['root'],self.clips()),(['Root','Root'],self.clips()),(['Root'],{})):
            with self.assertRaises(ValueError):audit_bank(ReferenceDouble(),names,clips)

    def test_incomplete_or_false_selection_proof_is_refused(self):
        for key,value in (('native_name_selection_match',1),('exact_case_sensitive',False),('selected_index',True),
                          ('selected_index',1),('allocation_or_binding_called',True)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'receipt'):
                audit_bank(ReferenceDouble(lambda r:r.update({key:value})),['Root'],self.clips())

    def test_descriptor_count_slot_and_event_claims_are_checked(self):
        for key,value in (('channels',{}),('slot',True),('slot',8),('event_channels_evaluated',True)):
            def mutate(row):
                if 'native_transform_descriptor_match' in row:row[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'receipt'):
                audit_bank(ReferenceDouble(mutate),['Root'],self.clips())


if __name__=='__main__':unittest.main()
