"""Pinned animation Open, path rewrite, header reads and pointer relocation.

File open/read/close, allocation and one driver polling callback are bounded
Python doubles. No host file API, loaded DLL, scene, renderer or game executes.
Only prevalidated transform-only v122 clips and a fresh object are supported.
"""
import re
import struct

from five_ds import parse_5ds,HEADER
from ls3d_math_oracle import MathOracle,DLL_SHA
from build_modern_equipment_hose import digest

START=0x10004ce0
RANGES=((START,0x10004e57),(0x1005d5b0,0x1005d5e2),(0x1005d60f,0x1005d654),
        (0x1005d665,0x1005d6c9),(0x1005d700,0x1005d715),(0x1005e580,0x1005e634),
        (0x1005e657,0x1005e681),(0x1005e6a5,0x1005e6c7))
OPEN=0x10098f22;READ=0x10098f10;CLOSE=0x10098f1c
ALIGNED_ALLOC=0x1008d42a;ALIGNED_FREE=0x1008d472;ALLOC=0x1008d41c


def resource_paths(name):
    if (not isinstance(name,str) or not re.fullmatch(
            r'(?:[Mm]odels\\)?PROTOTYPE_[A-Za-z0-9_]{1,32}\.(?:I3D|i3d|4ds|5ds)',name)):
        raise ValueError('Only bounded modern resource names are reviewed')
    stem=name.rsplit('.',1)[0]
    return stem+'.5ds',stem.rsplit('\\',1)[-1]


def validate(raw,name):
    requested,cached=resource_paths(name)
    if not isinstance(raw,bytes) or len(raw)-HEADER>0xf000:
        raise ValueError('Unreviewed native animation buffer size')
    parsed=parse_5ds(raw)
    if parsed['track_count']>128 or any(len(c['frames'])>180 for t in parsed['tracks'] for c in t['channels'].values()):
        raise ValueError('Unreviewed animation track or key count')
    return parsed,requested,cached


