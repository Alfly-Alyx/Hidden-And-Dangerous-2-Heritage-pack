"""Invented binary fixtures: model ownership is not runtime physics proof."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_reconstruction_variant as builder
from menu_gui_audit import parse_4ds_nodes
from model_instance import model_instance, resolve_model_child
from test_burgundy_ambient_patch import block, string, scene
from test_reconstruction_variants import fixture, field, MemorySources


def instance(name='Fixture', resource='fabricated', kind=9):
    return block(0x4010, b''.join([
        block(0x4011, struct.pack('<I', kind)), string(0x10, name), string(0x2012, resource),
        block(0x20, struct.pack('<3f', 1, 2, 3)), block(0x2C, struct.pack('<3f', 4, 5, 6)),
        block(0x22, struct.pack('<4f', 1, 0, 0, 0)), block(0x2D, struct.pack('<3f', 1, 1, 1)),
    ]))


def mesh(name='Triangle', parent=0, index=2, material=1, instance_id=0):
    node = (struct.pack('<BBHH', 1, 0, 0x1800, parent)
            + struct.pack('<3f4f3f', 0, 0, 0, 0, 0, 0, 1, 1, 1, 1)
            + b'\0'*5 + bytes([len(name)]) + name.encode() + b'\0')
    if instance_id:
        return node + struct.pack('<H', instance_id)
    vertices = b''.join(struct.pack('<8f', *point, 0, 0, 1, 0, 0)
                        for point in ((0, 0, 0), (1, 0, 0), (0, 1, 0)))
    return (node + struct.pack('<HBfIH', 0, 1, 0, 0, 3) + vertices
            + struct.pack('<BH3HH', 1, 1, 0, 1, index, material))


def model(*nodes):
    material = struct.pack('<I', 1) + b'\0'*73
    return (b'4DS\0' + struct.pack('<H', 41) + b'\0'*8 + struct.pack('<H', 1)
            + material + struct.pack('<H', len(nodes)) + b''.join(nodes) + b'\0')


SPEC = {'instance': 'Fixture', 'node': 'Triangle', 'model_entry': 'models/fabricated.4ds'}


class ModelInstanceTests(unittest.TestCase):
    def resolve(self, data=None, raw_scene=None, spec=None):
        return resolve_model_child(raw_scene if raw_scene is not None else scene([instance()]),
                                   data if data is not None else model(mesh()),
                                   'Fixture.Triangle', spec if spec is not None else SPEC)

    def test_exact_model_and_direct_mesh_without_physics_claim(self):
        proof = self.resolve()
        self.assertEqual(proof['instance']['world_position'], [4, 5, 6])
        self.assertEqual(proof['node']['rotation_serialized'], [0, 0, 0, 1])
        self.assertEqual(proof['lods'][0]['triangles'], 1)
        self.assertEqual(proof['lods'][0]['local_bounds'], [[0, 0, 0], [1, 1, 0]])
        self.assertFalse(proof['physics_validated'])
        self.assertFalse(proof['world_child_transform_computed'])

    def test_name_union_or_wrong_model_cannot_prove_instance(self):
        for raw in (scene([instance(resource='other')]), scene([instance(kind=6)]),
                    scene([instance(name='Other')]), scene([instance(), instance()]),
                    string(0x10, 'Fixture') + string(0x2012, 'fabricated')):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.resolve(raw_scene=raw)

    def test_child_must_be_unique_root_and_own_no_other_nodes(self):
        for raw in (model(mesh(parent=2), mesh('Other')), model(mesh(), mesh()),
                    model(mesh(), mesh('Other', parent=1)), model(mesh('Other'))):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.resolve(raw)

    def test_instanced_vertices_invalid_faces_materials_and_tail_refused(self):
        for raw in (model(mesh(instance_id=1)), model(mesh(index=3)), model(mesh(material=2)),
                    model(mesh()) + b'tail', model(mesh())[:-1]):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.resolve(raw)

    def test_nonfinite_child_and_scene_transforms_refused(self):
        raw = model(mesh())
        node = parse_4ds_nodes(raw)['nodes'][0]
        for offset in (node['position_offset'], node['position_offset']+12,
                       node['position_offset']+28):
            damaged = bytearray(raw)
            struct.pack_into('<f', damaged, offset, float('nan'))
            with self.assertRaisesRegex(ValueError, 'transform'):
                self.resolve(bytes(damaged))
        raw_scene = scene([instance()]).replace(struct.pack('<3f', 4, 5, 6),
                                               struct.pack('<3f', 4, float('inf'), 6))
        with self.assertRaisesRegex(ValueError, 'transform'):
            self.resolve(raw_scene=raw_scene)

    def test_spec_does_not_accept_paths_or_hierarchical_guessing(self):
        for key, value in [('model_entry', 'models/../x.4ds'), ('node', 'Other'),
                           ('instance', 'Fixture.Parent'), ('node', '')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.resolve(spec={**SPEC, key: value})


class ModelRecipeTests(unittest.TestCase):
    def setUp(self):
        self.profile, self.files = fixture()
        self.model = model(mesh())
        self.scene_entry = 'missions/example/scene2.bin'
        self.files[self.scene_entry] = ('missions.dta', scene([instance()]))
        self.profile['evidence'][self.scene_entry] = {
            'archive': 'missions.dta', 'size': len(self.files[self.scene_entry][1]),
            'sha256': builder.digest(self.files[self.scene_entry][1])}
        self.profile['asset_evidence'] = [{'path': SPEC['model_entry'], 'archive': 'models.dta',
            'size': len(self.model), 'sha256': builder.digest(self.model)}]
        self.sources = MemorySources(self.files)
        self.sources.read_asset = lambda name, archive: self.model

    def use_model_owner(self):
        self.profile.update(actor='Fixture.Triangle', owner_entry=self.scene_entry, owner_model=SPEC)
        registry = b'\0'*6 + field(1, 'Fixture.Triangle') + field(1, 'source.scr')
        self.files['missions/example/scripts.dta'] = ('missions.dta', registry)
        self.profile['evidence']['missions/example/scripts.dta'].update(
            size=len(registry), sha256=builder.digest(registry))

    def test_model_owner_proof_in_atomic_report_and_not_exported(self):
        self.use_model_owner()
        payload, report = builder.prepare_changes(self.profile, self.sources)
        self.assertEqual(report['changes'][0]['model_owner_proof']['node']['name'], 'Triangle')
        self.assertEqual(list(payload), [self.profile['source']])
        self.assertNotIn(self.model, next(iter(payload.values())))

    def test_prop_check_is_independent_of_script_owner(self):
        self.profile['model_checks'] = [SPEC]
        _, report = builder.prepare_changes(self.profile, self.sources)
        self.assertEqual(report['actor'], 'Owner')
        self.assertEqual(report['model_checks'][0]['instance']['instance'], 'Fixture')

    def test_prop_checks_need_pins_typed_scene_unique_targets(self):
        self.profile['model_checks'] = [SPEC]
        for mutation in ('pin', 'scene', 'duplicate', 'invalid'):
            p = copy.deepcopy(self.profile)
            if mutation == 'pin': p['asset_evidence'] = []
            elif mutation == 'scene': del p['evidence'][self.scene_entry]
            elif mutation == 'duplicate': p['model_checks'].append(SPEC)
            else: p['model_checks'][0]['instance'] += '.sub'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                builder.model_checks(p)

    def test_changed_resource_refuses_and_owner_needs_model_pin(self):
        self.use_model_owner()
        self.model += b'changed'
        with self.assertRaisesRegex(ValueError, 'asset changed'):
            builder.prepare_changes(self.profile, self.sources)
        self.profile['asset_evidence'] = []
        with self.assertRaisesRegex(ValueError, 'pinned model'):
            builder.change_specs(self.profile)

    def test_model_source_shadowed_by_patch_or_unknown_patch_refused(self):
        class Archive:
            def read(inner, entry): return self.model
        with tempfile.TemporaryDirectory() as directory:
            sources = builder.ArchiveSources(Path(directory), archives_only=True)
            path = SPEC['model_entry']
            sources.index = {'models.dta': (Archive(), {path: [object()]})}
            self.assertEqual(sources.read_asset(path, 'models.dta'), self.model)
            sources.index['Patch.dta'] = (Archive(), {path: [object()]})
            with self.assertRaisesRegex(ValueError, 'shadowed'):
                sources.read_asset(path, 'models.dta')
            self.assertEqual(sources.read_asset(path, 'Patch.dta'), self.model)
            sources.index['PatchX01.dta'] = (Archive(), {path: [object()]})
            with self.assertRaisesRegex(ValueError, 'Unreviewed'):
                sources.read_asset(path, 'Patch.dta')


if __name__ == '__main__':
    unittest.main()
