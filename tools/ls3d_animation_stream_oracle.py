"""Interleaved native attach/weight/tick in one bounded persistent memory.

Targets and relocated clips are diagnostic inputs, not a loaded scene.
No events, callbacks, extra poses, operating-system calls or renderer.
"""
from copy import deepcopy
import math
import struct

from ls3d_attach_oracle import (AttachOracle, START as ATTACH, validate as validate_attach,
                               reference_sequence, reference_attach_step)
from ls3d_tick_oracle import (TickOracle, validate_ticks, reference_tick, observe_native_poses)
from ls3d_time_oracle import START as TICK
from ls3d_math_oracle import f32

WEIGHT = 0x10034460
BOOTSTRAP = {'clip': None, 'slot': 7, 'weight': 1, 'mode': 0}


def validate(names, clips, initial, steps, model_kind=9):
    parsed, _ = validate_attach(names, clips, [BOOTSTRAP], model_kind)
    for data in parsed.values():
        if any(track['flags'] & ~14 for track in data['tracks']):
            raise ValueError('Stream supports transform channels only')
    poses = validate_ticks(initial, names, [0])
    if not isinstance(steps, list) or not 1 <= len(steps) <= 512:
        raise ValueError('Expected one to 512 stream steps')
    clean = []
    for step in steps:
        if not isinstance(step, dict):
            raise ValueError('Expected explicit stream step')
        kind = step.get('kind')
        if kind == 'attach' and set(step) == {'kind', 'clip', 'slot', 'weight', 'mode'}:
            op = {k: v for k, v in step.items() if k != 'kind'}
            _, ops = validate_attach(names, clips, [op], model_kind)
            clean.append({'kind': kind, **ops[0]})
        elif kind == 'weight' and set(step) == {'kind', 'slot', 'weight'}:
            weight = f32(step['weight'])
            if type(step['slot']) is not int or not 0 <= step['slot'] < 8 or not -2 <= weight <= 2:
                raise ValueError('Unreviewed stream weight operation')
            clean.append({**step, 'weight': weight})
        elif kind == 'tick' and set(step) == {'kind', 'delta'}:
            validate_ticks(initial, names, [step['delta']])
            clean.append(dict(step))
        else:
            raise ValueError('Unexpected stream step or fields')
    return parsed, poses, clean


def reference_step(state, poses, flags, names, clips, parsed, step):
    kind = step['kind']
    if kind == 'tick':
        return reference_tick(state, poses, flags, parsed, step['delta'])
    state, poses, flags = deepcopy(state), deepcopy(poses), list(flags)
    if kind == 'attach':
        state = reference_attach_step(state, names, clips, parsed,
                                     {k: v for k, v in step.items() if k != 'kind'})
        for i in state['touched']:
            flags[i] |= 0x10000000
    elif kind == 'weight':
        state['slots'][step['slot']]['weight'] = min(1.0, max(0.0, step['weight']))
        state['dirty'] = True
    else:
        raise ValueError('Unknown validated stream operation')
    return {'state': state, 'poses': poses, 'flags': flags, 'pose_calls': 0,
            'written_channels': 0, 'controller_processed': False}


