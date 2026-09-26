"""Invented data only: no licensed scripts, scenes or models in fixtures."""
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import audit_co_burgundy3_closure as audit
from build_reconstruction_lab import script_closure
from build_reconstruction_variant import ARCHIVES, digest
from test_burgundy_ambient_patch import block, dummy, registry, scene, string


def model_record(name='depot', resource='fuel', kind=9):
    return block(0x4010, block(0x4011, struct.pack('<I', kind))
                 + string(0x10, name) + string(0x2012, resource))


def nodes():
    return {'nodes': [
        {'index': 1, 'name': 'Root', 'parent_id': 0, 'frame_type': 1},
        {'index': 2, 'name': 'Barrel', 'parent_id': 1, 'frame_type': 1},
    ]}


class StructureTests(unittest.TestCase):
    def test_model_instance_ignores_lmap_but_requires_typed_record(self):
        lmap = block(0x4010, string(0x10, 'depot') + block(0x4090, b'LMAP'))
        self.assertEqual(audit.model_instance(scene([model_record(), lmap]), 'DEPOT'), 'fuel')
        with self.assertRaises(ValueError):
            audit.model_instance(scene([lmap]), 'depot')

    def test_parent_reference_is_not_a_model_instance(self):
        with self.assertRaisesRegex(ValueError, 'typed model instance'):
            audit.model_instance(scene([dummy('other', parent='depot')]), 'depot')

    def test_duplicate_instance_or_wrong_type_is_refused(self):
        for records in [[model_record(), model_record()], [model_record(kind=6)]]:
            with self.subTest(records=len(records)), self.assertRaises(ValueError):
                audit.model_instance(scene(records), 'depot')

    def test_nonlocal_model_resource_is_refused(self):
        for value in ('../fuel', 'folder\\fuel', 'd:fuel', '..', 'f\0uel', ''):
            with self.subTest(value=value), self.assertRaises(ValueError):
                audit.model_instance(scene([model_record(resource=value)]), 'depot')

    def test_node_identity_and_ancestry(self):
        result = audit.node_evidence(nodes(), ('bArReL',))
        self.assertEqual(result[0]['index'], 2)
        self.assertEqual(result[0]['ancestry_child_first'], ['Barrel', 'Root'])

    def test_missing_substring_and_duplicate_node_are_refused(self):
        for value in ('Barr', 'Barrel_2'):
            with self.assertRaisesRegex(ValueError, 'Missing or ambiguous'):
                audit.node_evidence(nodes(), (value,))
        parsed = nodes()
        parsed['nodes'].append({**parsed['nodes'][1], 'index': 3})
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            audit.node_evidence(parsed, ('Barrel',))

    def test_cycles_dangling_parents_and_duplicate_ids_are_refused(self):
        for parent in (2, 99):
            parsed = nodes()
            parsed['nodes'][0]['parent_id'] = parent
            with self.assertRaisesRegex(ValueError, 'ancestry'):
                audit.node_evidence(parsed, ('Barrel',))
        parsed = nodes()
        parsed['nodes'][1]['index'] = 1
        with self.assertRaisesRegex(ValueError, 'indices'):
            audit.node_evidence(parsed, ('Barrel',))


