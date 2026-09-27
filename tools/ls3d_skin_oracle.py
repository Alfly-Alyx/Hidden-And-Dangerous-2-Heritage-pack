"""Bounded CPU skin kernel, using supplied matrices, never a loaded scene.

Raw vertex bone bytes are one-based palette indices. This is established by
the unchanged read in 0x10053900 and the subtraction inside 0x10065c60; joint
IDs themselves remain zero-based. No loader, matrix assembly or GPU call runs.
"""
import math
import struct

from ls3d_math_oracle import MathOracle,f32,vector

START=0x10065c60
END=0x10065f95
TOLERANCE=1e-4


def validate(vertices,pairs,matrices,parents):
    if not isinstance(matrices,(list,tuple)) or not 1<=len(matrices)<=64:
        raise ValueError('Expected one to 64 skin matrices')
    matrices=[vector(m,16,10) for m in matrices]
    if any(any(m[i]!=v for i,v in ((3,0),(7,0),(11,0),(15,1))) for m in matrices):
        raise ValueError('Expected affine row-vector skin matrices')
    if (not isinstance(parents,(list,tuple)) or len(parents)!=len(matrices)
            or any(type(p) is not int or not 0<=p<=len(matrices) for p in parents)):
        raise ValueError('Parent outside reviewed skin palette')
    if not isinstance(vertices,(list,tuple)) or not 0<=len(vertices)<=2048:
        raise ValueError('Vertex count outside reviewed skin domain')
    vertices=[vector(v,8,10) for v in vertices]
    if not isinstance(pairs,(list,tuple)) or len(pairs)!=len(vertices):
        raise ValueError('Expected one bone/byte pair per vertex')
    for pair in pairs:
        if (not isinstance(pair,(list,tuple)) or len(pair)!=2 or any(type(v) is not int for v in pair)
                or not 1<=pair[0]<=len(matrices) or not 0<=pair[1]<=255):
            raise ValueError('Expected one-based bone and unsigned blend byte')
    return vertices,[list(p) for p in pairs],matrices,list(parents)


def transformed(v,m,normal=False):
    return [sum(v[j]*m[i+j*4] for j in range(3))+(0 if normal else m[12+i]) for i in range(3)]


def reference(vertices,pairs,matrices,parents):
    """Numerical reference preserving the kernel's intermediate float stores."""
    vertices,pairs,matrices,parents=validate(vertices,pairs,matrices,parents)
    result=[]
    for vertex,(bone,byte) in zip(vertices,pairs):
        position=transformed(vertex,matrices[bone-1])
        normal=[f32(v) for v in transformed(vertex[3:6],matrices[bone-1],True)]
        if not byte:
            result.append([f32(v) for v in position]+normal);continue
        weight=byte/256;remaining=1-weight;parent=parents[bone-1]
        other_position=transformed(vertex,matrices[parent-1]) if parent else vertex[:3]
        other_normal=(transformed(vertex[3:6],matrices[parent-1],True) if parent else vertex[3:6])
        # X stays in x87 until the final position sum. Y/Z are stored earlier.
        position[1:]=[f32(v) for v in position[1:]]
        other_position[2]=f32(other_position[2])
        left=[position[0]*remaining]+[f32(v*remaining) for v in position[1:]]
        position=[f32(a+f32(b*weight)) for a,b in zip(left,other_position)]
        # Every normal component is stored; only the final Z product stays live.
        other_normal=[f32(v) for v in other_normal]
        left=[f32(v*remaining) for v in normal[:2]]+[normal[2]*remaining]
        normal=[f32(a+f32(b*weight)) for a,b in zip(left,other_normal)]
        result.append(position+normal)
    return result


