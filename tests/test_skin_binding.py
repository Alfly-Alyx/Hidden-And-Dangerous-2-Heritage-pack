"""Invented skin trees, ordering rules and bounded native phase guards."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from ls3d_skin_binding_oracle import SkinBindingOracle, reference, START
from skin_binding_audit import node, controls, audit, from_model
from build_modern_equipment_fpv_rig import compile_flat_rig


class SkinBindingTests(unittest.TestCase):
    def test_bone_id_orders_palette_independently_of_traversal(self):
        nodes = [node()]+[node(0, 10, None, i) for i in (2, 0, 1)]
        row = reference(nodes)
        self.assertEqual(row['collected_nodes'], [1, 2, 3])
        self.assertEqual(row['ordered_nodes'], [2, 3, 1])

    def test_no_geometry_or_no_bones_returns_false(self):
        for nodes, present in (([node()], True), ([node(), node(0, 10, None, 0)], False)):
            row = reference(nodes, present)
            self.assertFalse(row['success'])
            self.assertEqual(row['bone_count'], 0)
            self.assertEqual(row['native_visual_type_lookup_calls'], 0)

    def test_nested_skin_stops_remaining_siblings_at_its_level(self):
        for subtype in (2, 3):
            nodes = [node(), node(0, 10, None, 0), node(0, 6, None), node(2, 10, None, 1),
                     node(2, 1, subtype), node(4, 10, None, 3), node(2, 10, None, 4), node(0, 10, None, 2)]
            row = reference(nodes)
            self.assertEqual(row['collected_nodes'], [1, 3, 7])
            self.assertEqual(row['stopped_at_nested_skin_nodes'], [4])

    def test_standard_visuals_and_dummy_allow_descent(self):
        nodes = [node(), node(0, 1, 0), node(1, 1, 1), node(2, 6, None), node(3, 10, None, 0)]
        self.assertEqual(reference(nodes)['collected_nodes'], [4])
        self.assertEqual(reference(nodes)['native_visual_type_lookup_calls'], 2)

    def test_input_preserved(self):
        nodes = [node(), node(0, 10, None, 0)]
        before = deepcopy(nodes)
        reference(nodes)
        self.assertEqual(nodes, before)

    def test_invalid_root_hierarchy_types_ids_and_flags_refused(self):
        for nodes in ([], [node(0)], [node(kind=6, visual=None)],
                      [node(), node(1, 10, None, 0)], [node(), node(0, 10, None, 1)],
                      [node(), node(0, 10, None, 0), node(0, 10, None, 0)],
                      [node(), node(0, 10, None, 64)], [node(), node(0, 10, None, True)],
                      [node(), node(0, 1, 9)], [node(), node(0, 6, 0)]):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                reference(nodes)
        with self.assertRaises(ValueError):
            reference([node()], 1)

    def test_unreviewed_failure_reporting_and_renderer_are_not_allowed(self):
        machine = object.__new__(SkinBindingOracle)
        machine.phase = 'skin_binding'
        machine.on_code(None, START, 1, None)
        for address in (0x100528b3, 0x10069680, 0x1005307a, 0x100529bf):
            with self.assertRaises(ValueError):
                machine.on_code(None, address, 1, None)

    def test_corpus_includes_sixty_four_joint_limit(self):
        rows = list(controls())
        self.assertEqual(len(rows), 77)
        self.assertEqual(max(reference(nodes, present)['bone_count'] for nodes, present in rows), 64)

    def test_flat_models_expose_exactly_eight_contiguous_hose_bones(self):
        for case, count in (('F35', 38), ('F2', 36)):
            raw, _, _ = compile_flat_rig(case)
            nodes = from_model(raw)
            self.assertEqual(len(nodes), count)
            row = reference(nodes)
            self.assertEqual(row['ordered_nodes'], list(range(count-8, count)))
            self.assertEqual(row['stopped_at_nested_skin_nodes'], [])

    def test_reference_only_receipt_rejected(self):
        class Fake:
            def bind(self, *args):
                return reference(*args)
        with self.assertRaisesRegex(ValueError, 'receipt'):
            audit(Fake())

    def test_invalid_library_refused(self):
        with self.assertRaises(ValueError):
            SkinBindingOracle(b'')


if __name__ == '__main__':
    unittest.main()
