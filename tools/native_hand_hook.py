"""Bounded original post-blend adapter; invented model and refresh stand-in.

No client patch, live model discovery, Windows loading or native scene refresh.
All compiled target/solve/commit stages execute; only the final virtual refresh
is an explicit RET 4 stand-in for checking the adapter's calling convention.
"""
import struct

from build_modern_equipment_hose import digest
from native_hand_targets import encode_inputs
from native_hand_pipeline import WORK_SIZE

BINARY_SHA='80c8524710e0828acf3e09bffbacbf9241db68cd249b24c57b7b410322920fa2'
BINARY_SIZE=18432
BASE=0x28000000
CODE_END=BASE+0x4ffe
ACTIVE=BASE+0x5320
ENTRY=BASE+0x4fd5
CALLBACK=BASE+0x4d27
EXPORTS={b'Hd2CommitArms':17839,b'Hd2ConfigureHandHook':19577,b'Hd2CorrectHandPose':4267,
         b'Hd2HandHookEntry':20420,b'Hd2PrepareArms':8347,b'Hd2SolveArm':15157}
FPU_REGISTERS=('FPCW','FPSW','FPTAG','FIP','FCS','FDP','FDS','FOP',*[f'FP{i}' for i in range(8)])


def emulator_restore_probe(uni,reg):
    """Measure this emulator's FRSTOR limitation independently of our adapter.

    Unicorn 2.1.4 restores the numerical x87 state but not FIP/FDP. Do not
    assert those two metadata fields passed. Every other saved byte is exact;
    the separate native console probe checks all 108 bytes on the host CPU.
    """
    machine=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32)
    machine.mem_map(0x10000,4096);machine.mem_map(0x20000,4096)
    code=(bytes.fromhex('d9e8d9ebd9ee dd35')+struct.pack('<I',0x20000)
          +bytes.fromhex('d905')+struct.pack('<I',0x20800)
          +bytes.fromhex('dd25')+struct.pack('<I',0x20000)
          +bytes.fromhex('dd35')+struct.pack('<I',0x20100))
    machine.mem_write(0x10000,code);machine.mem_write(0x20800,struct.pack('<f',2))
    for name,value in (('FPCW',0x27f),('FPSW',0),('FPTAG',0xffff)):
        machine.reg_write(getattr(reg,'UC_X86_REG_'+name),value)
    machine.emu_start(0x10000,0x10000+len(code),count=16,timeout=1_000_000)
    if machine.reg_read(reg.UC_X86_REG_EIP)!=0x10000+len(code):raise ValueError('Incomplete x87 emulator probe')
    before=bytes(machine.mem_read(0x20000,108));after=bytes(machine.mem_read(0x20100,108))
    if any(a!=b for i,(a,b) in enumerate(zip(before,after)) if i not in {*range(12,16),*range(20,24)}):
        raise ValueError('Emulator failed numerical x87 state restoration')
    return [name for name,at in (('FIP',12),('FDP',20)) if before[at:at+4]!=after[at:at+4]]


