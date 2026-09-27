"""Native attach -> controller tick -> full transform poses in one CPU memory.

Initial transforms and setup operations are explicit diagnostic inputs.
No callback-enabled targets, extra poses, scene loader, skin or renderer.
"""
from copy import deepcopy
import math
import struct

from ls3d_attach_oracle import AttachOracle, validate as validate_attachment, reference_sequence
from ls3d_pose_oracle import POSE_START, POSE_RANGES, reference as pose_reference, validate as validate_pose
from ls3d_time_oracle import START as TIME_START, reference as time_reference
from benelli_pose_chain_audit import key_window

TICK_RANGES = (*POSE_RANGES, (0x1001fac7, 0x1001fadc), (0x1001febc, 0x1001fec3),
               (TIME_START, 0x10020203), (0x10020212, 0x10020256), (0x10004e80, 0x10004e9b))


def validate_ticks(initial, names, deltas):
    if not isinstance(initial,list) or len(initial) != len(names):
        raise ValueError('Expected explicit initial pose for every tick target')
    poses = [validate_pose(pose,[],8)[0] for pose in initial]
    if (not isinstance(deltas,list) or not 1 <= len(deltas) <= 1024
            or any(type(delta) is not int or not 0 <= delta <= 10000 for delta in deltas)):
        raise ValueError('Unreviewed tick sequence')
    return poses


def reference_tick(state, poses, flags, parsed, delta):
    """Pose samples the advanced time BEFORE the controller wraps/deactivates."""
    if type(delta) is not int or not 0 <= delta <= 10000:
        raise ValueError('Unreviewed tick step')
    state=deepcopy(state); poses=deepcopy(poses); flags=list(flags)
    processed=state['dirty'] or bool(delta); calls=0; written=0
    if processed:
        for index, descriptors in state['owners'].items():
            slots=[]
            for slot, binding in zip(state['slots'],descriptors):
                time=slot['time']+(delta if slot['active'] else 0)
                if not 0 <= time <= 65535*40+39:
                    raise ValueError('Tick sample time outside reviewed nonnegative domain')
                channels={} if binding is None else parsed[binding[0]]['tracks'][binding[1]]['channels']
                slots.append({'active':slot['active'],'time':time,'weight':slot['weight'],
                    'channels':{kind:key_window(curve,time) for kind,curve in channels.items()}})
            row=pose_reference(poses[index],slots);poses[index]=row['pose'];calls+=1
            counts=row['accumulation_counts'];written+=sum(bool(n) for n in counts.values())
            if counts['position']: flags[index]=(flags[index]&0xfffffedf)|0x40000000
            if counts['rotation'] or counts['scale']: flags[index]=(flags[index]&0xfffffecb)|0x40000008
    time_slots=[{'active':slot['active'],'mode':slot['mode'],
        'frame_end':parsed[slot['clip']]['frame_end'] if slot['clip'] else 1,
        'time':slot['time'],'previous':slot['previous'],'last_delta':slot['last_delta']} for slot in state['slots']]
    clock=time_reference(time_slots,delta,state['dirty'])
    for slot, updated in zip(state['slots'],clock['slots']):
        slot.update({key:updated[key] for key in ('active','time','previous','last_delta')})
    state['dirty']=clock['dirty']
    return {'state':state,'poses':poses,'flags':flags,'pose_calls':calls,'written_channels':written,
            'controller_processed':processed}


