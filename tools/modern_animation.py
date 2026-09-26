"""Original rigid animation authoring; no commercial transforms are read.

5DS v122 layout: hdmaster's public mafia-formats/5ds.bt, XYZW quaternions.
Offline interpolation is an explicit modern choice, not an engine equivalence.
"""
from __future__ import annotations

from bisect import bisect_right
import math
import re
import struct

from build_modern_asset import finite, vector, node_header, pack
from five_ds import parse_5ds, FLAGS
from menu_gui_audit import parse_4ds_nodes
from model_transform import affine, compose, point

NAME=re.compile(r'[A-Za-z][A-Za-z0-9_]{0,62}\Z')


def integer(value,low,high,label):
    if type(value) is not int or not low<=value<=high:
        raise ValueError('Invalid '+label)
    return value


def unit_quaternion(value):
    value=vector(value,4)
    length=math.sqrt(sum(n*n for n in value))
    if length<1e-10 or abs(length-1)>1e-4:
        raise ValueError('Modern quaternion must already be unit length')
    return tuple(n/length for n in value)


def encode_5ds(clip):
    """Encode only explicitly modern finite transform channels, never events."""
    if (clip.get('provenance')!='MODERNE' or clip.get('runtime_status')!='pending'
            or set(clip)-{'provenance','runtime_status','frame_end','tracks'}):
        raise ValueError('Not an explicitly modern transform clip')
    end=integer(clip['frame_end'],1,65535,'terminal frame')
    tracks=clip['tracks']
    if not isinstance(tracks,list) or not 1<=len(tracks)<=256:
        raise ValueError('Invalid modern track count')
    data=bytearray(pack('HH',len(tracks),end)+bytes(8*len(tracks)))
    data.extend(bytes((-len(data))%16))
    links=[];names=set()
    for track in tracks:
        if not isinstance(track,dict) or set(track)!={'name','channels'}:
            raise ValueError('Invalid modern track')
        name=track['name']
        if not isinstance(name,str) or not NAME.fullmatch(name) or name.casefold() in names:
            raise ValueError('Invalid or duplicate modern track name')
        names.add(name.casefold())
        channels=track['channels']
        if not isinstance(channels,dict) or not channels or set(channels)-set(FLAGS):
            raise ValueError('Unsupported modern channel or event')
        links.append(len(data))
        data.extend(pack('I',sum(FLAGS[k] for k in channels)))
        for kind in FLAGS:
            if kind not in channels:continue
            channel=channels[kind]
            if not isinstance(channel,dict) or set(channel)!={'frames','values'}:
                raise ValueError('Invalid modern channel')
            frames,values=channel['frames'],channel['values']
            if (not isinstance(frames,list) or not isinstance(values,list)
                    or not 1<=len(frames)<=65535 or len(frames)!=len(values)):
                raise ValueError('Invalid modern keys')
            for frame in frames:integer(frame,0,end,'key frame')
            if any(a>=b for a,b in zip(frames,frames[1:])):
                raise ValueError('Modern keys must strictly increase')
            rows=[]
            for value in values:
                row=unit_quaternion(value) if kind=='rotation' else vector(value)
                if kind=='position' and any(abs(v)>10 for v in row):
                    raise ValueError('Modern translation outside reviewed domain')
                if kind=='scale' and any(not .001<=v<=10 for v in row):
                    raise ValueError('Modern scale must be positive and bounded')
                rows.append(row)
            data.extend(pack('H',len(frames))+pack('H'*len(frames),*frames))
            if kind=='rotation':data.extend(bytes((-len(data))%16))
            elif len(frames)%2==0:data.extend(bytes(2))
            for row in rows:data.extend(pack('f'*len(row),*row))
    for i,(track,offset) in enumerate(zip(tracks,links)):
        struct.pack_into('<II',data,4+8*i,len(data),offset)
        data.extend(track['name'].encode('ascii')+b'\0')
    result=b'5DS\0'+pack('HQI',122,0,len(data))+data
    parsed=parse_5ds(result)
    if parsed['track_count']!=len(tracks) or parsed['frame_end']!=end:
        raise ValueError('Modern 5DS readback failed')
    return result


