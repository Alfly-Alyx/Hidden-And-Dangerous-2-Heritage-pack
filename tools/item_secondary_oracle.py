"""Reviewed secondary-action argument paths, not a complete aim operation.

Only the pinned private image executes, with synthetic actor/camera objects.
Every gameplay, scene, animation, global-manager and rendering call is stopped
before execution. Native descriptor readers retain their own bounded oracle.
"""
from __future__ import annotations
import math
import struct

from item_native_contract import Oracle,sha
from item_native_layout import decode_record

# Each phase has its own instruction allowlist and BEFORE-call stop sites.
PHASES={
    'gate':(0x5458b3,((0x5458b3,0x5458cb),),(0x5458cb,0x545b5f)),
    'toggle':(0x54592a,((0x54592a,0x545950),(0x545985,0x54598f),(0x545b58,0x545b5a)),
              (0x545950,0x54598f,0x545b5a)),
    'action_pointer':(0x546d76,((0x546d76,0x546d82),),(0x546d82,)),
    'aim_arguments':(0x546d87,((0x546d87,0x546d90),),(0x546d90,)),
    'hud_arguments':(0x49dc9c,((0x49dc9c,0x49dcac),),(0x49dcac,)),
    'hud_branch':(0x4a8cc0,((0x4a8cc0,0x4a8cd4),),(0x4a8cd4,0x4a8cef,0x4a8cff,0x4a8d2d)),
    'fpv_target':(0x49217e,((0x49217e,0x49218d),(0x4921c5,0x4921c7)),(0x49218d,0x4921c7)),
    'camera_get':(0x465e80,((0x465e80,0x465e90),),(0x465e90,0x465e91)),
    'interpolate':(0x491b63,((0x491b63,0x491bb5),(0x491bc8,0x491bca)),(0x491bb5,0x491bca)),
    'camera_set':(0x465e50,((0x465e50,0x465e6b),),(0x465e6b,0x465e5d)),
}
HUD_BRANCHES={'two_frames':0x4a8cd4,'one_frame':0x4a8cef,'hide_frames':0x4a8cff,'no_frame_call':0x4a8d2d}
RATE_RAW=0x3b4de32f


def uint(value,label):
    if type(value) is not int or not 0<=value<=0xffffffff:raise ValueError('Invalid '+label)
    return value


def float_word(value,label):
    if type(value) not in (int,float):raise ValueError('Non-numeric '+label)
    try:
        if not math.isfinite(value):raise ValueError('Non-finite '+label)
        raw=struct.pack('<f',value)
    except (OverflowError,struct.error) as error:raise ValueError('Out-of-range '+label) from error
    if not math.isfinite(struct.unpack('<f',raw)[0]):raise ValueError('Out-of-range '+label)
    return struct.unpack('<I',raw)[0]


def as_float(raw):return struct.unpack('<f',struct.pack('<I',raw))[0]


def route(mode,current_state):
    uint(mode,'secondary mode');uint(current_state,'actor aim state')
    return 0 if current_state else 2 if mode==5 else 3


def hud_branch(mode):
    uint(mode,'secondary mode')
    return 'two_frames' if mode<4 else 'one_frame' if mode==4 else 'hide_frames' if mode==6 else 'no_frame_call'


def fields(raw):
    layout=decode_record(raw);action=layout['actions'][1]
    if layout['kind']!=1 or action['selector']!=5:raise ValueError('Expected Weapon secondary selector 5')
    reserved,runtime_type,mode,scalar=struct.unpack_from('<4I',raw,action['payload_offset'])
    value=as_float(scalar)
    if reserved!=0 or runtime_type!=4:raise ValueError('Unreviewed secondary action constants')
    # Bounded analysis domain, not a claim that the native client validates it.
    if not math.isfinite(value) or not 0<value<math.pi:raise ValueError('Secondary angle outside reviewed domain')
    return {'mode_raw':mode,'scalar_raw':scalar,'scalar_radians':value,
            'scalar_degrees':math.degrees(value),'record_sha256':sha(raw)}


def interpolation(current_raw,target_raw,step):
    current=as_float(uint(current_raw,'current camera scalar'));target=as_float(uint(target_raw,'target camera scalar'))
    step_raw=float_word(step,'synthetic time step');dt=as_float(step_raw)
    if not all(math.isfinite(v) and 0<v<math.pi for v in (current,target)) or not 0<=dt<=1000:
        raise ValueError('Interpolation outside bounded synthetic domain')
    if current==target:return {'setter_requested':False,'next_raw':current_raw,'step_raw':step_raw}
    distance=dt*as_float(RATE_RAW)
    value=max(target,current-distance) if current>target else min(target,current+distance)
    return {'setter_requested':True,'next_raw':float_word(value,'interpolated scalar'),'step_raw':step_raw}


