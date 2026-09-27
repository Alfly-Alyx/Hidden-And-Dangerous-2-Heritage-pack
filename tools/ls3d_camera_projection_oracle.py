"""Pinned camera FOV setters and perspective matrices on a supplied camera.

No camera constructor, window, driver, world/view matrix, scene or renderer is
executed. The optional external camera link and orthographic mode are excluded.
"""
import argparse
import json
import math
from pathlib import Path
import struct

from ls3d_math_oracle import MathOracle, f32, DLL_SHA

PRIMARY, SECONDARY = 0x10009e30, 0x10009e90
PROJECT = 0x10009b30
RANGES = ((PROJECT, 0x10009b54), (0x10009c43, 0x10009d04),
          (0x10009d26, 0x10009e24), (PRIMARY, 0x10009e85), (SECONDARY, 0x10009ee5))
PI = f32(math.pi)
MIN_FOV = f32(.01)


def validate(settings):
    keys = {'primary_fov', 'secondary_fov', 'aspect', 'near', 'far', 'secondary_near', 'secondary_far'}
    if not isinstance(settings, dict) or set(settings) != keys:
        raise ValueError('Incomplete supplied perspective camera')
    settings = {key: f32(value) for key, value in settings.items()}
    if (any(not MIN_FOV <= settings[k] <= PI for k in ('primary_fov', 'secondary_fov'))
            or not .5 <= settings['aspect'] <= 4
            or any(not .001 <= settings[a] < settings[b] <= 10000
                   or settings[b]-settings[a] < .001
                   for a, b in (('near', 'far'), ('secondary_near', 'secondary_far')))):
        raise ValueError('Camera outside reviewed perspective domain')
    return settings


def reference(settings):
    s = validate(settings)
    def projection(fov, near, far):
        angle = fov*.5
        if s['aspect'] > 2.5:
            angle = min(angle*2, 1.5)
        x = math.cos(angle)/math.sin(angle)
        y = x*s['aspect']
        depth = far/(far-near)
        m = [0.0]*16
        m[0], m[5], m[10], m[11], m[14] = map(f32, (x, y, depth, 1, -depth*near))
        return m, [f32(near/x), f32(near/y)], angle
    primary, p_extents, p_angle = projection(s['primary_fov'], s['near'], s['far'])
    secondary, s_extents, s_angle = projection(s['secondary_fov'], s['secondary_near'], s['secondary_far'])
    extended = primary[:]
    depth = s['far']*1000/(s['far']*1000-s['near']*10)
    extended[10], extended[14] = f32(depth), f32(depth*s['near']*-10)
    return {'primary': primary, 'extended': extended, 'secondary': secondary,
            'near_extents': p_extents+s_extents,
            'effective_horizontal_fov_radians': [p_angle*2, s_angle*2],
            'ultrawide_branch': s['aspect'] > 2.5}


def changed_settings(settings, target, value):
    settings = validate(settings)
    if target not in ('primary', 'secondary'):
        raise ValueError('Unreviewed camera setter')
    value = f32(value)
    if not -1 <= value <= 7:
        raise ValueError('Unreviewed camera setter input')
    settings[target+'_fov'] = max(MIN_FOV, min(PI, value))
    return settings


