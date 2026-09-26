"""Bounded offline proof of weapon-to-sound bank/index argument flow.

Only reviewed getter/argument/append blocks execute, never playback, stream
loading, audio APIs or the complete weapon operation. All objects are private
emulator data. The source executable and decompressed image remain untouched.
"""
import struct
from item_native_contract import Oracle
from item_native_layout import decode_record

SOUND_RANGES=((0x7d610b,0x7d6111),(0x7d6116,0x7d6132),
              (0x7e06f0,0x7e06f4),(0x7e07f0,0x7e07f4),
              (0x7d50d5,0x7d5103),(0x4392d5,0x4392e5),(0x43226e,0x43227e),
              (0x4326d0,0x432704))


class SoundOracle(Oracle):
    def on_code(self,uc,address,size,context):
        if any(a<=address and address+size<=b for a,b in SOUND_RANGES):return
        super().on_code(uc,address,size,context)

    def block(self,start,end):
        self.uc.emu_start(start,end,count=96,timeout=1_000_000)
        if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=end:
            raise ValueError('Sound argument block left its reviewed bounds')

    def lookup(self,bank,index,counts):
        if (not isinstance(counts,(tuple,list)) or not 1<=len(counts)<=16
                or any(type(n) is not int or not 0<=n<=256 for n in counts)
                or any(type(n) is not int or not 0<=n<=0xffffffff for n in (bank,index))):
            raise ValueError('Synthetic sound lookup outside bounded domain')
        if self.get(0x80f844)!=0x4326d0:raise ValueError('Changed final sound manager lookup method')
        self.allocations.clear();self.next_address=self.HEAP
        array=self.allocate(4*len(counts))
        for b,count in enumerate(counts):
            owner=self.allocate(20);entries=self.allocate(max(4,count*4))
            self.put(array+b*4,owner);self.put(owner+4,entries);self.put(owner+0xc,count)
            for i in range(count):self.put(entries+i*4,0x50000000+b*4096+i*4)
        previous={at:self.get(at) for at in (0x89994c,0x899954)}
        try:
            self.put(0x89994c,array);self.put(0x899954,len(counts))
            self.call(0x4326d0,0,bank,index)
            observed=self.uc.reg_read(self.reg.UC_X86_REG_EAX)
        finally:
            for at,value in previous.items():self.put(at,value)
        valid=bank<len(counts) and index<counts[bank]
        expected=0x50000000+bank*4096+index*4 if valid else 0
        if observed!=expected:raise ValueError('Native synthetic sound lookup differs from ordered banks')
        return {'bank':bank,'index':index,'entry_present':valid,
                'native_synthetic_lookup_matches':True,'entry_sentinel_dereferenced':False}

    def selection(self,raw,slot):
        layout=decode_record(raw);action=layout['actions'][0]
        if layout['kind']!=1 or action['selector']!=4:raise ValueError('Expected Weapon primary selector 4')
        expected=struct.unpack_from('<I',raw,action['payload_offset']+16)[0]
        reload_index=struct.unpack_from('<I',raw,action['payload_offset']+40)[0]
        self.inspect_record(raw,slot)
        descriptor=self.HEAP;instance=self.HEAP+0x8000
        manager=self.HEAP+0x9000;vtable=self.HEAP+0xa000;stack=self.STACK+0x8000
        self.put(instance+4,descriptor);self.put(manager,vtable)
        self.uc.reg_write(self.reg.UC_X86_REG_ESI,instance)
        self.uc.reg_write(self.reg.UC_X86_REG_ESP,stack)
        self.block(0x7d610b,0x7d6111) # Stops before acquiring the real manager.
        action_pointer=self.uc.reg_read(self.reg.UC_X86_REG_EDI)
        if action_pointer!=self.get(descriptor+0x48):raise ValueError('Wrong primary action pointer')
        self.uc.reg_write(self.reg.UC_X86_REG_EAX,manager)
        self.block(0x7d6116,0x7d6132) # Stops BEFORE sound manager virtual lookup.
        pointer=self.uc.reg_read(self.reg.UC_X86_REG_ESP)
        if pointer!=stack-8 or (self.get(pointer),self.get(pointer+4))!=(2,expected):
            raise ValueError('Native firing sound bank/index mismatch')
        if self.uc.reg_read(self.reg.UC_X86_REG_ECX)!=manager:
            raise ValueError('Unexpected synthetic sound manager')
        # Reload argument preparation writes three words in the emulated
        # global DATA area. Temporarily make only those two data pages writable;
        # no code page permission changes, files or actual process attachment.
        addresses=(0x98aff4,0x98affc,0x98b000)
        previous={at:self.get(at) for at in addresses}
        self.uc.mem_protect(0x98a000,8192,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        try:
            self.uc.reg_write(self.reg.UC_X86_REG_ESP,stack)
            self.uc.reg_write(self.reg.UC_X86_REG_EBP,stack+0x100)
            self.uc.reg_write(self.reg.UC_X86_REG_EAX,0)
            self.put(stack+0x2c,action_pointer);self.put(stack+0x108,0)
            self.block(0x7d50d5,0x7d5103) # Stops before any playback/manager call.
            if (self.get(0x98affc),self.get(0x98b000))!=(3,reload_index):
                raise ValueError('Native reload sound bank/index mismatch')
        finally:
            for at,value in previous.items():self.put(at,value)
            self.uc.mem_protect(0x98a000,8192,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC)
        return {'slot':slot,'shoot':{'bank':2,'index':expected},
                'reload':{'bank':3,'index':reload_index},'native_argument_flow_matches':True,
                'sound_lookup_or_playback_executed':False,'gameplay_operation_executed':False}

    def append_order(self):
        owner=self.HEAP+0xb000;array=self.HEAP+0xc000
        checks=[]
        for start,end,register,label in ((0x4392d5,0x4392e5,self.reg.UC_X86_REG_ESI,'banks'),
                                        (0x43226e,0x43227e,self.reg.UC_X86_REG_EBX,'entries')):
            for ordinal in (0,1,2,3,36,54):
                self.put(owner+4,array);self.put(owner+0xc,ordinal)
                self.uc.reg_write(register,owner)
                self.uc.reg_write(self.reg.UC_X86_REG_EDI,self.HEAP+0xd000)
                self.block(start,end)
                if self.get(array+4*ordinal)!=self.HEAP+0xd000 or self.get(owner+0xc)!=ordinal+1:
                    raise ValueError('Native sound ordered append differs')
                checks.append({'kind':label,'ordinal':ordinal,'native_append_matches':True})
        return {'checks':checks,'complete_file_loader_executed':False}
