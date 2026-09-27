"""Synthetic names/tables and fail-closed hooks; no commercial image is needed."""
import copy
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import fpv_resource_oracle as oracle
from test_fpv_table import chunk,variant,state,table
from test_fpv_table_oracle import benelli_table
from test_items_sav import invented_slot,table as items_table


def projected(resources=None):
    if resources is None:resources=[('first.I3D',100),None,None,None]
    channels=b''.join(chunk(3000+i,variant(*r) if r is not None else b'') for i,r in enumerate(resources))
    raw=table(chunk(459,b''.join(chunk(2000+i,channels) for i in range(13))))
    return oracle.validated_fpv(raw)[1]


class FpvResourceRulesTests(unittest.TestCase):
    def test_hand_fallback_is_case_sensitive_substring_not_a_general_default_rule(self):
        for source,expected in ((None,'FPV_hands'),('w_default','FPV_hands'),
                                ('xw_default.4ds','FPV_hands'),('W_DEFAULT.4ds','W_DEFAULT'),
                                ('w_Default','w_Default'),('','')):
            with self.subTest(source=source):self.assertEqual(oracle.hand_name(source),expected)

    def test_hand_name_truncates_only_last_extension_without_case_or_encoding_changes(self):
        for source,expected in (('FPV_hands_r.4ds','FPV_hands_r'),('a.b.c','a.b'),('.4ds',''),
                                ('A'*19,'A'*19),('manche_é.4ds','manche_é'),('name.','name')):
            with self.subTest(source=source):self.assertEqual(oracle.hand_name(source),expected)
        for bad in ('A'*20,'embedded\0name','x\n','x\x7f','💥',True,12,b'name'):
            with self.subTest(source=bad),self.assertRaises(ValueError):oracle.hand_name(bad)

    def test_first_populated_threshold_covers_all_benelli_draws_without_using_empty_sentinels(self):
        projection=projected();before=copy.deepcopy(projection)
        for state_id in range(13):
            for draw in range(101):
                result=oracle.request_plan(projection,359,state_id,draw)
                self.assertEqual(result['resource']['name'],'first.I3D');self.assertEqual(result['channel_ordinal'],0)
        self.assertEqual(projection,before)

    def test_signed_cumulative_thresholds_keep_equality_and_zero_draw_semantics(self):
        projection=projected([('negative',0xffffffff),('zero',0),('middle',50),('last',100)])
        for draw,channel in ((0,1),(1,2),(50,2),(51,3),(100,3)):
            self.assertEqual(oracle.request_plan(projection,359,0,draw)['channel_ordinal'],channel)
        with self.assertRaisesRegex(ValueError,'not covered'):
            oracle.request_plan(projected([('a',10),('b',20),('c',30),('d',40)]),359,0,100)

    def test_absent_cells_or_no_eligible_state_are_refused_instead_of_inventing_defaults(self):
        for resources in ([None,('b',100),None,None],[('a',30),None,('c',100),None]):
            with self.assertRaisesRegex(ValueError,'unqualified empty-cell'):
                oracle.request_plan(projected(resources),359,0,50)
        for resources in ([None]*4,[('a',0),None,None,None],[('a',0xffffffff),None,None,None]):
            with self.assertRaisesRegex(ValueError,'No populated positive'):
                oracle.request_plan(projected(resources),359,0,0)
        with self.assertRaisesRegex(ValueError,'not been loaded'):oracle.request_plan(projected(),358,0,0)

    def test_slot_state_draw_bounds_and_bool_aliases_are_refused(self):
        projection=projected()
        for slot,state_id,draw in ((True,0,0),(359,True,0),(359,0,True),(-1,0,0),(500,0,0),
                                   (359,13,0),(359,-1,0),(359,0,-1),(359,0,101),(359,0,1.0)):
            with self.subTest(args=(slot,state_id,draw)),self.assertRaises(ValueError):
                oracle.request_plan(projection,slot,state_id,draw)

    def test_only_successfully_loaded_state_can_be_consumed(self):
        machine=object.__new__(oracle.FpvResourceOracle);machine.loaded_projection=None
        with self.assertRaisesRegex(ValueError,'successfully loaded'):machine.inspect_request(359,0,50)
        machine.loaded_projection=projected()
        with patch.object(oracle.FpvTableOracle,'inspect_table',side_effect=ValueError('failed traversal')):
            with self.assertRaisesRegex(ValueError,'failed traversal'):machine.inspect_table(benelli_table())
        self.assertIsNone(machine.loaded_projection)

    def test_unreviewed_images_cannot_execute_any_native_path(self):
        for cls in (oracle.HandsNameOracle,oracle.FpvResourceOracle):
            with self.subTest(cls=cls),self.assertRaisesRegex(ValueError,'Unreviewed decompressed'):cls(b'invented')

    def test_active_hooks_refuse_loaders_rng_parent_routines_and_out_of_range_instruction_ends(self):
        hand=object.__new__(oracle.HandsNameOracle);hand.hand_active=True
        fpv=object.__new__(oracle.FpvResourceOracle);fpv.request_active=True
        for machine,allowed,denied in ((hand,0x492338,(0x490930,0x7e5302,0x7e0850,0x4923c0)),
                                      (fpv,0x492e21,(0x41fc10,0x7e5302,0x490e00,0x492f15))):
            machine.on_code(None,allowed,1,None)
            for address in denied:
                with self.subTest(address=hex(address)),self.assertRaisesRegex(ValueError,'refused'):
                    machine.on_code(None,address,1,None)
            with self.assertRaises(ValueError):machine.on_code(None,allowed,0x1000,None)

    def test_early_emulation_stop_is_not_a_successful_argument_path(self):
        machine=Mock();machine.uc.reg_read.return_value=0
        with self.assertRaisesRegex(ValueError,'budget'):oracle.run_block(machine,10,20)
        machine.uc.emu_start.assert_called_once_with(10,20,count=5000,timeout=1_000_000)

    def test_request_failure_restores_seeded_selector_and_all_animation_cache_cells(self):
        machine=object.__new__(oracle.FpvResourceOracle);machine.loaded_projection=projected()
        cell=oracle.request_plan(machine.loaded_projection,359,0,50);name=b'first.I3D'
        pointer=machine.STRINGS;machine.next_address=pointer+32;machine.allocations={pointer:len(name)+9}
        before=b'\xcd'*0x4d000
        machine.get=Mock(side_effect=lambda address:{machine.FPV+cell['name_member_offset']:pointer,
                                                     pointer:1,pointer+4:len(name)}[address])
        def read(address,size):
            if address==pointer+8:return name+b'\0'
            if address==machine.FPV:return before
            if address==pointer:return bytes(size)
            raise AssertionError((address,size))
        machine.uc=Mock();machine.uc.mem_read.side_effect=read
        machine.reg=SimpleNamespace(UC_X86_REG_ESP=1,UC_X86_REG_EBP=2,UC_X86_REG_ESI=3,UC_X86_REG_EFLAGS=4)
        with patch.object(oracle,'run_block',side_effect=ValueError('deliberate refusal')):
            with self.assertRaisesRegex(ValueError,'deliberate refusal'):machine.inspect_request(359,0,50)
        self.assertFalse(machine.request_active)
        self.assertEqual(machine.uc.mem_write.call_args.args,(machine.FPV,before))


