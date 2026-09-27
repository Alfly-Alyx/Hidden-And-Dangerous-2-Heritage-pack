#!/usr/bin/env python3
"""Original held-only presentation motions for the two modern equipment sets.

No hose/backpack animation, player hands, functional reload, fuel, particles,
sound or commercial source. Legacy clip-state names do not imply gameplay.
"""
import argparse
import json

import build_modern_asset as asset
from build_modern_equipment_components import ROOT,DIRECTORY,CASES,compile_components
from build_modern_animation_bank import compile_generated_model,write_generated_bank


def compile_equipment_bank(recipe,partition,spec):
    products,component_report=compile_components(recipe,partition)
    if spec.get('name')!=partition['name']:raise ValueError('Equipment animation name differs from partition')
    held=products['held'];part_names=held['report']['parts']
    expected_members=part_names+list(held['report']['anchors'])
    if spec.get('groups')!=[{'name':'MOD_held_pivot','pivot':[0,0,0],'members':expected_members}]:
        raise ValueError('Equipment bank must control only the complete held component')
    source_meshes={pair[0].name:pair for pair in asset.build_meshes(recipe)}
    meshes=[source_meshes[name] for name in part_names]
    # Native component nodes already contain -origin translations. Supplying
    # preview-translated vertices here would apply that recentering twice.
    rig,clips,meshes,report=compile_generated_model(held['data'],meshes,spec)
    report.update({'equipment_partition_sha256':component_report['specification_sha256'],
        'source_held_component_sha256':held['report']['model_sha256'],'held_component_only':True,
        'backpack_in_animation':False,'hose_in_animation':False,'hose_deformation_implemented':False,
        'functional_reload_implemented':False,'visual_state_labels_are_not_gameplay':True,
        'fpv_camera_calibrated':False})
    return rig,clips,meshes,report


def build(recipe,partition,spec,output):
    return write_generated_bank(recipe,spec,compile_equipment_bank(recipe,partition,spec),output,
                                contact_label='LOWER / RETURN (REL SLOT)')


def inputs(case):
    stem=CASES[case]
    return tuple(json.loads((DIRECTORY/f'modern-{stem}-{suffix}.json').read_text(encoding='utf-8'))
                 for suffix in ('world','components','held-animation'))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True);parser.add_argument('--output-name')
    args=parser.parse_args(argv)
    try:
        recipe,partition,spec=inputs(args.case)
        if args.output_name:report=build(recipe,partition,spec,asset.output_directory(ROOT,args.output_name))
        else:report=compile_equipment_bank(recipe,partition,spec)[3]
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError) as error:
        print('Modern equipment motion refused: '+str(error));return 1


if __name__=='__main__':raise SystemExit(main())
