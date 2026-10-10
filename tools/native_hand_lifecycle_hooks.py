"""Private entry interception of native membership before original mutations.

Only the pinned emulator image is patched. Refusal is a diagnostic CPU stop,
not a production client error path. No process, file or Windows DLL is patched.
"""
from copy import deepcopy
import struct

from build_modern_equipment_hose import digest
from build_native_hand_pipeline import invented_case
from native_hand_scatter_hook import HandScatterHookOracle,BASE as HOOK_BASE,ACTIVE
from native_hand_lifecycle import CONFIGURE,STATE_SIZE
from native_model_membership import ModelMembershipOracle,ADD,REMOVE,RELEASE

BASE=0x34000000;BINARY_SIZE=3072
BINARY_SHA='1d4c52aec99a023f957680f42a88343bb9c2150a7497273a06c34551dc7fe3a2'
CODE_END=BASE+0x15c5;WATCHED=BASE+0x2138
EXPORTS={b'Hd2WatchHandContext':0x1057,b'Hd2BeforeHandModelChange':0x114c,b'Hd2HandLifecycleSize':0x13d8,
    b'Hd2ConfigureLifecycleHooks':0x13e9,b'Hd2LifecycleAddEntry':0x14f4,b'Hd2LifecycleRemoveEntry':0x1505,
    b'Hd2LifecycleReleaseEntry':0x1516}
ARGUMENTS={b'Hd2WatchHandContext':4,b'Hd2BeforeHandModelChange':5,b'Hd2HandLifecycleSize':0,
    b'Hd2ConfigureLifecycleHooks':2,b'Hd2LifecycleAddEntry':0,b'Hd2LifecycleRemoveEntry':0,b'Hd2LifecycleReleaseEntry':0}
SITES={ADD:(bytes.fromhex('538b5c240c'),BASE+0x1527,BASE+0x1549),
       REMOVE:(bytes.fromhex('5356578b7c2410'),BASE+0x155c,BASE+0x157e),
       RELEASE:(bytes.fromhex('568b742408'),BASE+0x1593,BASE+0x15b2)}
REGISTERS=('EAX','EBX','ECX','EDX','ESI','EDI','EBP','EFLAGS','ESP')


def patch_bytes(site,original):
    if type(site) is not int or site not in SITES or type(original) is not bytes or original!=SITES[site][0]:
        raise ValueError('Unreviewed lifecycle entry bytes or site')
    return b'\xe8'+struct.pack('<i',SITES[site][1]-(site+5))+b'\x90'*(len(original)-5)


class LifecycleRefusal(ValueError):pass


