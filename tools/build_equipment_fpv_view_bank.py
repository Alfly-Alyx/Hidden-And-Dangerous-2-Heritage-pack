"""Private modern FPV-axis equipment and newly authored commercial-hand poses.

No source hand geometry or rest transforms are converted. A new grip basis,
elbow pole and finger curl are authored on those unchanged skeletons.
"""
from copy import deepcopy
import argparse
import json
from pathlib import Path

import modern_animation as motion
from modern_fpv_axes import compile_view_rig, position, native_rotation
from build_equipment_fpv_animation import compile_fpv_bank, numeric_world
from build_equipment_hand_animation import HAND_NAMES, bake_tracks, wrist_from_native, PROVENANCE
from build_equipment_hand_grips import effective_hands
from build_modern_animation_bank import ALIASES
from build_modern_equipment_hose import digest
from hand_pose_ik import author_pose, pinned_skin, validate_basis
from animation_tick_audit import model_poses
from five_ds import parse_5ds
from model_transform import matmul, matvec
from menu_gui_audit import parse_4ds_nodes
from benelli_fpv_rig_audit import HAND_MODELS

SWAP = [[1,0,0],[0,0,1],[0,1,0]]
PALM_NORMAL_FLIP = [[1,0,0],[0,-1,0],[0,0,1]]


def view_grips(spec, case):
    """Modern re-authoring choice, NOT reflection of the source hand skeleton.

    Rest palms span X/Z. Flipping the normal in the grip recipe supplies a
    proper rotation after the handedness-changing equipment axis conversion.
    Finger curl signs change consistently; thumbs are still source rest.
    """
    grips = effective_hands(spec, case)
    for hand in grips.values():
        hand['rest_to_equipment_rotation'] = matmul(matmul(SWAP, hand['rest_to_equipment_rotation']), PALM_NORMAL_FLIP)
        validate_basis(hand['rest_to_equipment_rotation'])
        hand['contact_offset'] = position(hand['contact_offset'])
        hand['elbow_pole'] = position(hand['elbow_pole'])
        hand['wrist_to_contact_in_rest'] = matvec(PALM_NORMAL_FLIP, hand['wrist_to_contact_in_rest'])
        hand['finger_curl_degrees'] = [-v for v in hand['finger_curl_degrees']]
    return grips


def converted_gear_tracks(raw, names):
    parsed = parse_5ds(raw)
    tracks = []
    for track in parsed['tracks']:
        if track['name'] in HAND_NAMES:
            continue
        if track['name'] not in names:
            raise ValueError('Unknown modern view equipment track')
        channels = {}
        for kind, channel in track['channels'].items():
            if kind not in ('position', 'scale', 'rotation'):
                raise ValueError('Unreviewed modern view animation channel')
            convert = native_rotation if kind == 'rotation' else position
            channels[kind] = {'frames': channel['frames'][:], 'values': [convert(v) for v in channel['values']]}
        tracks.append({'name': track['name'], 'channels': channels})
    if {t['name'] for t in tracks} != set(names) or len(tracks) != len(names):
        raise ValueError('Incomplete or duplicate converted equipment tracks')
    return tracks


def targets_at(rig, gear_tracks, time, grips):
    nodes = parse_4ds_nodes(rig)['nodes']
    names, seeds = model_poses(rig)
    world, _ = numeric_world(nodes, dict(zip(names, seeds)), {t['name']: t['channels'] for t in gear_tracks}, time)
    held = world['MOD_held_pivot']
    basis = [[held[i+4*j] for j in range(3)] for i in range(3)]
    return {side: {'position': wrist_from_native(held, world['MOD_'+label+'_hand'], grips[side]),
                   'rotation': matmul(basis, grips[side]['rest_to_equipment_rotation']),
                   'pole': grips[side]['elbow_pole'][:]} for side, label in (('L','left'), ('R','right'))}


