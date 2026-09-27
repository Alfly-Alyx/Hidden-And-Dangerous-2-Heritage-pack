"""Native joint-only skin palette assembly, stopped before GPU buffer access.

Objects, local poses and inverse binds are supplied by the caller. This does
not execute the scene loader, choose animation poses or validate game rendering.
"""
import math
import struct

from ls3d_math_oracle import MathOracle,basis,f32,unit,vector

START=0x1005307a
STOP=0x10053172
PALETTE=0x100bf3e0
RANGES=((START,STOP),(0x1005327f,0x10053311),(0x1001b8f0,0x1001b9f9),
        (0x1002d450,0x1002d57d),(0x1002d830,0x1002d9b0))
TOLERANCE=5e-5


def affine_matrix(value):
    value=vector(value,16,10)
    if any(value[i]!=v for i,v in ((3,0),(7,0),(11,0),(15,1))):raise ValueError('Expected affine inverse bind')
    return value


def product(left,right):
    """Row-vector affine product; rounds each written component to float32."""
    result=[0.0]*16;result[15]=1.0
    for row in range(3):
        for col in range(3):result[row*4+col]=f32(sum(left[row*4+k]*right[k*4+col] for k in range(3)))
    for col in range(3):
        result[12+col]=f32(left[12]*right[col]+right[12+col]+left[13]*right[4+col]+left[14]*right[8+col])
    return result


def local_matrix(pose):
    rotation=basis(pose['rotation']);matrix=[0.0]*16;matrix[15]=1.0
    for row in range(3):
        for col in range(3):matrix[row*4+col]=f32(f32(rotation[col][row])*pose['scale'][row])
    matrix[12:15]=pose['position']
    return matrix


def validate(poses,inverse_binds):
    if not isinstance(poses,(list,tuple)) or not 1<=len(poses)<=64:raise ValueError('Expected one to 64 joint poses')
    if not isinstance(inverse_binds,(list,tuple)) or len(inverse_binds)!=len(poses):raise ValueError('Inverse bind count differs')
    result=[]
    for i,pose in enumerate(poses):
        if not isinstance(pose,dict) or set(pose)!={'position','rotation','scale','parent'}:
            raise ValueError('Unexpected joint pose shape')
        parent=pose['parent']
        if type(parent) is not int or not -1<=parent<len(poses) or parent==i:raise ValueError('Invalid joint parent')
        scale=vector(pose['scale'],3,2)
        if any(v<.01 for v in scale):raise ValueError('Unreviewed zero, negative or tiny scale')
        result.append({'parent':parent,'position':vector(pose['position'],3,10),'rotation':unit(pose['rotation']),'scale':scale})
    for i in range(len(result)):
        visited=set();parent=i
        while parent!=-1:
            if parent in visited:raise ValueError('Cyclic joint hierarchy')
            visited.add(parent);parent=result[parent]['parent']
    return result,[affine_matrix(m) for m in inverse_binds]


def reference(poses,inverse_binds):
    poses,inverse_binds=validate(poses,inverse_binds)
    locals=[local_matrix(pose) for pose in poses];world={}
    # Match native traversal/caching order, which can affect float32 rounding.
    for index in range(len(poses)):
        value=locals[index];parent=poses[index]['parent']
        while parent!=-1:
            if parent in world:
                value=product(value,world[parent]);break
            value=product(value,locals[parent]);parent=poses[parent]['parent']
        if any(abs(v)>10 for v in value):raise ValueError('Composed hierarchy outside reviewed domain')
        world[index]=value
    palette=[product(inverse_binds[i],world[i]) for i in range(len(poses))]
    if any(abs(v)>10 for matrix in palette for v in matrix):raise ValueError('Composed palette outside reviewed domain')
    return {'local_matrices':locals,'world_matrices':[world[i] for i in range(len(poses))],'palette':palette}


