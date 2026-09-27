"""Pinned LS3DF math in bounded x86 emulation, never a loaded Windows DLL.

Only reviewed rotation, vector and single-channel sampling blocks are allowed.
No entry point, TLS, imports, scene/animation loader or driver is executed.
The synthetic x87 control word is 0x27f, not a claim about every game thread.
"""
from __future__ import annotations
import hashlib
import math
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
DLL_SIZE=864256
DLL_SHA='12c61eed2aec0c45700ad0a5ddfd7cbb3cbf0ea15ec67de155790bb24e7756ee'
BASE=0x10000000
PHASES={
    'rotation':(0x1002d260,((0x1002d260,0x1002d28f),(0x1002d450,0x1002d57d))),
    'point':(0x1002ea40,((0x1002ea40,0x1002eaa3),)),
    'slerp':(0x100302e0,((0x100302e0,0x10030433),(0x1008d4e0,0x1008d4f4),
        (0x1008d4fd,0x1008d545),(0x100904d8,0x100904e9),
        (0x100904fb,0x10090505),(0x10090523,0x10090525))),
}
EXPORTS={b'?SetRot@S_matrix@@QAGXABUS_quat@@@Z':0x2d260,
         b'??XS_vector@@QAGAAU0@ABUS_matrix@@@Z':0x2ea40,
         b'?Slerp@S_quat@@QBG?AU1@ABU1@M_N@Z':0x302e0}
THRESHOLD=.0001
NEAR_UNIT_SQUARED_TOLERANCE=2e-5 # Pinned Benelli keys reach 1.005e-5; never normalize them.
PHASES['rotation_track']=(0x1001f0fa,((0x1001f0fa,0x1001f1cf),*PHASES['slerp'][1]))
TRACK_STOP=0x1001f1cf
VECTOR_TRACKS={'position':(0x1001ef37,0x1001f015,0x10,'EDX'),
               'scale':(0x1001f2c7,0x1001f3a5,0xc,'ECX')}
for _kind,(_start,_stop,_,_) in VECTOR_TRACKS.items():
    PHASES[_kind+'_track']=(_start,((_start,_stop),))
TIME_FACTOR=struct.unpack('<f',bytes.fromhex('cdcccc3c'))[0]


def f32(value):
    if type(value) not in (int,float):raise ValueError('Expected finite scalar')
    try:
        if not math.isfinite(value):raise ValueError('Expected finite scalar')
        value=struct.unpack('<f',struct.pack('<f',value))[0]
    except (OverflowError,struct.error) as error:raise ValueError('Scalar outside float32') from error
    if not math.isfinite(value):raise ValueError('Scalar outside float32')
    return value


def vector(value,count,limit):
    if not isinstance(value,(list,tuple)) or len(value)!=count:raise ValueError('Unexpected vector shape')
    result=[f32(v) for v in value]
    if any(abs(v)>limit for v in result):raise ValueError('Vector outside reviewed math domain')
    return result


def unit(value):
    result=vector(value,4,1.00002)
    if abs(sum(v*v for v in result)-1)>NEAR_UNIT_SQUARED_TOLERANCE:
        raise ValueError('Expected nearly unit native quaternion')
    return result # No implicit normalization: preserves serialized float32.


def basis(value):
    """Independent reference for the native row-vector matrix in active form."""
    x,y,z,w=unit(value)
    if abs(w)>=1:return [[1,0,0],[0,1,0],[0,0,1]]
    return [[1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w)],
            [2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w)],
            [2*(x*z+y*w),2*(y*z-x*w),1-2*(x*x+y*y)]]


def interpolation(left,right,amount):
    """Bounded numerical reference, not bit-exact x87 or whole-track playback."""
    left,right=unit(left),unit(right);amount=f32(amount)
    if not 0<=amount<=1:raise ValueError('Interpolation fraction outside reviewed domain')
    # The reviewed x87 path accumulates z, y, x, w before a float32 store.
    cosine=f32(sum(left[i]*right[i] for i in (2,1,0,3)))
    antipode=cosine<0
    if antipode:cosine=-cosine;right=[-v for v in right]
    spherical=1-cosine>THRESHOLD
    if spherical:
        theta=math.acos(cosine);stored_theta=f32(theta)
        reciprocal=f32(1/math.sin(theta))
        a=math.sin((1-amount)*stored_theta)*reciprocal
        b=math.sin(amount*stored_theta)*reciprocal
    else:a,b=1-amount,amount
    result=[f32(a*x+b*y) for x,y in zip(left,right)]
    return {'value':result,'branch':'spherical' if spherical else 'linear',
            'right_antipode_selected':antipode,'result_normalized':False}


