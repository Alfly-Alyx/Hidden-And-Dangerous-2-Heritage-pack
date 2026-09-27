#!/usr/bin/env python3
"""Native joint discovery on invented trees and modern flat FPV candidates."""
import argparse
import hashlib
from itertools import permutations
import json
from pathlib import Path
import struct
import sys

from build_modern_equipment_fpv_rig import compile_flat_rig
from ls3d_math_oracle import DLL_SHA
from ls3d_skin_binding_oracle import SkinBindingOracle, reference
from menu_gui_audit import parse_4ds_nodes


def node(parent=-1, kind=1, visual=2, bone=None):
    return {'parent': parent, 'frame_type': kind, 'visual_type': visual, 'bone_id': bone}


def controls():
    for count in (0, 1, 2, 8, 36, 64):
        for chain in (False, True):
            for reverse in (False, True):
                ids = list(reversed(range(count))) if reverse else list(range(count))
                nodes = [node()]+[node(i if chain else 0, 10, None, bone) for i, bone in enumerate(ids)]
                for present in (False, True):
                    yield nodes, present
    for ids in permutations(range(4)):
        yield [node()]+[node(0, 10, None, i) for i in ids], True
    for subtype in (2, 3):
        # Nested skin terminates its sibling loop; parent's next sibling survives.
        yield [node(), node(0, 10, None, 0), node(0, 6, None), node(2, 10, None, 1),
               node(2, 1, subtype), node(4, 10, None, 3), node(2, 10, None, 4),
               node(0, 10, None, 2)], True
        # At the root-child level it also prevents scanning later root children.
        yield [node(), node(0, 10, None, 0), node(0, 1, subtype),
               node(2, 10, None, 1), node(0, 10, None, 2)], True
    yield [node(), node(0, 1, 0), node(1, 10, None, 0),
           node(0, 1, 1), node(3, 6, None), node(4, 10, None, 1)], True


def check_receipt(row, nodes, present):
    expected = reference(nodes, present)
    if (any(type(row.get(k)) is not type(v) or row.get(k) != v for k, v in expected.items())
            or any(row.get(k) is not True for k in ('native_joint_discovery_and_ownership_match',
                'unrelated_fields_preserved', 'fresh_post_load_tree_is_supplied', 'allocation_is_bounded_double'))
            or any(row.get(k) is not False for k in ('bounds_refresh_executed', 'native_loader_executed',
                'native_clone_executed', 'palette_skin_renderer_executed', 'library_loaded', 'game_started'))):
        raise ValueError('Incomplete native skin-binding receipt')


def from_model(raw):
    return [{'parent': n['parent_id']-1, 'frame_type': n['frame_type'], 'visual_type': n['visual_type'],
             'bone_id': struct.unpack_from('<I', raw, n['end']-4)[0] if n['frame_type'] == 10 else None}
            for n in parse_4ds_nodes(raw)['nodes']]


def audit(machine):
    totals = dict(cases=0, successful_bindings=0, bound_bones=0, visual_type_queries=0)
    for nodes, present in controls():
        row = machine.bind(nodes, present)
        check_receipt(row, nodes, present)
        totals['cases'] += 1
        totals['successful_bindings'] += row['success']
        totals['bound_bones'] += row['bone_count']
        totals['visual_type_queries'] += row['native_visual_type_lookup_calls']
    models = {}
    for case in ('F35', 'F2'):
        raw, _, _ = compile_flat_rig(case)
        nodes = from_model(raw)
        row = machine.bind(nodes)
        check_receipt(row, nodes, True)
        if row['bone_count'] != 8 or row['stopped_at_nested_skin_nodes']:
            raise ValueError('Flat hose did not resolve all eight bones')
        models[case] = {'model_sha256': hashlib.sha256(raw).hexdigest(), 'nodes': len(nodes), **row}
    return {'schema_version': 1, 'scope': 'native_skin_joint_discovery_with_supplied_post_load_tree',
            'library_sha256': DLL_SHA, 'synthetic': totals, 'models': models,
            'native_joint_discovery_and_ownership_match': True,
            'allocation_is_bounded_double': True, 'bounds_refresh_executed': False,
            'native_loader_executed': False, 'native_clone_executed': False,
            'palette_skin_renderer_executed': False, 'game_started': False, 'game_modified': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', required=True, type=Path)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():
            raise ValueError('Report exists; use a fresh name')
        report = audit(SkinBindingOracle(args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True, exist_ok=True)
            with args.json_output.open('x', encoding='utf-8') as stream:
                json.dump(report, stream, indent=2)
                stream.write('\n')
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError, ImportError) as error:
        print('Native skin binding audit refused: '+str(error), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
