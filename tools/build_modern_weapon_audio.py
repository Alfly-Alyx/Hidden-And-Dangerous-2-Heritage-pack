#!/usr/bin/env python3
"""Original procedural sound-design candidates; no samples or game access.

Produces disabled mono PCM effects from deterministic authored layers. This is
not a historical acoustic reconstruction, a sound-bank allocation, or playback.
"""
import argparse
import io
import json
import math
from pathlib import Path
import re
import struct
import sys
import wave

from audit_audio_resources import pcm_metadata
from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest

RECIPES={'FG42':ROOT/'experimental/FG42/modern-audio.json',
         'ZK383':ROOT/'experimental/GAROTA_AND_ZK383/modern-zk383-audio.json'}
RATE=22050


def scalar(value,lo,hi):
    if type(value) not in (int,float) or not math.isfinite(value) or not lo<=value<=hi:
        raise ValueError('Unreviewed sound-design scalar')
    return float(value)


def validate(recipe):
    keys={'schema_version','case','provenance','runtime_status','description','sample_rate_hz','effects'}
    if (not isinstance(recipe,dict) or set(recipe)!=keys or type(recipe['schema_version']) is not int
            or recipe['schema_version']!=1 or recipe['case'] not in RECIPES
            or recipe['provenance']!='MODERNE_SYNTHESE_ORIGINALE' or recipe['runtime_status']!='pending'
            or type(recipe['sample_rate_hz']) is not int or recipe['sample_rate_hz']!=RATE
            or not isinstance(recipe['description'],str) or not recipe['description'].strip()
            or not isinstance(recipe['effects'],dict) or set(recipe['effects'])!={'shot','reload'}):
        raise ValueError('Expected an explicitly modern complete audio recipe')
    for kind,effect in recipe['effects'].items():
        if (not isinstance(effect,dict) or set(effect)!={'stem','duration_seconds','seed','layers'}
                or effect['stem']!=f"MOD_{recipe['case']}_{'F' if kind=='shot' else 'R'}"
                or not re.fullmatch(r'MOD_[A-Z0-9_]{1,15}',effect['stem'])
                or type(effect['seed']) is not int or not 1<=effect['seed']<=0xffffffff
                or not isinstance(effect['layers'],list) or not 1<=len(effect['layers'])<=24):
            raise ValueError('Invalid modern audio effect')
        duration=scalar(effect['duration_seconds'],.1,5)
        for layer in effect['layers']:
            if not isinstance(layer,dict) or set(layer)!={'at','length','gain','attack','decay','tone_hz','noise_mix','noise_smoothing'}:
                raise ValueError('Incomplete modern audio layer')
            at=scalar(layer['at'],0,duration);length=scalar(layer['length'],.005,2)
            if at+length>duration+1e-9:raise ValueError('Audio layer exceeds the effect')
            scalar(layer['gain'],.001,.5);scalar(layer['attack'],.0001,min(.03,length/2))
            scalar(layer['decay'],.001,2);scalar(layer['noise_mix'],0,1);scalar(layer['noise_smoothing'],.01,1)
            if not isinstance(layer['tone_hz'],list) or len(layer['tone_hz'])!=2:raise ValueError('Invalid modern tone sweep')
            for value in layer['tone_hz']:scalar(value,30,6000)
    return recipe