def verify_library(raw):
    if not isinstance(raw,bytes) or len(raw)!=DLL_SIZE or hashlib.sha256(raw).hexdigest()!=DLL_SHA:
        raise ValueError('Unreviewed LS3DF library; no routine executed')


def validate_channel(frames,values,time):
    if (not isinstance(frames,(list,tuple)) or not isinstance(values,(list,tuple))
            or not 1<=len(frames)<=180 or len(frames)!=len(values)
            or any(type(f) is not int or not 0<=f<=65535 for f in frames)
            or any(a>=b for a,b in zip(frames,frames[1:]))):
        raise ValueError('Keys outside reviewed channel domain')
    if type(time) is not int or not 0<=time<=65535*40+39:
        raise ValueError('Channel time outside reviewed integer domain')


def rotation_sample(frames,values,time):
    """Reference for one rotation channel, not blending or a whole model."""
    validate_channel(frames,values,time)
    values=[unit(value) for value in values]
    index=time//40
    if index<frames[0]:return {'value':values[0],'key_indices':[0],'frame_index':index,'fraction':None,'branch':'held_first'}
    if index>=frames[-1]:
        return {'value':values[-1],'key_indices':[len(frames)-1],'frame_index':index,'fraction':None,'branch':'held_last'}
    after=next(i for i,frame in enumerate(frames) if frame>index);before=after-1
    amount=f32((time*TIME_FACTOR-frames[before])/(frames[after]-frames[before]))
    return {**interpolation(values[before],values[after],amount),'key_indices':[before,after],
            'frame_index':index,'fraction':amount}


def vector_sample(frames,values,time):
    """Position/scale reference; unlike Slerp, fraction has no float32 store."""
    validate_channel(frames,values,time)
    values=[vector(value,3,10) for value in values];index=time//40
    if index<frames[0]:return {'value':values[0],'key_indices':[0],'frame_index':index,'fraction':None,'branch':'held_first'}
    if index>=frames[-1]:
        return {'value':values[-1],'key_indices':[len(frames)-1],'frame_index':index,'fraction':None,'branch':'held_last'}
    after=next(i for i,frame in enumerate(frames) if frame>index);before=after-1
    amount=(time*TIME_FACTOR-frames[before])/(frames[after]-frames[before])
    return {'value':[f32((b-a)*amount+a) for a,b in zip(values[before],values[after])],
            'key_indices':[before,after],'frame_index':index,'fraction':amount,'branch':'linear'}