class HandHookOracle:
    STOP=0x3000000;REFRESH=0x3001000;FPU_INIT=0x3002000;STACK=0x3100000
    ARENA=0x3900000;INPUT=0x3a00000;WORK=0x3b00000;CONTEXT=0x3c00000
    POSES=0x3d00000;MODEL=0x3e00000;VTABLE=0x3e01000

    def __init__(self,raw):
        if type(raw) is not bytes or len(raw)!=BINARY_SIZE or digest(raw)!=BINARY_SHA:
            raise ValueError('Unreviewed original hand hook image')
        import pefile
        import unicorn as uni
        from unicorn import x86_const as reg
        pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=BASE
                or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!=EXPORTS):
            raise ValueError('Unreviewed hand hook PE contract')
        if any(not hasattr(reg,'UC_X86_REG_'+name) for name in FPU_REGISTERS):
            raise ValueError('Emulator lacks required x87 state inspection')
        self.uni,self.reg=uni,reg;self.uc=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32)
        self.emulator_restore_limitations=emulator_restore_probe(uni,reg)
        self.mode=None;self.allowed=[];self.count=0;self.calls={};self.refresh_calls=0
        for address,size,permissions in ((BASE,(len(mapped)+4095)&~4095,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.STOP,0x3000,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.STACK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.ARENA,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.INPUT,0x3000,uni.UC_PROT_READ),
                (self.WORK,8192,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.CONTEXT,4096,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.POSES,8192,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.MODEL,8192,uni.UC_PROT_READ)):
            self.uc.mem_map(address,size,permissions)
        self.uc.mem_write(BASE,mapped)
        self.uc.mem_protect(BASE+0x5000,4096,uni.UC_PROT_READ|uni.UC_PROT_WRITE)
        self.uc.mem_write(self.REFRESH,bytes.fromhex('c20400')) # Explicit synthetic stand-in.
        self.uc.mem_write(self.FPU_INIT,bytes.fromhex('d9e8d9ebd9ee')) # fld1; fldpi; fldz.
        models=bytearray(8192)
        for offset in (0,0x200):struct.pack_into('<I',models,offset,self.VTABLE)
        struct.pack_into('<I',models,0x1000+0x24,self.REFRESH)
        self.uc.mem_write(self.MODEL,bytes(models));self.model_bytes=bytes(models)
        self.image_data=bytes(self.uc.mem_read(BASE+0x5000,4096))
        self.uc.hook_add(uni.UC_HOOK_CODE,self.on_code);self.uc.hook_add(uni.UC_HOOK_MEM_WRITE,self.on_write)

    def reg_read(self,name):return self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+name))

    def fpu_state(self):return {name:self.reg_read(name) for name in FPU_REGISTERS}

    def check_fpu(self):
        actual=self.fpu_state();differences=[k for k,v in self.expected_fpu.items() if actual[k]!=v]
        if any(k not in self.emulator_restore_limitations for k in differences):
            raise ValueError('Adapter changed a qualified x87 state field')
        return differences

    def on_code(self,uc,address,size,context):
        if self.mode=='fpu_init' and self.FPU_INIT<=address<address+size<=self.FPU_INIT+6:return
        if self.mode=='hook' and address==self.REFRESH and size==3:
            if struct.unpack('<I',uc.mem_read(self.reg_read('ESP')+4,4))[0]!=self.expected_integer['ESI']:
                raise ValueError('Adapter forwarded the wrong refresh model')
            for name,value in self.expected_integer.items():
                if self.reg_read(name)!=(self.VTABLE if name=='ECX' else value):
                    raise ValueError('Adapter changed register before refresh: '+name)
            self.fpu_differences_at_refresh=self.check_fpu()
            self.refresh_calls+=1;self.arena_at_refresh=bytes(uc.mem_read(self.ARENA,65536));return
        if self.mode not in ('configure','hook') or not BASE+0x1000<address<address+size<=CODE_END:
            raise ValueError('Hand hook instruction outside reviewed adapter or stand-in')
        for name,rva in EXPORTS.items():
            if address==BASE+rva:self.calls[name.decode()]=self.calls.get(name.decode(),0)+1
        if address==CALLBACK:self.calls['Hd2OnModelHandPose']=self.calls.get('Hd2OnModelHandPose',0)+1

    def on_write(self,uc,access,address,size,value,context):
        if self.mode not in ('configure','hook') or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),*self.allowed)):
            raise ValueError('Hand hook write outside current phase contract')

    def seed(self,data,arena,offsets,roles):
        if self.mode is not None or struct.unpack('<I',self.uc.mem_read(ACTIVE,4))[0]:
            raise ValueError('Unregister the diagnostic context before reseeding')
        if (not isinstance(data,dict) or type(arena) is not bytes or len(arena)!=65536 or not isinstance(offsets,list)
                or not isinstance(roles,list) or len(roles)!=11 or data.get('roles')!=roles[:5]
                or any(type(v) is not int or not 0<=v<65536 for v in offsets+roles)):
            raise ValueError('Invalid diagnostic hand hook fixture')
        count,source=encode_inputs(data)
        if len(offsets)!=count or not 11<=count<=128:raise ValueError('Invalid hand hook count')
        if any(v>=count for v in roles) or any(at+0x170>65536 for at in offsets):
            raise ValueError('Invalid hand hook fixture offset or role')
        source=bytearray(source);struct.pack_into('<11I',source,0x1b00,*roles)
        struct.pack_into('<'+'I'*count,source,0x2400,*offsets)
        self.source=bytes(source);self.count=count;self.offsets=offsets[:];self.roles=roles[:]
        self.uc.mem_write(self.INPUT,self.source);self.uc.mem_write(self.ARENA,arena)
        self.uc.mem_write(self.WORK,b'Z'*8192);self.uc.mem_write(self.POSES,b'Z'*8192)
        context=struct.pack('<16I',self.MODEL,self.ARENA,65536,self.INPUT+0x2400,count,self.INPUT+0x1800,
            self.INPUT+0x1b00,11,self.INPUT+0x1c00,self.INPUT+0x2000,self.POSES,self.WORK,WORK_SIZE,0,0,0)
        self.uc.mem_write(self.CONTEXT,context+bytes(4096-64))

    def invoke(self,entry,args,mode,*,model=None,control=0x27f):
        if self.mode is not None or mode not in ('configure','hook') or type(control) is not int or control not in (0x27f,0x37f):
            raise ValueError('Unreviewed hand adapter invocation')
        if (not isinstance(args,list) or any(type(v) is not int for v in args)
                or model not in (None,self.MODEL,self.MODEL+0x200)
                or (mode=='configure' and (entry!=BASE+EXPORTS[b'Hd2ConfigureHandHook'] or args not in ([0],[self.CONTEXT])))
                or (mode=='hook' and (entry!=ENTRY or args!=[]))):
            raise ValueError('Unreviewed hand adapter entry or arguments')
        self.uc.mem_write(self.STACK,bytes(65536));stack=self.STACK+0xf000
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        registers={'EAX':0x12345678,'EBX':0x23456781,'ECX':0x34567812,'EDX':0x45678123,
            'ESI':self.MODEL if model is None else model,'EDI':0x56781234,'EBP':0x67812345,'ESP':stack,
            'EFLAGS':0x402 if mode=='hook' else 2,'FPCW':control,'FPSW':0,'FPTAG':0xffff}
        for name,value in registers.items():self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.mode='fpu_init'
        try:self.uc.emu_start(self.FPU_INIT,self.FPU_INIT+6,count=3)
        finally:self.mode=None
        self.expected_integer={k:self.reg_read(k) for k in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP','EFLAGS')}
        self.expected_fpu=self.fpu_state();self.calls={};self.refresh_calls=0;self.arena_at_refresh=None
        self.mode=mode
        try:
            self.uc.emu_start(entry,self.STOP,count=2500000,timeout=5_000_000)
            if self.reg_read('EIP')!=self.STOP or self.reg_read('ESP')!=stack+4:
                raise ValueError('Hand adapter budget or stack cleanup differs')
            for name in ('EBX','ESI','EDI','EBP'):
                if self.reg_read(name)!=registers[name]:raise ValueError('Hand adapter callee-saved register changed')
        finally:self.mode=None
        return self.reg_read('EAX')

    def check_constants(self):
        data=bytes(self.uc.mem_read(BASE+0x5000,4096));offset=ACTIVE-(BASE+0x5000)
        if (data[:offset]!=self.image_data[:offset] or data[offset+4:]!=self.image_data[offset+4:]
                or bytes(self.uc.mem_read(self.INPUT,0x3000))!=self.source
                or bytes(self.uc.mem_read(self.MODEL,8192))!=self.model_bytes
                or bytes(self.uc.mem_read(self.WORK+WORK_SIZE,8192-WORK_SIZE))!=b'Z'*(8192-WORK_SIZE)
                or bytes(self.uc.mem_read(self.POSES+self.count*40,8192-self.count*40))!=b'Z'*(8192-self.count*40)):
            raise ValueError('Hand adapter changed constants, inputs, models or guards')

    def configure(self,registered=True):
        if type(registered) is not bool or not self.count:raise ValueError('Seed before configuring hook')
        arena=bytes(self.uc.mem_read(self.ARENA,65536));context=bytes(self.uc.mem_read(self.CONTEXT,4096))
        prior=bytes(self.uc.mem_read(ACTIVE,4))
        self.allowed=[(ACTIVE,ACTIVE+4),(self.CONTEXT+56,self.CONTEXT+64)]
        status=self.invoke(BASE+EXPORTS[b'Hd2ConfigureHandHook'],[self.CONTEXT if registered else 0],'configure')
        after=bytes(self.uc.mem_read(self.CONTEXT,4096));current=bytes(self.uc.mem_read(ACTIVE,4))
        if (status not in (0,1,2) or bytes(self.uc.mem_read(self.ARENA,65536))!=arena
                or after[:56]!=context[:56] or after[64:]!=context[64:]
                or (status and (after!=context or current!=prior))
                or (not status and not registered and after!=context)
                or (not status and registered and after[56:64]!=bytes(8))
                or (not status and current!=struct.pack('<I',self.CONTEXT if registered else 0))):
            raise ValueError('Diagnostic hook registration changed protected or failed state')
        self.check_constants();return status

    def frame(self,*,other_model=False,control=0x27f):
        if type(other_model) is not bool or not self.count:raise ValueError('Invalid hand hook frame')
        arena=bytes(self.uc.mem_read(self.ARENA,65536));context=bytes(self.uc.mem_read(self.CONTEXT,4096))
        self.allowed=[(self.CONTEXT+52,self.CONTEXT+64),(self.WORK,self.WORK+WORK_SIZE),(self.POSES,self.POSES+self.count*40)]
        for i in self.roles[5:]:
            at=self.ARENA+self.offsets[i];self.allowed.extend(((at+0xc0,at+0xd0),(at+0xe0,at+0xe4)))
        self.invoke(ENTRY,[],'hook',model=self.MODEL+(0x200 if other_model else 0),control=control)
        after=bytes(self.uc.mem_read(self.ARENA,65536));updated=bytes(self.uc.mem_read(self.CONTEXT,4096))
        busy,status,calls=struct.unpack_from('<3I',updated,52);old_calls=struct.unpack_from('<I',context,60)[0]
        attempted=(calls-old_calls)&0xffffffff
        if (self.refresh_calls!=1 or after!=self.arena_at_refresh or attempted not in (0,1)
                or updated[:52]!=context[:52] or updated[64:]!=context[64:]
                or (not attempted and updated!=context) or (attempted and busy)
                or ((not attempted or status) and after!=arena)):
            raise ValueError('Hand adapter changed protected, rejected or restored state')
        fpu_differences=self.check_fpu()
        if fpu_differences!=self.fpu_differences_at_refresh:raise ValueError('Refresh stand-in changed x87 metadata')
        self.check_constants()
        return after,{'status':status,'attempted':bool(attempted),'compiled_calls':dict(self.calls),
            'compiled_sha256':BINARY_SHA,'refresh_calls':self.refresh_calls,'integer_state_preserved_before_refresh':True,
            'x87_math_state_preserved_before_refresh':True,'x87_math_state_preserved_after_return':True,
            'x87_exception_addresses_qualified_in_emulator':not self.emulator_restore_limitations,
            'emulator_restore_limitations':self.emulator_restore_limitations[:],
            'x87_metadata_differences':fpu_differences,'input_and_guards_unchanged':True,
            'failed_or_skipped_arena_unchanged':True,'snapshot_collected_by_compiled_code':bool(attempted and status not in (6,7)),
            'refresh_is_synthetic_stand_in':True,'native_refresh_executed':False,'client_hook_installed':False,'game_started':False}
