#!/usr/bin/env python3
"""Private before/after thumb authoring candidates; no emitted game clips.

Read pinned hands and previously generated corrected modern banks. The FOVs
65/40 are diagnostic choices informed by static client constants, not calibrated
camera instances. Images contain private derived hands without source textures.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path

import build_modern_asset as asset
from animation_tick_audit import model_poses
from benelli_fpv_rig_audit import read_hands, HAND_MODELS
from build_equipment_fpv_animation import numeric_world
from build_equipment_fpv_view_bank import preview_meshes
from build_equipment_hand_grips import posed_hand_mesh
from build_modern_equipment_assembly import ROOT, inputs
from build_modern_equipment_hose import digest
from five_ds import parse_5ds
from fpv_perspective_preview import preview
from hand_pose_ik import pinned_skin
from modern_thumb_pose import DEFAULT, apply, turns, validate


def detail(recipe, meshes, centers, output, title):
    """Close orthographic inspection without cutting or changing source mesh."""
    from PIL import Image, ImageDraw
    from software_depth import draw_triangles
    image = Image.new('RGB', (1600, 1000), '#101820')
    draw = ImageDraw.Draw(image)
    dot = lambda a,b: sum(x*y for x,y in zip(a,b))
    views = (((0,0,1),(0,1,0)), ((.6,0,.8),(-.3,.9,.2)), ((0,0,1),(-1,0,0)))
    for row, side in enumerate(('L','R')):
        center = centers[side]
        for column, (right, up) in enumerate(views):
            left, top, width, height = column*533, row*500, 533, 500
            right, up = asset.unit(right), asset.unit(up)
            forward = asset.unit(asset.cross(right,up))
            up = asset.cross(forward,right)
            scale = 1800
            triangles = []
            for mesh in meshes:
                for face in mesh.triangles:
                    points = [mesh.points[i] for i in face]
                    n = asset.cross(asset.sub(points[1],points[0]),asset.sub(points[2],points[0]))
                    if dot(n,n)<1e-18:continue
                    normal=asset.unit(n)
                    shade=.38+.62*max(0,dot(normal,asset.unit((.6,.9,-.4))))
                    rgb=tuple(round(255*min(1,c*shade)**(1/2.2)) for c in recipe['materials'][mesh.material-1]['diffuse'])
                    screen=[(left+width/2+dot(asset.sub(p,center),right)*scale,
                             top+height/2-dot(asset.sub(p,center),up)*scale,
                             dot(p,forward)) for p in points]
                    triangles.append((screen,rgb))
            draw_triangles(image,triangles,(left,top+38,width,height-38))
            draw.text((left+12,top+10),f'PRIVATE / {side} / {title}',fill='#d2b984')
    image.save(output)


def build(case, hands, bank, output, spec=DEFAULT):
    from PIL import Image
    spec = validate(spec)
    manifest = json.loads((bank/'MANIFEST.json').read_text(encoding='utf-8'))
    if manifest.get('private_only') is not True or manifest.get('runtime_status') != 'pending':
        raise ValueError('Expected private corrected bank manifest')
    rig = (bank/f'PROTOTYPE_{case}_FPVView.4ds.disabled').read_bytes()
    prepared = []
    for source in HAND_MODELS:
        _, skin = pinned_skin(hands[source])
        row = manifest['variants'][source]
        if digest(rig) != row['rig']['model_sha256'] or digest(hands[source]) != row['hand_sha256']:
            raise ValueError('Preview source differs from corrected bank')
        nodes = {n['name']: n for n in skin['nodes']}
        bases = {name: skin['rest_world'][nodes[name]['index']][0] for name in turns(spec)}
        for clip, end, fov in (('Idle1', 0, 65), ('Aim', 12, 40)):
            entry = row['clips'][clip]
            stem = entry['stem']
            if (not stem.startswith(f'PROTOTYPE_{case}V') or not asset.NAME.fullmatch(stem)
                    or len(stem) > 19):
                raise ValueError('Unexpected corrected bank clip alias')
            raw = (bank/(stem+'.5ds.disabled')).read_bytes()
            if digest(raw) != entry['sha256'] or parse_5ds(raw)['frame_end'] < end:
                raise ValueError('Changed corrected source clip')
            prepared.append((source, skin, bases, clip, end, fov, raw))
    output.mkdir(parents=True, exist_ok=False)
    recipe = deepcopy(inputs(case)[0])
    recipe['materials'].append({'name': 'private_hand_preview', 'diffuse': [.68, .65, .60]})
    reports = []
    contacts = {source: Image.new('RGB', (1920, 1200), '#101820') for source in HAND_MODELS}
    for source, skin, bases, clip, end, fov, raw in prepared:
        names, seeds = model_poses(hands[source])
        tracks = {t['name']: t['channels'] for t in parse_5ds(raw)['tracks']}
        hand_world, poses = numeric_world(skin['nodes'], dict(zip(names, seeds)), tracks, end*40)
        centers={side:[(a+b)*.5 for a,b in zip(hand_world[f'Bip01 {side} Hand'][12:15],
                    hand_world[f'Bip01 {side} Finger2'][12:15])] for side in ('L','R')}
        after = apply(poses, bases, spec)
        gear = preview_meshes(rig, raw, end*40)
        for index, (label, values) in enumerate((('source_rest_thumbs', poses), ('modern_thumb_candidate', after))):
            meshes = gear+[posed_hand_mesh(hands[source], values, len(recipe['materials']))]
            name = f'{Path(source).stem}_{clip}_{label}.png'
            preview(recipe, meshes, output/name, f'{case} / {clip} / {label}', horizontal_fov=fov)
            detail(recipe,meshes,centers,output/(name.removesuffix('.png')+'_detail.png'),clip+' / '+label)
            with Image.open(output/name) as picture:
                contacts[source].paste(picture, (index*960, 0 if clip == 'Idle1' else 600))
            # Orthographic detail is essential: perspective may hide the right thumb.
            pairs = []
            for mesh in meshes:
                mapped = asset.Mesh(mesh.name, mesh.material, [(p[0],p[2],p[1]) for p in mesh.points],
                                    [(a,c,b) for a,b,c in mesh.triangles])
                pairs.append((mapped,mapped))
            asset.preview(recipe,pairs,output/(name.removesuffix('.png')+'_geometry.png'),
                          labels=('PRIVATE / THUMB GRIP CANDIDATE / '+label,
                                  'Modern rotations only / source geometry untouched / not game validated'))
        reports.append({'source': source, 'source_sha256': digest(hands[source]), 'clip': clip,
                        'clip_sha256': digest(raw), 'frame': end, 'diagnostic_horizontal_fov': fov})
    for source, picture in contacts.items():
        picture.save(output/(Path(source).stem+'_contact.png'))
    report = {'schema_version': 1, 'provenance': 'DERIVE_MODERNE_SUR_SQUELETTE_COMMERCIAL',
              'runtime_status': 'pending', 'private_only': True, 'thumb_spec': spec, 'samples': reports,
              'hand_geometry_modified': False, 'rest_positions_and_scales_changed': False,
              'commercial_geometry_exported': False, 'game_clips_emitted': False,
              'thumb_contact_qualified': False, 'camera_calibrated': False,
              'game_started': False, 'game_modified': False,
              'files': {p.name: digest(p.read_bytes()) for p in sorted(output.iterdir())}}
    (output/'MANIFEST.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=('F35','F2'),required=True)
    parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true')
    parser.add_argument('--bank',type=Path,required=True)
    parser.add_argument('--output-name',required=True)
    args=parser.parse_args(argv)
    try:
        output=asset.output_directory(ROOT,args.output_name)
        hands,_=read_hands(args.game,archives_only=args.archives_only)
        report=build(args.case,hands,args.bank,output)
        print(json.dumps({'output':str(output),'samples':len(report['samples']),
                          'private_images':len(report['files']),'game_clips_emitted':False},indent=2))
        return 0
    except (OSError,ValueError,KeyError) as error:
        print('Private thumb candidates refused: '+str(error))
        return 1


if __name__=='__main__':raise SystemExit(main())