def rig_model(data,groups):
    """Insert original pivot dummies; preserve vertices, materials and rest pose.

    Only root-local original asset-factory geometry is accepted. Reparenting
    subtracts the pivot in the child transform instead of rewriting vertices.
    """
    parsed=parse_4ds_nodes(data)
    nodes=parsed['nodes']
    if (parsed['has_animation'] or not nodes or nodes[0]['parent_id']
            or not nodes[0]['name'].startswith('PROTOTYPE_HERITAGE_')
            or any(n['parent_id']!=1 for n in nodes[1:])):
        raise ValueError('Expected unanimated modern root-local model')
    if not isinstance(groups,list) or not 1<=len(groups)<=32:
        raise ValueError('Invalid modern pivot count')
    known={n['name']:n for n in nodes[1:]}
    if len(known)!=len(nodes)-1:raise ValueError('Ambiguous modern nodes')
    names={n['name'].casefold() for n in nodes};owners={}
    pivots={}
    for i,group in enumerate(groups,2):
        if not isinstance(group,dict) or set(group)!={'name','pivot','members'}:
            raise ValueError('Invalid pivot description')
        name=group['name']
        if not isinstance(name,str) or not NAME.fullmatch(name) or not name.startswith('MOD_') or name.casefold() in names:
            raise ValueError('Invalid or duplicate modern pivot')
        names.add(name.casefold());pivot=vector(group['pivot'])
        if any(abs(v)>10 for v in pivot):raise ValueError('Pivot outside reviewed domain')
        members=group['members']
        if not isinstance(members,list) or not members:raise ValueError('Empty modern pivot')
        for member in members:
            if not isinstance(member,str) or member not in known or member in owners:
                raise ValueError('Missing or multiply owned modern mesh/anchor')
            owners[member]=(i,pivot)
        pivots[name]=list(pivot)
    output=bytearray(data[:parsed['node_count_offset']])
    output.extend(pack('H',len(nodes)+len(groups)))
    root=nodes[0]
    output.extend(data[root['start']:root['end']])
    for group in groups:
        output.extend(b'\x06'+node_header(group['name'],group['pivot']))
        output.extend(pack('3fi3fi',-.002,-.002,-.002,0,.002,.002,.002,0))
    for node in nodes[1:]:
        raw=bytearray(data[node['start']:node['end']])
        if node['name'] in owners:
            owner,pivot=owners[node['name']]
            struct.pack_into('<H',raw,node['parent_offset']-node['start'],owner)
            position=[a-b for a,b in zip(node['position'],pivot)]
            struct.pack_into('<3f',raw,node['position_offset']-node['start'],*position)
        output.extend(raw)
    output.extend(b'\0') # Bank is explicitly loaded; no automatic companion yet.
    output=bytes(output)
    checked=parse_4ds_nodes(output)
    if checked['node_count']!=len(nodes)+len(groups):raise ValueError('Rig readback failed')
    return output,{'root':root['name'],'pivots':pivots,'members':{g['name']:g['members'] for g in groups},
                   'vertices_rewritten':False,'engine_validated':False,'player_skeleton':False}


def slerp(left,right,amount):
    """Shortest-arc normalized interpolation, chosen for this offline authoring."""
    left=unit_quaternion(list(left));right=unit_quaternion(list(right))
    cosine=sum(a*b for a,b in zip(left,right))
    if cosine<0:right=tuple(-v for v in right);cosine=-cosine
    cosine=min(1,max(-1,cosine))
    if cosine>.9995:
        value=tuple(a+(b-a)*amount for a,b in zip(left,right))
    else:
        angle=math.acos(cosine)
        a=math.sin((1-amount)*angle)/math.sin(angle)
        b=math.sin(amount*angle)/math.sin(angle)
        value=tuple(a*x+b*y for x,y in zip(left,right))
    length=math.sqrt(sum(v*v for v in value))
    return [v/length for v in value]


def sample_channel(channel,frame,quaternion=False):
    frames,values=channel['frames'],channel['values']
    if frame<=frames[0]:return list(values[0])
    if frame>=frames[-1]:return list(values[-1])
    i=bisect_right(frames,frame)-1
    alpha=(frame-frames[i])/(frames[i+1]-frames[i])
    if quaternion:return slerp(values[i],values[i+1],alpha)
    return [a+(b-a)*alpha for a,b in zip(values[i],values[i+1])]


def pose(data,animation,frame):
    """Evaluate local absolute SRT for original clips; no claims about the engine."""
    frame=finite(frame)
    parsed=parse_4ds_nodes(data);clip=parse_5ds(animation)
    if not 0<=frame<=clip['frame_end']:raise ValueError('Frame outside modern clip')
    by_name={n['name']:n for n in parsed['nodes']}
    if len(by_name)!=len(parsed['nodes']):raise ValueError('Ambiguous model names')
    tracks={t['name']:t for t in clip['tracks']}
    if set(tracks)-set(by_name):raise ValueError('Unbound modern animation track')
    transforms={}
    for node in parsed['nodes']:
        channels=tracks.get(node['name'],{}).get('channels',{})
        values={'position':node['position'],
                'rotation':struct.unpack_from('<4f',data,node['position_offset']+12),
                'scale':node['scale']}
        for kind,channel in channels.items():
            values[kind]=sample_channel(channel,frame,kind=='rotation')
        local=affine(values['position'],values['rotation'],values['scale'])
        parent=node['parent_id']
        if parent and parent not in transforms:raise ValueError('Non-topological modern hierarchy')
        transforms[node['index']]=compose(transforms[parent],local) if parent else local
    return transforms


def animated_meshes(recipe,meshes,rig,animation,frame):
    """Deform only rigid original parts for the offline geometric preview."""
    from build_modern_asset import Mesh
    parsed=parse_4ds_nodes(rig);transforms=pose(rig,animation,frame)
    nodes={n['name']:n for n in parsed['nodes']}
    result=[]
    for pair in meshes:
        node=nodes[pair[0].name]
        result.append(tuple(Mesh(mesh.name,mesh.material,
                                [tuple(point(transforms[node['index']],p)) for p in mesh.points],
                                list(mesh.triangles)) for mesh in pair))
    return result

