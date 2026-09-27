#!/usr/bin/env python3
"""Audit original LS3DF math on invented inputs, without a native DLL load."""
import argparse
import json
import math
from pathlib import Path
import sys

from ls3d_math_oracle import MathOracle,DLL_SHA,DLL_SIZE,THRESHOLD,TIME_FACTOR


def channel_cases():
    def q(angle):return [0,0,math.sin(angle/2),math.cos(angle/2)]
    return [([2],[q(.3)],[0,79,80,81,65535*40+39]),
            ([0,10],[q(0),q(1)],[0,1,39,40,199,399,400,401]),
            ([2,4,10],[q(0),q(1),q(math.pi)],[0,79,80,81,159,160,161,399,400,401]),
            ([0,1],[q(0),q(.028)],[0,1,20,39,40,41]),
            ([0,1],[q(0),[-v for v in q(.029)]],[0,1,20,39,40,41]),
            (list(range(180)),[q(i/100) for i in range(180)],[0,1,39,40,89*40+20,178*40+20,179*40]),
            ([65533,65534,65535],[q(.3),q(.5),q(.7)],
             [0,65533*40-1,65533*40,65534*40,65535*40-1,65535*40,65535*40+39])]


def audit(machine):
    transforms=[];interpolations=[];samples=[];vectors=[]
    for axis in ((1,0,0),(0,1,0),(0,0,1),(1/math.sqrt(14),2/math.sqrt(14),3/math.sqrt(14))):
        for angle in (0,.0001,.01,.25,1,math.pi/2,math.pi,-.7):
            q=[v*math.sin(angle/2) for v in axis]+[math.cos(angle/2)]
            transforms.append(machine.transform(q,[(1,0,0),(0,1,0),(0,0,1),(.1,-.2,3)]))
    for angle in (0,.01,.028,.029,.04,.05,.3,math.pi/2,math.pi):
        for sign in (1,-1):
            left=[0,0,0,1];right=[0,0,sign*math.sin(angle/2),sign*math.cos(angle/2)]
            for amount in (0,.25,.5,.75,1):
                cases=[machine.slerp(left,right,amount,flag) for flag in (False,True)]
                if cases[0]['value']!=cases[1]['value']:raise ValueError('Legacy flags differ on this corpus')
                interpolations.extend(cases)
    for frames,values,times in channel_cases():
        for time in times:samples.append(machine.sample_rotation(frames,values,time))
        for kind in ('position','scale'):
            values=[[i/100,-i/100,1+i/100] for i in range(len(frames))]
            for time in times:vectors.append(machine.sample_vector(kind,frames,values,time))
    for row in transforms+interpolations+samples+vectors:
        if any(row.get(key) is not False for key in ('library_loaded','game_started','scene_evaluated')):
            raise ValueError('Invalid math audit execution receipt')
        if row.get('inputs_preserved') is not True:raise ValueError('Missing math input preservation proof')
    if any(r.get('native_rotation_and_point_match') is not True for r in transforms):
        raise ValueError('Incomplete transform proof')
    if any(r.get('native_interpolation_match') is not True or r.get('whole_track_evaluated') is not False
           or r.get('result_normalized') is not False or r.get('x87_control_word')!=0x27f for r in interpolations):
        raise ValueError('Incomplete interpolation proof')
    if any(r.get('native_channel_sample_match') is not True or r.get('blending_executed') is not False
           or r.get('time_unit_seconds_qualified') is not False or r.get('time_integer_units_per_frame')!=40
           or r.get('time_factor_float32')!=TIME_FACTOR for r in samples+vectors):raise ValueError('Incomplete channel sampling proof')
    for rows,fields in ((transforms,('matrix_max_error','point_max_error')),
                        (interpolations,('max_error',)),(samples+vectors,('max_error',))):
        if any(type(r.get(k)) not in (int,float) or not math.isfinite(r[k]) or not 0<=r[k]<=5e-6
               for r in rows for k in fields):raise ValueError('Invalid numerical error receipt')
    return {'schema_version':1,'scope':'pinned_ls3df_isolated_math_with_invented_inputs',
        'library':{'size':DLL_SIZE,'sha256':DLL_SHA},'synthetic_x87_control_word':0x27f,
        'rotation_cases':len(transforms),'point_cases':sum(r['point_count'] for r in transforms),
        'matrix_max_error':max(r['matrix_max_error'] for r in transforms),
        'point_max_error':max(r['point_max_error'] for r in transforms),
        'identity_shortcut_cases':sum(r['identity_shortcut'] for r in transforms),
        'interpolation_cases':len(interpolations),'threshold_one_minus_abs_dot':THRESHOLD,
        'spherical_cases':sum(r['branch']=='spherical' for r in interpolations),
        'linear_cases':sum(r['branch']=='linear' for r in interpolations),
        'interpolation_max_error':max(r['max_error'] for r in interpolations),
        'max_squared_norm_error':max(r['squared_norm_error'] for r in interpolations),
        'legacy_flags_agree_on_corpus':True,'interpolation_output_normalized':False,
        'rotation_channel_samples':len(samples),'rotation_channel_max_error':max(r['max_error'] for r in samples),
        'rotation_channel_branches':{branch:sum(r['branch']==branch for r in samples)
                                     for branch in ('held_first','held_last','linear','spherical')},
        'vector_channel_samples':len(vectors),'vector_channel_max_error':max(r['max_error'] for r in vectors),
        'vector_channel_branches':{branch:sum(r['branch']==branch for r in vectors)
                                   for branch in ('held_first','held_last','linear')},
        'time_integer_units_per_frame':40,'time_factor_float32':TIME_FACTOR,
        'library_loaded':False,'game_started':False,'game_modified':False,
        'scene_evaluated':False,'whole_track_evaluated':False,'skin_evaluated':False,
        'native_time_units_qualified':False,'commercial_geometry_or_keys_exported':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',type=Path,required=True)
    parser.add_argument('--json-output',type=Path)
    args=parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():raise ValueError('Report already exists; use a fresh name')
        report=audit(MathOracle(args.library.read_bytes()))
        if args.json_output:
            args.json_output.parent.mkdir(parents=True,exist_ok=True)
            with args.json_output.open('x',encoding='utf-8') as stream:
                json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
        print(json.dumps(report,indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Native math audit refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