class CameraProjectionOracle(MathOracle):
    STATE, SIZE = 0x4200000, 4096

    def __init__(self, library):
        super().__init__(library)
        self.uc.mem_map(self.STATE, self.SIZE, self.uni.UC_PROT_READ | self.uni.UC_PROT_WRITE)
        if tuple(struct.unpack('<II', self.uc.mem_read(0x1009bde4, 8))) != (PRIMARY, SECONDARY):
            raise ValueError('Changed native camera vtable')

    def on_code(self, uc, address, size, context):
        if self.phase != 'camera_projection':
            return super().on_code(uc, address, size, context)
        if not any(a <= address and address+size <= b for a, b in RANGES):
            raise ValueError(f'Unreviewed camera instruction/call: {address:#x}')
        self.visited.add(address)

    def compute(self, settings, *, target=None, value=None):
        original = validate(settings)
        if (target is None) != (value is None):
            raise ValueError('Camera setter requires both target and value')
        final = changed_settings(original, target, value) if target else original
        expected = reference(final)
        if self.phase is not None:
            raise ValueError('Nested camera phase')
        state = bytearray(b'Z'*self.SIZE)
        root = self.STATE+0x100
        struct.pack_into('<I', state, 0x100, 0x1009bd70)
        struct.pack_into('<I', state, 0x204, 11)
        offsets = {'primary_fov': 0x120, 'near': 0x124, 'far': 0x128, 'secondary_fov': 0x12c,
                   'secondary_near': 0x130, 'secondary_far': 0x134, 'aspect': 0x138}
        for key, offset in offsets.items():
            struct.pack_into('<f', state, 0x100+offset, original[key])
        state[0x23c] = 0
        struct.pack_into('<I', state, 0x4e0, 0)
        self.uc.mem_write(self.STATE, bytes(state))
        stack = self.STACK+0xf000
        self.uc.mem_write(self.STACK, bytes(65536))
        args = [self.STOP] if target is None else [self.STOP, root, struct.unpack('<I', struct.pack('<f', value))[0]]
        self.uc.mem_write(stack, struct.pack('<'+'I'*len(args), *args))
        for name in ('EAX', 'EBX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), 0)
        for name, val in (('ECX', root), ('ESP', stack), ('EFLAGS', 2), ('FPCW', 0x27f), ('FPSW', 0), ('FPTAG', 0xffff)):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), val)
        self.phase, self.visited = 'camera_projection', set()
        fields = [(0x104, 4), (0x190, 64), (0x2d0, 64), (0x350, 64), (0x3d0, 16)]
        if target:
            fields.append((offsets[target+'_fov'], 4))
        self.writes = tuple((root+offset, root+offset+length) for offset, length in fields)
        try:
            start = PROJECT if target is None else PRIMARY if target == 'primary' else SECONDARY
            self.uc.emu_start(start, self.STOP, count=2048, timeout=1_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP) != self.STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP) != stack+len(args)*4):
                raise ValueError('Native camera did not return in bounds')
        finally:
            self.phase, self.writes = None, ()
        actual = bytes(self.uc.mem_read(self.STATE, self.SIZE))
        result = {key: list(struct.unpack_from('<16f', actual, 0x100+offset))
                  for key, offset in (('primary', 0x190), ('extended', 0x2d0), ('secondary', 0x350))}
        result['near_extents'] = list(struct.unpack_from('<4f', actual, 0x4d0))
        error = max(abs(a-b) for key in result for a, b in zip(result[key], expected[key]))
        if (any(not math.isfinite(v) for values in result.values() for v in values)
                or any(abs(a-b) > 2e-5+1e-6*abs(b) for key in result for a, b in zip(result[key], expected[key]))
                or (0x10009c62 in self.visited) != expected['ultrawide_branch']
                or (0x10009d8a in self.visited) != expected['ultrawide_branch']):
            raise ValueError('Native projection differs from independent reference')
        struct.pack_into('<I', state, 0x204, 12)
        if target:
            struct.pack_into('<f', state, 0x100+offsets[target+'_fov'], final[target+'_fov'])
        for offset, length in fields:
            if offset in (0x104, 0x120, 0x12c):
                continue
            state[0x100+offset:0x100+offset+length] = actual[0x100+offset:0x100+offset+length]
        if actual != bytes(state):
            raise ValueError('Native camera changed unrelated fields or supplied inputs')
        return {**result, 'settings': final, 'max_error': error,
                'effective_horizontal_fov_radians': expected['effective_horizontal_fov_radians'],
                'ultrawide_branch': expected['ultrawide_branch'], 'native_projection_matches': True,
                'unrelated_fields_preserved': True, 'camera_is_supplied': True,
                'native_constructor_executed': False, 'external_camera_link_present': False,
                'orthographic_mode': False, 'viewport_or_rendering_executed': False,
                'actual_fpv_camera_selection_qualified': False, 'library_loaded': False, 'game_started': False}


def controls():
    for aspect in (.75, 1, 4/3, 1.6, 16/9, 2.5, 2.50001, 32/9):
        for angle in (.4, math.pi/4, math.pi/2, 2.8):
            settings = {'primary_fov': angle, 'secondary_fov': .8, 'aspect': aspect,
                        'near': 1, 'far': 1000, 'secondary_near': .01, 'secondary_far': 20}
            yield settings, {}
            for target in ('primary', 'secondary'):
                for value in (-.5, .01, .5, 2.5, 4):
                    yield settings, {'target': target, 'value': value}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--json-output', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.json_output and args.json_output.exists():
            raise ValueError('Report exists; use a fresh name')
        machine = CameraProjectionOracle(args.library.read_bytes())
        count, error, wide = 0, 0, 0
        for settings, options in controls():
            row = machine.compute(settings, **options)
            count += 1
            wide += row['ultrawide_branch']
            error = max(error, row['max_error'])
        report = {'schema_version': 1, 'scope': 'supplied_native_perspective_camera_and_fov_setters',
                  'library_sha256': DLL_SHA, 'cases': count, 'ultrawide_cases': wide, 'max_error': error,
                  'native_projection_matches': True, 'unrelated_fields_preserved': True,
                  'actual_fpv_camera_selection_qualified': False, 'camera_calibrated': False,
                  'game_started': False, 'game_modified': False}
        if args.json_output:
            with args.json_output.open('x', encoding='utf-8') as out:
                json.dump(report, out, indent=2)
                out.write('\n')
        print(json.dumps(report, indent=2))
        return 0
    except (OSError, ValueError, ImportError) as error:
        print('Native camera audit refused: '+str(error))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
