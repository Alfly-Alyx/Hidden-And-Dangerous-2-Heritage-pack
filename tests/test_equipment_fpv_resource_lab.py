"""Original modern state associations; no commercial data or emulator needed."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_equipment_fpv_resource_lab import group,STATE_CLIPS,SLOTS
from fpv_table import parse
from item_native_layout import fpv_native_projection
from fpv_resource_oracle import request_plan


class EquipmentFPVResourceTests(unittest.TestCase):
    def test_thirteen_states_four_ordered_channels_and_nine_resources(self):
        for case in SLOTS:
            for hand in ('H','R'):
                raw,bindings=group(case,hand);parsed=parse(raw)
                self.assertEqual([g['id'] for g in parsed['groups']],[SLOTS[case]+100])
                self.assertEqual(len(bindings),13)
                self.assertEqual(len({r['resource_name'] for r in bindings}),9)
                self.assertEqual([r['clip'] for r in bindings],list(STATE_CLIPS))
                projection=fpv_native_projection(parsed)
                self.assertEqual(projection['cell_count'],52)
                for row in bindings:
                    for draw in range(101):
                        selected=request_plan(projection,SLOTS[case],row['state_index'],draw)
                        self.assertEqual(selected['channel_ordinal'],0)
                        self.assertEqual(selected['resource']['name'],row['resource_name'])

    def test_variant_names_disjoint_but_same_group_is_explicitly_exclusive(self):
        for case in SLOTS:
            first,a=group(case,'H');second,b=group(case,'R')
            self.assertNotEqual(first,second)
            self.assertEqual(parse(first)['groups'][0]['id'],parse(second)['groups'][0]['id'])
            self.assertFalse({r['resource_name'] for r in a}&{r['resource_name'] for r in b})
            for row in a+b:self.assertLessEqual(len(row['resource_name'].rsplit('.',1)[0]),19)

    def test_unreviewed_cases_or_hand_variants_refused(self):
        for case,hand in (('F35','both'),('F2',''),('Benelli','H'),('F35',None)):
            with self.assertRaises(ValueError):group(case,hand)


if __name__=='__main__':unittest.main()
