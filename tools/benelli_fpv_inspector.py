"""Self-contained, private RAW-key inspector; not an animation player/emulator."""
import base64
import json
from pathlib import Path

from benelli_fpv_static import geometry
from five_ds import parse_5ds
from menu_gui_audit import parse_4ds_nodes
from model_transform import world_transforms

TEMPLATE=Path(__file__).with_name('fpv_inspector.html')


def inspection_data(data,states):
    pairs={}
    for state in states:
        raw=data[f'models/#fpvbeneli{state}.4ds']
        parsed=parse_4ds_nodes(raw)
        transforms=world_transforms(raw,parsed['nodes'])
        vertices,faces,_=geometry(raw)
        clip=parse_5ds(data[f'models/#fpvbeneli{state}.5ds'])
        pairs[state]={'vertices':vertices,'faces':faces,'frame_end':clip['frame_end'],
                      'tracks':clip['tracks'],
                      'nodes':[{'id':n['index'],'parent':n['parent_id'],'name':n['name'],
                                'type':n['frame_type'],'position':transforms[n['index']][1]}
                               for n in parsed['nodes']]}
    return {'pairs':pairs,'textures':{name:base64.b64encode(raw).decode('ascii')
                                     for name,raw in data.items() if name.startswith('maps/')},
            'audio':{name:base64.b64encode(raw).decode('ascii')
                     for name,raw in data.items() if name.startswith('sounds/')},
            'frame_rate':None,'animation_playback':False,'commercial_data_private':True,
            'pose_mode':'4ds_bind_pose_only','key_mode':'raw_samples_no_interpolation',
            'engine_validated':False}


def render(data,states):
    payload=inspection_data(data,states)
    # JSON is data, never executable code or markup. Escape closing script tags
    # and HTML characters even though commercial sources are pinned upstream.
    encoded=json.dumps(payload,ensure_ascii=True,separators=(',',':'),allow_nan=False)
    encoded=encoded.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    template=TEMPLATE.read_text(encoding='utf-8')
    if template.count('__FPV_DATA__')!=1: raise ValueError('Invalid FPV inspector template')
    return template.replace('__FPV_DATA__',encoded)
