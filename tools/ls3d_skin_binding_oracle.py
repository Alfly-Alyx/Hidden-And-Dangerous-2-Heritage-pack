"""Pinned skin joint discovery/ownership on synthetic post-load frame trees.

Real GetType, hierarchy traversal, ID ordering and owner writes execute.
Fresh skin only: free(NULL), bounded pointer allocation and bounds-refresh
are explicit doubles. No mesh loading, cloning, palette, skin or rendering.
"""
import struct
from ls3d_math_oracle import MathOracle

START = 0x100527d0
GET_TYPE = 0x10057050
FREE, ALLOC, BOUNDS = 0x1008d310, 0x1008d41c, 0x10052330
COUNT, SCRATCH = 0x100bf3d0, 0x100c03e0
RANGES = ((START, 0x100528b3), (0x100528ca, 0x1005295e),
          (0x10052960, 0x100529bf), (GET_TYPE, 0x10057065))


def reference(nodes, geometry_present=True):
    if type(geometry_present) is not bool or not isinstance(nodes, list) or not 1 <= len(nodes) <= 128:
        raise ValueError('Unreviewed skin tree or geometry flag')
    children = {i: [] for i in range(len(nodes))}
    ids = []
    for i, node in enumerate(nodes):
        if not isinstance(node, dict) or set(node) != {'parent', 'frame_type', 'visual_type', 'bone_id'}:
            raise ValueError('Unexpected skin binding node')
        kind, visual, bone, parent = (node[k] for k in ('frame_type', 'visual_type', 'bone_id', 'parent'))
        if type(parent) is not int or not (parent == -1 if i == 0 else 0 <= parent < i):
            raise ValueError('Expected one parent-first skin tree')
        if type(kind) is not int or kind not in (1, 6, 10):
            raise ValueError('Unreviewed skin-tree frame kind')
        if (kind == 1 and (type(visual) is not int or visual not in (0, 1, 2, 3))) or (kind != 1 and visual is not None):
            raise ValueError('Unreviewed skin-tree visual kind')
        if kind == 10:
            if type(bone) is not int or not 0 <= bone < 64 or bone in ids:
                raise ValueError('Invalid or duplicate bone ID')
            ids.append(bone)
        elif bone is not None:
            raise ValueError('Non-joint has a bone ID')
        if i:
            children[parent].append(i)
    if nodes[0]['frame_type'] != 1 or nodes[0]['visual_type'] != 2:
        raise ValueError('Expected a skin visual root')
    collected, stopped, visual_queries = [], [], []
    def visit(parent):
        for i in children[parent]:
            node = nodes[i]
            if node['frame_type'] == 1:
                visual_queries.append(i)
            if node['frame_type'] == 1 and node['visual_type'] in (2, 3):
                stopped.append(i)
                break  # Native exits this sibling loop, not merely this subtree.
            if node['frame_type'] == 10:
                collected.append(i)
            visit(i)
    if geometry_present:
        visit(0)
    if {nodes[i]['bone_id'] for i in collected} != set(range(len(collected))):
        raise ValueError('Collected bones must have contiguous IDs; no null palette entries')
    ordered = sorted(collected, key=lambda i: nodes[i]['bone_id'])
    return {'collected_nodes': collected, 'ordered_nodes': ordered,
            'stopped_at_nested_skin_nodes': stopped, 'bone_count': len(collected),
            'success': bool(collected), 'native_visual_type_lookup_calls': len(visual_queries)}


