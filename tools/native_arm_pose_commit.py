"""Original C commit -> native joint refresh -> palette, in persistent memory.

Bounded caller-supplied joint trees, not loaded models or a live client hook.
The owning visual is a diagnostic record; its bounds/skin are not evaluated.
"""
from copy import deepcopy
import math
import struct

from ls3d_math_oracle import MathOracle,unit
from ls3d_palette_oracle import PaletteOracle,reference,validate,START,STOP,PALETTE,TOLERANCE
from build_modern_equipment_hose import digest

BINARY_SIZE=3584
BINARY_SHA='cadf4a0bab1f3ac6c9e078f9e32e2dccaa048bf4f68183511bfdb81ce859e7e1'
BASE=0x22000000
ENTRY=BASE+0x11d2
CODE_END=BASE+0x1000+1592
JOINT_VTABLE=0x1009b9d8
REFRESH=0x1001e610
REFRESH_RANGES=((0x1001e550,0x1001e604),(REFRESH,0x1001e73e),
                (0x1001e77e,0x1001e784),(0x10020ad0,0x10020b48),(0x1001e790,0x1001e7c9))


def reference_commit(arena,offsets,before,after,flags):
    """Independent byte-level contract; six inputs only, no live pointers."""
    if (not isinstance(arena,bytes) or not 6*0x170<=len(arena)<=0x10000
            or len(offsets)!=6 or len(before)!=6 or len(after)!=6 or len(flags)!=6):
        raise ValueError('Invalid commit fixture')
    checked=[]
    for i,at in enumerate(offsets):
        if type(at) is not int or not 0<=at<=0xffffffff:raise ValueError('Invalid offset scalar')
        if type(flags[i]) is not int or not 0<=flags[i]<=0xffffffff:raise ValueError('Invalid flag scalar')
        if at%16 or at>len(arena)-0x170 or any(at<a+0x170 and a<at+0x170 for a in checked):return arena,2
        checked.append(at)
        kind=struct.unpack_from('<I',arena,at+0xf8)[0];actual_flags=struct.unpack_from('<I',arena,at+0xe0)[0]
        if kind!=10 or actual_flags!=flags[i] or not flags[i]&8 or flags[i]&0x1200:return arena,3
        try:
            old=unit(before[i]);new=unit(after[i])
        except (ValueError,OverflowError,struct.error):return arena,4
        if arena[at+0xc0:at+0xd0]!=struct.pack('<4f',*old):return arena,5
    output=bytearray(arena)
    for at,q,flag in zip(offsets,after,flags):
        struct.pack_into('<4f',output,at+0xc0,*q)
        struct.pack_into('<I',output,at+0xe0,(flag&0xfffffecb)|0x40000008)
    return bytes(output),0


def reference_refresh(arena,parents,owner_offset=0xf000):
    """Joint-only hierarchy and separate owning visual, matching supplied tree."""
    data=bytearray(arena);children={i:[] for i in range(len(parents))};roots=[]
    for i,parent in enumerate(parents):
        if parent==-1:roots.append(i)
        else:children[parent].append(i)
    def get(at):return struct.unpack_from('<I',data,at)[0]
    def put(at,value):struct.pack_into('<I',data,at,value&0xffffffff)
    def joint(i):
        at=i*0x200;flag=get(at+0xe0)
        if flag&0x40002000:put(at+0x164,get(at+0x164)&0xffffffe7)
        if flag&0x40000000:
            put(owner_offset+0x218,get(owner_offset+0x218)+1)
            put(owner_offset+0x1d0,get(owner_offset+0x1d0)&0xfff9ffff)
            put(owner_offset+0xe0,(get(owner_offset+0xe0)&0xfffffeff)|0x40000000)
    def visit(i):
        at=i*0x200;dirty=get(at+0xe0)&0x40002000
        if dirty:put(at+0x104,get(at+0x104)+1)
        for child in children[i]:
            ca=child*0x200
            if dirty:put(ca+0xe0,(get(ca+0xe0)&0xfffffedf)|0x2000)
            visit(child);joint(child)
            if get(ca+0xe0)&0x40002000:
                put(ca+0xe0,get(ca+0xe0)&0xbfffdfff)
                put(at+0xe0,(get(at+0xe0)&0xfffffeff)|0x2000)
    for i in roots:
        visit(i);joint(i)
        put(owner_offset+0xe0,get(owner_offset+0xe0)&0xfffffeff)
        put(i*0x200+0xe0,get(i*0x200+0xe0)&0xbfffdfff)
    return bytes(data)


