"""Native animated skin bounds from supplied cached joint-space matrices.

Executes corner transforms, box union, sphere and root invalidation. Joint
matrices, descriptor and geometry presence are synthetic inputs; no loader,
joint discovery, animation, clone, graphics driver or OS API executes.
"""
from itertools import product
import math
import struct

from ls3d_math_oracle import MathOracle, f32, vector
from ls3d_palette_oracle import affine_matrix

START = 0x10052330
POINT = 0x1002eab0
UNION = 0x10015050
RANGES = ((START, 0x10052368), (0x1005237b, 0x10052385), (0x100523bb, 0x100523c5),
          (0x10052410, 0x10052480), (0x100524c7, 0x100526eb), (0x10052786, 0x100527ac),
          (0x1001e790, 0x1001e7a9), (0x1001e7c8, 0x1001e7c9),
          (POINT, 0x1002eb3d), (UNION, 0x100150c3),
          (0x10005a60, 0x10005a79), (0x10010930, 0x10010953), (0x1002ff30, 0x1002ff47))


def box(value):
    value = vector(value, 8, 10)
    if value[3] != 0 or value[7] != 0 or any(value[i] > value[4+i] for i in range(3)):
        raise ValueError('Expected nonempty finite box with zero padding')
    return value


def validate(base, bounds, matrices):
    base = box(base)
    if (not isinstance(bounds, (list, tuple)) or not 1 <= len(bounds) <= 64
            or not isinstance(matrices, (list, tuple)) or len(matrices) != len(bounds)):
        raise ValueError('Expected one to 64 paired joint boxes and cached matrices')
    return base, [box(b) for b in bounds], [affine_matrix(m) for m in matrices]


def reference(base, bounds, matrices):
    base, bounds, matrices = validate(base, bounds, matrices)
    low, high = base[:3], base[4:7]
    for bound, matrix in zip(bounds, matrices):
        for corner in product(*[(bound[i], bound[4+i]) for i in range(3)]):
            point = [f32(corner[0]*matrix[i]+matrix[12+i]+
                         corner[1]*matrix[4+i]+corner[2]*matrix[8+i]) for i in range(3)]
            low = [min(a, b) for a, b in zip(low, point)]
            high = [max(a, b) for a, b in zip(high, point)]
    half = [f32(f32(b-a)*.5) for a, b in zip(low, high)]
    center = [f32(a+b) for a, b in zip(low, half)]
    radius = f32(math.sqrt(sum(v*v for v in half)))
    return {'bounds': low+[0.0]+high+[0.0], 'center': center, 'radius': radius}


class SkinBoundsOracle(MathOracle):
    SOURCE, SOURCE_SIZE = 0x3f00000, 0x20000
    STATE, STATE_SIZE = 0x4100000, 4096

    def __init__(self, library):
        super().__init__(library)
        self.uc.mem_map(self.SOURCE, self.SOURCE_SIZE, self.uni.UC_PROT_READ)
        self.uc.mem_map(self.STATE, self.STATE_SIZE, self.uni.UC_PROT_READ | self.uni.UC_PROT_WRITE)

    def on_code(self, uc, address, size, context):
        if self.phase != 'skin_bounds':
            return super().on_code(uc, address, size, context)
        if not any(a <= address and address+size <= b for a, b in RANGES):
            raise ValueError(f'Unreviewed skin bounds instruction: {address:#x}')
        if address == POINT:
            self.point_calls += 1
        elif address == UNION:
            self.union_calls += 1

    def compute(self, base, bounds, matrices):
        expected = reference(base, bounds, matrices)
        base, bounds, matrices = validate(base, bounds, matrices)
        if self.phase is not None:
            raise ValueError('Nested skin bounds phase')
        source, state = bytearray(self.SOURCE_SIZE), bytearray(self.STATE_SIZE)
        root = self.STATE+0x100
        struct.pack_into('<HH', state, 0x1f8, 1, 2)
        struct.pack_into('<I', state, 0x204, 11)
        struct.pack_into('<I', state, 0x2d0, 0x40000)
        struct.pack_into('<I', state, 0x2e0, self.SOURCE+0x300)
        struct.pack_into('<IIII', state, 0x310, len(bounds), self.SOURCE+0x400, 7, 0)
        struct.pack_into('<I', state, 0x320, self.SOURCE+0x200)
        struct.pack_into('<I', source, 0x208, self.SOURCE+0x10000)
        struct.pack_into('<8f', source, 0x210, *base)
        for i, (bound, matrix) in enumerate(zip(bounds, matrices)):
            joint = self.SOURCE+0x1000+i*0x200
            struct.pack_into('<I', source, 0x400+i*4, joint)
            struct.pack_into('<I', source, joint-self.SOURCE+0x164, 0x10)
            struct.pack_into('<16f', source, joint-self.SOURCE+0x120, *matrix)
            struct.pack_into('<8f', source, 0x10000+i*96+64, *bound)
        self.uc.mem_write(self.SOURCE, bytes(source))
        self.uc.mem_write(self.STATE, bytes(state))
        stack = self.STACK+0xf000
        self.uc.mem_write(self.STACK, bytes(65536))
        self.uc.mem_write(stack, struct.pack('<I', self.STOP))
        for name in ('EAX', 'EBX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), 0)
        for name, value in (('ECX', root), ('ESP', stack), ('EFLAGS', 2),
                            ('FPCW', 0x27f), ('FPSW', 0), ('FPTAG', 0xffff)):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), value)
        writes = ((root+0x104, root+0x108), (root+0x1a0, root+0x1d4), (root+0x21c, root+0x220))
        self.phase, self.writes, self.point_calls, self.union_calls = 'skin_bounds', writes, 0, 0
        try:
            self.uc.emu_start(START, self.STOP, count=250000, timeout=3_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != self.STOP:
                raise ValueError('Skin bounds instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP) != stack+4:
                raise ValueError('Skin bounds stack differs')
        finally:
            self.phase, self.writes = None, ()
        actual = bytes(self.uc.mem_read(self.STATE, self.STATE_SIZE))
        result = {'bounds': list(struct.unpack_from('<8f', actual, 0x2a0)),
                  'center': list(struct.unpack_from('<3f', actual, 0x2c0)),
                  'radius': struct.unpack_from('<f', actual, 0x2cc)[0]}
        error = max([abs(a-b) for k in ('bounds', 'center') for a, b in zip(result[k], expected[k])]
                    +[abs(result['radius']-expected['radius'])])
        if (any(not math.isfinite(v) for v in result['bounds']+result['center']+[result['radius']])
                or error > 2e-5 or self.point_calls != 8*len(bounds) or self.union_calls != 8*len(bounds)):
            raise ValueError('Native skin bounds or corner count differs')
        struct.pack_into('<I', state, 0x204, 12)
        struct.pack_into('<I', state, 0x2d0, 0x20000)
        struct.pack_into('<I', state, 0x31c, 7)
        state[0x2a0:0x2d0] = actual[0x2a0:0x2d0]
        if actual != bytes(state) or bytes(self.uc.mem_read(self.SOURCE, len(source))) != bytes(source):
            raise ValueError('Skin bounds changed unrelated fields or cached joint inputs')
        return {**result, 'max_error': error, 'native_corner_transforms': self.point_calls,
                'native_bounds_and_sphere_match': True, 'inputs_preserved': True,
                'cached_joint_matrices_are_supplied': True, 'skin_root_has_no_parent': True,
                'native_joint_discovery_executed': False, 'native_loader_executed': False,
                'native_clone_executed': False, 'animation_skin_renderer_executed': False,
                'allocation_called': False, 'library_loaded': False, 'game_started': False}
