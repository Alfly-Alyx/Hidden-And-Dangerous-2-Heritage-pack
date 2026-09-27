#!/usr/bin/env python3
"""Private native position/scale sampling; never scene, blending or skin."""
import argparse
import json
import math
from pathlib import Path
import sys

from build_benelli_fpv_lab import read_sources,MANIFEST,STATES,sha
from five_ds import parse_5ds
from benelli_rotation_audit import sample_times
from ls3d_math_oracle import MathOracle,DLL_SHA,TIME_FACTOR


def audit(sources,machine,progress=None):
    reports={};branches=('held_first','held_last','linear')
    for state in STATES:
        name='models/#fpvbeneli'+state+'.5ds';raw=sources[name];clip=parse_5ds(raw)
        report={'source':name,'size':len(raw),'sha256':sha(raw),'channels':{}}
        for kind in ('position','scale'):
            stats={'channels':0,'keys':0,'samples':0,'max_error':0,'branches':dict.fromkeys(branches,0)}
            for track in clip['tracks']:
                channel=track['channels'].get(kind)
                if channel is None:continue
                frames,values=channel['frames'],channel['values']
                stats['channels']+=1;stats['keys']+=len(frames)
                for time in sample_times(frames):
                    result=machine.sample_vector(kind,frames,values,time)
                    if (result.get('native_channel_sample_match') is not True or result.get('inputs_preserved') is not True
                            or result.get('channel_kind')!=kind or result.get('branch') not in branches
                            or any(result.get(key) is not False for key in ('blending_executed','whole_track_evaluated',
                                'time_unit_seconds_qualified','library_loaded','game_started','scene_evaluated'))
                            or type(result.get('max_error')) not in (int,float) or not math.isfinite(result['max_error'])
                            or not 0<=result['max_error']<=2e-6 or result.get('time_integer_units_per_frame')!=40
                            or result.get('time_factor_float32')!=TIME_FACTOR):
                        raise ValueError('Invalid native vector sampling receipt')
                    value=result.get('value')
                    if not isinstance(value,list) or len(value)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in value):
                        raise ValueError('Invalid sampled vector receipt')
                    stats['max_error']=max(stats['max_error'],result['max_error'])
                    stats['branches'][result['branch']]+=1;stats['samples']+=1
            report['channels'][kind]=stats
        reports[state]=report
        if progress:progress(state,report)
    totals={kind:{key:sum(r['channels'][kind][key] for r in reports.values())
                  for key in ('channels','keys','samples')} for kind in ('position','scale')}
    if not totals['position']['channels']:raise ValueError('No Benelli position channels')
    return {'schema_version':1,'scope':'private_benelli_native_vector_channel_sampling',
            'library_sha256':DLL_SHA,'clips':reports,'totals':totals,
            'max_error':max(s['max_error'] for r in reports.values() for s in r['channels'].values()),
            'time_integer_units_per_frame':40,'time_factor_float32':TIME_FACTOR,
            'time_unit_seconds_qualified':False,'partial_pose_inheritance_qualified':False,
            'blending_executed':False,'skin_evaluated':False,'native_library_loaded':False,
            'game_started':False,'game_modified':False,'playable_weapon':False,
            'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report exists; use a fresh name')
        manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
        sources,excluded=read_sources(args.game,manifest,archives_only=args.archives_only)
        report=audit(sources,MathOracle((args.game/'LS3DF.dll').read_bytes()),
                     lambda state,row:print('Checked vector channels: '+state,file=sys.stderr,flush=True))
        report['source_pins']=manifest['sources'];report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('source_pins','excluded_loose_overrides','clips')},indent=2))
        return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Benelli native vector audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