class MathOracle:
    STOP=0x3000000;STACK=0x3100000;INPUT=0x3200000;OUTPUT=0x3300000

    def __init__(self,raw):
        verify_library(raw)
        sys.path.insert(0,str(ROOT/'.research/binary-patch-deps'))
        import pefile
        import unicorn as uni
        from unicorn import x86_const as reg
        pe=pefile.PE(data=raw)
        if pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=BASE:
            raise ValueError('Unexpected math library architecture or base')
        exports={entry.name:entry.address for entry in pe.DIRECTORY_ENTRY_EXPORT.symbols}
        if any(exports.get(name)!=rva for name,rva in EXPORTS.items()):raise ValueError('Changed math exports')
        image=pe.get_memory_mapped_image()
        if struct.unpack_from('<d',image,0x9cda0)[0]!=THRESHOLD:raise ValueError('Changed interpolation threshold')
        if struct.unpack_from('<f',image,0x9cacc)[0]!=TIME_FACTOR:raise ValueError('Changed animation time factor')
        self.uni,self.reg=uni,reg;self.uc=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32)
        self.uc.mem_map(BASE,(len(image)+4095)&~4095,uni.UC_PROT_READ|uni.UC_PROT_EXEC)
        self.uc.mem_write(BASE,image)
        self.uc.mem_map(self.STOP,4096,uni.UC_PROT_READ|uni.UC_PROT_EXEC)
        self.uc.mem_map(self.STACK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE)
        self.uc.mem_map(self.INPUT,4096,uni.UC_PROT_READ)
        self.uc.mem_map(self.OUTPUT,4096,uni.UC_PROT_READ|uni.UC_PROT_WRITE)
        self.phase=None;self.writes=();self.visited=set()
        self.uc.hook_add(uni.UC_HOOK_CODE,self.on_code)
        self.uc.hook_add(uni.UC_HOOK_MEM_WRITE,self.on_write)

    def on_code(self,uc,address,size,_):
        if self.phase is None or not any(a<=address and address+size<=b for a,b in PHASES[self.phase][1]):
            raise ValueError('Unreviewed math instruction or external call')
        self.visited.add(address)

    def on_write(self,uc,access,address,size,value,_):
        if self.phase is None or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),*self.writes)):
            raise ValueError('Math write outside its bounded output or stack')

    def run(self,phase,arguments,writes):
        if self.phase is not None or phase not in PHASES:raise ValueError('Invalid or nested math phase')
        stack=self.STACK+0xf000
        self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(arguments)),self.STOP,*arguments))
        for name in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP'):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),0)
        for name,value in (('ESP',stack),('EFLAGS',2),('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        stop=self.STOP;expected_stack=stack+4*(1+len(arguments))
        if phase=='rotation_track':
            if len(arguments)!=2:raise ValueError('Invalid rotation channel fixture')
            self.uc.mem_write(stack+0x18,struct.pack('<I',arguments[0]))
            self.uc.reg_write(self.reg.UC_X86_REG_EBX,arguments[1])
            stop=TRACK_STOP;expected_stack=stack
        elif phase in ('position_track','scale_track'):
            if len(arguments)!=2:raise ValueError('Invalid vector channel fixture')
            _,stop,_,state_register=VECTOR_TRACKS[phase.removesuffix('_track')]
            self.uc.reg_write(self.reg.UC_X86_REG_EBX,arguments[0])
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+state_register),arguments[1])
            expected_stack=stack
        self.phase=phase;self.writes=writes;self.visited=set()
        try:
            self.uc.emu_start(PHASES[phase][0],stop,count=2048,timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=stop:raise ValueError('Math instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=expected_stack:
                raise ValueError('Math calling convention mismatch')
        finally:self.phase=None;self.writes=()

    def transform(self,quaternion,points):
        q=unit(quaternion)
        if not isinstance(points,(list,tuple)) or not 1<=len(points)<=32:raise ValueError('Invalid point count')
        points=[vector(p,3,10) for p in points]
        source=struct.pack('<4f',*q);self.uc.mem_write(self.INPUT,source)
        self.uc.mem_write(self.OUTPUT,b'Z'*4096)
        self.run('rotation',[self.OUTPUT,self.INPUT],((self.OUTPUT,self.OUTPUT+64),))
        matrix_raw=bytes(self.uc.mem_read(self.OUTPUT,64));matrix=struct.unpack('<16f',matrix_raw)
        expected=basis(q)
        error=max(abs(matrix[i+j*4]-expected[i][j]) for i in range(3) for j in range(3))
        if not all(math.isfinite(v) for v in matrix) or error>2e-6:raise ValueError('Native rotation disagrees with independent reference')
        if any(matrix[i]!=v for i,v in ((3,0),(7,0),(11,0),(12,0),(13,0),(14,0),(15,1))):
            raise ValueError('Unexpected homogeneous rotation members')
        errors=[]
        for value in points:
            self.uc.mem_write(self.OUTPUT+0x100,struct.pack('<3f',*value))
            self.run('point',[self.OUTPUT+0x100,self.OUTPUT],((self.OUTPUT+0x100,self.OUTPUT+0x10c),))
            actual=struct.unpack('<3f',self.uc.mem_read(self.OUTPUT+0x100,12))
            expected_point=[sum(matrix[i+j*4]*value[j] for j in range(3)) for i in range(3)]
            residual=max(abs(a-b) for a,b in zip(actual,expected_point))
            if not all(math.isfinite(v) for v in actual) or residual>5e-6:raise ValueError('Native point transform disagrees')
            errors.append(residual)
        if bytes(self.uc.mem_read(self.INPUT,16))!=source or bytes(self.uc.mem_read(self.OUTPUT,64))!=matrix_raw:
            raise ValueError('Native math changed protected input or matrix')
        return {'native_rotation_and_point_match':True,'matrix_max_error':error,'point_max_error':max(errors),
                'point_count':len(points),'identity_shortcut':abs(q[3])>=1,
                'inputs_preserved':True,'library_loaded':False,'game_started':False,'scene_evaluated':False}

    def slerp(self,left,right,amount,flag=False):
        if type(flag) is not bool:raise ValueError('Expected boolean legacy flag')
        left,right=unit(left),unit(right);amount=f32(amount)
        expected=interpolation(left,right,amount)
        source=struct.pack('<8f',*left,*right);self.uc.mem_write(self.INPUT,source)
        self.uc.mem_write(self.OUTPUT,b'Z'*4096)
        self.run('slerp',[self.INPUT,self.OUTPUT,self.INPUT+16,
                 struct.unpack('<I',struct.pack('<f',amount))[0],int(flag)],((self.OUTPUT,self.OUTPUT+16),))
        value=list(struct.unpack('<4f',self.uc.mem_read(self.OUTPUT,16)))
        error=max(abs(a-b) for a,b in zip(value,expected['value']))
        if not all(math.isfinite(v) for v in value) or error>2e-6:raise ValueError('Native interpolation disagrees with reference')
        branch='spherical' if 0x1003037e in self.visited else 'linear' if 0x100303bd in self.visited else None
        antipode=0x1003031d in self.visited
        if branch!=expected['branch'] or antipode!=expected['right_antipode_selected']:
            raise ValueError('Native interpolation branch disagrees')
        if bytes(self.uc.mem_read(self.INPUT,32))!=source:raise ValueError('Interpolation changed input')
        return {**expected,'value':value,'max_error':error,'native_interpolation_match':True,
                'squared_norm_error':abs(sum(v*v for v in value)-1),'legacy_flag':flag,
                'inputs_preserved':True,'x87_control_word':0x27f,'whole_track_evaluated':False,
                'library_loaded':False,'game_started':False,'scene_evaluated':False}

    def sample_rotation(self,frames,values,time):
        expected=rotation_sample(frames,values,time);values=[unit(value) for value in values]
        # Entire synthetic curve, descriptor and time state fit in the RO page.
        source=bytearray(4096);keys=self.INPUT+256;value_start=(256+2*len(frames)+15)&~15
        struct.pack_into('<I',source,32,keys);struct.pack_into('<H',source,32+0xe,len(frames))
        struct.pack_into('<i',source,64+0x14,time)
        struct.pack_into('<'+'H'*len(frames),source,256,*frames)
        for i,value in enumerate(values):struct.pack_into('<4f',source,value_start+i*16,*value)
        self.uc.mem_write(self.INPUT,bytes(source))
        self.run('rotation_track',[self.INPUT+32,self.INPUT+64],())
        pointer=self.uc.reg_read(self.reg.UC_X86_REG_ECX)
        indices=expected['key_indices']
        target=self.INPUT+value_start+16*indices[0] if len(indices)==1 else self.STACK+0xf040
        if pointer!=target:raise ValueError('Native channel selected an unexpected value address')
        value=list(struct.unpack('<4f',self.uc.mem_read(pointer,16)))
        error=max(abs(a-b) for a,b in zip(value,expected['value']))
        if not all(math.isfinite(v) for v in value) or error>2e-6:raise ValueError('Native channel differs from reference')
        if bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source):raise ValueError('Native channel changed its input')
        called=0x100302e0 in self.visited
        if called!=(len(indices)==2):raise ValueError('Native channel interpolation call differs')
        if called:
            branch='spherical' if 0x1003037e in self.visited else 'linear' if 0x100303bd in self.visited else None
            if branch!=expected['branch']:raise ValueError('Native channel interpolation branch differs')
        return {**expected,'value':value,'max_error':error,'native_channel_sample_match':True,
                'time_integer_units_per_frame':40,'time_factor_float32':TIME_FACTOR,
                'time_unit_seconds_qualified':False,'blending_executed':False,'whole_track_evaluated':False,
                'inputs_preserved':True,'library_loaded':False,'game_started':False,'scene_evaluated':False}

    def sample_vector(self,kind,frames,values,time):
        if kind not in VECTOR_TRACKS:raise ValueError('Unreviewed vector channel kind')
        expected=vector_sample(frames,values,time);values=[vector(value,3,10) for value in values]
        source=bytearray(4096);keys=self.INPUT+258
        # Relative padding is native: two bytes after an even key count.
        value_start=258+2*len(frames)+(2 if len(frames)%2==0 else 0)
        struct.pack_into('<I',source,32,keys)
        struct.pack_into('<H',source,32+VECTOR_TRACKS[kind][2],len(frames))
        struct.pack_into('<i',source,64+0x14,time)
        struct.pack_into('<'+'H'*len(frames),source,258,*frames)
        for i,value in enumerate(values):struct.pack_into('<3f',source,value_start+i*12,*value)
        self.uc.mem_write(self.INPUT,bytes(source))
        self.run(kind+'_track',[self.INPUT+32,self.INPUT+64],())
        pointer=self.uc.reg_read(self.reg.UC_X86_REG_ESI);indices=expected['key_indices']
        target=self.INPUT+value_start+12*indices[0] if len(indices)==1 else self.STACK+0xf080
        if pointer!=target:raise ValueError('Native vector selected unexpected value address')
        value=list(struct.unpack('<3f',self.uc.mem_read(pointer,12)))
        error=max(abs(a-b) for a,b in zip(value,expected['value']))
        if not all(math.isfinite(v) for v in value) or error>2e-6:raise ValueError('Native vector differs from reference')
        if bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source):raise ValueError('Native vector changed input')
        return {**expected,'value':value,'max_error':error,'native_channel_sample_match':True,'channel_kind':kind,
                'time_integer_units_per_frame':40,'time_factor_float32':TIME_FACTOR,
                'time_unit_seconds_qualified':False,'blending_executed':False,'whole_track_evaluated':False,
                'inputs_preserved':True,'library_loaded':False,'game_started':False,'scene_evaluated':False}
