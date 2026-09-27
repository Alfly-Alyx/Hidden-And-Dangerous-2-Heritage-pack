"""Original isolated resource groups; no commercial assets or native runtime."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_rigid_weapon_resource_lab import SLOTS,group,prepare,STATE_CLIPS
from build_equipment_fpv_resource_lab import require_empty_slot
from fpv_table import parse
from item_native_layout import fpv_native_projection
from fpv_resource_oracle import request_plan


class RigidWeaponResourceTests(unittest.TestCase):
    def test_all_thirteen_states_select_nine_short_resources_on_first_channel(self):
        for case,slot in SLOTS.items():
            for variant in ('H','R'):
                raw,rows=group(case,variant);table=parse(raw);projection=fpv_native_projection(table)
                self.assertEqual([g['id'] for g in table['groups']],[slot+100]);self.assertEqual(projection['cell_count'],52)
                self.assertEqual([r['clip'] for r in rows],list(STATE_CLIPS));self.assertEqual(len({r['resource_name'] for r in rows}),9)
                for row in rows:
                    self.assertLessEqual(len(row['resource_name'].split('.')[0]),19)
                    for draw in range(101):
                        selected=request_plan(projection,slot,row['state_index'],draw)
                        self.assertEqual(selected['channel_ordinal'],0);self.assertEqual(selected['resource']['name'],row['resource_name'])

    def test_six_variant_names_are_disjoint_but_each_pair_uses_exclusive_same_group(self):
        used=set()
        for case in SLOTS:
            pair=[]
            for variant in ('H','R'):
                raw,rows=group(case,variant);names={r['resource_name'] for r in rows}
                self.assertFalse(used&names);used|=names;pair.append(parse(raw)['groups'][0]['id'])
            self.assertEqual(pair[0],pair[1])
        self.assertEqual(len(used),54)

    def test_invalid_selection_and_slot_domain_refused_before_reading_resources(self):
        for case,variant in (('Other','H'),('FG42','both'),('MG34',None)):
            with self.assertRaises(ValueError):group(case,variant)
            with self.assertRaises(ValueError):prepare(case,variant,None,None,None,None,None,None)
        for slot in (27,32,358,365,True,None,362.0):
            with self.assertRaises(ValueError):require_empty_slot(None,slot)


if __name__=='__main__':unittest.main()
