"""Original named-node binder on caller-owned guarded records, no live discovery."""
import struct

from build_modern_equipment_hose import digest

BASE=0x2e000000
BINARY_SIZE=5120
BINARY_SHA='fd5cee2af99f7f76f52221ae4bf2be9afdf54543a5157fbc5e27441430a5a688'
CODE_END=BASE+0x1d50
SNAPSHOT_CHECK=BASE+0x1bd3
OUTPUT_SIZE=1588;WORK_SIZE=3636
EXPORTS={b'Hd2BuildHandModelBinding':0x11b9,b'Hd2HandBindingWorkspaceSize':0x1d3f,b'Hd2HandModelBindingSize':0x1d2e}
NAMES=['fpv_weapon','MOD_left_hand','MOD_right_hand','Bip01 L Clavicle','Bip01 L UpperArm',
       'Bip01 L Forearm','Bip01 L Hand','Bip01 R Clavicle','Bip01 R UpperArm','Bip01 R Forearm','Bip01 R Hand']
PARENTS=[-1,0,0,-1,3,4,5,-1,7,8,9]
ROLES=[0,1,2,5,9,4,5,6,8,9,10]


def reference_binding(model,records):
    """Independent stable topological scan of a validated supplied forest."""
    remaining=list(range(len(records)));order=[];by_pointer={r['pointer']:i for i,r in enumerate(records)}
    while remaining:
        ready=[]
        for i in remaining:
            p=records[i]['parent']
            if p==model or by_pointer.get(p) in order:order.append(i);ready.append(i)
        if not ready:raise ValueError('Unresolved binding hierarchy')
        remaining=[i for i in remaining if i not in ready]
    indices={records[i]['pointer']:j for j,i in enumerate(order)}
    names={records[i]['name']:j for j,i in enumerate(order)}
    result=bytearray(OUTPUT_SIZE);struct.pack_into('<II',result,0,model,len(records))
    for j,i in enumerate(order):
        record=records[i];struct.pack_into('<II',result,8+j*8,record['pointer'],record['bytes'])
        struct.pack_into('<i',result,0x408+j*4,-1 if record['parent']==model else indices[record['parent']])
    struct.pack_into('<11I',result,0x608,*(names[NAMES[i]] for i in ROLES))
    return bytes(result),order