class PaletteOracle(MathOracle):
    SOURCE=0x3800000
    SOURCE_SIZE=0x4000
    NODES=0x3900000
    NODES_SIZE=0x10000

    def __init__(self,raw):
        super().__init__(raw)
        self.uc.mem_map(self.SOURCE,self.SOURCE_SIZE,self.uni.UC_PROT_READ)
        self.uc.mem_map(self.NODES,self.NODES_SIZE,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        # Only data pages containing the native scratch palette are writable.
        self.uc.mem_protect(0x100bf000,0x2000,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.joints=0;self.calls={}

    def on_code(self,uc,address,size,_):
        if self.phase!='palette':return super().on_code(uc,address,size,_)
        if not any(a<=address and address+size<=b for a,b in RANGES):
            raise ValueError('Unreviewed palette instruction, missing joint or GPU call')
        if address in (0x1001b8f0,0x1002d450,0x1002d830,0x100532eb):
            self.calls[address]=self.calls.get(address,0)+1

    def on_write(self,uc,access,address,size,value,_):
        if self.phase!='palette':return super().on_write(uc,access,address,size,value,_)
        if self.STACK<=address and address+size<=self.STACK+65536:return
        if PALETTE<=address and address+size<=PALETTE+64*self.joints:return
        offset=address-self.NODES
        if 0<=offset<self.joints*0x200:
            field=offset%0x200
            if any(a<=field and field+size<=b for a,b in ((0x80,0x8c),(0x90,0x9c),(0xa0,0xac),
                    (0xe0,0xe4),(0x120,0x160),(0x164,0x168))):return
        raise ValueError('Palette write outside reviewed joint fields or scratch matrices')

    def assemble(self,poses,inverse_binds):
        if self.phase is not None:raise ValueError('Nested palette phase')
        poses,inverse_binds=validate(poses,inverse_binds);expected=reference(poses,inverse_binds)
        count=len(poses);source=bytearray(self.SOURCE_SIZE);nodes=bytearray(self.NODES_SIZE)
        model=self.SOURCE;root=self.SOURCE+0x500;pointer_array=self.SOURCE+0x900;inverses=self.SOURCE+0x1000
        struct.pack_into('<II',source,0x210,count,pointer_array)
        struct.pack_into('<H',source,0x500+0xf8,1) # Visual root stops the native ancestor walk.
        for i,(pose,inverse) in enumerate(zip(poses,inverse_binds)):
            offset=i*0x200;pointer=self.NODES+offset
            struct.pack_into('<I',source,0x900+i*4,pointer)
            struct.pack_into('<16f',source,0x1000+i*96,*inverse)
            struct.pack_into('<f',nodes,offset+0xbc,1)
            struct.pack_into('<3f',nodes,offset+0xb0,*pose['position'])
            struct.pack_into('<4f',nodes,offset+0xc0,*pose['rotation'])
            struct.pack_into('<3f',nodes,offset+0xd0,*pose['scale'])
            struct.pack_into('<I',nodes,offset+0xe0,8) # Quaternion supplied, local matrix not built.
            struct.pack_into('<H',nodes,offset+0xf8,10)
            parent=root if pose['parent']==-1 else self.NODES+pose['parent']*0x200
            struct.pack_into('<I',nodes,offset+0x108,parent)
        self.uc.mem_write(self.SOURCE,bytes(source));self.uc.mem_write(self.NODES,bytes(nodes))
        self.uc.mem_write(PALETTE,b'Z'*4096)
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        struct_values={0x38:inverses,0x3c:model}
        for offset,value in struct_values.items():self.uc.mem_write(stack+offset,struct.pack('<I',value))
        for name in ('EAX','EBX','ECX','EDX','ESI'):self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),0)
        for name,value in (('EDI',model),('EBP',stack+0x400),('ESP',stack),('EFLAGS',2),
                           ('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase='palette';self.joints=count;self.calls={}
        try:
            self.uc.emu_start(START,STOP,count=4096+800*count*count,timeout=5_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=STOP:raise ValueError('Palette instruction/time budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack:raise ValueError('Palette calling convention differs')
        finally:self.phase=None;self.joints=0
        if bytes(self.uc.mem_read(self.SOURCE,self.SOURCE_SIZE))!=bytes(source):raise ValueError('Palette source changed')
        actual=bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE));palette_raw=bytes(self.uc.mem_read(PALETTE,4096))
        if palette_raw[count*64:]!=b'Z'*(4096-count*64):raise ValueError('Unused palette changed')
        values={'local_matrices':[],'world_matrices':[],
                'palette':[list(struct.unpack_from('<16f',palette_raw,i*64)) for i in range(count)]}
        allowed=set()
        for i in range(count):
            offset=i*0x200
            for key,at in (('local_matrices',0x80),('world_matrices',0x120)):
                values[key].append(list(struct.unpack_from('<16f',actual,offset+at)))
            if struct.unpack_from('<I',actual,offset+0xe0)[0]!=0x1c or struct.unpack_from('<I',actual,offset+0x164)[0]!=0x10:
                raise ValueError('Unexpected native joint cache flags')
            for a,b in ((0x80,0x8c),(0x90,0x9c),(0xa0,0xac),(0xe0,0xe4),(0x120,0x160),(0x164,0x168)):
                allowed.update(range(offset+a,offset+b))
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(nodes,actual))):raise ValueError('Unrelated joint data changed')
        errors={key:max(abs(a-b) for row,ref in zip(values[key],expected[key]) for a,b in zip(row,ref)) for key in values}
        if any(not math.isfinite(v) for rows in values.values() for row in rows for v in row) or max(errors.values())>TOLERANCE:
            raise ValueError('Native palette differs from reference')
        if self.calls.get(0x1002d450)!=count:raise ValueError('Unexpected local rotation rebuild count')
        return {**values,'joints':count,'max_errors':errors,'native_palette_match':True,'inputs_preserved':True,
            'local_rotations_built':self.calls[0x1002d450],'matrix_products':self.calls.get(0x1002d830,0),
            'cached_ancestor_reuses':self.calls.get(0x100532eb,0),
            'joint_only_palette_assembly_qualified':True,'loaded_scene_qualified':False,
            'animation_pose_selection_qualified':False,'gpu_called':False,'library_loaded':False,'game_started':False}