class SkinBindingOracle(MathOracle):
    NODES, NODES_SIZE = 0x3d00000, 0x30000
    SOURCE, SOURCE_SIZE = 0x3e00000, 4096

    def __init__(self, library):
        super().__init__(library)
        self.uc.mem_map(self.NODES, self.NODES_SIZE, self.uni.UC_PROT_READ | self.uni.UC_PROT_WRITE)
        self.uc.mem_map(self.SOURCE, self.SOURCE_SIZE, self.uni.UC_PROT_READ)
        for page in (COUNT & ~4095, SCRATCH & ~4095):
            self.uc.mem_protect(page, 4096, self.uni.UC_PROT_READ | self.uni.UC_PROT_WRITE)

    def on_code(self, uc, address, size, context):
        if self.phase != 'skin_binding':
            return super().on_code(uc, address, size, context)
        if address in (FREE, ALLOC, BOUNDS):
            stack = uc.reg_read(self.reg.UC_X86_REG_ESP)
            ret = struct.unpack('<I', uc.mem_read(stack, 4))[0]
            arg = struct.unpack('<I', uc.mem_read(stack+4, 4))[0]
            if address == FREE:
                if ret != 0x10052813 or arg != 0:
                    raise ValueError('Only a fresh skin free(NULL) is reviewed')
                self.calls.append('free_null')
                result = 0
            elif address == ALLOC:
                if ret != 0x100528a4 or arg != self.expected_count*4 or not 4 <= arg <= 256:
                    raise ValueError('Unreviewed skin pointer-array allocation')
                self.calls.append('allocate_pointers')
                result = self.NODES+0x20000
            else:
                if ret != 0x10052943 or uc.reg_read(self.reg.UC_X86_REG_ECX) != self.root:
                    raise ValueError('Unreviewed skin bounds-refresh caller')
                self.calls.append('bounds_refresh_not_executed')
                result = 0
            uc.reg_write(self.reg.UC_X86_REG_EAX, result)
            uc.reg_write(self.reg.UC_X86_REG_ESP, stack+4)
            uc.reg_write(self.reg.UC_X86_REG_EIP, ret)
            return
        if address == GET_TYPE:
            stack = uc.reg_read(self.reg.UC_X86_REG_ESP)
            ret, node = struct.unpack('<II', uc.mem_read(stack, 8))
            if ret not in (0x1005286d, 0x1005299e) or node not in self.visuals:
                raise ValueError('Unreviewed visual type lookup')
            self.type_calls += 1
        if not any(a <= address and address+size <= b for a, b in RANGES):
            raise ValueError('Unreviewed skin binding instruction or call')

    def bind(self, nodes, geometry_present=True):
        expected = reference(nodes, geometry_present)
        if self.phase is not None:
            raise ValueError('Nested skin binding phase')
        state, source = bytearray(self.NODES_SIZE), bytearray(self.SOURCE_SIZE)
        pointers = [self.NODES+0x1000+i*0x300 for i in range(len(nodes))]
        self.root, self.expected_count = pointers[0], expected['bone_count']
        self.visuals = {p for p, n in zip(pointers, nodes) if n['frame_type'] == 1}
        struct.pack_into('<I', source, 0x104, GET_TYPE)
        children = {i: [] for i in range(len(nodes))}
        for i, node in enumerate(nodes):
            if i:
                children[node['parent']].append(i)
            offset = pointers[i]-self.NODES
            struct.pack_into('<I', state, offset, self.SOURCE+0x100)
            struct.pack_into('<HH', state, offset+0xf8, node['frame_type'], node['visual_type'] or 0)
            if node['frame_type'] == 10:
                struct.pack_into('<I', state, offset+0x160, node['bone_id'])
        for parent, rows in children.items():
            if rows:
                struct.pack_into('<I', state, pointers[parent]-self.NODES+0x10c, pointers[rows[0]])
                for left, right in zip(rows, rows[1:]):
                    struct.pack_into('<I', state, pointers[left]-self.NODES+0x110, pointers[right])
        struct.pack_into('<I', state, 0x1000+0x1e0, self.SOURCE+0x200 if geometry_present else 0)
        struct.pack_into('<I', state, 0x1000+0x1d0, 0x40000)
        state[0x20000:0x20100] = b'Z'*256
        self.uc.mem_write(self.NODES, bytes(state))
        self.uc.mem_write(self.SOURCE, bytes(source))
        self.uc.mem_write(COUNT, bytes(4))
        self.uc.mem_write(SCRATCH, b'Z'*256)
        stack = self.STACK+0xf000
        self.uc.mem_write(self.STACK, bytes(65536))
        self.uc.mem_write(stack, struct.pack('<I', self.STOP))
        for name in ('EAX', 'EBX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), 0)
        for name, value in (('ECX', self.root), ('ESP', stack), ('EFLAGS', 2)):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), value)
        writes = [(COUNT, COUNT+4), (SCRATCH, SCRATCH+256), (self.root+0x210, self.root+0x218),
                  (self.root+0x1d0, self.root+0x1d4),
                  (self.NODES+0x20000, self.NODES+0x20000+expected['bone_count']*4)]
        writes += [(p+0x168, p+0x16c) for p, n in zip(pointers, nodes) if n['frame_type'] == 10]
        self.phase, self.writes, self.calls, self.type_calls = 'skin_binding', tuple(writes), [], 0
        try:
            self.uc.emu_start(START, self.STOP, count=100000, timeout=2_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP) != self.STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP) != stack+4
                    or self.uc.reg_read(self.reg.UC_X86_REG_EAX)&255 != int(expected['success'])):
                raise ValueError('Native skin binding result or execution budget differs')
        finally:
            self.phase, self.writes = None, ()
        wanted_calls = ['free_null']
        if expected['success']:
            wanted_calls += ['allocate_pointers', 'bounds_refresh_not_executed']
            struct.pack_into('<II', state, 0x1000+0x210, expected['bone_count'], self.NODES+0x20000)
            struct.pack_into('<I', state, 0x1000+0x1d0, 0)
            for bone, index in enumerate(expected['ordered_nodes']):
                struct.pack_into('<I', state, 0x20000+bone*4, pointers[index])
                struct.pack_into('<I', state, pointers[index]-self.NODES+0x168, self.root)
        scratch = bytearray(b'Z'*256)
        for i, index in enumerate(expected['collected_nodes']):
            struct.pack_into('<I', scratch, i*4, pointers[index])
        if (bytes(self.uc.mem_read(self.NODES, len(state))) != bytes(state)
                or bytes(self.uc.mem_read(self.SOURCE, len(source))) != bytes(source)
                or bytes(self.uc.mem_read(SCRATCH, 256)) != bytes(scratch)
                or struct.unpack('<I', self.uc.mem_read(COUNT, 4))[0] != expected['bone_count']
                or self.calls != wanted_calls or self.type_calls != expected['native_visual_type_lookup_calls']):
            raise ValueError('Native skin joint collection, sorting, ownership or preserved state differs')
        return {**expected, 'native_joint_discovery_and_ownership_match': True,
                'unrelated_fields_preserved': True,
                'fresh_post_load_tree_is_supplied': True, 'allocation_is_bounded_double': True,
                'bounds_refresh_executed': False, 'native_loader_executed': False,
                'native_clone_executed': False, 'palette_skin_renderer_executed': False,
                'library_loaded': False, 'game_started': False}
