#!/usr/bin/env python3
"""Private native sampling of pinned Benelli rotation channels, no scene/skin."""
import argparse
import json
import math
from pathlib import Path
import sys

from build_benelli_fpv_lab import read_sources,MANIFEST,STATES,sha
from five_ds import parse_5ds
from ls3d_math_oracle import MathOracle,DLL_SHA,TIME_FACTOR,NEAR_UNIT_SQUARED_TOLERANCE


def sample_times(frames):
    limit=65535*40+39
    times={0}
    for frame in frames:
        times.update(t for t in (frame*40-1,frame*40,frame*40+1) if 0<=t<=limit)
    times.update((a+b)*20 for a,b in zip(frames,frames[1:]))
    return sorted(times)


def audit(sources,machine):
    reports={};branches=('held_first','held_last','linear','spherical')
    for state in STATES:
        name='models/#fpvbeneli'+state+'.5ds';raw=sources[name];clip=parse_5ds(raw)
        report={'source':name,'size':len(raw),'sha256':sha(raw),'frame_end':clip['frame_end'],
                'rotation_channels':0,'rotation_keys':0,'samples':0,'max_error':0,
                'max_input_squared_norm_error':0,'max_output_squared_norm_error':0,
                'branches':dict.fromkeys(branches,0)}
        for track in clip['tracks']:
            channel=track['channels'].get('rotation')
            if channel is None:continue
            frames,values=channel['frames'],channel['values']
            report['rotation_channels']+=1;report['rotation_keys']+=len(frames)
            report['max_input_squared_norm_error']=max(report['max_input_squared_norm_error'],
                max(abs(sum(v*v for v in value)-1) for value in values))
            for time in sample_times(frames):
                result=machine.sample_rotation(frames,values,time)
                if (result.get('native_channel_sample_match') is not True or result.get('inputs_preserved') is not True
                        or any(result.get(key) is not False for key in ('blending_executed','whole_track_evaluated',
                            'time_unit_seconds_qualified','library_loaded','game_started','scene_evaluated'))
                        or type(result.get('max_error')) not in (int,float) or not math.isfinite(result['max_error'])
                        or not 0<=result['max_error']<=2e-6 or result.get('branch') not in branches
                        or result.get('time_integer_units_per_frame')!=40 or result.get('time_factor_float32')!=TIME_FACTOR):
                    raise ValueError('Invalid native rotation sampling receipt')
                value=result.get('value')
                if not isinstance(value,list) or len(value)!=4 or any(type(v) not in (int,float) or not math.isfinite(v) for v in value):
                    raise ValueError('Invalid sampled quaternion receipt')
                report['max_error']=max(report['max_error'],result['max_error'])
                report['max_output_squared_norm_error']=max(report['max_output_squared_norm_error'],abs(sum(v*v for v in value)-1))
                report['branches'][result['branch']]+=1;report['samples']+=1
        if not report['rotation_channels']:raise ValueError('No Benelli rotation channels')
        reports[state]=report
    return {'schema_version':1,'scope':'private_benelli_native_rotation_channel_sampling',
        'library_sha256':DLL_SHA,'clips':reports,
        'rotation_channels':sum(r['rotation_channels'] for r in reports.values()),
        'rotation_keys':sum(r['rotation_keys'] for r in reports.values()),
        'samples':sum(r['samples'] for r in reports.values()),'max_error':max(r['max_error'] for r in reports.values()),
        'input_squared_norm_tolerance':NEAR_UNIT_SQUARED_TOLERANCE,
        'time_integer_units_per_frame':40,'time_factor_float32':TIME_FACTOR,
        'time_unit_seconds_qualified':False,'partial_pose_inheritance_qualified':False,
        'position_or_scale_channels_evaluated':False,'blending_executed':False,'skin_evaluated':False,
        'native_library_loaded':False,'game_started':False,'game_modified':False,'playable_weapon':False,
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
        report=audit(sources,MathOracle((args.game/'LS3DF.dll').read_bytes()))
        report['source_pins']=manifest['sources'];report['excluded_loose_overrides']=excluded
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps({key:value for key,value in report.items() if key not in ('source_pins','excluded_loose_overrides')},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Benelli native rotation audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
