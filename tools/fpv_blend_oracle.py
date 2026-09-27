"""Pinned client crossfade controller with the real LS3DF weight setter.

The weight setter changes only a synthetic controller. Detach and refresh
remain argument-recording doubles. No loader, allocator, OS API or game runs.
"""
import math
import struct

from item_native_contract import Oracle
from ls3d_math_oracle import f32,verify_library,BASE

START=0x491440
END=0x491631
FACTOR=struct.unpack('<f',bytes.fromhex('6f12833a'))[0]
GATES=('global_enabled','instance_active','has_animation','has_model')


def validate(current,previous,delta,gates):
    if type(delta) is not int or not 0<=delta<=1_000_000:raise ValueError('Unreviewed blend time step')
    if not isinstance(gates,dict) or set(gates)!=set(GATES) or any(type(v) is not bool for v in gates.values()):
        raise ValueError('Invalid blend gates')
    if not isinstance(previous,list) or len(previous)>3:raise ValueError('Unreviewed prior blend count')
    clean=[]
    for row in [current,*previous]:
        if not isinstance(row,dict) or set(row)!={'slot','weight','rate'}:raise ValueError('Unexpected blend record')
        if type(row['slot']) is not int or not 0<=row['slot']<8:raise ValueError('Invalid blend slot')
        weight,rate=f32(row['weight']),f32(row['rate'])
        if not 0<=weight<=1 or not 0<=rate<=10:raise ValueError('Unreviewed blend weight or rate')
        clean.append({'slot':row['slot'],'weight':weight,'rate':rate})
    if len({r['slot'] for r in clean})!=len(clean):raise ValueError('Duplicate active blend slots')
    return clean[0],clean[1:]


def detach(slot):return {'operation':'detach','slot':slot,'weight':1.0,'mode':0,'animation_present':False}


def reference(current,previous,delta,gates):
    current,previous=validate(current,previous,delta,gates);calls=[]
    if not all(gates.values()):return {'current':current,'previous':previous,'model_call_arguments':calls}
    if current['weight']==1:
        calls=[detach(row['slot']) for row in reversed(previous)]
        return {'current':current,'previous':[],'model_call_arguments':calls}
    current['weight']=min(1.0,f32(delta*current['rate']*FACTOR+current['weight']))
    calls.append({'operation':'weight','slot':current['slot'],'weight':current['weight']})
    remaining=[]
    for row in previous:
        weight=row['weight']-f32(delta)*row['rate']*FACTOR
        if weight<=0:calls.append(detach(row['slot']))
        else:
            row={**row,'weight':f32(weight)};remaining.append(row)
            calls.append({'operation':'weight','slot':row['slot'],'weight':row['weight']})
    calls.append({'operation':'refresh'})
    return {'current':current,'previous':remaining,'model_call_arguments':calls}


