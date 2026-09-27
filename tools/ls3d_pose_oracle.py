"""Synthetic eight-slot pose application, no scene/event/skin or matrix fallback.

Only objects already holding quaternion-form rotation (flag 8) are accepted.
The extra pose pointer is always null; at most three keys per channel.
"""
import math
import struct

from ls3d_math_oracle import MathOracle,PHASES,f32,vector,unit,rotation_sample,vector_sample,THRESHOLD

POSE_START=0x1001eed0
POSE_STOP=0x1001fac7
POSE_RANGES=((POSE_START,0x1001f446),(0x1001f9c4,POSE_STOP),
             (0x10030540,0x100305f8),*PHASES['slerp'][1])


def normalize(value):
    value=vector(value,4,1.01);length=math.sqrt(sum(v*v for v in value))
    if not .99<=length<=1.01:raise ValueError('Pose quaternion outside reviewed normalization domain')
    factor=(-1 if value[3]<0 else 1)/length
    return [f32(v*factor) for v in value]


def mix_rotation(left,right,weight):
    # Intermediate Slerp values need not satisfy the serialized-key unit bound.
    left=vector(left,4,1.01);right=vector(right,4,1.01)
    if any(abs(sum(v*v for v in q)-1)>.001 for q in (left,right)):
        raise ValueError('Pose blend quaternion outside reviewed domain')
    cosine=f32(sum(left[i]*right[i] for i in (2,1,0,3)))
    if cosine<0:cosine=-cosine;right=[-v for v in right]
    if 1-cosine>THRESHOLD:
        angle=math.acos(cosine);stored=f32(angle);reciprocal=f32(1/math.sin(angle))
        a=math.sin((1-weight)*stored)*reciprocal;b=math.sin(weight*stored)*reciprocal
    else:a,b=1-weight,weight
    return [f32(a*x+b*y) for x,y in zip(left,right)]


def validate(initial,slots,flags):
    if not isinstance(initial,dict) or set(initial)!={'position','rotation','scale'}:
        raise ValueError('Expected initial pose with all three channels')
    initial={'position':vector(initial['position'],3,10),'rotation':unit(initial['rotation']),
             'scale':vector(initial['scale'],3,10)}
    if type(flags) is not int or flags not in (8,0x88):raise ValueError('Unreviewed target pose flags')
    if not isinstance(slots,list) or not 0<=len(slots)<=8:raise ValueError('Expected zero to eight pose slots')
    clean=[]
    for slot in slots:
        if not isinstance(slot,dict) or set(slot)!={'active','weight','time','channels'}:
            raise ValueError('Unexpected pose slot shape')
        if type(slot['active']) is not bool:raise ValueError('Invalid active flag')
        weight=f32(slot['weight'])
        if not 0<=weight<=2:raise ValueError('Weight outside reviewed domain')
        channels=slot['channels']
        if not isinstance(channels,dict) or set(channels)-set(initial):raise ValueError('Unsupported pose channel')
        if type(slot['time']) is not int or not 0<=slot['time']<=65535*40+39:raise ValueError('Unreviewed pose time')
        validated={}
        for kind,channel in channels.items():
            if not isinstance(channel,dict) or set(channel)!={'frames','values'}:raise ValueError('Invalid pose curve')
            frames,values=channel['frames'],channel['values']
            (rotation_sample if kind=='rotation' else vector_sample)(frames,values,slot['time'])
            if len(frames)>3:raise ValueError('Synthetic pose curve exceeds three keys')
            validated[kind]={'frames':list(frames),'values':[unit(v) if kind=='rotation' else vector(v,3,10) for v in values]}
        clean.append({**slot,'weight':weight,'channels':validated})
    return initial,clean


def reference(initial,slots,flags=8):
    initial,slots=validate(initial,slots,flags)
    output={k:list(v) for k,v in initial.items()};counts=dict.fromkeys(initial,0);out_flags=flags
    for kind in initial:
        accumulated=None;count=0
        for slot in slots:
            if not slot['active'] or slot['weight']<=0 or kind not in slot['channels']:continue
            curve=slot['channels'][kind]
            sampled=(rotation_sample if kind=='rotation' else vector_sample)(curve['frames'],curve['values'],slot['time'])['value']
            if accumulated is None or slot['weight']>=1:
                accumulated=sampled
                count=1 if kind=='rotation' else count+1
            else:
                weight=slot['weight']
                accumulated=mix_rotation(accumulated,sampled,weight) if kind=='rotation' else [f32((1-weight)*a+weight*b) for a,b in zip(accumulated,sampled)]
                count+=1
        counts[kind]=count
        if count:
            if kind=='position':
                if not flags&0x80:output[kind]=accumulated;out_flags=(out_flags&0xfffffedf)|0x40000000
            elif kind=='rotation':
                if count>1:accumulated=normalize(accumulated)
                output[kind]=normalize(accumulated);out_flags=(out_flags&0xfffffecb)|0x40000008
            else:output[kind]=accumulated;out_flags=(out_flags&0xfffffecb)|0x40000008
    return {'pose':output,'flags':out_flags,'accumulation_counts':counts}


