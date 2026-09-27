"""Native name selection and transform-channel descriptors, no actual loader.

Selection stops before binding/allocation. Descriptor setup writes only a
synthetic owner. The input 5DS remains private, pinned by its caller.
"""
import struct

from five_ds import parse_5ds,HEADER
from ls3d_math_oracle import MathOracle

NAME_START=0x10020320
NAME_STOPS=(0x100203c1,0x1002048c,0x10020490)
DESCRIPTOR_START=0x100203ce
DESCRIPTOR_STOP=0x1002048c


def name_bytes(value):
    if not isinstance(value,str) or not 1<=len(value)<=63:raise ValueError('Unreviewed binding name length')
    try:raw=value.encode('cp1252')
    except UnicodeEncodeError as error:raise ValueError('Unreviewed binding name encoding') from error
    if any(v<32 or v==127 for v in raw):raise ValueError('Control character in binding name')
    return raw+b'\0'


def select_name(names,query):
    name_bytes(query)
    if not isinstance(names,list) or len(names)>128:raise ValueError('Unreviewed target list size')
    for name in names:name_bytes(name)
    return next((i for i,name in enumerate(names) if name==query),None)


class BindingOracle(MathOracle):
    BIND_INPUT=0x3400000

    def __init__(self,raw):
        super().__init__(raw)
        self.uc.mem_map(self.BIND_INPUT,65536,self.uni.UC_PROT_READ)

    def on_code(self,uc,address,size,_):
        if self.phase not in ('name','descriptor'):return super().on_code(uc,address,size,_)
        stops=NAME_STOPS if self.phase=='name' else (DESCRIPTOR_STOP,)
        if address in stops:self.stopped=address;uc.emu_stop();return
        start,end=(NAME_START,NAME_STOPS[0]) if self.phase=='name' else (DESCRIPTOR_START,DESCRIPTOR_STOP)
        if not start<=address or address+size>end:raise ValueError('Unreviewed binding instruction or loader call')
        self.visited.add(address)

    def execute(self,phase,registers,stack_fields,writes):
        if self.phase is not None or phase not in ('name','descriptor'):raise ValueError('Nested or unreviewed binding phase')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        for offset,value in stack_fields.items():self.uc.mem_write(stack+offset,struct.pack('<I',value))
        for name in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP'):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),registers.get(name,0))
        for name,value in (('ESP',stack),('EFLAGS',2),('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase=phase;self.writes=writes;self.visited=set();self.stopped=None
        try:
            self.uc.emu_start(NAME_START if phase=='name' else DESCRIPTOR_START,self.STOP,count=100000,timeout=1_000_000)
            if self.stopped is None:raise ValueError('Binding instruction/time budget exhausted')
        finally:self.phase=None;self.writes=()
        expected_stack=stack-4 if self.stopped==NAME_STOPS[0] else stack
        if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=expected_stack:raise ValueError('Binding stack differs')

    def select(self,names,query,model_kind=9):
        expected=select_name(names,query)
        if type(model_kind) is not int or model_kind not in (9,0):raise ValueError('Unreviewed target container kind')
        source=bytearray(65536);base=self.BIND_INPUT
        owner=base+0x100;array=base+0x400
        struct.pack_into('<I',source,0,owner);struct.pack_into('<H',source,0x100+0xf8,model_kind)
        offset,count_offset=(0x120,0x128) if model_kind==9 else (0x234,0x23c)
        struct.pack_into('<I',source,0x100+offset,array);struct.pack_into('<I',source,0x100+count_offset,len(names))
        for i,name in enumerate(names):
            node=0x800+i*0x100;string=0x9000+i*64;raw=name_bytes(name)
            struct.pack_into('<I',source,0x400+i*4,base+node)
            struct.pack_into('<I',source,node+0xe8,base+string)
            source[string:string+len(raw)]=raw
        raw=name_bytes(query);source[0xc000:0xc000+len(raw)]=raw
        struct.pack_into('<I',source,0xc100,base+0xc000)
        self.uc.mem_write(base,bytes(source))
        self.execute('name',{'EBX':base},{0x1c:base+0xc100,0x10:base},())
        found=self.stopped==NAME_STOPS[0]
        if found!=(expected is not None):raise ValueError('Native exact-name result differs')
        if found:
            pointer=base+0x800+expected*0x100
            stack=self.STACK+0xeffc
            if (self.uc.reg_read(self.reg.UC_X86_REG_EDX)!=pointer
                    or struct.unpack('<I',self.uc.mem_read(stack,4))[0]!=pointer
                    or self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=base):raise ValueError('Native selected target differs')
        if bytes(self.uc.mem_read(base,65536))!=bytes(source):raise ValueError('Name selection changed input')
        return {'native_name_selection_match':True,'selected_index':expected,'exact_case_sensitive':True,
                'model_kind':model_kind,'inputs_preserved':True,'allocation_or_binding_called':False,
                'scene_loaded':False,'game_started':False,'library_loaded':False}

    def describe(self,data,track_index,slot=0):
        clip=parse_5ds(data)
        if type(track_index) is not int or not 0<=track_index<len(clip['tracks']):raise ValueError('Invalid track index')
        if type(slot) is not int or not 0<=slot<8:raise ValueError('Invalid descriptor slot')
        if len(data)-HEADER>0xf000:raise ValueError('5DS exceeds reviewed descriptor input page')
        track=clip['tracks'][track_index];source=bytearray(65536);base=self.BIND_INPUT
        source[0x1000:0x1000+len(data)-HEADER]=data[HEADER:]
        struct.pack_into('<I',source,4,base+0x1000+track['offset']-HEADER)
        self.uc.mem_write(base,bytes(source));self.uc.mem_write(self.OUTPUT,b'Z'*4096)
        target=self.OUTPUT+slot*0x1c
        self.execute('descriptor',{'EAX':self.OUTPUT,'EDI':slot*0x1c},{0x1c:base},((target+0xc,target+0x26),))
        if bytes(self.uc.mem_read(base,65536))!=bytes(source):raise ValueError('Descriptor setup changed source')
        cursor=track['offset']+4;channels={}
        for kind,pointer_offset,count_offset,width in (('rotation',0x10,0x1e,4),('position',0xc,0x1c,3),('scale',0x14,0x20,3)):
            count=struct.unpack('<H',self.uc.mem_read(target+count_offset,2))[0]
            channel=track['channels'].get(kind)
            if channel is None:
                if count:raise ValueError('Absent channel not cleared')
                continue
            if count!=len(channel['frames']):raise ValueError('Native descriptor count differs')
            cursor+=2;pointer=base+0x1000+cursor-HEADER
            if struct.unpack('<I',self.uc.mem_read(target+pointer_offset,4))[0]!=pointer:raise ValueError('Native channel pointer differs')
            cursor+=count*2
            cursor+=(-(cursor-HEADER))%16 if kind=='rotation' else 2 if count%2==0 else 0
            cursor+=count*width*4;channels[kind]=count
        if cursor!=track['end']:raise ValueError('Native descriptor end differs')
        if struct.unpack('<H',self.uc.mem_read(target+0x24,2))[0]!=track['flags']:
            raise ValueError('Native channel flags differ')
        if struct.unpack('<H',self.uc.mem_read(target+0x22,2))[0]!=0:raise ValueError('Unexpected event channel')
        return {'native_transform_descriptor_match':True,'channels':channels,'slot':slot,'inputs_preserved':True,
                'event_channels_evaluated':False,'allocation_or_binding_called':False,
                'scene_loaded':False,'game_started':False,'library_loaded':False}