def compile_view_bank(case, hand_raw, spec):
    source, skin = pinned_skin(hand_raw)
    rig, rig_report = compile_view_rig(case)
    original_rig, original_clips, original_report = compile_fpv_bank(case, hand_raw, spec)
    if digest(original_rig) != rig_report['source_model_sha256']:
        raise ValueError('View rig does not match source clip geometry')
    gear_names, _ = model_poses(rig)
    hand_names = [n['name'] for n in skin['nodes']]
    if set(hand_names) != HAND_NAMES or len(hand_names) != 37:
        raise ValueError('Changed reviewed source hands')
    grips = view_grips(spec, case)
    curls = {side: {'finger_curl_degrees': g['finger_curl_degrees']} for side, g in grips.items()}
    variant = 'H' if source == HAND_MODELS[0] else 'R'
    clips, reports = {}, {}
    allowed = HAND_NAMES | set(gear_names)
    for name, (_, source_clip) in original_clips.items():
        end = parse_5ds(source_clip)['frame_end']
        gear = converted_gear_tracks(source_clip, gear_names)
        samples = [author_pose(hand_raw, targets_at(rig, gear, frame*40, grips), curls,
                               arm_rotation_policy='bend_plane')[0] for frame in range(end+1)]
        hands = bake_tracks(samples, hand_names, end)
        raw = motion._encode_transform_tracks(end, hands+gear, preserve_native_rotations=True,
                                               name_validator=lambda value: value in allowed)
        if len(raw)-18 > 0xf000:
            raise ValueError('View bank exceeds reviewed native animation body capacity')
        stem = f'PROTOTYPE_{case}V{variant}{ALIASES[name]}'
        if len(stem) > 19:
            raise ValueError('View animation alias too long')
        actual = {t['name']: t['channels'] for t in parse_5ds(raw)['tracks']}
        if any(actual[t['name']] != t['channels'] for t in gear):
            raise ValueError('Converted modern gear channels changed during hand merge')
        clips[name] = (stem, raw)
        reports[name] = {'stem': stem, 'frame_end': end, 'sha256': digest(raw),
                         'bytes': len(raw), 'tracks': len(hands)+len(gear), 'source_clip_sha256': digest(source_clip)}
    return rig, clips, {'schema_version': 1, 'case': case, 'provenance': PROVENANCE,
        'runtime_status': 'pending', 'hand_source': source, 'hand_sha256': digest(hand_raw),
        'rig': rig_report, 'clips': reports, 'grips': deepcopy(grips),
        'source_grip_specification_sha256': original_report['specification_sha256'],
        'equipment_axes': '+X right / +Y up / +Z forward',
        'hand_geometry_and_rest_transforms_unchanged': True, 'hand_poses_reauthored': True,
        'finger_contact_qualified': False, 'thumb_pose_authored': False,
        'camera_calibrated': False, 'old_animation_banks_compatible': False,
        'commercial_geometry_exported': False, 'native_loader_executed': False,
        'game_started': False, 'game_modified': False, 'engine_validated': False}


def preview_meshes(rig, animation, time, lod=0):
    """Read geometry AND poses from serialized corrected modern files."""
    import build_modern_asset as asset
    from modern_fpv_geometry import geometry
    from ls3d_palette_oracle import product
    from ls3d_skin_oracle import reference, transformed
    clip = parse_5ds(animation)
    motion.integer(time, 0, clip['frame_end']*40, 'view preview time')
    meshes, hose = geometry(rig, lod)
    names, seeds = model_poses(rig)
    world, _ = numeric_world(parse_4ds_nodes(rig)['nodes'], dict(zip(names, seeds)),
                             {t['name']: t['channels'] for t in clip['tracks']}, time)
    result = []
    for mesh in meshes:
        points = [tuple(transformed(v[:3], world[mesh['name']])) for v in mesh['vertices']]
        for group in mesh['face_groups']:
            result.append(asset.Mesh(mesh['name'], group['material'], points,
                                     [tuple(f) for f in group['triangles']]))
    by_index = {n['index']: n for n in hose['nodes']}
    matrices = [product(inv, world[by_index[index]['name']])
                for index, inv in zip(hose['joint_node_indices'], hose['inverse_binds'])]
    points = [tuple(v[:3]) for v in reference(hose['vertices'], hose['pairs'], matrices, hose['parents'])]
    for group in hose['face_groups']:
        result.append(asset.Mesh('MOD_hose', group['material'], points, [tuple(f) for f in group['triangles']]))
    return result