class HandsMachine:
    def __init__(self,mutate=None):self.mutate=mutate
    def inspect_name(self,source):
        result={'source_name':source,'requested_name':oracle.hand_name(source),'native_name_argument_matches':True,
                'source_read_only_unchanged':True,'stopped_before_loader':True,'model_loader_executed':False}
        if self.mutate:self.mutate(result)
        return result


class ResourceMachine:
    def __init__(self,mutate=None):self.mutate=mutate;self.requests=[]
    def inspect_table(self,raw):
        _,self.projection=oracle.validated_fpv(raw)
        return {'table_sha256':oracle.sha(raw),'native_nested_traversal_matches':True,'native_strings_and_values_match':True}
    def inspect_request(self,slot,state_id,draw):
        cell=oracle.request_plan(self.projection,slot,state_id,draw);self.requests.append((slot,state_id,draw))
        result={'requested_name':cell['resource']['name'],'channel':cell['channel_ordinal'],
                'slot':slot,'state_index':state_id,'synthetic_draw':draw,'cache_member_offset':cell['name_member_offset']-16,
                'native_request_arguments_match':True,'loaded_names_and_values_unchanged':True,'resource_loader_executed':False}
        if self.mutate:self.mutate(result)
        return result


class FpvResourceAuditTests(unittest.TestCase):
    def run_audit(self,hand=None,fpv=None,changed=False):
        one=bytearray(invented_slot(kind=2));one[8:28]=b'FPV_hands\0'.ljust(20,b'\0')
        odd=bytearray(invented_slot(kind=1));odd[8:28]=b'FPV_hands_r\0'.ljust(20,b'\0')
        items=items_table([bytes(one),bytes(odd),None]);animation=benelli_table()
        sources={(archive,'tables/items.sav'):items for archive in
                 ('others.DTA','Patch.dta','SabreSquadron.dta','PatchX01.dta')}
        sources.update({(archive,'tables/fpvanims.sav'):animation for archive in ('others.DTA','SabreSquadron.dta')})
        pins={key:(len(raw),oracle.sha(raw)) for key,raw in sources.items()}
        if changed:sources['SabreSquadron.dta','tables/items.sav']+=b'changed'
        with patch('benelli_table_audit.TABLE_PINS',pins):
            return oracle.audit(sources,hand or HandsMachine(),fpv or ResourceMachine())

    def test_originals_and_disabled_addition_request_13_states_for_3_explicit_draws(self):
        machine=ResourceMachine();report=self.run_audit(fpv=machine)
        self.assertEqual(len(machine.requests),156);self.assertEqual(len(report['hands_name_cases']),13)
        self.assertEqual(report['commercial_hand_references']['SabreSquadron.dta'][1]['kind'],1)
        for case in report['animation_cases'].values():self.assertEqual(len(case['requests']),39)
        for key in ('inventory_item_selection_qualified','model_or_animation_loading_qualified',
                    'native_joint_name_binding_qualified','game_started','game_modified','playable_weapon'):
            self.assertFalse(report[key])

    def test_changed_sources_and_incomplete_hands_receipts_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'reviewed item source'):self.run_audit(changed=True)
        for key,value in (('requested_name','wrong'),('native_name_argument_matches',1),
                          ('source_read_only_unchanged',False),('stopped_before_loader',False),('model_loader_executed',True)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Incomplete hands'):
                self.run_audit(hand=HandsMachine(lambda receipt:receipt.update({key:value})))

    def test_incomplete_animation_receipts_fail_closed(self):
        for key,value in (('requested_name','wrong'),('channel',True),('channel',1),
                          ('native_request_arguments_match',1),('loaded_names_and_values_unchanged',False),
                          ('resource_loader_executed',True),('slot',10),('state_index',True),
                          ('synthetic_draw',0.0),('cache_member_offset',0)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'Incomplete animation'):
                self.run_audit(fpv=ResourceMachine(lambda receipt:receipt.update({key:value})))


if __name__=='__main__':unittest.main()