def synthesize(effect):
    """Only called after validate; all wave layers are generated from numbers."""
    count=round(effect['duration_seconds']*RATE);values=[0.0]*count
    for number,layer in enumerate(effect['layers']):
        start=round(layer['at']*RATE);frames=round(layer['length']*RATE)
        state=(effect['seed']+number*0x9e3779b9)&0xffffffff;filtered=0.0
        f0,f1=layer['tone_hz'];length=layer['length'];fade=min(.01,length/4)
        for i in range(min(frames,count-start)):
            t=i/RATE;state=(1664525*state+1013904223)&0xffffffff
            noise=(state/2147483648.0)-1;filtered+=layer['noise_smoothing']*(noise-filtered)
            phase=2*math.pi*(f0*t+.5*(f1-f0)*t*t/length)
            envelope=min(1,t/layer['attack'])*math.exp(-t/layer['decay'])*min(1,max(0,(length-t)/fade))
            sample=(1-layer['noise_mix'])*math.sin(phase)+layer['noise_mix']*filtered
            values[start+i]+=layer['gain']*envelope*sample
    # Remove near-DC drift with a fixed high-pass recurrence, then fade the
    # whole buffer boundaries. Limit peaks downward only; never boost silence.
    previous=0.0;filtered=0.0;edge=max(1,round(.002*RATE))
    for i,value in enumerate(values):
        filtered=value-previous+.995*filtered;previous=value
        values[i]=filtered*min(1,i/edge,(count-1-i)/edge)
    peak=max(abs(v) for v in values);gain=min(1,.5/peak) if peak else 1
    pcm=[round(v*gain*32767) for v in values]
    if not any(pcm) or max(map(abs,pcm))>16384 or pcm[0] or pcm[-1]:
        raise ValueError('Invalid synthesized headroom or boundaries')
    stream=io.BytesIO()
    with wave.open(stream,'wb') as output:
        output.setnchannels(1);output.setsampwidth(2);output.setframerate(RATE)
        output.writeframes(struct.pack('<'+str(count)+'h',*pcm))
    raw=stream.getvalue();metadata=pcm_metadata(raw)
    metadata.update(peak_pcm=max(map(abs,pcm)),rms_pcm=math.sqrt(sum(v*v for v in pcm)/count),
                    mean_pcm=sum(pcm)/count,headroom_gain_applied=gain,clipped_samples=0,
                    first_last_pcm=[pcm[0],pcm[-1]],all_samples_originally_synthesized=True,
                    historical_fidelity_claimed=False,playback_or_mix_qualified=False)
    return raw,metadata


def prepare(recipe):
    validate(recipe);files={};effects={}
    for kind,effect in recipe['effects'].items():
        raw,metadata=synthesize(effect);name=effect['stem']+'.wav.disabled';files[name]=raw
        effects[kind]={'filename':name,'intended_stem':effect['stem'],'metadata':metadata,
                       'timing_is_modern_sound_design':True,'animation_event_alignment_qualified':False}
    return files,{'schema_version':1,'case':recipe['case'],'provenance':recipe['provenance'],'runtime_status':'pending',
        'algorithm':'original_layered_lcg32_swept_tone_v1','format':'mono_pcm_s16le_22050',
        'recipe_sha256':digest(json.dumps(recipe,sort_keys=True).encode()),'effects':effects,
        'files':{name:{'size':len(raw),'sha256':digest(raw)} for name,raw in files.items()},
        'source_audio_samples_read':False,'commercial_audio_exported':False,'game_resources_read':False,
        'historical_fg42_symbols_resolved':False,'sound_bank_indices_allocated':False,
        'sound_definition_modified':False,'listened':False,'game_started':False,'game_modified':False,
        'engine_validated':False,'pending_requirements':['listening_and_mix_review','sound_bank_additive_contract',
            'resource_alias_collision_check','animation_and_gameplay_event_timing','native_audio_playback']}


def build(recipe,output):
    if output.exists():raise FileExistsError('Use a fresh modern audio directory')
    files,report=prepare(recipe);output.mkdir(parents=True,exist_ok=False)
    for name,raw in files.items():
        with (output/name).open('xb') as stream:stream.write(raw)
        if (output/name).read_bytes()!=raw:raise ValueError('Modern audio readback differs')
    with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=RECIPES,required=True)
    parser.add_argument('--output-name',required=True);args=parser.parse_args(argv)
    try:
        recipe=json.loads(RECIPES[args.case].read_text(encoding='utf-8'))
        if recipe['case']!=args.case:raise ValueError('Audio recipe case differs')
        output=output_directory(ROOT,args.output_name);report=build(recipe,output)
        print(json.dumps({'output':str(output),'effects':report['effects'],'listened':False,'engine_validated':False},indent=2))
        return 0
    except (OSError,ValueError,KeyError,wave.Error) as error:
        print('Modern audio generation refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
