"""Original explicit lifetime guard coupled to the real compiled hand registry."""
import struct

from build_modern_equipment_hose import digest
from native_hand_scatter_hook import HandScatterHookOracle,BASE as HOOK_BASE,ACTIVE,EXPORTS as HOOK_EXPORTS

BASE=0x32000000;BINARY_SIZE=2048
BINARY_SHA='8990a6f58a1d7c96a070117787731b76169fa5506b1042349fad985279486d3f'
CODE_END=BASE+0x13f0;STATE_SIZE=20
EXPORTS={b'Hd2WatchHandContext':0x1057,b'Hd2BeforeHandModelChange':0x114c,b'Hd2HandLifecycleSize':0x13d8}
ARGUMENTS={b'Hd2WatchHandContext':4,b'Hd2BeforeHandModelChange':5,b'Hd2HandLifecycleSize':0}
CONFIGURE=HOOK_BASE+HOOK_EXPORTS[b'Hd2ConfigureHandHook']


class HandLifecycleOracle(HandScatterHookOracle):
    STATE=0x4b00000

    def __init__(self,hook_raw,lifecycle_raw):
        if type(lifecycle_raw) is not bytes or len(lifecycle_raw)!=BINARY_SIZE or digest(lifecycle_raw)!=BINARY_SHA:
            raise ValueError('Unreviewed hand lifecycle image')
        super().__init__(hook_raw)
        import pefile
        pe=pefile.PE(data=lifecycle_raw);mapped=pe.get_memory_mapped_image()
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=BASE or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!=EXPORTS):
            raise ValueError('Unreviewed lifecycle PE contract')
        self.uc.mem_map(BASE,(len(mapped)+4095)&~4095,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC)
        self.uc.mem_write(BASE,mapped)
        self.uc.mem_map(self.STATE,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_write(self.STATE,bytes(STATE_SIZE)+b'Z'*(4096-STATE_SIZE))

    def on_code(self,uc,address,size,context):
        if self.mode!='lifecycle':return super().on_code(uc,address,size,context)
        if not (BASE+0x1000<address<address+size<=CODE_END or HOOK_BASE+0x5314<=address<address+size<=HOOK_BASE+0x54b1):
            raise ValueError('Lifecycle instruction outside original guard and compiled registration')
        for name,entry in ((*( (k.decode(),BASE+v) for k,v in EXPORTS.items()),('Hd2ConfigureHandHook',CONFIGURE))):
            if address==entry:self.calls[name]=self.calls.get(name,0)+1

    def on_write(self,uc,access,address,size,value,context):
        if self.mode!='lifecycle':return super().on_write(uc,access,address,size,value,context)
        if not any(a<=address and address+size<=b for a,b in ((self.STACK,self.STACK+65536),
                (self.STATE,self.STATE+STATE_SIZE),(ACTIVE,ACTIVE+4),(self.CONTEXT+44,self.CONTEXT+52))):
            raise ValueError('Lifecycle write outside state and registration metadata')

    def invoke_guard(self,name,args):
        if (self.mode is not None or self.active or name not in ARGUMENTS or not isinstance(args,list)
                or len(args)!=ARGUMENTS[name] or any(type(v) is not int or not 0<=v<=0xffffffff for v in args)):
            raise ValueError('Invalid or nested lifecycle invocation')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        for key,value in {'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EBX':0x12345678,'ESI':0x23456781,
                          'EDI':0x34567812,'EBP':0x45678123,'EFLAGS':2}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+key),value)
        before=[bytes(self.uc.mem_read(p,4096)) for p in self.pages]
        self.mode='lifecycle';self.active=True;self.calls={}
        try:
            self.uc.emu_start(BASE+EXPORTS[name],self.STOP,count=100000,timeout=1_000_000)
            if self.reg_read('EIP')!=self.STOP or self.reg_read('ESP')!=stack+4:raise ValueError('Lifecycle stack/budget mismatch')
            for key,value in (('EBX',0x12345678),('ESI',0x23456781),('EDI',0x34567812),('EBP',0x45678123)):
                if self.reg_read(key)!=value:raise ValueError('Lifecycle callee-saved register differs')
            result=self.reg_read('EAX')
        finally:self.mode=None;self.active=False
        if (before!=[bytes(self.uc.mem_read(p,4096)) for p in self.pages]
                or bytes(self.uc.mem_read(self.STATE+STATE_SIZE,4096-STATE_SIZE))!=b'Z'*(4096-STATE_SIZE)):
            raise ValueError('Lifecycle changed native records or state guard')
        self.check_constants();return result

    def state(self):return struct.unpack('<5I',self.uc.mem_read(self.STATE,STATE_SIZE))
    def watch(self):return self.invoke_guard(b'Hd2WatchHandContext',[self.STATE,STATE_SIZE,self.CONTEXT,CONFIGURE])
    def event(self,model,node,kind):return self.invoke_guard(b'Hd2BeforeHandModelChange',[self.STATE,STATE_SIZE,model,node,kind])

    def retired_callback_probe(self):
        if self.state()[0] or struct.unpack('<I',self.uc.mem_read(ACTIVE,4))[0]:raise ValueError('Lifecycle has not retired registry')
        # A stale callback must not read the retired context, views, names or
        # node pages. CPU page permissions enforce this; no memory is freed.
        ranges=[(self.CONTEXT,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE),(self.INPUT,self.uni.UC_PROT_READ),
                *((page,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE) for page in self.pages)]
        for page,_ in ranges:self.uc.mem_protect(page,4096,0)
        try:
            self.invoke_adapter()
            if self.calls!={'Hd2OnModelHandPose':1} or self.refresh_calls!=1:
                raise ValueError('Retired callback used correction or skipped replay')
        finally:
            for page,permission in ranges:self.uc.mem_protect(page,4096,permission)
        return {'retired_context_views_and_nodes_cpu_inaccessible':True,'correction_calls':0,
                'refresh_calls':1,'refresh_is_synthetic_stand_in':True,'native_free_executed':False}