class HandModelBindingOracle:
    STOP=0x3000000;STACK=0x3100000;INPUT=0x5000000;OUTPUT=0x5100000;WORK=0x5200000;NODES=0x5300000;MODEL=0x5700000
    BASE=BASE;BINARY_SIZE=BINARY_SIZE;BINARY_SHA=BINARY_SHA;CODE_END=CODE_END;SNAPSHOT_CHECK=SNAPSHOT_CHECK
    EXPORTS=EXPORTS;WORK_SIZE=WORK_SIZE;WORK_MAP_SIZE=4096
    ARGUMENTS={b'Hd2BuildHandModelBinding':7,b'Hd2HandBindingWorkspaceSize':0,b'Hd2HandModelBindingSize':0}

    def __init__(self,raw,parent=None):
        if type(raw) is not bytes or len(raw)!=self.BINARY_SIZE or digest(raw)!=self.BINARY_SHA:
            raise ValueError('Unreviewed original hand model binding image')
        import pefile
        import unicorn as uni
        from unicorn import x86_const as reg
        pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=self.BASE
                or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!=self.EXPORTS):
            raise ValueError('Unreviewed hand binding PE contract')
        self.uni,self.reg=uni,reg;self.uc=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32) if parent is None else parent.uc
        self.active=False;self.calls={};self.output_writes=0;self.late_fault=None;self.injected=False
        for at,size,permissions in ((self.BASE,(len(mapped)+4095)&~4095,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.STOP,4096,uni.UC_PROT_READ|uni.UC_PROT_EXEC),(self.STACK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.INPUT,4096,uni.UC_PROT_READ),(self.OUTPUT,4096,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.WORK,self.WORK_MAP_SIZE,uni.UC_PROT_READ|uni.UC_PROT_WRITE)):
            if parent is not None and at in (self.STOP,self.STACK):continue
            self.uc.mem_map(at,size,permissions)
        self.uc.mem_write(self.BASE,mapped)
        if parent is None:
            for i in range(128):self.uc.mem_map(self.NODES+i*0x2000,4096,uni.UC_PROT_READ)
            self.uc.hook_add(uni.UC_HOOK_CODE,self.on_code);self.uc.hook_add(uni.UC_HOOK_MEM_WRITE,self.on_write)

    def on_code(self,uc,address,size,context):
        if not self.active or not self.BASE+0x1000<address<address+size<=self.CODE_END:
            raise ValueError('Binding instruction outside reviewed original code')
        for name,rva in self.EXPORTS.items():
            if address==self.BASE+rva:self.calls[name.decode()]=self.calls.get(name.decode(),0)+1
        if address==self.SNAPSHOT_CHECK and self.late_fault is not None:
            at,value=self.late_fault;uc.mem_write(at,struct.pack('<I',value));self.injected=True;self.late_fault=None

    def on_write(self,uc,access,address,size,value,context):
        if not self.active or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),(self.WORK,self.WORK+self.WORK_SIZE),(self.OUTPUT,self.OUTPUT+OUTPUT_SIZE))):
            raise ValueError('Binding write outside result, workspace or stack')
        if self.OUTPUT<=address<self.OUTPUT+OUTPUT_SIZE:self.output_writes+=1

    def invoke(self,entry,args):
        allowed={self.BASE+self.EXPORTS[name]:count for name,count in self.ARGUMENTS.items()}
        if (self.active or entry not in allowed or not isinstance(args,list)
                or len(args)!=allowed[entry]
                or any(type(v) is not int or not 0<=v<=0xffffffff for v in args)):
            raise ValueError('Invalid or nested binding invocation')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        for name,value in {'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EBX':0x12345678,'ESI':0x23456781,
                'EDI':0x34567812,'EBP':0x45678123,'EFLAGS':2}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.active=True;self.calls={};self.output_writes=0
        try:
            self.uc.emu_start(entry,self.STOP,count=6_000_000,timeout=10_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+4:
                raise ValueError('Binding budget or stack mismatch')
            for name,value in (('EBX',0x12345678),('ESI',0x23456781),('EDI',0x34567812),('EBP',0x45678123)):
                if self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+name))!=value:raise ValueError('Binding changed callee-saved register')
            return self.uc.reg_read(self.reg.UC_X86_REG_EAX)
        finally:self.active=False

    def bind(self,model,records,*,overrides=None):
        if (self.active or type(model) is not int or not 0x1000<=model<=0xffffffff or model&3
                or not isinstance(records,list) or not 11<=len(records)<=128):raise ValueError('Invalid binding fixture')
        source=bytearray(4096)
        for i,row in enumerate(records):struct.pack_into('<4I',source,i*16,row['pointer'],row['bytes'],row['name_pointer'],row['name_bytes'])
        args=[model,self.INPUT,len(records),self.OUTPUT,OUTPUT_SIZE,self.WORK,WORK_SIZE]
        if overrides:
            if any(type(i) is not int or i not in (0,2,4,6) or type(v) is not int for i,v in overrides.items()):
                raise ValueError('Unreviewed binding ABI override')
            for i,v in overrides.items():args[i]=v
        self.uc.mem_write(self.INPUT,bytes(source));self.uc.mem_protect(self.OUTPUT,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_write(self.OUTPUT,b'Z'*4096);self.uc.mem_write(self.WORK,b'Z'*4096)
        for name,size in ((b'Hd2HandModelBindingSize',OUTPUT_SIZE),(b'Hd2HandBindingWorkspaceSize',WORK_SIZE)):
            if self.invoke(BASE+EXPORTS[name],[])!=size:raise ValueError('Binding workspace/output ABI differs')
        status=self.invoke(BASE+EXPORTS[b'Hd2BuildHandModelBinding'],args)
        raw=bytes(self.uc.mem_read(self.OUTPUT,OUTPUT_SIZE))
        if (bytes(self.uc.mem_read(self.INPUT,4096))!=bytes(source)
                or bytes(self.uc.mem_read(self.OUTPUT+OUTPUT_SIZE,4096-OUTPUT_SIZE))!=b'Z'*(4096-OUTPUT_SIZE)
                or bytes(self.uc.mem_read(self.WORK+WORK_SIZE,4096-WORK_SIZE))!=b'Z'*(4096-WORK_SIZE)
                or (status and (raw!=b'Z'*OUTPUT_SIZE or self.output_writes))):
            raise ValueError('Binding changed source/guard or failed output')
        order=None
        if not status:
            expected,order=reference_binding(model,records)
            if raw!=expected:raise ValueError('Compiled binding differs from independent topology/role reference')
        self.uc.mem_protect(self.OUTPUT,4096,self.uni.UC_PROT_READ)
        return raw,order,{'status':status,'compiled_calls':dict(self.calls),'output_write_operations':self.output_writes,
            'source_and_guards_unchanged':True,'failed_output_unchanged':True,'native_nodes_not_written':True,
            'adversarial_metadata_change_injected':self.injected,'live_model_discovery_implemented':False,'game_started':False}