class SecondaryOracle(Oracle):
    def __init__(self,image):super().__init__(image);self.phase=None

    def on_code(self,uc,address,size,context):
        if self.phase is None:return super().on_code(uc,address,size,context)
        _,ranges,stops=PHASES[self.phase]
        if address in stops:self.uc.emu_stop();return
        if not any(a<=address and address+size<=b for a,b in ranges):
            raise ValueError('Secondary phase refused an unreviewed instruction or external call')

    def _run(self,phase):
        if self.phase is not None:raise ValueError('Nested secondary phase refused')
        start,_,stops=PHASES[phase];self.phase=phase
        try:
            self.uc.emu_start(start,self.STOP,count=512,timeout=1_000_000)
            result=self.uc.reg_read(self.reg.UC_X86_REG_EIP)
            if result not in stops:raise ValueError('Secondary phase exceeded instruction/time budget')
            return result
        finally:self.phase=None

    def registers(self,**values):
        for name,value in values.items():self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)

    def inspect_action(self,raw,slot):
        expected=fields(raw);self.inspect_record(raw,slot)
        obj=self.HEAP;action=self.get(obj+0x4c);stack=self.STACK+0x8000
        actor=self.HEAP+0x8000;item=self.HEAP+0x9000;manager=self.HEAP+0xa000;hud=self.HEAP+0xb000
        self.put(actor+0xa8,item);self.put(item+4,obj);self.put(manager+0x5c,self.FPV)
        self.put(actor+0x52c,0)
        arena_before=bytes(self.uc.mem_read(self.HEAP,65536));fpv_before=bytes(self.uc.mem_read(self.FPV,0x4d000))
        checks=[]
        try:
            self.registers(EDI=item,ESP=stack,EFLAGS=2)
            if self._run('gate')!=0x5458cb:raise ValueError('Secondary runtime-type gate rejected the decoded action')
            for current in (0,1,2,3):
                self.put(actor+0x52c,current);self.registers(ESI=actor,ESP=stack,EFLAGS=2)
                stop=self._run('toggle');state=route(expected['mode_raw'],current)
                if (stop!={0:0x545b5a,2:0x545950,3:0x54598f}[state]
                        or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=actor
                        or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-4 or self.get(stack-4)!=state
                        or self.get(actor+0x52c)!=current):raise ValueError('Secondary actor-state argument differs')
                checks.append({'synthetic_current_state':current,'requested_state':state})
            self.put(actor+0x52c,0)
            self.registers(ESI=actor,ESP=stack)
            self._run('action_pointer')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESI)!=action:raise ValueError('Secondary descriptor pointer differs')
            self.registers(EAX=manager);self._run('aim_arguments')
            if (self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-8
                    or (self.get(stack-8),self.get(stack-4))!=(1,expected['scalar_raw'])
                    or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=self.FPV):raise ValueError('Secondary FPV scalar argument differs')
            self.registers(EAX=item,ESI=hud,ESP=stack);self._run('hud_arguments')
            if (self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-4 or self.get(stack-4)!=expected['mode_raw']
                    or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=hud+0x2e60):raise ValueError('Secondary HUD mode argument differs')
            self.put(stack,self.STOP);self.put(stack+4,expected['mode_raw'])
            self.registers(ESP=stack,ECX=hud+0x2e60)
            branch=hud_branch(expected['mode_raw'])
            if self._run('hud_branch')!=HUD_BRANCHES[branch]:raise ValueError('Secondary HUD dispatch differs')
            for enabled,state in ((True,11),(False,12)):
                self.put(stack+0x10,expected['scalar_raw']);self.registers(ESP=stack,ESI=self.FPV,EBX=int(enabled))
                stop=self._run('fpv_target')
                if (stop!=(0x49218d if enabled else 0x4921c7) or self.get(self.FPV+0x30)!=expected['scalar_raw']
                        or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-4 or self.get(stack-4)!=state
                        or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=self.FPV):raise ValueError('Secondary target or animation-state argument differs')
            changed=bytearray(fpv_before);struct.pack_into('<I',changed,0x30,expected['scalar_raw'])
            if bytes(self.uc.mem_read(self.FPV,len(changed)))!=bytes(changed) or bytes(self.uc.mem_read(self.HEAP,65536))!=arena_before:
                raise ValueError('Secondary path changed unexpected synthetic object bytes')
            return {**expected,'slot':slot,'native_secondary_paths_match':True,'actor_state_requests':checks,
                    'hud_dispatch':branch,'fpv_aim_state':11,'fpv_deaim_state':12,'fpv_target_member':0x30,
                    'descriptor_and_objects_unchanged':True,'complete_aim_operation_executed':False,
                    'scene_or_animation_calls_executed':False,'camera_rendering_qualified':False,
                    'deaim_scalar_source_qualified':False,
                    'game_started':False,'game_modified':False}
        finally:
            self.put(actor+0x52c,0);self.uc.mem_write(self.FPV,fpv_before)

    def inspect_interpolation(self,current,target,step):
        current_raw=float_word(current,'current scalar');target_raw=float_word(target,'target scalar')
        expected=interpolation(current_raw,target_raw,step)
        if self.get(0x80ff1c)!=RATE_RAW:raise ValueError('Changed camera interpolation rate')
        if (self.get(0x80fe20),self.get(0x80fe24))!=(0x465e50,0x465e80):raise ValueError('Changed camera module methods')
        stack=self.STACK+0x8000;module=self.HEAP+0x8000;camera=self.HEAP+0x9000;vtable=self.HEAP+0xa000
        self.put(module+0x240,camera);self.put(camera,vtable);self.put(camera+0x120,current_raw)
        before=bytes(self.uc.mem_read(self.FPV,0x4d000));arena=bytes(self.uc.mem_read(self.HEAP,65536))
        self.put(self.FPV+0x30,target_raw);self.put(stack+0xc,expected['step_raw']);self.put(stack+8,0xdeadbeef)
        seeded=bytes(self.uc.mem_read(self.FPV,len(before)))
        try:
            self.registers(ESP=stack,ECX=module,FPCW=0x37f,FPSW=0,FPTAG=0xffff)
            if self._run('camera_get')!=0x465e90:raise ValueError('Synthetic camera getter unexpectedly used fallback')
            self.registers(ESI=self.FPV)
            stop=self._run('interpolate')
            if (stop==0x491bb5)!=expected['setter_requested']:raise ValueError('Camera interpolation branch differs')
            if expected['setter_requested']:
                if self.get(stack+8)!=expected['next_raw']:raise ValueError('Camera interpolation differs from independent finite rule')
                self.put(stack,self.STOP);self.put(stack+4,expected['next_raw']);self.registers(ECX=module,ESP=stack)
                if (self._run('camera_set')!=0x465e6b or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-12
                        or (self.get(stack-12),self.get(stack-8))!=(camera,expected['next_raw'])
                        or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=vtable):raise ValueError('Camera scene-method arguments differ')
            if bytes(self.uc.mem_read(self.FPV,len(before)))!=seeded or bytes(self.uc.mem_read(self.HEAP,65536))!=arena:
                raise ValueError('Camera argument path mutated an input object')
            return {'current_raw':current_raw,'target_raw':target_raw,**expected,
                    'native_interpolation_matches':True,'camera_getter_member':0x120,'scene_setter_vtable_offset':0x74,
                    'scene_camera_method_executed':False,'time_step_source_qualified':False,'rendering_qualified':False}
        finally:self.uc.mem_write(self.FPV,before)


