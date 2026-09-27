"""Native eight-slot time controller with no attached targets or callbacks.

Duration reads use the real pinned getter and an invented 5DS header. This
does not qualify the wall-clock source, pose application or event delivery.
"""
import struct

from ls3d_math_oracle import MathOracle

START=0x10020150
RANGES=((START,0x10020199),(0x100201ad,0x100201e4),(0x10020212,0x10020256),
        (0x10004e80,0x10004e9b))
LIMIT=1<<27


def signed(value):
    if type(value) is not int or not -LIMIT<=value<=LIMIT:raise ValueError('Time outside reviewed signed domain')
    return value


def validate(slots,delta,dirty):
    signed(delta)
    if type(dirty) is not bool:raise ValueError('Expected controller dirty flag')
    if not isinstance(slots,list) or len(slots)!=8:raise ValueError('Expected exactly eight time slots')
    result=[]
    for slot in slots:
        if not isinstance(slot,dict) or set(slot)!={'active','mode','frame_end','time','previous','last_delta'}:
            raise ValueError('Unexpected time slot shape')
        if type(slot['active']) is not bool:raise ValueError('Invalid time slot activity')
        if type(slot['mode']) is not int or not 0<=slot['mode']<=3:raise ValueError('Unreviewed playback mode')
        if type(slot['frame_end']) is not int or not 1<=slot['frame_end']<=65535:raise ValueError('Unreviewed terminal frame')
        for field in ('time','previous','last_delta'):signed(slot[field])
        if slot['active']:signed(slot['time']+delta)
        result.append(dict(slot))
    return result


def reference(slots,delta,dirty=False):
    result=validate(slots,delta,dirty)
    if delta:
        dirty=True
        for slot in result:
            if slot['active']:slot['time']+=delta;slot['last_delta']=delta
    processed=dirty
    if dirty:
        for slot in result:
            if not slot['active']:continue
            slot['previous']=slot['time'];duration=slot['frame_end']*40
            if slot['time']<0 or slot['time']>=duration:
                if slot['mode']==2:slot['time']+=duration if slot['time']<0 else -duration
                else:slot['active']=False
    return {'slots':result,'dirty':False,'controller_processed':processed}


class TimeOracle(MathOracle):
    def on_code(self,uc,address,size,_):
        if self.phase!='time':return super().on_code(uc,address,size,_)
        if not any(a<=address and address+size<=b for a,b in RANGES):
            raise ValueError('Unreviewed time instruction, target pose or callback')
        self.visited.add(address)

    def advance(self,slots,delta,dirty=False):
        expected=reference(slots,delta,dirty);slots=validate(slots,delta,dirty)
        if self.phase is not None:raise ValueError('Nested time phase')
        source=bytearray(4096);target=bytearray(4096);target[4]=int(dirty)
        writes=[(self.OUTPUT+4,self.OUTPUT+5)]
        for index,slot in enumerate(slots):
            clip=0x100+index*0x80;header=clip+0x40;offset=index*0x1c
            struct.pack_into('<I',source,clip,0x1009b400)
            struct.pack_into('<I',source,clip+0x10,self.INPUT+header)
            struct.pack_into('<HH',source,header,1,slot['frame_end'])
            struct.pack_into('<I',target,offset+8,self.INPUT+clip)
            target[offset+0xc]=int(slot['active']);struct.pack_into('<I',target,offset+0x10,slot['mode'])
            struct.pack_into('<iii',target,offset+0x14,slot['time'],slot['previous'],slot['last_delta'])
            writes.extend(((self.OUTPUT+offset+0xc,self.OUTPUT+offset+0xd),
                           (self.OUTPUT+offset+0x14,self.OUTPUT+offset+0x20)))
        # The controller has zero target objects, so no model/pose/event path runs.
        self.uc.mem_write(self.INPUT,bytes(source));self.uc.mem_write(self.OUTPUT,bytes(target))
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<Ii',self.STOP,delta))
        for name in ('EAX','EBX','EDX','ESI','EDI','EBP'):self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),0)
        for name,value in (('ECX',self.OUTPUT),('ESP',stack),('EFLAGS',2),('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase='time';self.writes=tuple(writes);self.visited=set()
        try:
            self.uc.emu_start(START,self.STOP,count=4096,timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP:raise ValueError('Time instruction budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+8:raise ValueError('Time calling convention differs')
        finally:self.phase=None;self.writes=()
        if bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source):raise ValueError('Time controller changed input clips')
        actual=bytes(self.uc.mem_read(self.OUTPUT,4096));actual_slots=[]
        for index,slot in enumerate(slots):
            offset=index*0x1c;time,previous,last_delta=struct.unpack_from('<iii',actual,offset+0x14)
            actual_slots.append({**slot,'time':time,'previous':previous,'last_delta':last_delta,'active':bool(actual[offset+0xc])})
        processed=0x100201ad in self.visited
        if actual_slots!=expected['slots'] or actual[4]!=0 or processed!=expected['controller_processed']:
            raise ValueError('Native time controller differs from reference')
        allowed={i-self.OUTPUT for a,b in writes for i in range(a,b)}
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(target,actual))):raise ValueError('Time controller changed unrelated fields')
        return {**expected,'native_time_controller_match':True,'inputs_preserved':True,
                'duration_integer_units_per_terminal_frame':40,'time_unit_seconds_qualified':False,
                'target_pose_evaluated':False,'callbacks_called':False,'scene_loaded':False,
                'library_loaded':False,'game_started':False}