class SkinOracle(MathOracle):
    SOURCE=0x3400000
    SOURCE_SIZE=0x20000
    TARGET=0x3600000
    TARGET_SIZE=0x10000

    def __init__(self,raw):
        super().__init__(raw)
        if struct.unpack('<f',self.uc.mem_read(0x1009d2bc,4))[0]!=1/256:
            raise ValueError('Changed native skin blend divisor')
        self.uc.mem_map(self.SOURCE,self.SOURCE_SIZE,self.uni.UC_PROT_READ)
        self.uc.mem_map(self.TARGET,self.TARGET_SIZE,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.vertex_count=0;self.hits={}

    def on_code(self,uc,address,size,_):
        if self.phase!='skin':return super().on_code(uc,address,size,_)
        if not START<=address or address+size>END:raise ValueError('Unreviewed skin instruction or call')
        if address in (0x10065ca0,0x10065d50,0x10065da2,0x10065e48):
            self.hits[address]=self.hits.get(address,0)+1

    def on_write(self,uc,access,address,size,value,_):
        if self.phase!='skin':return super().on_write(uc,access,address,size,value,_)
        if self.STACK<=address and address+size<=self.STACK+65536:return
        offset=address-self.TARGET
        if 0<=offset<self.vertex_count*32 and offset%32+size<=24:return
        raise ValueError('Skin write outside position/normal or stack')

    def deform(self,vertices,pairs,matrices,parents):
        if self.phase is not None:raise ValueError('Nested skin phase')
        vertices,pairs,matrices,parents=validate(vertices,pairs,matrices,parents)
        expected=reference(vertices,pairs,matrices,parents)
        source=bytearray(self.SOURCE_SIZE)
        source[0x100:0x100+len(parents)]=bytes(parents)
        for i,matrix in enumerate(matrices):struct.pack_into('<16f',source,0x400+i*64,*matrix)
        for i,vertex in enumerate(vertices):struct.pack_into('<8f',source,0x2000+i*32,*vertex)
        for i,pair in enumerate(pairs):source[0x12000+i*2:0x12002+i*2]=bytes(pair)
        self.uc.mem_write(self.SOURCE,bytes(source));self.uc.mem_write(self.TARGET,b'Z'*self.TARGET_SIZE)
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<6I',self.STOP,self.SOURCE+0x2000,len(vertices),
            self.SOURCE+0x12000,self.SOURCE+0x400,self.SOURCE+0x100))
        for name in ('EAX','EBX','ESI','EDI','EBP'):self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),0)
        for name,value in (('ECX',self.TARGET),('EDX',32),('ESP',stack),('EFLAGS',2),
                           ('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase='skin';self.vertex_count=len(vertices);self.hits={}
        try:
            self.uc.emu_start(START,self.STOP,count=4096+400*len(vertices),timeout=5_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP:raise ValueError('Skin instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+24:raise ValueError('Skin calling convention differs')
        finally:self.phase=None;self.vertex_count=0
        if bytes(self.uc.mem_read(self.SOURCE,self.SOURCE_SIZE))!=bytes(source):raise ValueError('Skin input changed')
        actual=bytes(self.uc.mem_read(self.TARGET,self.TARGET_SIZE))
        if any(value!=90 for i,value in enumerate(actual) if i>=len(vertices)*32 or i%32>=24):
            raise ValueError('Skin overwrote UV/padding or unused output')
        values=[list(struct.unpack_from('<6f',actual,i*32)) for i in range(len(vertices))]
        if any(not math.isfinite(v) for row in values for v in row):raise ValueError('Nonfinite skin result')
        error=max((abs(a-b) for row,wanted in zip(values,expected) for a,b in zip(row,wanted)),default=0)
        if error>TOLERANCE:raise ValueError('Native skin differs from numerical reference')
        branches={'rigid':sum(byte==0 for _,byte in pairs),
            'parent_matrix':sum(byte!=0 and parents[bone-1]!=0 for bone,byte in pairs),
            'parent_identity':sum(byte!=0 and parents[bone-1]==0 for bone,byte in pairs)}
        if (self.hits.get(0x10065ca0,0)!=len(vertices) or any(self.hits.get(address,0)!=branches[name]
                for address,name in ((0x10065d50,'rigid'),(0x10065da2,'parent_matrix'),(0x10065e48,'parent_identity')))):
            raise ValueError('Native skin selected unexpected branches')
        return {'values':values,'vertices':len(vertices),'branches':branches,'max_error':error,
            'native_skin_kernel_match':True,'bone_index_base':1,'blend_byte_divisor':256,
            'inputs_preserved':True,'uv_output_untouched':True,'normals_renormalized':False,
            'matrix_palette_assembly_qualified':False,'scene_loaded':False,'library_loaded':False,
            'game_started':False,'engine_validated':False}