def preview_bank(case, hand_raw, rig, clips, output):
    import build_modern_asset as asset
    from build_modern_equipment_assembly import inputs
    from build_equipment_hand_grips import posed_hand_mesh
    from fpv_perspective_preview import preview
    from PIL import Image, ImageDraw
    recipe = deepcopy(inputs(case)[0])
    recipe['materials'].append({'name': 'private_hand_preview', 'diffuse': [.68, .65, .60]})
    source, skin = pinned_skin(hand_raw)
    label = Path(source).stem
    names, seeds = model_poses(hand_raw)
    samples = (('Idle1', 0), ('Aim', 12), ('Arm', 0), ('Arm', 13.5), ('Rel', 32), ('Jammed', 16))
    contact = Image.new('RGB', (1920, 1800), '#101820')
    for index, (name, frame) in enumerate(samples):
        raw = clips[name][1]
        tracks = {t['name']: t['channels'] for t in parse_5ds(raw)['tracks']}
        time = int(frame*40)
        _, poses = numeric_world(skin['nodes'], dict(zip(names, seeds)), tracks, time)
        meshes = preview_meshes(rig, raw, time)
        meshes.append(posed_hand_mesh(hand_raw, poses, len(recipe['materials'])))
        path = output/f'{label}_{name}_{frame:05.1f}_perspective.png'
        preview(recipe, meshes, path, f'{case} / {label} / {name} / {frame}')
        with Image.open(path) as picture:
            contact.paste(picture, ((index%2)*960, (index//2)*600))
        # Reorient for the existing orthographic inspection camera only.
        pairs = []
        for mesh in meshes:
            mapped = asset.Mesh(mesh.name, mesh.material, [tuple(position(p)) for p in mesh.points],
                                [(a, c, b) for a, b, c in mesh.triangles])
            pairs.append((mapped, mapped))
        asset.preview(recipe, pairs, output/f'{label}_{name}_{frame:05.1f}_geometry.png',
            labels=('PRIVATE / CORRECTED FPV AXES / DERIVED HAND POSES',
                    'Serialized modern geometry and clips / no commercial textures / outside game'))
    contact.save(output/(label+'_contact.png'))


def build(case, hands, spec, output, *, previews=False):
    from benelli_fpv_rig_audit import HAND_PINS
    if set(hands) != set(HAND_PINS):
        raise ValueError('Incomplete pinned source set')
    for name, raw in hands.items():
        if (len(raw), digest(raw)) != HAND_PINS[name][1:]:
            raise ValueError('Changed pinned private source')
    banks = [compile_view_bank(case, hands[name], spec) for name in HAND_MODELS]
    if banks[0][0] != banks[1][0]:
        raise ValueError('Hand variant changed corrected equipment geometry')
    output.mkdir(parents=True, exist_ok=False)
    (output/f'PROTOTYPE_{case}_FPVView.4ds.disabled').write_bytes(banks[0][0])
    for _, clips, _ in banks:
        for stem, raw in clips.values():
            (output/(stem+'.5ds.disabled')).write_bytes(raw)
    if previews:
        for (rig, clips, _), source in zip(banks, HAND_MODELS):
            preview_bank(case, hands[source], rig, clips, output)
    report = {'schema_version': 1, 'provenance': PROVENANCE, 'runtime_status': 'pending',
        'private_only': True, 'variants': {row['hand_source']: row for _, _, row in banks},
        'commercial_hand_models_exported': False, 'auto_load_companions_created': False,
        'private_derived_previews_created': previews, 'preview_is_native_game_rendering': False,
        'files': {p.name: digest(p.read_bytes()) for p in sorted(output.iterdir())}}
    (output/'MANIFEST.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


def main(argv=None):
    import build_modern_asset as asset
    from build_modern_equipment_assembly import CASES, ROOT
    from build_equipment_hand_grips import RECIPE
    from benelli_fpv_rig_audit import read_hands
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--game', type=Path, required=True)
    parser.add_argument('--archives-only', action='store_true')
    parser.add_argument('--output-name')
    parser.add_argument('--previews', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.previews and not args.output_name:
            raise ValueError('Previews require a fresh private output directory')
        output = asset.output_directory(ROOT, args.output_name) if args.output_name else None
        hands, excluded = read_hands(args.game, archives_only=args.archives_only)
        spec = json.loads(RECIPE.read_text(encoding='utf-8'))
        report = (build(args.case, hands, spec, output, previews=args.previews) if output else
                  {'variants': {name: compile_view_bank(args.case, hands[name], spec)[2] for name in HAND_MODELS}})
        report['excluded_loose_overrides'] = excluded
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print('Private corrected FPV bank refused: '+str(error))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