class FpvBlendOracle(Oracle):
    DETACH=Oracle.STOP+0x100
    WEIGHT=0x10034460
    REFRESH=Oracle.STOP+0x120

    def __init__(self,image,library):
        verify_library(library)
        super().__init__(image)
        import pefile
        pe=pefile.PE(data=library);mapped=pe.get_memory_mapped_image()
        if pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=BASE:raise ValueError('Unexpected weight-setter library')
        self.uc.mem_map(BASE,(len(mapped)+4095)&~4095,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC)
        self.uc.mem_write(BASE,mapped)
        if struct.unpack('<f',self.uc.mem_read(0x80f514,4))[0]!=FACTOR:raise ValueError('Changed client blend factor')
        self.active=False;self.writes=();self.recorded=[]
        self.uc.hook_add(self.uni.UC_HOOK_MEM_WRITE,self.on_write)

    def on_write(self,uc,access,address,size,value,_):
        if not self.active or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),*self.writes)):
            raise ValueError('Blend write outside reviewed state/list/stack')

    def on_code(self,uc,address,size,_):
        if not self.active:raise ValueError('Blend execution outside active phase')
        if address in (self.DETACH,self.WEIGHT,self.REFRESH):
            stack=uc.reg_read(self.reg.UC_X86_REG_ESP);ret=self.get(stack)
            count={self.DETACH:5,self.WEIGHT:3,self.REFRESH:1}[address]
            args=[self.get(stack+4+i*4) for i in range(count)]
            if args[0]!=self.INPUT+0x100:raise ValueError('Unreviewed model-call receiver')
            if address==self.DETACH:
                if ret not in (0x4914c5,0x4915a8) or args[1]!=0 or args[3:]!=[0x3f800000,0]:
                    raise ValueError('Unexpected detach arguments')
                self.recorded.append(detach(args[2]))
            elif address==self.WEIGHT:
                if ret not in (0x49153b,0x491615):raise ValueError('Unexpected weight caller')
                self.recorded.append({'operation':'weight','slot':args[1],
                    'weight':struct.unpack('<f',struct.pack('<I',args[2]))[0]})
                return # Execute the actual pinned setter, including its ret 0xc.
            else:
                if ret!=0x491627:raise ValueError('Unexpected refresh caller')
                self.recorded.append({'operation':'refresh'})
            uc.reg_write(self.reg.UC_X86_REG_EAX,0)
            uc.reg_write(self.reg.UC_X86_REG_ESP,stack+4*(count+1))
            uc.reg_write(self.reg.UC_X86_REG_EIP,ret)
            return
        if not any(a<=address and address+size<=b for a,b in ((START,END),(self.WEIGHT,0x100344dd))):
            raise ValueError('Unreviewed blend instruction or call')

    def advance(self,current,previous,delta,**gates):
        if self.active:raise ValueError('Nested blend phase')
        if not gates:gates=dict.fromkeys(GATES,True)
        current,previous=validate(current,previous,delta,gates);expected=reference(current,previous,delta,gates)
        source=bytearray(4096);model=self.INPUT+0x100;vtable=self.INPUT+0x200
        struct.pack_into('<I',source,0x100,vtable)
        controller=self.HEAP+0x1000
        struct.pack_into('<I',source,0x230,controller) # Synthetic model +0x130.
        for offset,target in ((0x84,self.DETACH),(0x94,self.WEIGHT),(0x24,self.REFRESH)):
            struct.pack_into('<I',source,0x200+offset,target)
        self.uc.mem_write(self.INPUT,bytes(source))
        target=bytearray(0x4d000);target[0x3c]=int(gates['instance_active'])
        struct.pack_into('<I',target,0x40,model if gates['has_model'] else 0)
        struct.pack_into('<IIff',target,0x70,1 if gates['has_animation'] else 0,
                         current['slot'],current['rate'],current['weight'])
        prior=self.HEAP+0x100;heap=bytearray(65536)
        weights=[.25]*8
        for row in [current,*previous]:weights[row['slot']]=row['weight']
        for i,weight in enumerate(weights):struct.pack_into('<f',heap,0x1020+i*0x1c,weight)
        struct.pack_into('<III',target,0x84,prior,prior+16*len(previous),prior+48)
        for i,row in enumerate(previous):struct.pack_into('<IIff',heap,0x100+16*i,i+2,row['slot'],row['rate'],row['weight'])
        self.uc.mem_write(self.FPV,bytes(target));self.uc.mem_write(self.HEAP,bytes(heap))
        old_gate=bytes(self.uc.mem_read(0x982100,1))
        self.uc.mem_write(0x982100,bytes([2 if gates['global_enabled'] else 0]))
        stack=self.STACK+0x8000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<II',self.STOP,delta))
        for name in ('EAX','EBX','EDX','ESI','EDI','EBP'):self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),0)
        for name,value in (('ECX',self.FPV),('ESP',stack),('EFLAGS',2),('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.active=True;self.recorded=[]
        weight_writes=[(controller+4,controller+5),*((controller+0x20+i*0x1c,controller+0x24+i*0x1c) for i in range(8))]
        self.writes=((self.FPV+0x7c,self.FPV+0x80),(self.FPV+0x88,self.FPV+0x8c),
                     (prior,prior+16*len(previous)),*weight_writes)
        try:
            self.uc.emu_start(START,self.STOP,count=12000,timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP:raise ValueError('Blend instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+8:raise ValueError('Blend calling convention differs')
        finally:
            self.active=False;self.writes=();self.uc.mem_write(0x982100,old_gate)
        end=self.get(self.FPV+0x88)
        if not prior<=end<=prior+16*len(previous) or (end-prior)%16:raise ValueError('Invalid native prior-list boundary')
        result=[]
        for i in range((end-prior)//16):
            clip,slot,rate,weight=struct.unpack('<IIff',self.uc.mem_read(prior+i*16,16))
            expected_clips={row['slot']:j+2 for j,row in enumerate(previous)}
            if clip!=expected_clips.get(slot):raise ValueError('Prior animation token changed during list compaction')
            result.append({'slot':slot,'rate':rate,'weight':weight})
        actual_current={**current,'weight':struct.unpack('<f',self.uc.mem_read(self.FPV+0x7c,4))[0]}
        if actual_current!=expected['current'] or result!=expected['previous'] or self.recorded!=expected['model_call_arguments']:
            raise ValueError('Native FPV blend differs from independent reference')
        actual=bytes(self.uc.mem_read(self.FPV,len(target)));actual_heap=bytes(self.uc.mem_read(self.HEAP,len(heap)))
        weight_calls=[call for call in self.recorded if call['operation']=='weight']
        for call in weight_calls:weights[call['slot']]=max(0.0,min(1.0,call['weight']))
        actual_weights=[struct.unpack_from('<f',actual_heap,0x1020+i*0x1c)[0] for i in range(8)]
        if actual_weights!=weights or actual_heap[0x1004]!=int(bool(weight_calls)):
            raise ValueError('Native model weight setter differs from expected fields')
        heap_mutable=set(range(0x100,0x100+16*len(previous)))
        for a,b in weight_writes:heap_mutable.update(range(a-self.HEAP,b-self.HEAP))
        mutable=set(range(0x7c,0x80))|set(range(0x88,0x8c))
        if (bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source)
                or any(a!=b and i not in mutable for i,(a,b) in enumerate(zip(target,actual)))
                or any(a!=b and i not in heap_mutable for i,(a,b) in enumerate(zip(heap,actual_heap)))):
            raise ValueError('Blend changed unrelated data')
        return {**expected,'native_blend_state_and_arguments_match':True,'inputs_preserved':True,
            'native_weight_setter_calls':len(weight_calls),'native_model_weight_writes_checked':True,
            'detach_and_refresh_recorded_not_executed':True,'model_effects_qualified':False,'time_unit_seconds_qualified':False,
            'allocation_called':False,'library_loaded':False,'game_started':False}