class PoseOracle(MathOracle):
    def on_code(self,uc,address,size,_):
        if self.phase!='pose':return super().on_code(uc,address,size,_)
        if not any(a<=address and address+size<=b for a,b in POSE_RANGES):
            raise ValueError('Unreviewed pose instruction, scene, event or matrix fallback')
        self.visited.add(address)
        if address==0x10030540:self.normalizations+=1

    def apply(self,initial,slots,flags=8):
        expected=reference(initial,slots,flags);initial,slots=validate(initial,slots,flags)
        if self.phase is not None:raise ValueError('Nested pose phase')
        source=bytearray(4096);owner=self.INPUT;states=self.INPUT+0x100;cursor=0x300
        struct.pack_into('<II',source,0xec,self.OUTPUT,states)
        for index,slot in enumerate(slots):
            header=index*0x1c;state=0x100+index*0x1c
            source[state+0xc]=int(slot['active']);struct.pack_into('<i',source,state+0x14,slot['time'])
            struct.pack_into('<f',source,state+0x20,slot['weight'])
            mask=0
            for kind,pointer_offset,count_offset,bit,width in (
                    ('position',0xc,0x1c,2,3),('rotation',0x10,0x1e,4,4),('scale',0x14,0x20,8,3)):
                if kind not in slot['channels']:continue
                curve=slot['channels'][kind];frames,values=curve['frames'],curve['values'];mask|=bit
                if kind!='rotation':cursor+=((2-cursor)%4)
                struct.pack_into('<I',source,header+pointer_offset,self.INPUT+cursor)
                struct.pack_into('<H',source,header+count_offset,len(frames))
                struct.pack_into('<'+'H'*len(frames),source,cursor,*frames);cursor+=2*len(frames)
                cursor=(cursor+15)&~15 if kind=='rotation' else cursor+(2 if len(frames)%2==0 else 0)
                for value in values:struct.pack_into('<'+'f'*width,source,cursor,*value);cursor+=width*4
            struct.pack_into('<H',source,header+0x24,mask)
        if cursor>4096:raise ValueError('Pose fixture exceeds input page')
        target=bytearray(b'Z'*4096)
        for kind,offset in (('position',0xb0),('rotation',0xc0),('scale',0xd0)):
            struct.pack_into('<'+'f'*len(initial[kind]),target,offset,*initial[kind])
        struct.pack_into('<I',target,0xe0,flags)
        self.uc.mem_write(self.INPUT,bytes(source));self.uc.mem_write(self.OUTPUT,bytes(target))
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        for name in ('EAX','EBX','EDX','ESI','EDI','EBP'):self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),0)
        for name,value in (('ECX',owner),('ESP',stack),('EFLAGS',2),('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase='pose';self.writes=((self.OUTPUT+0xb0,self.OUTPUT+0xbc),(self.OUTPUT+0xc0,self.OUTPUT+0xe4));self.visited=set();self.normalizations=0
        try:
            self.uc.emu_start(POSE_START,POSE_STOP,count=12000,timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=POSE_STOP:raise ValueError('Pose instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack-0xf0:raise ValueError('Pose stack contract differs')
        finally:self.phase=None;self.writes=()
        if bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source):raise ValueError('Pose changed input')
        actual=bytes(self.uc.mem_read(self.OUTPUT,4096));pose={}
        for kind,offset,width in (('position',0xb0,3),('rotation',0xc0,4),('scale',0xd0,3)):
            pose[kind]=list(struct.unpack_from('<'+'f'*width,actual,offset))
        error=max(abs(a-b) for kind in pose for a,b in zip(pose[kind],expected['pose'][kind]))
        if any(not math.isfinite(v) for values in pose.values() for v in values) or error>2e-6:
            raise ValueError('Native synthetic pose differs from reference')
        actual_flags=struct.unpack_from('<I',actual,0xe0)[0]
        if actual_flags!=expected['flags']:raise ValueError('Native pose flags differ')
        counts={kind:struct.unpack('<I',self.uc.mem_read(stack-0xf0+offset,4))[0]
                for kind,offset in (('position',0x14),('rotation',0xc),('scale',0x10))}
        if counts!=expected['accumulation_counts']:raise ValueError('Native accumulation counts differ')
        if self.normalizations!=int(counts['rotation']>0)+int(counts['rotation']>1):
            raise ValueError('Native pose normalization count differs')
        for kind,offset,size in (('position',0xb0,12),('rotation',0xc0,16),('scale',0xd0,12)):
            if not counts[kind] or (kind=='position' and flags&0x80):
                if actual[offset:offset+size]!=target[offset:offset+size]:raise ValueError('Absent or locked pose channel changed')
        allowed=set(range(0xb0,0xbc))|set(range(0xc0,0xe4))
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(target,actual))):raise ValueError('Pose altered unrelated fields')
        return {**expected,'pose':pose,'max_error':error,'normalization_calls':self.normalizations,'native_synthetic_pose_match':True,
                'inputs_preserved':True,'extra_pose_evaluated':False,'matrix_rotation_fallback_evaluated':False,
                'event_or_scene_called':False,'skin_evaluated':False,'model_loading_qualified':False,
                'game_started':False,'library_loaded':False}
