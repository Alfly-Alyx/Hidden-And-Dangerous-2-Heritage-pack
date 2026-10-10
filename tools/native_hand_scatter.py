"""Pinned original scatter bridge on separated guarded emulator allocations."""
import struct

from build_modern_equipment_hose import digest
from build_native_hand_pipeline import compare

BINARY_SHA='b6c39defcef9a92834a507d25650f496bf6fecd13b3719ca2943bbe28d94c958'
BINARY_SIZE=19456
BASE=0x2a000000
CODE_END=BASE+0x5314
WORK_SIZE=61808
EXPORTS={b'Hd2CommitArms':0x45af,b'Hd2CorrectHandPose':0x10ab,b'Hd2CorrectScatteredHandPose':0x4b18,
         b'Hd2HandScatterWorkspaceSize':0x5303,b'Hd2PrepareArms':0x209b,b'Hd2SolveArm':0x3b35}
CASES=('valid','count','role_count','work_size','null_model','short_record','overlap','pointer_overflow',
       'parent_cycle','parent_changed','wrong_role','late_kind','late_callback','unreachable','zero_quaternion',
       'changed_marker','changed_quaternion','changed_flags','changed_kind','changed_parent')


class HandScatterOracle:
    BINARY_SHA=BINARY_SHA;BINARY_SIZE=BINARY_SIZE;BASE=BASE;CODE_END=CODE_END;EXPORTS=EXPORTS
    STOP=0x3000000;STACK=0x3100000;NODES=0x4000000;WORK=0x4400000;INPUT=0x4500000;MODEL=0x4900000

    def __init__(self,raw,parent=None):
        if type(raw) is not bytes or len(raw)!=self.BINARY_SIZE or digest(raw)!=self.BINARY_SHA:
            raise ValueError('Unreviewed original hand scatter image')
        import pefile
        import unicorn as uni
        from unicorn import x86_const as reg
        pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=self.BASE
                or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!=self.EXPORTS):
            raise ValueError('Unreviewed scatter PE contract')
        self.uni,self.reg=uni,reg;self.uc=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32) if parent is None else parent.uc
        self.active=False;self.allowed=[];self.calls={};self.return_to_scatter=None;self.late_mutation=None
        for at,size,permissions in ((self.BASE,(len(mapped)+4095)&~4095,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.STOP,4096,uni.UC_PROT_READ|uni.UC_PROT_EXEC),(self.STACK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.WORK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),(self.INPUT,4096,uni.UC_PROT_READ)):
            if parent is not None and at in (self.STOP,self.STACK):continue
            self.uc.mem_map(at,size,permissions)
        self.uc.mem_write(self.BASE,mapped)
        for i in range(128):self.uc.mem_map(self.NODES+i*0x2000,4096,uni.UC_PROT_READ|uni.UC_PROT_WRITE)
        if parent is None:
            self.uc.hook_add(uni.UC_HOOK_CODE,self.on_code);self.uc.hook_add(uni.UC_HOOK_MEM_WRITE,self.on_write)

    def on_code(self,uc,address,size,context):
        if not self.active or not self.BASE+0x1000<address<address+size<=self.CODE_END:
            raise ValueError('Scatter instruction outside reviewed original code')
        for name,rva in self.EXPORTS.items():
            if address==self.BASE+rva:self.calls[name.decode()]=self.calls.get(name.decode(),0)+1
        if address==self.BASE+self.EXPORTS[b'Hd2CorrectHandPose']:
            self.return_to_scatter=struct.unpack('<I',uc.mem_read(uc.reg_read(self.reg.UC_X86_REG_ESP),4))[0]
        if address==self.return_to_scatter and self.late_mutation is not None:
            # Explicit adversarial host mutation after numerical calculation,
            # not a write performed by compiled code or normal production flow.
            at,raw=self.late_mutation;uc.mem_write(at,raw);self.injected=True;self.late_mutation=None
            self.after_fault=[bytes(uc.mem_read(page,4096)) for page in self.pages]

    def on_write(self,uc,access,address,size,value,context):
        if not self.active or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),(self.WORK,self.WORK+WORK_SIZE),*self.allowed)):
            raise ValueError('Scatter write outside workspace or six selected rotations/flags')
        if any(a<=address and address+size<=b for a,b in self.allowed):self.native_writes+=1

    def invoke(self,entry,args):
        if self.active or entry not in (self.BASE+self.EXPORTS[b'Hd2CorrectScatteredHandPose'],self.BASE+self.EXPORTS[b'Hd2HandScatterWorkspaceSize']):
            raise ValueError('Invalid or nested scatter entry')
        if (not isinstance(args,list) or any(type(v) is not int or not 0<=v<=0xffffffff for v in args)
                or len(args)!=(0 if entry==self.BASE+self.EXPORTS[b'Hd2HandScatterWorkspaceSize'] else 10)):
            raise ValueError('Invalid scatter argument contract')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        for name,value in {'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EBX':0x12345678,'ESI':0x23456781,
                'EDI':0x34567812,'EBP':0x45678123,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.active=True;self.calls={};self.native_writes=0;self.return_to_scatter=None
        try:
            self.uc.emu_start(entry,self.STOP,count=6_000_000,timeout=10_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+4:
                raise ValueError('Scatter budget or stack mismatch')
            for name,value in (('EBX',0x12345678),('ESI',0x23456781),('EDI',0x34567812),('EBP',0x45678123)):
                if self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+name))!=value:raise ValueError('Scatter callee-saved register changed')
            return self.uc.reg_read(self.reg.UC_X86_REG_EAX)
        finally:self.active=False

    def seed(self,data,arena,offsets,roles,*,alignment=0,case='valid',model_identity=None):
        if self.active or type(alignment) is not int or alignment not in (0,4) or case not in CASES:
            raise ValueError('Invalid scatter diagnostic switch')
        count=len(offsets)
        model=self.MODEL if model_identity is None else model_identity
        if type(model) is not int or not 0x1000<=model<=0xffffffff or model&3:
            raise ValueError('Invalid supplied model identity')
        if (count not in (11,128) or len(data['poses'])!=count or len(roles)!=11
                or offsets!=[i*0x200 for i in range(count)] or type(arena) is not bytes or len(arena)!=65536):
            raise ValueError('Invalid scatter diagnostic layout')
        self.pages=[self.NODES+((i*37)%128)*0x2000 for i in range(count)]
        pointers=[page+alignment for page in self.pages]
        self.allowed=[(pointers[i]+at,pointers[i]+at+n) for i in roles[5:] for at,n in ((0xc0,16),(0xe0,4))]
        source=bytearray(4096);blocks=[]
        for i,(pointer,offset) in enumerate(zip(pointers,offsets)):
            block=bytearray(b'Z'*4096);block[alignment:alignment+0x170]=arena[offset:offset+0x170]
            parent=data['parents'][i]
            struct.pack_into('<I',block,alignment+0x108,model if parent<0 else pointers[parent])
            struct.pack_into('<II',source,8*i,pointer,0x170);blocks.append(block)
        struct.pack_into('<'+'i'*count,source,0x800,*data['parents'])
        struct.pack_into('<11I',source,0xa00,*roles)
        struct.pack_into('<90d',source,0xb00,*data['rest']);struct.pack_into('<30d',source,0xe00,*data['grips'])
        args=[model,self.INPUT,count,self.INPUT+0x800,self.INPUT+0xa00,11,self.INPUT+0xb00,self.INPUT+0xe00,self.WORK,WORK_SIZE]
        if case=='count':args[2]=129
        elif case=='role_count':args[5]=10
        elif case=='work_size':args[9]-=1
        elif case=='null_model':args[0]=0
        elif case=='short_record':struct.pack_into('<I',source,8*(count-1)+4,0x108)
        elif case=='overlap':struct.pack_into('<I',source,8*(count-1),pointers[-2])
        elif case=='pointer_overflow':struct.pack_into('<I',source,8*(count-1),0xfffffffc)
        elif case=='parent_cycle':struct.pack_into('<i',source,0x800+4*(count-1),count-1)
        elif case=='parent_changed':struct.pack_into('<I',blocks[-1],alignment+0x108,0)
        elif case=='wrong_role':struct.pack_into('<I',source,0xa00+12,8)
        elif case=='late_kind':struct.pack_into('<I',blocks[10],alignment+0xf8,1)
        elif case=='late_callback':struct.pack_into('<I',blocks[10],alignment+0xe0,0x1208)
        elif case=='unreachable':struct.pack_into('<f',blocks[2],alignment+0xb0,3)
        elif case=='zero_quaternion':blocks[10][alignment+0xc0:alignment+0xd0]=bytes(16)
        self.late_mutation=None;self.injected=False;self.after_fault=None
        if case.startswith('changed_'):
            at,raw={'changed_marker':(pointers[1]+0xb0,struct.pack('<f',.39)),
                'changed_quaternion':(pointers[10]+0xc0,struct.pack('<f',.25)),
                'changed_flags':(pointers[10]+0xe0,struct.pack('<I',0x1208)),
                'changed_kind':(pointers[10]+0xf8,struct.pack('<I',1)),
                'changed_parent':(pointers[10]+0x108,struct.pack('<I',self.MODEL))}[case]
            self.late_mutation=(at,raw)
        for page,block in zip(self.pages,blocks):self.uc.mem_write(page,bytes(block))
        self.uc.mem_write(self.INPUT,bytes(source));self.uc.mem_write(self.WORK,b'Z'*65536)
        self.source=bytes(source);self.blocks=[bytes(b) for b in blocks];self.pointers=pointers
        self.count=count;self.roles=roles[:];self.offsets=offsets[:]
        return args,bytes(source),blocks

    def correct(self,data,arena,offsets,roles,*,alignment=0,case='valid'):
        args,source,blocks=self.seed(data,arena,offsets,roles,alignment=alignment,case=case)
        count=len(offsets)
        if self.invoke(self.BASE+self.EXPORTS[b'Hd2HandScatterWorkspaceSize'],[])!=WORK_SIZE:
            raise ValueError('Scatter workspace ABI differs')
        status=self.invoke(self.BASE+self.EXPORTS[b'Hd2CorrectScatteredHandPose'],args)
        actual=[bytes(self.uc.mem_read(page,4096)) for page in self.pages]
        protected=self.after_fault if self.injected else [bytes(b) for b in blocks]
        before=bytearray(arena);after=bytearray(arena)
        for i,offset in enumerate(offsets):
            before[offset:offset+0x170]=blocks[i][alignment:alignment+0x170]
            after[offset:offset+0x170]=actual[i][alignment:alignment+0x170]
        error=compare(data,bytes(before),bytes(after),offsets,roles) if not status else 0
        for i,(wanted,block) in enumerate(zip(protected,actual)):
            allowed={at for a,b in self.allowed for at in range(a-self.pages[i],b-self.pages[i])} if not status else set()
            if any(a!=b and at not in allowed for at,(a,b) in enumerate(zip(wanted,block))):
                raise ValueError('Scatter changed a guard, unrelated record byte or refused destination')
        if (bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source)
                or bytes(self.uc.mem_read(self.WORK+WORK_SIZE,65536-WORK_SIZE))!=b'Z'*(65536-WORK_SIZE)
                or (status and self.native_writes) or self.injected!=case.startswith('changed_')):
            raise ValueError('Scatter source, workspace guard or refusal changed')
        return {'status':status,'case':case,'count':count,'alignment':alignment,'max_rotation_error':error,
            'compiled_calls':dict(self.calls),'native_write_operations':self.native_writes,
            'input_and_guards_unchanged':True,'all_refused_destinations_unchanged':True,
            'adversarial_late_mutation_injected':self.injected,'native_allocations_are_separate_guarded_pages':True,
            'allocation_ownership_is_supplied':True,'game_started':False}