def checked_action(machine,raw,slot):
    if type(slot) is not int or not 0<=slot<500:raise ValueError('Secondary item slot outside bounded domain')
    expected=fields(raw);receipt=machine.inspect_action(raw,slot)
    states=receipt.get('actor_state_requests')
    valid_states=(isinstance(states,list) and len(states)==4 and all(isinstance(case,dict)
        and set(case)=={'synthetic_current_state','requested_state'}
        and type(case['synthetic_current_state']) is int and case['synthetic_current_state']==state
        and type(case['requested_state']) is int and case['requested_state']==route(expected['mode_raw'],state)
        for state,case in enumerate(states)))
    if (any(type(receipt.get(key)) is not type(value) or receipt[key]!=value for key,value in
            {**expected,'slot':slot,'native_secondary_paths_match':True,'descriptor_and_objects_unchanged':True,
             'hud_dispatch':hud_branch(expected['mode_raw']),'fpv_aim_state':11,'fpv_deaim_state':12,'fpv_target_member':0x30,
             'complete_aim_operation_executed':False,'scene_or_animation_calls_executed':False,
             'deaim_scalar_source_qualified':False,
             'camera_rendering_qualified':False,'game_started':False,'game_modified':False}.items())
            or not valid_states):
        raise ValueError('Incomplete or mismatched secondary-action receipt')
    return receipt


def checked_interpolation(machine,current,target,step):
    current_raw=float_word(current,'current scalar');target_raw=float_word(target,'target scalar')
    expected={'current_raw':current_raw,'target_raw':target_raw,**interpolation(current_raw,target_raw,step),
              'native_interpolation_matches':True,'camera_getter_member':0x120,'scene_setter_vtable_offset':0x74,
              'scene_camera_method_executed':False,'time_step_source_qualified':False,'rendering_qualified':False}
    receipt=machine.inspect_interpolation(current,target,step)
    if any(type(receipt.get(key)) is not type(value) or receipt[key]!=value for key,value in expected.items()):
        raise ValueError('Incomplete or mismatched camera-interpolation receipt')
    return receipt