class AnimationStreamOracle(TickOracle):
    def on_code(self, uc, address, size, context):
        if self.phase == 'stream_weight':
            if not WEIGHT <= address < address+size <= 0x100344dd:
                raise ValueError('Unreviewed stream weight instruction')
            self.visited.add(address)
            return
        return super().on_code(uc, address, size, context)

    def _invoke(self, entry, phase, arguments, writes, controller):
        if self.phase is not None:
            raise ValueError('Nested stream operation')
        stack = self.STACK+0xf000
        self.uc.mem_write(self.STACK, bytes(65536))
        self.uc.mem_write(stack, struct.pack('<'+'I'*(1+len(arguments)), self.STOP, *arguments))
        for name in ('EAX', 'EBX', 'ECX', 'EDX', 'ESI', 'EDI', 'EBP'):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), 0)
        for name, value in (('ESP', stack), ('ECX', controller if phase == 'tick' else 0),
                            ('EFLAGS', 2), ('FPCW', 0x27f), ('FPSW', 0), ('FPTAG', 0xffff)):
            self.uc.reg_write(getattr(self.reg, 'UC_X86_REG_'+name), value)
        self.phase, self.writes, self.visited, self.pose_calls = phase, tuple(writes), set(), 0
        try:
            self.uc.emu_start(entry, self.STOP, count=6_000_000, timeout=20_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP) != self.STOP:
                raise ValueError('Stream instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP) != stack+4*(1+len(arguments)):
                raise ValueError('Stream calling convention differs')
            if phase != 'tick' and self.uc.reg_read(self.reg.UC_X86_REG_EAX) != 0:
                raise ValueError('Native stream operation returned an error')
        finally:
            self.phase, self.writes = None, ()

    def stream(self, names, clips, initial, steps, model_kind=9, *, pose_observer=None):
        if pose_observer is not None and not callable(pose_observer):
            raise ValueError('Invalid stream observer')
        parsed, poses, steps = validate(names, clips, initial, steps, model_kind)
        bootstrap = AttachOracle.sequence(self, names, clips, [BOOTSTRAP], model_kind)
        state = reference_sequence(names, clips, [BOOTSTRAP], model_kind)[-1]
        flags = [8]*len(names)
        model, controller = self.STATE+0x100, self.STATE+0x400
        nodes = [self.STATE+0x1000+i*0x100 for i in range(len(names))]
        pointers = {key: self.STATE+0xa000+i*0x100 for i, key in enumerate(clips)}
        data_pointers = {key: self.SOURCE+0x10000+i*0x10000 for i, key in enumerate(clips)}
        # These are the diagnostic layout checked by the bootstrap, not game addresses.
        for node, pose in zip(nodes, poses):
            for kind, offset in (('position', 0xb0), ('rotation', 0xc0), ('scale', 0xd0)):
                self.uc.mem_write(node+offset, struct.pack('<'+'f'*len(pose[kind]), *pose[kind]))
        source = bytes(self.uc.mem_read(self.SOURCE, 0xa0000))
        attach_writes = [(0, 4), (controller+4, controller+5), (controller+8, controller+0xe8),
                         (controller+0xf0, controller+0xf4), (self.STATE+0x800, self.STATE+0xa00),
                         (self.STATE+0x10000, self.STATE+0x18000)]
        attach_writes += [(node+0xe0, node+0xe4) for node in nodes]
        attach_writes += [(pointer+4, pointer+8) for pointer in pointers.values()]
        tick_writes = [(controller+4, controller+5)]
        for i in range(8):
            tick_writes.extend(((controller+i*0x1c+0xc, controller+i*0x1c+0xd),
                                (controller+i*0x1c+0x14, controller+i*0x1c+0x20)))
        for node in nodes:
            tick_writes.extend(((node+0xb0, node+0xbc), (node+0xc0, node+0xe4)))
        reports, tick_count, max_error = [], 0, 0
        for step in steps:
            expected = reference_step(state, poses, flags, names, clips, parsed, step)
            before = bytes(self.uc.mem_read(self.STATE, self.STATE_SIZE))
            kind = step['kind']
            if kind == 'attach':
                weight = struct.unpack('<I', struct.pack('<f', step['weight']))[0]
                writes = attach_writes
                self._invoke(ATTACH, 'attach', [model, pointers.get(step['clip'], 0),
                             step['slot'], weight, step['mode']], writes, controller)
            elif kind == 'weight':
                slot = step['slot']
                writes = [(controller+4, controller+5),
                          (controller+0x20+slot*0x1c, controller+0x24+slot*0x1c)]
                weight = struct.unpack('<I', struct.pack('<f', step['weight']))[0]
                self._invoke(WEIGHT, 'stream_weight', [model, slot, weight], writes, controller)
            else:
                writes = tick_writes
                self._invoke(TICK, 'tick', [step['delta']], writes, controller)
            actual = bytes(self.uc.mem_read(self.STATE, self.STATE_SIZE))
            self.check_state(actual, expected['state'], parsed, pointers, data_pointers,
                             nodes, node_flags=expected['flags'])
            observed, error = [], 0
            for i, node in enumerate(nodes):
                pose = {}
                for channel, offset, width in (('position', 0xb0, 3), ('rotation', 0xc0, 4), ('scale', 0xd0, 3)):
                    values = struct.unpack_from('<'+'f'*width, actual, node-self.STATE+offset)
                    if any(not math.isfinite(value) for value in values):
                        raise ValueError('Nonfinite persistent stream pose')
                    error = max(error, max(abs(a-b) for a, b in zip(values, expected['poses'][i][channel])))
                    pose[channel] = list(values)
                observed.append(pose)
            if error > 2e-6 or self.pose_calls != expected['pose_calls']:
                raise ValueError('Persistent stream poses or native pose count differ')
            allowed = {i-self.STATE for a, b in writes if a >= self.STATE for i in range(a, b)}
            if (bytes(self.uc.mem_read(self.SOURCE, len(source))) != source
                    or bytes(self.uc.mem_read(0, 4096)) != b'\xff'*4+bytes(4092)
                    or any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, actual)))):
                raise ValueError('Stream changed source, SEH or unrelated state')
            state, poses, flags = expected['state'], expected['poses'], expected['flags']
            max_error = max(max_error, error)
            reports.append({'kind': kind, 'pose_calls': self.pose_calls,
                            'written_channels': expected['written_channels'], 'max_error': error,
                            'active_slots': sum(row['active'] for row in state['slots']),
                            'owners': len(state['owners'])})
            if kind == 'tick':
                observe_native_poses(pose_observer, tick_count, step['delta'], observed)
                tick_count += 1
        return {'bootstrap': bootstrap, 'steps': reports, 'ticks': tick_count, 'max_error': max_error,
                'owner_allocations': self.alloc_count, 'owner_releases': self.free_count,
                'native_interleaved_attach_weight_tick_checked': True,
                'same_native_memory_across_steps': True, 'poses_seeded_only_once': True,
                'full_state_and_descriptors_checked_each_step': True, 'source_inputs_preserved': True,
                'allocator_is_bounded_double': True, 'clip_relocation_is_synthetic': True,
                'client_transition_decision_executed': False, 'native_loader_executed': False,
                'events_or_callbacks_called': False, 'skin_or_renderer_called': False,
                'scene_loaded': False, 'library_loaded': False, 'game_started': False}
