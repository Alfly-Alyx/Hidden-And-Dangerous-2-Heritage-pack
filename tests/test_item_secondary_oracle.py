"""Synthetic descriptors and guarded control flow; no commercial image needed."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import Mock,patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import item_secondary_oracle as oracle
import item_secondary_audit as audit
from item_weapon_descriptor import build_weapon
from test_item_weapon_descriptor import fixture
from test_items_sav import table


def weapon(mode=5,scalar=1.0):
    spec=fixture();spec['secondary'].update(mode_raw=mode,scalar=scalar)
    return build_weapon(spec)


class Machine:
    def __init__(self,mutate=None):self.mutate=mutate
    def inspect_action(self,raw,slot):
        expected=oracle.fields(raw)
        result={**expected,'slot':slot,'native_secondary_paths_match':True,'descriptor_and_objects_unchanged':True,
                'actor_state_requests':[{'synthetic_current_state':s,'requested_state':oracle.route(expected['mode_raw'],s)} for s in range(4)],
                'hud_dispatch':oracle.hud_branch(expected['mode_raw']),'fpv_aim_state':11,'fpv_deaim_state':12,'fpv_target_member':0x30,
                'complete_aim_operation_executed':False,'scene_or_animation_calls_executed':False,
                'deaim_scalar_source_qualified':False,
                'camera_rendering_qualified':False,'game_started':False,'game_modified':False}
        if self.mutate:self.mutate(result)
        return result
    def inspect_interpolation(self,current,target,step):
        a=oracle.float_word(current,'current');b=oracle.float_word(target,'target')
        result={'current_raw':a,'target_raw':b,**oracle.interpolation(a,b,step),'native_interpolation_matches':True,
                'camera_getter_member':0x120,'scene_setter_vtable_offset':0x74,
                'scene_camera_method_executed':False,'time_step_source_qualified':False,'rendering_qualified':False}
        if self.mutate:self.mutate(result)
        return result


class SecondaryRulesTests(unittest.TestCase):
    def test_secondary_offsets_follow_primary_descriptor_size(self):
        raw=weapon();self.assertEqual(oracle.fields(raw)['mode_raw'],5)
        changed=bytearray(raw);struct.pack_into('<I',changed,136,3)
        changed[276:296]=raw[268:288]
        self.assertEqual(oracle.fields(bytes(changed))['scalar_raw'],oracle.float_word(1,'angle'))
        self.assertEqual(raw,weapon())

    def test_unreviewed_class_action_constants_and_angles_are_refused(self):
        for offset,value in ((4,0),(268,0),(272,1),(276,3),(284,0),(284,0xbf800000),(284,0x7f800000),
                             (284,0x7fc00000),(284,0x40800000)):
            changed=bytearray(weapon());struct.pack_into('<I',changed,offset,value)
            with self.subTest(offset=offset,value=value),self.assertRaises(ValueError):oracle.fields(bytes(changed))
        for raw in (b'',weapon()[:-1],weapon()+b'\0'):
            with self.assertRaises(ValueError):oracle.fields(raw)

    def test_mode_five_is_the_only_initial_state_two_path(self):
        for mode in (0,1,2,3,4,5,6,7,0xffffffff):
            self.assertEqual(oracle.route(mode,0),2 if mode==5 else 3)
            for state in (1,2,3,0xffffffff):self.assertEqual(oracle.route(mode,state),0)

    def test_hud_branch_includes_mode_five_noop_and_unsigned_out_of_range(self):
        self.assertEqual([oracle.hud_branch(n) for n in range(8)],
                         ['two_frames']*4+['one_frame','no_frame_call','hide_frames','no_frame_call'])
        self.assertEqual(oracle.hud_branch(0xffffffff),'no_frame_call')
        for value in (-1,2**32,True,5.0,'5',None):
            for func in (oracle.hud_branch,lambda v:oracle.route(v,0),lambda v:oracle.route(5,v)):
                with self.subTest(value=value),self.assertRaises(ValueError):func(value)

    def test_interpolation_moves_both_ways_and_clamps_without_overshooting(self):
        word=lambda n:oracle.float_word(n,'test')
        for current,target,step,result in ((1,2,0,1),(1,2,1000,2),(2,1,1000,1),(1,1,16,1)):
            receipt=oracle.interpolation(word(current),word(target),step)
            self.assertEqual(receipt['next_raw'],word(result));self.assertEqual(receipt['setter_requested'],current!=target)
        up=oracle.as_float(oracle.interpolation(word(1),word(2),16)['next_raw'])
        down=oracle.as_float(oracle.interpolation(word(2),word(1),16)['next_raw'])
        self.assertAlmostEqual(up,1+16*oracle.as_float(oracle.RATE_RAW),places=6)
        self.assertAlmostEqual(down,2-16*oracle.as_float(oracle.RATE_RAW),places=6)

    def test_interpolation_domain_is_finite_bounded_and_rejects_boolean_aliases(self):
        word=oracle.float_word(1,'test')
        for bad in (-1,1001,float('nan'),float('inf'),True,'16',1e100):
            with self.subTest(step=bad),self.assertRaises(ValueError):oracle.interpolation(word,word,bad)
        for value in (0,0xbf800000,0x7fc00000,0x7f800000,0x40800000,True,-1):
            for pair in ((value,word),(word,value)):
                with self.subTest(pair=pair),self.assertRaises(ValueError):oracle.interpolation(*pair,16)

    def test_unknown_image_refused_before_any_native_execution(self):
        with self.assertRaisesRegex(ValueError,'Unreviewed decompressed'):oracle.SecondaryOracle(b'invented')

    def test_each_phase_refuses_other_phase_instructions_and_whole_external_operations(self):
        machine=object.__new__(oracle.SecondaryOracle);machine.uc=Mock()
        for name,(start,ranges,stops) in oracle.PHASES.items():
            machine.phase=name;machine.on_code(None,start,1,None)
            machine.on_code(None,stops[0],1,None);machine.uc.emu_stop.assert_called()
            for address in (0x5469e0,0x492130,0x492a90,0x6987d0,0x7e0850,0x401000):
                with self.subTest(phase=name,address=address),self.assertRaisesRegex(ValueError,'refused'):
                    machine.on_code(None,address,1,None)
            with self.assertRaises(ValueError):machine.on_code(None,start,0x10000,None)

    def test_budget_failure_and_native_exception_reset_active_phase(self):
        machine=object.__new__(oracle.SecondaryOracle);machine.phase=None;machine.uc=Mock();machine.reg=Mock()
        machine.uc.reg_read.return_value=0
        with self.assertRaisesRegex(ValueError,'budget'):machine._run('toggle')
        self.assertIsNone(machine.phase)
        machine.uc.emu_start.side_effect=ValueError('deliberate native failure')
        with self.assertRaisesRegex(ValueError,'deliberate'):machine._run('toggle')
        self.assertIsNone(machine.phase)
        machine.phase='gate'
        with self.assertRaisesRegex(ValueError,'Nested'):machine._run('toggle')

    def test_incomplete_action_receipts_do_not_waive_camera_and_operation_limits(self):
        raw=weapon();receipt=oracle.checked_action(Machine(),raw,359)
        self.assertFalse(receipt['camera_rendering_qualified'])
        for key,value in (('slot',True),('slot',9),('scalar_raw',0),('mode_raw',1),('native_secondary_paths_match',1),
                          ('fpv_aim_state',12),('hud_dispatch','two_frames'),('descriptor_and_objects_unchanged',False),
                          ('game_started',True),('scene_or_animation_calls_executed',True),('actor_state_requests',None)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'receipt'):
                oracle.checked_action(Machine(lambda r:r.update({key:value})),raw,359)
        with self.assertRaisesRegex(ValueError,'receipt'):
            oracle.checked_action(Machine(lambda r:r['actor_state_requests'][0].update(synthetic_current_state=False)),raw,359)
        for invalid in (True,359.0,-1,500):
            with self.assertRaisesRegex(ValueError,'slot'):oracle.checked_action(Machine(),raw,invalid)

    def test_incomplete_camera_receipts_fail_without_claiming_rendering(self):
        self.assertTrue(oracle.checked_interpolation(Machine(),1,2,16)['native_interpolation_matches'])
        for key,value in (('next_raw',0),('setter_requested',1),('native_interpolation_matches',1),
                          ('scene_camera_method_executed',True),('time_step_source_qualified',True),('rendering_qualified',True)):
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'receipt'):
                oracle.checked_interpolation(Machine(lambda r:r.update({key:value})),1,2,16)

    def test_camera_failure_restores_seeded_fpv_state(self):
        machine=object.__new__(oracle.SecondaryOracle);machine.uc=Mock();machine.reg=Mock()
        before=b'\xcd'*0x4d000
        machine.uc.mem_read.side_effect=lambda address,size:before if address==machine.FPV else bytes(size)
        machine.get=lambda address:{0x80ff1c:oracle.RATE_RAW,0x80fe20:0x465e50,0x80fe24:0x465e80}[address]
        machine._run=Mock(side_effect=ValueError('deliberate camera failure'))
        with self.assertRaisesRegex(ValueError,'deliberate camera'):machine.inspect_interpolation(1,2,16)
        self.assertEqual(machine.uc.mem_write.call_args.args,(machine.FPV,before))

    def test_secondary_failure_restores_seeded_fpv_state_and_actor_fixture(self):
        machine=object.__new__(oracle.SecondaryOracle);machine.uc=Mock();machine.reg=Mock()
        before=b'\xcd'*0x4d000
        machine.uc.mem_read.side_effect=lambda address,size:before if address==machine.FPV else bytes(size)
        machine.get=Mock(return_value=machine.HEAP+0x100);machine.inspect_record=Mock()
        machine._run=Mock(side_effect=ValueError('deliberate action failure'))
        with self.assertRaisesRegex(ValueError,'deliberate action'):machine.inspect_action(weapon(),359)
        self.assertEqual(machine.uc.mem_write.call_args.args,(machine.FPV,before))
        self.assertIn(unittest.mock.call(machine.HEAP+0x8000+0x52c,bytes(4)),machine.uc.mem_write.call_args_list)


class SecondaryAuditTests(unittest.TestCase):
    def run_audit(self,changed=None,machine=None):
        slots=[None]*30;slots[0]=weapon(1,0.3);slots[23]=weapon()
        data=table(slots);tables={(a,'tables/items.sav'):data for a in ('others.DTA','Patch.dta','SabreSquadron.dta','PatchX01.dta')}
        tables['others.DTA','tables/item_shoot.tbl']=b'invented-editor-table'
        pins={key:(len(raw),oracle.sha(raw)) for key,raw in tables.items()}
        if changed:changed(tables)
        with patch('benelli_table_audit.TABLE_PINS',pins),patch('item_editor_table.require_row',return_value={'fields':{}}),\
             patch('build_benelli_descriptor_lab.specification',return_value=fixture()):
            return audit.audit(tables,machine or Machine())

    def test_all_layers_and_modern_descriptor_are_checked_with_both_camera_directions(self):
        report=self.run_audit()
        self.assertEqual([r['records_checked'] for r in report['layers'].values()],[2]*4)
        self.assertEqual(report['modern_benelli']['slot'],359);self.assertEqual(report['distinct_camera_targets'],2)
        self.assertEqual([r['mode_raw'] for r in report['synthetic_mode_cases']],[4,6,7,0xffffffff])
        self.assertEqual(len(report['camera_cases']),12)
        for key in ('complete_aim_operation_executed','native_scene_methods_executed','input_and_cooldown_gates_qualified',
                    'animation_timing_qualified','game_started','game_modified','playable_weapon'):
            self.assertFalse(report[key])

    def test_changed_missing_sources_and_invalid_receipts_fail_closed(self):
        for mutation in (lambda t:t.pop(('Patch.dta','tables/items.sav')),
                         lambda t:t.update({('SabreSquadron.dta','tables/items.sav'):b'changed'}),
                         lambda t:t.update({('others.DTA','tables/item_shoot.tbl'):b'changed'})):
            with self.assertRaises(ValueError):self.run_audit(changed=mutation)
        with self.assertRaisesRegex(ValueError,'receipt'):
            self.run_audit(machine=Machine(lambda r:r.update(game_started=True)))


if __name__=='__main__':unittest.main()
