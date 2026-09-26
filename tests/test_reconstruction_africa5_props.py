"""Africa 5 modern recipe contracts; no game execution or commercial fixtures."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_reconstruction_variant as builder


class Africa5PropRecipes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = builder.load_catalog()

    def test_fan_variants_only_target_first_child_and_keep_rotation(self):
        for kind in ('onuse', 'proximity'):
            p = self.profiles[f'africa5-fan-{kind}-oneshot']
            self.assertEqual(p['classification'], 'MODERNE')
            self.assertEqual(p['actor'], 'm_AF5_vetrak.Rectangle07')
            self.assertEqual(p['owner_model']['model_entry'], 'models/m_af5_vetrak01.4ds')
            self.assertEqual(p['asset_evidence'][0]['size'], 8201)
            self.assertIn('scripts/africa5/af4_vetrak02.scr', p['evidence'])
            self.assertFalse(p.get('additional_changes'))
            self.assertEqual(len(p['edits']), 2)
            tail = '\nFRM_RotateY(this, 108000, 360);\nDelay(8000);\ngoto LOOP;'
            raw = '\n'.join(e['before'] for e in p['edits']) + tail
            self.assertTrue(builder.apply_edits(raw.encode(), p['edits']).endswith(tail.encode()))

    def test_fan_latch_and_proximity_disarm_precede_single_conversion(self):
        for kind in ('onuse', 'proximity'):
            handler = self.profiles[f'africa5-fan-{kind}-oneshot']['edits'][1]['after']
            self.assertEqual(handler.count('FRM_CreatePhysicalObject(this, 5);'), 1)
            self.assertIn('(_PlayerInRange(3)) AND (heritage_physical_created == 0)', handler)
            self.assertLess(handler.index('heritage_physical_created = 1;'), handler.index('FRM_CreatePhysicalObject'))
            self.assertLess(handler.index('FRM_CreatePhysicalObject'), handler.index('EndScript();'))
            if kind == 'proximity':
                self.assertLess(handler.index('SetWhenever(heritage_fan_pir, false);'), handler.index('FRM_CreatePhysicalObject'))
            else:
                self.assertIn('OnUse()', handler)
                self.assertNotIn('Whenever', handler)

    def test_reader_requires_two_exact_prop_resources(self):
        p = self.profiles['africa5-guard19-reading-interruptible']
        self.assertEqual(p['actor'], 'AF4_19')
        self.assertEqual(p['classification'], 'MODERNE')
        self.assertEqual([s['instance'] for s in p['model_checks']], ['m_AF5_slozky01a7', 'm_AF5_slozky01b14'])
        self.assertEqual(len(p['asset_evidence']), 2)
        self.assertFalse(p.get('additional_changes'))

    def test_reader_arms_flags_before_calls_and_disarms_before_cleanup(self):
        edits = self.profiles['africa5-guard19-reading-interruptible']['edits']
        for api, flag in [('HUMAN_PickObject(book, 1)', 'heritage_book_pending'),
                          ('HUMAN_ACTIVITY_Read(1, book)', 'heritage_read_active')]:
            spec = next(e for e in edits if api in e['before'])
            self.assertLess(spec['after'].index(flag + ' = 1;'), spec['after'].index(api))
        for prefix in ('OnDeath', 'OnAlarm(){', 'OnAlarmDone'):
            code = next(e['after'] for e in edits if e['before'].startswith(prefix))
            self.assertLess(code.index('heritage_read_active = 0;'), code.index('HUMAN_ACTIVITY_Read(0, book)'))
            self.assertLess(code.index('heritage_book_pending = 0;'), code.index('HUMAN_DropObject()'))
            self.assertNotIn('DisableAlarms', code)
        alarm = next(e['after'] for e in edits if e['before'].startswith('OnAlarm(){'))
        self.assertNotIn('if (heritage_book_pending', alarm)  # commercial drop is unconditional
        death = next(e['after'] for e in edits if e['before'].startswith('OnDeath'))
        self.assertNotIn('HUMAN_SETMODE', death)

    def test_reader_repeated_signal_does_not_restart_active_cycle(self):
        edits = self.profiles['africa5-guard19-reading-interruptible']['edits']
        code = next(e['after'] for e in edits if e['before'].startswith('OnSignal(1)'))
        self.assertIn('if (heritage_cycle_running == 0)', code)
        self.assertLess(code.index('heritage_cycle_running = 1;'), code.index('goto ACTIVATE;'))
        for spec in edits:
            self.assertNotIn('SetObjective', spec['after'])
            self.assertNotIn('FRM_Create', spec['after'])
            self.assertNotIn('SendSignal', spec['after'])


if __name__ == '__main__':
    unittest.main()
