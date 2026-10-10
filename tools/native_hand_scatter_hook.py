"""Original scatter adapter, caller-owned registry and separated node allocations."""
import struct

from native_hand_scatter import HandScatterOracle,WORK_SIZE
from native_hand_hook import HandHookOracle,emulator_restore_probe

BASE=0x2c000000
BINARY_SHA='1f123fb2de5ae8c222aa4bf3191ec417c5507d3b77dbab0d0787410bf5ed91d9'
BINARY_SIZE=20480
ENTRY=BASE+0x5617
CALLBACK=BASE+0x54b1
ACTIVE=BASE+0x6374
CODE_END=BASE+0x5640
EXPORTS={**HandScatterOracle.EXPORTS,b'Hd2ConfigureHandHook':0x5403,b'Hd2HandHookEntry':0x5606}


class HandScatterHookOracle(HandScatterOracle):
    BASE=BASE;BINARY_SHA=BINARY_SHA;BINARY_SIZE=BINARY_SIZE;CODE_END=CODE_END;EXPORTS=EXPORTS
    ENTRY=ENTRY;CALLBACK=CALLBACK;ACTIVE=ACTIVE
    REFRESH=0x3001000;FPU_INIT=0x3002000;CONTEXT=0x4600000;VTABLE=HandScatterOracle.MODEL+0x1000
    reg_read=HandHookOracle.reg_read
    fpu_state=HandHookOracle.fpu_state
    check_fpu=HandHookOracle.check_fpu

    def __init__(self,raw,parent=None):
        self.mode=None;self.count=0
        super().__init__(raw,parent)
        self.emulator_restore_limitations=emulator_restore_probe(self.uni,self.reg)
        for at,size,permissions in ((self.REFRESH,8192,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC),
                (self.CONTEXT,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE),
                (self.MODEL,8192,self.uni.UC_PROT_READ)):
            self.uc.mem_map(at,size,permissions)
        self.uc.mem_protect(BASE+0x6000,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_write(self.REFRESH,bytes.fromhex('c20400'))
        self.uc.mem_write(self.FPU_INIT,bytes.fromhex('d9e8d9ebd9ee'))
        models=bytearray(8192)
        for at in (0,0x200):struct.pack_into('<I',models,at,self.VTABLE)
        struct.pack_into('<I',models,0x1024,self.REFRESH)
        self.model_bytes=bytes(models);self.uc.mem_write(self.MODEL,self.model_bytes)
        self.image_data=bytes(self.uc.mem_read(BASE+0x6000,4096))

    def on_code(self,uc,address,size,context):
        if self.mode=='fpu_init' and self.FPU_INIT<=address<address+size<=self.FPU_INIT+6:return
        if self.mode=='hook' and address==self.REFRESH and size==3:
            if struct.unpack('<I',uc.mem_read(self.reg_read('ESP')+4,4))[0]!=self.expected_integer['ESI']:
                raise ValueError('Scatter adapter forwarded wrong refresh model')
            for name,value in self.expected_integer.items():
                if self.reg_read(name)!=(self.VTABLE if name=='ECX' else value):
                    raise ValueError('Scatter adapter changed integer state before refresh')
            self.check_fpu();self.refresh_calls+=1
            self.at_refresh=[bytes(uc.mem_read(p,4096)) for p in self.pages];return
        if address==CALLBACK:self.calls['Hd2OnModelHandPose']=self.calls.get('Hd2OnModelHandPose',0)+1
        return super().on_code(uc,address,size,context)

    def on_write(self,uc,access,address,size,value,context):
        if self.mode is not None:
            if self.mode not in ('configure','hook') or not any(a<=address and address+size<=b for a,b in
                    ((self.STACK,self.STACK+65536),*self.phase_writes)):
                raise ValueError('Scatter adapter write outside current phase')
            return
        return super().on_write(uc,access,address,size,value,context)

    def seed(self,*args,**kwargs):
        if self.mode is not None or struct.unpack('<I',self.uc.mem_read(ACTIVE,4))[0]:
            raise ValueError('Unregister scattered model before reseeding')
        result=super().seed(*args,**kwargs)
        # model, views, count, parents, roles, role_count, rest, grips, work, bytes;
        # busy, last status and call count complete the caller-owned context.
        self.uc.mem_write(self.CONTEXT,struct.pack('<13I',*result[0],0,0,0)+bytes(4096-52))
        return result

    def invoke_adapter(self,*,registered=None,other_model=False,control=0x27f):
        if (self.mode is not None or self.active or not self.count or type(other_model) is not bool
                or type(control) is not int or control not in (0x27f,0x37f)
                or (registered is not None and type(registered) is not bool)):
            raise ValueError('Invalid scatter adapter invocation')
        configure=registered is not None
        stack=self.STACK+0xf000;args=[self.CONTEXT if registered else 0] if configure else []
        self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        for name,value in {'ESP':stack,'EAX':0x12345678,'EBX':0x23456781,'ECX':0x34567812,'EDX':0x45678123,
                'ESI':self.MODEL+(0x200 if other_model else 0),'EDI':0x56781234,'EBP':0x67812345,
                'EFLAGS':2 if configure else 0x402,'FPCW':control,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.mode='fpu_init'
        try:self.uc.emu_start(self.FPU_INIT,self.FPU_INIT+6,count=3)
        finally:self.mode=None
        self.expected_integer={k:self.reg_read(k) for k in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP','EFLAGS')}
        self.expected_fpu=self.fpu_state();self.calls={};self.refresh_calls=0;self.at_refresh=None
        self.return_to_scatter=None;self.late_mutation=None
        self.mode='configure' if configure else 'hook';self.active=True
        self.phase_writes=[(ACTIVE,ACTIVE+4),(self.CONTEXT+44,self.CONTEXT+52)] if configure else [
            (self.CONTEXT+40,self.CONTEXT+52),(self.WORK,self.WORK+WORK_SIZE),*self.allowed]
        try:
            self.uc.emu_start(BASE+EXPORTS[b'Hd2ConfigureHandHook'] if configure else ENTRY,self.STOP,
                              count=6_000_000,timeout=10_000_000)
            if self.reg_read('EIP')!=self.STOP or self.reg_read('ESP')!=stack+4:raise ValueError('Scatter adapter return contract differs')
            for name in ('EBX','ESI','EDI','EBP'):
                if self.reg_read(name)!=self.expected_integer[name]:raise ValueError('Scatter adapter callee-saved register differs')
            if not configure:self.check_fpu()
            return self.reg_read('EAX')
        finally:self.active=False;self.mode=None

    def check_constants(self):
        current=bytes(self.uc.mem_read(BASE+0x6000,4096));at=ACTIVE-(BASE+0x6000)
        if (current[:at]!=self.image_data[:at] or current[at+4:]!=self.image_data[at+4:]
                or bytes(self.uc.mem_read(self.INPUT,4096))!=self.source
                or bytes(self.uc.mem_read(self.MODEL,8192))!=self.model_bytes
                or bytes(self.uc.mem_read(self.WORK+WORK_SIZE,65536-WORK_SIZE))!=b'Z'*(65536-WORK_SIZE)):
            raise ValueError('Scatter adapter changed constants or guards')

    def configure(self,registered=True):
        if type(registered) is not bool:raise ValueError('Expected explicit registration switch')
        before=bytes(self.uc.mem_read(self.CONTEXT,4096));old=bytes(self.uc.mem_read(ACTIVE,4))
        nodes=[bytes(self.uc.mem_read(p,4096)) for p in self.pages]
        status=self.invoke_adapter(registered=registered)
        after=bytes(self.uc.mem_read(self.CONTEXT,4096));active=bytes(self.uc.mem_read(ACTIVE,4))
        if (status not in (0,1,2) or after[:44]!=before[:44] or after[52:]!=before[52:]
                or (status and (after!=before or active!=old)) or (not status and not registered and after!=before)
                or (not status and registered and after[44:52]!=bytes(8))
                or (not status and active!=struct.pack('<I',self.CONTEXT if registered else 0))
                or nodes!=[bytes(self.uc.mem_read(p,4096)) for p in self.pages]):
            raise ValueError('Scatter adapter registration changed protected state')
        self.check_constants();return status

    def frame(self,*,other_model=False,control=0x27f):
        before=[bytes(self.uc.mem_read(p,4096)) for p in self.pages]
        old=bytes(self.uc.mem_read(self.CONTEXT,4096));self.invoke_adapter(other_model=other_model,control=control)
        after=[bytes(self.uc.mem_read(p,4096)) for p in self.pages];current=bytes(self.uc.mem_read(self.CONTEXT,4096))
        busy,status,calls=struct.unpack_from('<3I',current,40);attempted=(calls-struct.unpack_from('<I',old,48)[0])&0xffffffff
        if (attempted not in (0,1) or self.refresh_calls!=1 or after!=self.at_refresh
                or current[:40]!=old[:40] or current[52:]!=old[52:] or (not attempted and current!=old)
                or (attempted and busy) or ((not attempted or status) and after!=before)):
            raise ValueError('Scatter adapter failed or skipped frame changed protected state')
        for i,(a,b) in enumerate(zip(before,after)):
            allowed={at for lo,hi in self.allowed for at in range(lo-self.pages[i],hi-self.pages[i])}
            if any(x!=y and at not in allowed for at,(x,y) in enumerate(zip(a,b))):raise ValueError('Scatter adapter changed unrelated node bytes')
        self.check_constants()
        return before,after,{'status':status,'attempted':bool(attempted),'compiled_calls':dict(self.calls),
            'refresh_calls':self.refresh_calls,'integer_and_x87_math_state_preserved':True,
            'x87_exception_addresses_qualified_in_emulator':not self.emulator_restore_limitations,
            'emulator_restore_limitations':self.emulator_restore_limitations[:],
            'input_and_guards_unchanged':True,'refresh_is_synthetic_stand_in':True,
            'client_hook_installed':False,'game_started':False}