class TickOracle(AttachOracle):
    def on_code(self,uc,address,size,context):
        if self.phase != 'tick': return super().on_code(uc,address,size,context)
        if not any(a<=address and address+size<=b for a,b in TICK_RANGES):
            raise ValueError(f'Unreviewed tick instruction/extra pose/callback: {address:#x}')
        self.visited.add(address)
        if address==POSE_START:self.pose_calls+=1

    def sequence_with_ticks(self,names,clips,operations,initial,deltas,model_kind=9):
        parsed,operations=validate_attachment(names,clips,operations,model_kind)
        poses=validate_ticks(initial,names,deltas)
        attachment=super().sequence(names,clips,operations,model_kind)
        state=reference_sequence(names,clips,operations,model_kind)[-1]
        flags=[8|(0x10000000 if i in state['touched'] else 0) for i in range(len(names))]
        nodes=[self.STATE+0x1000+i*0x100 for i in range(len(names))]
        # Explicit seed after attachment. This is not a claim about a loaded
        # model's initial pose; subsequent ticks carry the actual node memory.
        for node,pose in zip(nodes,poses):
            for kind,offset in (('position',0xb0),('rotation',0xc0),('scale',0xd0)):
                self.uc.mem_write(node+offset,struct.pack('<'+'f'*len(pose[kind]),*pose[kind]))
        source=bytes(self.uc.mem_read(self.SOURCE,0xa0000))
        controller=self.STATE+0x400;writes=[(controller+4,controller+5)]
        for i in range(8):
            writes.extend(((controller+i*0x1c+0xc,controller+i*0x1c+0xd),
                           (controller+i*0x1c+0x14,controller+i*0x1c+0x20)))
        for node in nodes:writes.extend(((node+0xb0,node+0xbc),(node+0xc0,node+0xe4)))
        allowed={i-self.STATE for a,b in writes for i in range(a,b)}
        reports=[];max_error=0
        for delta in deltas:
            expected=reference_tick(state,poses,flags,parsed,delta)
            before=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE))
            stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
            self.uc.mem_write(stack,struct.pack('<II',self.STOP,delta))
            for name in ('EAX','EBX','EDX','ESI','EDI','EBP'):self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),0)
            for name,value in (('ESP',stack),('ECX',controller),('EFLAGS',2),('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
                self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
            self.phase='tick';self.writes=tuple(writes);self.visited=set();self.pose_calls=0
            try:
                self.uc.emu_start(TIME_START,self.STOP,count=2_000_000,timeout=10_000_000)
                if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP:raise ValueError('Tick instruction/time budget exhausted')
                if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+8:raise ValueError('Tick calling convention differs')
            finally:self.phase=None;self.writes=()
            actual=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE));error=0
            for index,node in enumerate(nodes):
                for kind,offset,width in (('position',0xb0,3),('rotation',0xc0,4),('scale',0xd0,3)):
                    values=struct.unpack_from('<'+'f'*width,actual,node-self.STATE+offset)
                    if any(not math.isfinite(value) for value in values):raise ValueError('Nonfinite native tick pose')
                    error=max(error,max(abs(a-b) for a,b in zip(values,expected['poses'][index][kind])))
                if struct.unpack_from('<I',actual,node-self.STATE+0xe0)[0]!=expected['flags'][index]:
                    raise ValueError('Native tick pose flags differ')
            if error>2e-6:raise ValueError('Native attached tick pose differs from independent reference')
            for index,slot in enumerate(expected['state']['slots']):
                offset=0x400+index*0x1c
                if (actual[offset+0xc]!=int(slot['active']) or struct.unpack_from('<iii',actual,offset+0x14)!=
                        (slot['time'],slot['previous'],slot['last_delta'])):raise ValueError('Native attached tick times differ')
            if actual[0x404]!=0 or self.pose_calls!=expected['pose_calls']:
                raise ValueError('Native attached tick processing/count differs')
            if (bytes(self.uc.mem_read(self.SOURCE,len(source)))!=source
                    or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,actual)))):
                raise ValueError('Tick changed clips, descriptors or unrelated target data')
            state,poses,flags=expected['state'],expected['poses'],expected['flags'];max_error=max(max_error,error)
            reports.append({'delta':delta,'controller_processed':expected['controller_processed'],
                'pose_calls':self.pose_calls,'written_channels':expected['written_channels'],
                'active_slots':sum(slot['active'] for slot in state['slots']),'max_error':error})
        return {'attachment':attachment,'ticks':reports,'max_error':max_error,
            'native_attached_time_pose_checked':True,'same_native_memory_across_phases':True,
            'full_original_channels_sampled':True,'initial_pose_is_explicit_seed':True,
            'inputs_and_descriptors_preserved':True,'poses_before_wrap_or_deactivation':True,
            'allocator_is_bounded_double':True,'poses_carried_between_ticks':True,
            'events_or_callbacks_called':False,'extra_poses_evaluated':False,
            'native_loader_executed':False,'skin_or_renderer_called':False,
            'game_initial_pose_policy_qualified':False,'time_unit_seconds_qualified':False,
            'scene_loaded':False,'library_loaded':False,'game_started':False}