class AnimationLoadOracle(MathOracle):
    SOURCE=0x3b00000;STATE=0x3c00000;SIZE=0x20000;HANDLE=0x5678

    def __init__(self,library):
        super().__init__(library)
        self.uc.mem_map(self.SOURCE,4096,self.uni.UC_PROT_READ)
        self.uc.mem_map(self.STATE,self.SIZE,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        for page in (0x100c0000,0x100d0000,0x100d1000):
            self.uc.mem_protect(page,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        if bytes(self.uc.mem_read(0x100a70ec,5))!=b'.5ds\0':raise ValueError('Native animation suffix changed')
        if bytes(self.uc.mem_read(0x100a7254,4))!=b'5DS\0':raise ValueError('Native animation signature changed')

    def return_double(self,stack,ret,count,value=0,cdecl=False):
        self.uc.reg_write(self.reg.UC_X86_REG_EAX,value)
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,stack+4+(0 if cdecl else 4*count))
        self.uc.reg_write(self.reg.UC_X86_REG_EIP,ret)

    def on_code(self,uc,address,size,context):
        if self.phase!='animation_load':return super().on_code(uc,address,size,context)
        if address in (OPEN,READ,CLOSE,ALIGNED_ALLOC,ALIGNED_FREE,ALLOC,self.STOP+0x100):
            stack=uc.reg_read(self.reg.UC_X86_REG_ESP)
            def word(offset):return struct.unpack('<I',uc.mem_read(stack+4*offset,4))[0]
            ret=word(0)
            if address==ALIGNED_FREE:
                if ret!=0x10004cf1 or word(1)!=0:raise ValueError('Only fresh animation objects supported')
                self.return_double(stack,ret,1,cdecl=True);return
            if address==self.STOP+0x100:
                if ret!=0x1005d621 or word(1)!=self.STATE+0x300 or self.polls:
                    raise ValueError('Unexpected native driver polling callback')
                self.polls+=1;self.return_double(stack,ret,1);return
            if address==OPEN:
                pointer=word(1)
                if ret!=0x1005e5a2 or word(2)!=0 or self.opened or not self.STACK<=pointer<self.STACK+65536-128:
                    raise ValueError('Unreviewed memory file open')
                name=bytes(uc.mem_read(pointer,128)).split(b'\0',1)[0].decode('ascii')
                if name!=self.requested:raise ValueError('Native resource filename differs')
                self.opened=True;self.open_count+=1;self.return_double(stack,ret,2,self.HANDLE);return
            if address==READ:
                target,count=word(2),word(3)
                sequence=((0x1005e5c8,4),(0x1005e605,2),(0x1005e62c,8),
                          (0x1005e66c,4),(0x1005e6b1,len(self.raw)-HEADER))
                if (not self.opened or word(1)!=self.HANDLE or self.reads>=len(sequence)
                        or (ret,count)!=sequence[self.reads] or self.position+count>len(self.raw)):
                    raise ValueError('Unexpected native memory read')
                if self.reads==4:
                    if target!=self.STATE+0x1000 or not self.body_allocated:raise ValueError('Unallocated native body')
                elif not self.STACK<=target<=self.STACK+65536-count:raise ValueError('Header read outside stack')
                uc.mem_write(target,self.raw[self.position:self.position+count]);self.position+=count;self.reads+=1
                self.return_double(stack,ret,3,count);return
            if address==CLOSE:
                if ret!=0x1005e6b7 or word(1)!=self.HANDLE or not self.opened or self.position!=len(self.raw):
                    raise ValueError('Unexpected memory file close')
                self.opened=False;self.close_count+=1;self.return_double(stack,ret,1);return
            if address==ALIGNED_ALLOC:
                if (ret!=0x1005e678 or word(1)!=len(self.raw)-HEADER or word(2)!=16 or self.body_allocated):
                    raise ValueError('Unreviewed aligned animation allocation')
                self.body_allocated=True;pointer=self.STATE+0x1000
            else:
                if ret!=0x10004e0e or word(1)!=len(self.cached)+1 or self.name_allocated:
                    raise ValueError('Unreviewed animation name allocation')
                self.name_allocated=True;pointer=self.STATE+0x11000
            self.return_double(stack,ret,1,pointer,cdecl=True);return
        if not any(a<=address and address+size<=b for a,b in RANGES):
            raise ValueError(f'Unreviewed animation loading instruction/call: {address:#x}')

    def on_write(self,uc,access,address,size,value,context):
        if self.phase!='animation_load':return super().on_write(uc,access,address,size,value,context)
        if self.STACK<=address and address+size<=self.STACK+65536:return
        if address==0x100d00a9 and size==1 and value in (0,1):return
        if address in (0x100c0664,0x100c0668) and size==4 and value==0:return
        if address in (self.STATE+0x10c,self.STATE+0x110) and size==4:return
        start=self.STATE+0x1004
        if start<=address and address+size<=start+8*self.parsed['track_count'] and size==4:return
        start=self.STATE+0x11000
        if start<=address and address+size<=start+len(self.cached)+1:return
        raise ValueError('Native animation loader wrote outside reviewed fields')

    def load(self,raw,name):
        if self.phase is not None:raise ValueError('Nested animation load')
        self.parsed,self.requested,self.cached=validate(raw,name);self.raw=raw
        self.position=self.reads=self.polls=self.open_count=self.close_count=0
        self.opened=self.body_allocated=self.name_allocated=False
        state=bytearray(self.SIZE);model=self.STATE+0x100
        struct.pack_into('<III',state,0x100,0x1009b400,1,2)
        struct.pack_into('<I',state,0x300,self.STATE+0x400)
        struct.pack_into('<I',state,0x414,self.STOP+0x100)
        self.uc.mem_write(self.STATE,bytes(state));source=name.encode('ascii')+b'\0'
        self.uc.mem_write(self.SOURCE,source.ljust(4096,b'\0'))
        self.uc.mem_write(0x100d16f4,struct.pack('<I',self.STATE+0x300))
        self.uc.mem_write(0x100d00a9,b'\0')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<4I',self.STOP,model,self.SOURCE,0))
        for register in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP'):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+register),0)
        for register,value in (('ESP',stack),('EFLAGS',2)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+register),value)
        self.phase='animation_load'
        try:
            self.uc.emu_start(START,self.STOP,count=1_000_000,timeout=5_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_EAX)!=0
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+16):
                raise ValueError('Native animation load did not return success')
        finally:self.phase=None
        expected=bytearray(state);body=bytearray(raw[HEADER:])
        for i in range(self.parsed['track_count']*2):
            offset=4+i*4;relative=struct.unpack_from('<I',body,offset)[0]
            struct.pack_into('<I',body,offset,self.STATE+0x1000+relative)
        expected[0x1000:0x1000+len(body)]=body
        cached=self.cached.encode('ascii')+b'\0';expected[0x11000:0x11000+len(cached)]=cached
        struct.pack_into('<II',expected,0x10c,self.STATE+0x11000,self.STATE+0x1000)
        if (bytes(self.uc.mem_read(self.STATE,self.SIZE))!=bytes(expected)
                or bytes(self.uc.mem_read(self.SOURCE,4096))!=source.ljust(4096,b'\0')
                or bytes(self.uc.mem_read(0x100d00a9,1))!=b'\0' or self.opened
                or (self.open_count,self.close_count,self.polls,self.reads,self.position)!=(1,1,1,5,len(raw))):
            raise ValueError('Native relocated data, source, callback or file lifetime differs')
        return {'schema_version':1,'library_sha256':DLL_SHA,'animation_sha256':digest(raw),
            'resource_name':name,'requested_memory_filename':self.requested,'cached_basename':self.cached,
            'track_count':self.parsed['track_count'],'frame_end':self.parsed['frame_end'],
            'read_calls':self.reads,'bytes_read':self.position,'relocated_pointers':2*self.parsed['track_count'],
            'native_animation_open_and_relocation_executed':True,'relocated_body_and_name_match':True,
            'all_other_object_bytes_preserved':True,'memory_file_closed':True,'source_preserved':True,
            'file_io_and_allocation_are_bounded_doubles':True,'driver_poll_is_noop_double':True,
            'native_scene_model_loader_executed':False,'animation_events_supported':False,
            'pose_or_renderer_executed':False,'library_loaded':False,'game_started':False,'game_modified':False}
