#!/usr/bin/env python3
"""Native preallocated model membership and compiled binding, private emulator."""
import argparse
import json
from pathlib import Path
import sys

from build_modern_equipment_hose import digest
from native_model_membership import ModelMembershipOracle


def audit(library,compiled):
    machine=ModelMembershipOracle(library,compiled)
    rows=[machine.scenario(count) for count in (11,128)]
    return {'schema_version':1,'scope':'private_native_model_membership','runtime_status':'pending',
        'library_sha256':digest(library),'compiled_collection_sha256':digest(compiled),'sequences':rows,
        'operations':sum(row['operations'] for row in rows),'live_lifetime_qualified':False,
        'native_allocator_or_destructor_executed':False,'game_started':False,'game_modified':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('library','compiled-collection','json-output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args(argv)
    try:
        if args.json_output.exists():raise ValueError('Use a fresh native membership report path')
        report=audit(args.library.read_bytes(),args.compiled_collection.read_bytes())
        with args.json_output.open('x',encoding='utf-8') as out:json.dump(report,out,indent=2);out.write('\n')
        print(json.dumps({'operations':report['operations'],'sequences':len(report['sequences'])},indent=2));return 0
    except (OSError,ValueError,ImportError,KeyError) as error:
        print('Native model membership refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