class PersistentArmCommitOracle(PaletteOracle):
    def __init__(self,library,compiled):
        if type(compiled) is not bytes or len(compiled)!=BINARY_SIZE or digest(compiled)!=BINARY_SHA:
            raise ValueError('Unreviewed original arm commit image')
        super().__init__(library)
        import pefile
        pe=pefile.PE(data=compiled);mapped=pe.get_memory_mapped_image()
        if (pe.OPTIONAL_HEADER.ImageBase!=BASE or pe.FILE_HEADER.Machine!=0x14c
                or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!={b'Hd2CommitArms':ENTRY-BASE}):
            raise ValueError('Changed arm commit PE contract')
        self.uc.mem_map(BASE,(len(mapped)+4095)&~4095,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC)
        self.uc.mem_write(BASE,mapped)
        if struct.unpack('<I',self.uc.mem_read(0x100be46c,4))[0]!=0:
            raise ValueError('Only an empty deferred refresh queue is reviewed')

    def on_code(self,uc,address,size,context):
        if self.phase=='arm_commit':
            if not BASE+0x1000<address<address+size<=CODE_END:
                raise ValueError('Unreviewed commit instruction or startup')
            return
        if self.phase=='joint_refresh':
            if not any(a<=address and address+size<=b for a,b in REFRESH_RANGES):
                raise ValueError(f'Unreviewed joint refresh instruction: {address:#x}')
            return
        return super().on_code(uc,address,size,context)

    def on_write(self,uc,access,address,size,value,context):
        if self.phase in ('arm_commit','joint_refresh'):
            return MathOracle.on_write(self,uc,access,address,size,value,context)
        return super().on_write(uc,access,address,size,value,context)

    def invoke(self,entry,args,phase,writes,*,cdecl=False):
        if self.phase is not None:raise ValueError('Nested persistent pose phase')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        preserved={'EBX':0x12345678,'ESI':0x34567812,'EDI':0x56781234,'EBP':0x78123456}
        for name,value in {**preserved,'EAX':0,'ECX':0,'EDX':0,'ESP':stack,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase,self.writes=phase,tuple(writes)
        try:
            self.uc.emu_start(entry,self.STOP,count=500000,timeout=3_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+4*(1+(0 if cdecl else len(args)))
                    or any(self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+n))!=v for n,v in preserved.items())):
                raise ValueError('Persistent pose execution/ABI contract differs')
        finally:self.phase,self.writes=None,()
        return self.uc.reg_read(self.reg.UC_X86_REG_EAX)

    def commit(self,offsets,before,after,flags):
        arena=bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))
        expected,status=reference_commit(arena,offsets,before,after,flags)
        source=bytearray(4096)
        struct.pack_into('<6I',source,0,*offsets)
        for i in range(6):
            struct.pack_into('<4f',source,0x40+16*i,*before[i])
            struct.pack_into('<4f',source,0x100+16*i,*after[i])
        struct.pack_into('<6I',source,0x200,*flags);self.uc.mem_write(self.INPUT,bytes(source))
        writes=[]
        if status==0:
            for at in offsets:writes.extend(((self.NODES+at+0xc0,self.NODES+at+0xd0),
                                             (self.NODES+at+0xe0,self.NODES+at+0xe4)))
        result=self.invoke(ENTRY,[self.NODES,self.NODES_SIZE,self.INPUT,self.INPUT+0x40,
            self.INPUT+0x100,self.INPUT+0x200],'arm_commit',writes,cdecl=True)
        if (result!=status or bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))!=expected
                or bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source)):
            raise ValueError('Compiled pose commit differs or changed protected fields')
        return result

    def exercise(self,poses,inverse_binds,indices,replacements,*,failure=None):
        poses,inverse_binds=validate(poses,inverse_binds)
        if (len(poses)>64 or not isinstance(indices,list) or len(indices)!=6 or len(set(indices))!=6
                or any(type(i) is not int or not 0<=i<len(poses) for i in indices)
                or not isinstance(replacements,list) or len(replacements)!=6
                or failure not in (None,'late_snapshot','late_flags','late_kind','late_quaternion','duplicate','range','alignment','callback')):
            raise ValueError('Invalid persistent pose scenario')
        replacements=[unit(q) for q in replacements]
        initial=self.assemble(poses,inverse_binds)
        arena=bytearray(self.uc.mem_read(self.NODES,self.NODES_SIZE));owner=0xf000
        children={i:[] for i in range(len(poses))};roots=[]
        for i,pose in enumerate(poses):
            at=i*0x200;parent=pose['parent']
            (roots if parent==-1 else children[parent]).append(i)
            struct.pack_into('<I',arena,at,JOINT_VTABLE)
            struct.pack_into('<I',arena,at+0xe0,0x11c)
            struct.pack_into('<I',arena,at+0x104,7)
            struct.pack_into('<I',arena,at+0x108,self.NODES+(owner if parent==-1 else parent*0x200))
            struct.pack_into('<I',arena,at+0x168,self.NODES+owner)
        for i,rows in children.items():
            if rows:struct.pack_into('<I',arena,i*0x200+0x10c,self.NODES+rows[0]*0x200)
            for a,b in zip(rows,rows[1:]):struct.pack_into('<I',arena,a*0x200+0x110,self.NODES+b*0x200)
        struct.pack_into('<I',arena,owner+0xf8,1)
        struct.pack_into('<I',arena,owner+0xe0,0x11c)
        struct.pack_into('<I',arena,owner+0x1d0,0x60000)
        before=[list(struct.unpack_from('<4f',arena,i*0x200+0xc0)) for i in indices]
        offsets=[i*0x200 for i in indices];flags=[0x11c]*6
        if failure=='late_snapshot':before[-1]=[-v for v in before[-1]]
        elif failure=='late_flags':flags[-1]|=1
        elif failure=='late_kind':struct.pack_into('<I',arena,offsets[-1]+0xf8,9)
        elif failure=='late_quaternion':replacements[-1]=[0,0,0,0]
        elif failure=='duplicate':offsets[-1]=offsets[0]
        elif failure=='range':offsets[-1]=0xffffff00
        elif failure=='alignment':offsets[-1]+=1
        elif failure=='callback':
            flags[-1]|=0x200;struct.pack_into('<I',arena,offsets[-1]+0xe0,flags[-1])
        self.uc.mem_write(self.NODES,bytes(arena));source=bytes(self.uc.mem_read(self.SOURCE,self.SOURCE_SIZE))
        status=self.commit(offsets,before,replacements,flags)
        if failure:
            if status==0 or bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))!=bytes(arena):
                raise ValueError('Rejected pose commit changed arena')
            return {'status':status,'failure':failure,'all_nodes_unchanged':True,'game_started':False}
        if status:raise ValueError('Valid persistent pose commit failed')
        before_refresh=bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))
        expected_refresh=reference_refresh(before_refresh,[p['parent'] for p in poses])
        writes=[(self.NODES+i*0x200+at,self.NODES+i*0x200+at+4)
                for i in range(len(poses)) for at in (0xe0,0x104,0x164)]
        writes.extend((self.NODES+owner+at,self.NODES+owner+at+4) for at in (0xe0,0x1d0,0x218))
        for root in roots:self.invoke(REFRESH,[self.NODES+root*0x200],'joint_refresh',writes)
        if bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))!=expected_refresh:
            raise ValueError('Native recursive refresh differs from independent reference')
        updated=deepcopy(poses)
        for i,q in zip(indices,replacements):updated[i]['rotation']=q
        expected=reference(updated,inverse_binds)
        # Re-enter palette calculation without resetting any joint or cache.
        self.uc.mem_write(PALETTE,b'Z'*4096);stack=self.STACK+0xf000
        self.uc.mem_write(self.STACK,bytes(65536))
        for at,value in ((0x38,self.SOURCE+0x1000),(0x3c,self.SOURCE)):
            self.uc.mem_write(stack+at,struct.pack('<I',value))
        for name,value in {'EAX':0,'EBX':0,'ECX':0,'EDX':0,'ESI':0,'EDI':self.SOURCE,
                'EBP':stack+0x400,'ESP':stack,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase='palette';self.joints=len(poses);self.calls={}
        try:
            self.uc.emu_start(START,STOP,count=4096+800*len(poses)**2,timeout=5_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack):raise ValueError('Persistent palette did not finish')
        finally:self.phase=None;self.joints=0
        actual=bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE));pal=bytes(self.uc.mem_read(PALETTE,4096))
        error=0;allowed=set()
        for i in range(len(poses)):
            for key,at in (('local_matrices',0x80),('world_matrices',0x120)):
                row=struct.unpack_from('<16f',actual,i*0x200+at)
                if any(not math.isfinite(v) for v in row):raise ValueError('Nonfinite persistent matrix')
                error=max(error,*(abs(a-b) for a,b in zip(row,expected[key][i])))
            row=struct.unpack_from('<16f',pal,i*64)
            if any(not math.isfinite(v) for v in row):raise ValueError('Nonfinite persistent palette')
            error=max(error,*(abs(a-b) for a,b in zip(row,expected['palette'][i])))
            for a,b in ((0x80,0x8c),(0x90,0x9c),(0xa0,0xac),(0xe0,0xe4),(0x120,0x160),(0x164,0x168)):
                allowed.update(range(i*0x200+a,i*0x200+b))
        if (error>TOLERANCE or pal[len(poses)*64:]!=b'Z'*(4096-len(poses)*64)
                or bytes(self.uc.mem_read(self.SOURCE,self.SOURCE_SIZE))!=source
                or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(expected_refresh,actual)))):
            raise ValueError('Persistent palette changed protected state or differs')
        return {'status':0,'joints':len(poses),'committed_rotations':6,'max_matrix_error':error,
                'local_rotations_rebuilt':self.calls.get(0x1002d450,0),
                'owner_change_counter':struct.unpack_from('<I',actual,owner+0x218)[0],
                'initial_palette_max_error':max(initial['max_errors'].values()),
                'compiled_commit_native_refresh_palette_same_memory':True,'inputs_and_other_pose_channels_preserved':True,
                'model_tick_callsite_hooked':False,'owning_visual_bounds_evaluated':False,
                'loaded_skeleton_binding_qualified':False,'skin_or_renderer_executed':False,'game_started':False}