class NativeHandLifecycleHooksOracle(ModelMembershipOracle):
    STATE=0x4b00000

    def __init__(self,library,collection_raw,hook_raw,lifecycle_raw):
        if type(lifecycle_raw) is not bytes or len(lifecycle_raw)!=BINARY_SIZE or digest(lifecycle_raw)!=BINARY_SHA:
            raise ValueError('Unreviewed native lifecycle delivery image')
        self.adapter=None;self.setup_active=False;self.guard_executing=False;self.patched=False;self.entries=[]
        super().__init__(library,collection_raw)
        self.adapter=HandScatterHookOracle(hook_raw,self)
        import pefile
        pe=pefile.PE(data=lifecycle_raw);mapped=pe.get_memory_mapped_image()
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=BASE or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!=EXPORTS):
            raise ValueError('Unreviewed lifecycle delivery PE contract')
        self.uc.mem_map(BASE,(len(mapped)+4095)&~4095,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC);self.uc.mem_write(BASE,mapped)
        self.uc.mem_protect(BASE+0x2000,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_map(self.STATE,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_write(self.STATE,bytes(STATE_SIZE)+b'Z'*(4096-STATE_SIZE))
        self.pristine_image=self.native_image;self.delivery_data=bytes(self.uc.mem_read(BASE+0x2000,4096))
        self.delivery_calls={};self.prologue_checks=0
        for site,(original,_,_) in SITES.items():
            if bytes(self.uc.mem_read(site,len(original)))!=original:raise ValueError('Native lifecycle entry differs')

    def set_patches(self,enabled):
        if type(enabled) is not bool or self.phase is not None or self.setup_active or self.entries:
            raise ValueError('Active or invalid lifecycle patch change')
        if bytes(self.uc.mem_read(0x10000000,self.native_size))!=self.native_image:raise ValueError('Lifecycle image changed outside patch scope')
        for site,(original,_,_) in SITES.items():
            expected=patch_bytes(site,original) if self.patched else original
            if bytes(self.uc.mem_read(site,len(original)))!=expected:raise ValueError('Lifecycle patch bytes differ')
            self.uc.mem_write(site,patch_bytes(site,original) if enabled else original)
            self.uc.ctl_remove_cache(site,site+0x100)
        self.patched=enabled;self.native_image=bytes(self.uc.mem_read(0x10000000,self.native_size))
        if not enabled and self.native_image!=self.pristine_image:raise ValueError('Lifecycle image not fully restored')

    def on_code(self,uc,address,size,context):
        if self.collector is not None and self.collector.active:return super().on_code(uc,address,size,context)
        if self.adapter is not None and self.adapter.mode is not None:return self.adapter.on_code(uc,address,size,context)
        # Unicorn may report a sentinel instruction size for UD2. Match the
        # pinned trap address/bytes before applying ordinary code-span bounds.
        if any(address==row[2] for row in SITES.values()):
            if self.phase!='membership' or not self.entries or bytes(uc.mem_read(address,2))!=b'\x0f\x0b':
                raise ValueError('Unexpected lifecycle diagnostic trap')
            raise LifecycleRefusal('Lifecycle stopped before forwarding an unsafe native mutation')
        is_guard=BASE+0x1000<address<address+size<=CODE_END
        is_registry=HOOK_BASE+0x5314<=address<address+size<=HOOK_BASE+0x54b1
        if is_guard or is_registry:
            if not self.setup_active and self.phase!='membership':raise ValueError('Lifecycle guard outside explicit setup or native event')
            self.guard_executing=True
            for name,rva in EXPORTS.items():
                if address==BASE+rva:self.delivery_calls[name.decode()]=self.delivery_calls.get(name.decode(),0)+1
            if address==CONFIGURE:self.delivery_calls['Hd2ConfigureHandHook']=self.delivery_calls.get('Hd2ConfigureHandHook',0)+1
            return
        self.guard_executing=False
        if self.patched and address in SITES:
            stack=self.uc.reg_read(self.reg.UC_X86_REG_ESP)
            args=struct.unpack('<'+'I'*(1 if address==RELEASE else 2),uc.mem_read(stack+4,4 if address==RELEASE else 8))
            state=self.guard_state();target=args[0] if address==RELEASE else args[1]
            matched=bool(state[0] and (args[0]==self.MODELS[0] or target in self.watched_nodes))
            self.entries.append({'site':address,'registers':{k:self.adapter.reg_read(k) for k in REGISTERS},
                                 'args':args,'fpu':self.adapter.fpu_state(),'state':state,'matched':matched})
        elif self.patched and any(address==site+len(row[0]) for site,row in SITES.items()):
            if not self.entries:raise ValueError('Lifecycle replay has no saved native entry')
            saved=self.entries.pop();site=saved['site'];registers=dict(saved['registers']);stack=registers['ESP']
            if address!=site+len(SITES[site][0]):raise ValueError('Lifecycle replay returned to another native entry')
            if site==ADD:registers['ESP']-=4;registers['EBX']=saved['args'][1];pushed=('EBX',)
            elif site==REMOVE:registers['ESP']-=12;registers['EDI']=saved['args'][0];pushed=('EBX','ESI','EDI')
            else:registers['ESP']-=4;registers['ESI']=saved['args'][0];pushed=('ESI',)
            if any(self.adapter.reg_read(k)!=v for k,v in registers.items()) or self.adapter.fpu_state()!=saved['fpu']:
                raise ValueError('Lifecycle replay changed native integer, flags or x87 state')
            if saved['matched']:
                event={ADD:1,REMOVE:2,RELEASE:3}[site]
                old=saved['state']
                if self.guard_state()!=(0,0,old[2],event,old[4]+1) or struct.unpack('<I',uc.mem_read(ACTIVE,4))[0]:
                    raise ValueError('Lifecycle registry not retired before first original mutation')
            elif self.guard_state()!=saved['state']:
                raise ValueError('Unrelated native entry changed lifecycle state')
            for i,key in enumerate(pushed):
                if struct.unpack('<I',uc.mem_read(stack-4*(i+1),4))[0]!=saved['registers'][key]:raise ValueError('Lifecycle replay saved wrong native register')
            self.prologue_checks+=1
        return super().on_code(uc,address,size,context)

    def on_write(self,uc,access,address,size,value,context):
        if self.collector is not None and self.collector.active:return super().on_write(uc,access,address,size,value,context)
        if self.adapter is not None and self.adapter.mode is not None:return self.adapter.on_write(uc,access,address,size,value,context)
        if self.guard_executing or self.setup_active:
            if not any(a<=address and address+size<=b for a,b in ((self.STACK,self.STACK+65536),
                    (self.STATE,self.STATE+STATE_SIZE),(WATCHED,WATCHED+4),(ACTIVE,ACTIVE+4),
                    (self.adapter.CONTEXT+44,self.adapter.CONTEXT+52))):
                raise ValueError('Lifecycle delivery wrote outside state or registry metadata')
            return
        return super().on_write(uc,access,address,size,value,context)

    def setup_call(self,name,args):
        if (self.setup_active or self.phase is not None or name not in ARGUMENTS or not isinstance(args,list)
                or len(args)!=ARGUMENTS[name] or any(type(v) is not int or not 0<=v<=0xffffffff for v in args)):
            raise ValueError('Invalid lifecycle setup invocation')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        for key,value in {'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EBX':0x12345678,'ESI':0x23456781,
                          'EDI':0x34567812,'EBP':0x45678123,'EFLAGS':2}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+key),value)
        self.setup_active=True
        try:
            self.uc.emu_start(BASE+EXPORTS[name],self.STOP,count=100000,timeout=1_000_000)
            if self.adapter.reg_read('EIP')!=self.STOP or self.adapter.reg_read('ESP')!=stack+4:raise ValueError('Lifecycle setup stack mismatch')
            for key,value in (('EBX',0x12345678),('ESI',0x23456781),('EDI',0x34567812),('EBP',0x45678123)):
                if self.adapter.reg_read(key)!=value:raise ValueError('Lifecycle setup changed callee-saved register')
            return self.adapter.reg_read('EAX')
        finally:self.setup_active=False;self.guard_executing=False

    def guard_state(self):return struct.unpack('<5I',self.uc.mem_read(self.STATE,STATE_SIZE))

    def watch_model(self,count):
        if self.guard_state()[0]:raise ValueError('Retire before rebuilding native model binding')
        self.collect(0,0)
        h=self.adapter;h.seed(*invented_case(count),alignment=4,model_identity=self.MODELS[0])
        for offset,pointer in ((4,self.collector.OUTPUT+8),(12,self.collector.OUTPUT+0x408),(16,self.collector.OUTPUT+0x608)):
            self.uc.mem_write(h.CONTEXT+offset,struct.pack('<I',pointer))
        self.watched_nodes=[struct.unpack('<I',self.uc.mem_read(self.collector.OUTPUT+8+i*8,4))[0] for i in range(count)]
        if self.setup_call(b'Hd2WatchHandContext',[self.STATE,STATE_SIZE,h.CONTEXT,CONFIGURE]):raise ValueError('Native lifecycle watch failed')

    def operation(self,*args):
        try:
            result=super().operation(*args)
            if self.entries:raise ValueError('Lifecycle native entry did not replay its prologue')
            return result
        finally:
            self.guard_executing=False
            # A refused diagnostic entry leaves a saved frame, never a native
            # mutation. The stopped CPU is reset by the next explicit call.
            if self.entries:self.entries.clear()

    def release_retained(self,node):
        if self.phase is not None or type(node) is not int or not 0<=node<len(self.pointers) or self.state['refs'][node]<2:
            raise ValueError('Unreviewed final or nested release')
        expected=deepcopy(self.state);expected['refs'][node]-=1;self.check_pages(self.state)
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<2I',self.STOP,self.pointers[node]))
        for key,value in {'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EBX':0x12345678,'ESI':0x23456781,
                          'EDI':0x34567812,'EBP':0x45678123,'EFLAGS':0x402}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+key),value)
        self.phase='membership';self.calls={};self.writes=((self.pointers[node]+0xe4,self.pointers[node]+0xe6),)
        try:
            self.uc.emu_start(RELEASE,self.STOP,count=100000,timeout=1_000_000)
            if (self.adapter.reg_read('EIP')!=self.STOP or self.adapter.reg_read('ESP')!=stack+8
                    or self.adapter.reg_read('EAX')!=expected['refs'][node] or self.entries):
                raise ValueError('Retained release return contract differs')
            for key,value in (('EBX',0x12345678),('ESI',0x23456781),('EDI',0x34567812),('EBP',0x45678123)):
                if self.adapter.reg_read(key)!=value:raise ValueError('Retained release callee-saved register differs')
        finally:self.phase=None;self.writes=();self.guard_executing=False;self.entries=[]
        self.check_pages(expected);self.state=expected

    def scenario(self,count):
        self.seed(count);self.delivery_calls={};self.prologue_checks=0
        self.uc.mem_write(self.STATE,bytes(STATE_SIZE)+b'Z'*(4096-STATE_SIZE))
        if self.setup_call(b'Hd2ConfigureLifecycleHooks',[self.STATE,STATE_SIZE]):raise ValueError('Native lifecycle delivery setup failed')
        for node in range(count):self.operation('add',0,node)
        self.watch_model(count)
        if self.setup_call(b'Hd2ConfigureLifecycleHooks',[0,0])!=1:raise ValueError('Active lifecycle hook state was replaced')
        self.set_patches(True)
        rows=[]
        try:
            self.adapter.mode='fpu_init'
            try:self.uc.emu_start(self.adapter.FPU_INIT,self.adapter.FPU_INIT+6,count=3)
            finally:self.adapter.mode=None
            self.operation('add',0,count//2)
            if self.guard_state()!=(0,0,1,1,1):raise ValueError('Native add did not retire before mutation')
            rows.append({'operation':'same_model_add','state':list(self.guard_state())})
            self.watch_model(count);self.operation('remove',0,count//2)
            if self.guard_state()!=(0,0,2,2,2):raise ValueError('Native remove did not retire before mutation')
            rows.append({'operation':'remove','state':list(self.guard_state())})
            self.operation('add',0,count//2);self.watch_model(count)
            self.uc.mem_write(self.adapter.CONTEXT+40,struct.pack('<I',1));before=self.guard_state()
            try:self.operation('remove',0,0)
            except LifecycleRefusal:pass
            else:raise ValueError('Busy guard forwarded native mutation')
            if self.guard_state()!=before:raise ValueError('Busy native guard changed lifecycle state')
            self.check_pages(self.state);self.uc.mem_write(self.adapter.CONTEXT+40,bytes(4))
            rows.append({'operation':'busy_remove','native_operation_stopped':True})
            # Transfer to the other model matches the node, not the target
            # model identity. Its implicit old-owner removal/release execute
            # only after the context has been retired by the outer add.
            self.operation('add',1,0)
            if self.guard_state()!=(0,0,3,1,3):raise ValueError('Native transfer did not retire old-model node')
            rows.append({'operation':'transfer','state':list(self.guard_state())})
            self.operation('add',0,0);self.watch_model(count)
            self.release_retained(count-1)
            if self.guard_state()!=(0,0,4,3,4):raise ValueError('Native positive release did not retire watched node')
            rows.append({'operation':'positive_reference_release','state':list(self.guard_state()),'remaining_references':self.state['refs'][-1]})
            self.check_pages(self.state)
        finally:
            self.entries=[];self.guard_executing=False;self.set_patches(False)
        if self.setup_call(b'Hd2ConfigureLifecycleHooks',[0,0]):raise ValueError('Native lifecycle delivery final detach failed')
        if bytes(self.uc.mem_read(self.STATE+STATE_SIZE,4096-STATE_SIZE))!=b'Z'*(4096-STATE_SIZE):raise ValueError('Lifecycle state guard changed')
        current=bytes(self.uc.mem_read(BASE+0x2000,4096));at=WATCHED-(BASE+0x2000)
        if current!=self.delivery_data or struct.unpack('<I',self.uc.mem_read(ACTIVE,4))[0]:
            raise ValueError('Lifecycle delivery or correction registry not fully retired')
        self.adapter.check_constants()
        return {'nodes':count,'operations':rows,'delivery_calls':self.delivery_calls,'native_prologue_checks':self.prologue_checks,
            'native_entry_notifications_delivered':True,'busy_mutation_stopped_before_original_prologue':True,
            'native_image_fully_restored':True,'integer_flags_and_x87_preserved_at_native_resume':True,
            'collector_and_registry_share_native_objects':True,'hand_correction_executed':False,
            'native_allocator_or_destructor_executed':False,'game_started':False,'game_modified':False,
            'production_client_refusal_handling_qualified':False,'live_model_lifetime_qualified':False}