class RoutingTests(unittest.TestCase):
    def test_signal_facts_distinguish_sender_and_receiver(self):
        report = audit.signal_facts({
            'bur3_maquis01.scr': 'OnAlarm() { goto DESTROY; }',
            'bur3_vybuch.scr': 'OnSignal(1) { goto BOOM; }',
            'caller.scr': 'FRM_FindFrame(x, "MAQUIS01"); _SignalPistolFired();',
        })
        self.assertTrue(report['maquis_alarm_goto_destroy'])
        self.assertEqual(report['maquis_active_signal1_handler_count'], 0)
        self.assertEqual(report['explosion_active_signal1_handler_count'], 1)
        self.assertEqual(report['maquis_literal_frame_reference_scripts'], ['caller.scr'])
        self.assertEqual(report['signal_pistol_scripts'], ['caller.scr'])

    def test_commented_protocol_is_not_reported_active(self):
        report = audit.signal_facts({
            'bur3_maquis01.scr': '//OnSignal(1) { goto DESTROY; }\n',
            'bur3_vybuch.scr': '/* DisableSignals(true); */ OnSignal(1) {}',
            'caller.scr': '// FRM_FindFrame(x, "maquis01");\n/* _SignalPistolFired(); */',
        })
        self.assertEqual(report['maquis_active_signal1_handler_count'], 0)
        self.assertFalse(report['explosion_signal1_disabled_in_script'])
        self.assertEqual(report['maquis_literal_frame_reference_scripts'], [])
        self.assertEqual(report['signal_pistol_scripts'], [])

    def test_coop_registry_is_selected_not_merged_with_solo(self):
        files = {'missions/example/scripts.dta': registry([('solo', 'missing.scr')]),
                 'missions/example/mpscripts.dta': registry([('coop', 'coop.scr')]),
                 'scripts/example/coop.scr': b'// ScriptAssign(x, "missing");'}
        result = script_closure(files, 'example', 'mpscripts.dta')
        self.assertEqual(result['reachable_scripts'], 1)
        with self.assertRaisesRegex(ValueError, 'Missing script'):
            script_closure(files, 'example')

    def test_unreviewed_registry_name_is_refused(self):
        for name in ('../scripts.dta', 'other.dta', 'scripts.dta/mpscripts.dta'):
            with self.assertRaisesRegex(ValueError, 'Unsupported script registry'):
                script_closure({}, 'example', name)


class ModelSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raw = b'x' * 54457  # Not a model; this fixture tests source selection only.
        archive = SimpleNamespace(read=lambda entry: self.raw)
        self.sources = SimpleNamespace(game=Path(self.temp.name), archives_only=False,
                                       excluded_loose_overrides={},
                                       index={n: (archive, {}) for n in ARCHIVES})
        self.sources.index['SabreSquadron.dta'][1][audit.MODEL_ENTRY] = ['fixture']

    def test_reviewed_source_and_duplicate_entry_guard(self):
        with patch.object(audit, 'MODEL_SHA', digest(self.raw)):
            self.assertEqual(audit.fuel_model(self.sources), ('SabreSquadron.dta', self.raw))
            self.sources.index['SabreSquadron.dta'][1][audit.MODEL_ENTRY].append('duplicate')
            with self.assertRaisesRegex(ValueError, 'Ambiguous'):
                audit.fuel_model(self.sources)

    def test_changed_model_and_unreviewed_patch_refused(self):
        with self.assertRaisesRegex(ValueError, 'has changed'):
            audit.fuel_model(self.sources)
        self.sources.index['PatchX01.dta'] = (None, {audit.MODEL_ENTRY: ['override']})
        with self.assertRaisesRegex(ValueError, 'PatchX01'):
            audit.fuel_model(self.sources)
        del self.sources.index['PatchX01.dta']
        del self.sources.index['SabreSquadron.dta'][1][audit.MODEL_ENTRY]
        with self.assertRaisesRegex(ValueError, 'absent'):
            audit.fuel_model(self.sources)

    def test_loose_override_refused_or_fingerprinted_without_being_used(self):
        loose = self.sources.game / audit.MODEL_ENTRY
        loose.parent.mkdir()
        loose.write_bytes(b'installed user model')
        with self.assertRaisesRegex(ValueError, 'Loose override'):
            audit.fuel_model(self.sources)
        self.sources.archives_only = True
        with patch.object(audit, 'MODEL_SHA', digest(self.raw)):
            self.assertEqual(audit.fuel_model(self.sources)[1], self.raw)
        self.assertEqual(self.sources.excluded_loose_overrides[audit.MODEL_ENTRY]['sha256'],
                         digest(b'installed user model'))
        self.assertEqual(loose.read_bytes(), b'installed user model')


if __name__ == '__main__':
    unittest.main()
