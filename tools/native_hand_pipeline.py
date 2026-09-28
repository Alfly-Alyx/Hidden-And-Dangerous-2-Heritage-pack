"""Original compiled numerical pipeline on exclusively supplied joint records.

No live model discovery, hook, scene loading or Windows DLL execution.
The optional parent shares an existing emulator and never reseeds its arena.
"""
import math
import struct
from copy import deepcopy

from build_modern_equipment_hose import digest
from native_hand_targets import encode_inputs

BINARY_SHA='62f1827ab5d173d9f683fc4b896a83862752219b392222ff60295f01787e2a65'
BINARY_SIZE=17408
BASE=0x26000000
EXPORTS={b'Hd2CommitArms':17839,b'Hd2CorrectHandPose':4267,b'Hd2PrepareArms':8347,b'Hd2SolveArm':15157}
CODE_SIZE=14864
WORK_SIZE=7536
EXPECTED_CALLS={'Hd2CorrectHandPose':1,'Hd2PrepareArms':1,'Hd2SolveArm':2,'Hd2CommitArms':1}


def validate_receipt(receipt):
    if (not isinstance(receipt,dict) or type(receipt.get('status')) is not int or receipt['status']!=0
            or receipt.get('compiled_sha256')!=BINARY_SHA or receipt.get('compiled_calls')!=EXPECTED_CALLS
            or any(type(v) is not int for v in receipt.get('compiled_calls',{}).values())
            or any(receipt.get(k) is not True for k in ('inputs_unchanged','unrelated_arena_unchanged',
                'failed_arena_unchanged','workspace_guard_unchanged','native_cdecl_preserved','shared_animation_arena'))
            or any(receipt.get(k) is not False for k in ('game_started','client_hook_implemented'))):
        raise ValueError('Incomplete shared compiled pipeline receipt')
    error=receipt.get('max_input_error')
    if type(error) not in (int,float) or not math.isfinite(error) or not 0<=error<=2e-6:
        raise ValueError('Invalid compiled pipeline target comparison')
    return error


def correct_pipeline(hand,nodes,poses,grips,machine):
    from native_hand_constraints import correction_context
    from native_hand_targets import preparation_inputs
    from fpv_contact_constraints import targets,world,wrist_errors
    if machine.parent is None:raise ValueError('Animation pipeline must share its arena')
    source,skin=correction_context(hand,nodes,poses)
    data,reference=preparation_inputs(skin,nodes,poses,grips)
    names=[n['name'] for n in [*skin['nodes'],*nodes]]
    arms=[f'Bip01 {side} {part}' for side in ('L','R') for part in ('UpperArm','Forearm','Hand')]
    roles=data['roles']+[names.index(n) for n in arms];offsets=[i*0x200 for i in range(len(names))]
    arena=bytes(machine.uc.mem_read(machine.ARENA,65536))
    after,receipt=machine.correct(data,arena,offsets,roles)
    if receipt['status']:raise ValueError('Compiled shared pipeline refused: '+str(receipt['status']))
    prepared=struct.unpack('<120d',machine.uc.mem_read(machine.WORK+6144,960))
    receipt={**receipt,'max_input_error':max(abs(a-b) for a,b in zip(prepared,reference))}
    validate_receipt(receipt)
    result=deepcopy(poses)
    for name,index in zip(arms,roles[5:]):result[name]['rotation']=list(struct.unpack_from('<4f',after,offsets[index]+0xc0))
    wanted=targets(world(nodes,poses),grips,root_name='fpv_weapon')
    return result,{'hand_source':source,'before':wrist_errors(world(skin['nodes'],poses),wanted),
        'after':wrist_errors(world(skin['nodes'],result),wanted),'compiled_target_preparation':None,
        'compiled_pipeline':receipt,'engine_hook_implemented':False,'runtime_status':'pending'}


class HandPipelineOracle:
    STOP=0x3000000;STACK=0x3100000;INPUT=0x3a00000;WORK=0x3b00000;ARENA=0x3900000

    def __init__(self,raw,parent=None):
        if type(raw) is not bytes or len(raw)!=BINARY_SIZE or digest(raw)!=BINARY_SHA:
            raise ValueError('Unreviewed original hand pipeline image')
        import pefile
        import unicorn as uni
        from unicorn import x86_const as reg
        pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
        exports={s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=BASE
                or hasattr(pe,'DIRECTORY_ENTRY_IMPORT') or exports!=EXPORTS):
            raise ValueError('Unreviewed compiled pipeline PE contract')
        self.parent=parent;self.uni,self.reg=uni,reg;self.raw_sha=digest(raw)
        self.active=False;self.allowed=();self.calls={}
        if parent is None:
            self.uc=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32)
            for address,size,permissions in ((self.STOP,4096,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                    (self.STACK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                    (self.ARENA,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE)):
                self.uc.mem_map(address,size,permissions)
            self.uc.hook_add(uni.UC_HOOK_CODE,self.on_code);self.uc.hook_add(uni.UC_HOOK_MEM_WRITE,self.on_write)
        else:
            self.uc=parent.uc;self.ARENA=parent.bridge.NODES
            self.STACK=parent.bridge.STACK;self.STOP=parent.bridge.STOP
        for address,size,permissions in ((BASE,(len(mapped)+4095)&~4095,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.INPUT,0x3000,uni.UC_PROT_READ),(self.WORK,8192,uni.UC_PROT_READ|uni.UC_PROT_WRITE)):
            self.uc.mem_map(address,size,permissions)
        self.uc.mem_write(BASE,mapped)

    def on_code(self,uc,address,size,context):
        if not self.active or not BASE+0x1000<address<address+size<=BASE+0x1000+CODE_SIZE:
            raise ValueError('Pipeline instruction outside reviewed code')
        for name,rva in EXPORTS.items():
            if address==BASE+rva:self.calls[name.decode('ascii')]=self.calls.get(name.decode('ascii'),0)+1

    def on_write(self,uc,access,address,size,value,context):
        if not self.active or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),(self.WORK,self.WORK+WORK_SIZE),*self.allowed)):
            raise ValueError('Pipeline write outside six rotations, flags, scratch or stack')

    def correct(self,data,arena,offsets,roles,*,role_count=11,work_bytes=WORK_SIZE):
        if (self.active or not isinstance(data,dict) or type(arena) is not bytes or len(arena)!=65536
                or not isinstance(offsets,list) or len(offsets)!=len(data.get('poses',[]))
                or any(type(v) is not int or not 0<=v<=65536 for v in offsets)
                or not isinstance(roles,list) or len(roles)!=11
                or any(type(v) is not int or not 0<=v<=65535 for v in roles)
                or type(role_count) is not int or role_count not in (10,11)
                or type(work_bytes) is not int or work_bytes not in (WORK_SIZE-1,WORK_SIZE)):
            raise ValueError('Unreviewed pipeline ABI')
        if data.get('roles')!=roles[:5]:raise ValueError('Pipeline role prefixes differ')
        count,source=encode_inputs(data);source=bytearray(source)
        struct.pack_into('<11I',source,0x1b00,*roles)
        struct.pack_into('<'+'I'*count,source,0x2400,*offsets)
        source=bytes(source)
        if self.parent is None:self.uc.mem_write(self.ARENA,arena)
        elif bytes(self.uc.mem_read(self.ARENA,65536))!=arena:raise ValueError('Shared pipeline arena changed before call')
        self.uc.mem_write(self.INPUT,source);self.uc.mem_write(self.WORK,b'Z'*8192)
        self.uc.mem_write(self.STACK,bytes(65536));stack=self.STACK+0xf000
        args=[self.ARENA,65536,self.INPUT+0x2400,count,self.INPUT,self.INPUT+0x1800,
              self.INPUT+0x1b00,role_count,self.INPUT+0x1c00,self.INPUT+0x2000,self.WORK,work_bytes]
        self.uc.mem_write(stack,struct.pack('<13I',self.STOP,*args))
        preserved={'EBX':0x12345678,'ESI':0x34567812,'EDI':0x56781234,'EBP':0x78123456}
        for name,value in {**preserved,'EAX':0,'ECX':0,'EDX':0,'ESP':stack,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.allowed=[]
        for i in roles[5:]:
            if i<count and offsets[i]+0x170<=65536:
                at=self.ARENA+offsets[i];self.allowed.extend(((at+0xc0,at+0xd0),(at+0xe0,at+0xe4)))
        self.active=True;self.calls={}
        try:
            self.uc.emu_start(BASE+EXPORTS[b'Hd2CorrectHandPose'],self.STOP,count=2000000,timeout=5_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+4
                    or any(self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+k))!=v for k,v in preserved.items())):
                raise ValueError('Pipeline calling convention or instruction budget differs')
        finally:self.active=False
        status=self.uc.reg_read(self.reg.UC_X86_REG_EAX);after=bytes(self.uc.mem_read(self.ARENA,65536))
        scratch=bytes(self.uc.mem_read(self.WORK,8192))
        permitted={i-self.ARENA for a,b in self.allowed for i in range(a,b)}
        if (status not in {*range(6),*range(11,16),*range(21,26),*range(31,36),*range(41,46)}
                or bytes(self.uc.mem_read(self.INPUT,0x3000))!=source or scratch[WORK_SIZE:]!=b'Z'*(8192-WORK_SIZE)
                or (status and after!=arena)
                or any(a!=b and i not in permitted for i,(a,b) in enumerate(zip(arena,after)))):
            raise ValueError('Pipeline changed protected inputs, failed arena or guards')
        if status==0:
            if self.calls!=EXPECTED_CALLS:
                raise ValueError('Pipeline did not execute its complete compiled chain')
            if any(not math.isfinite(v) for v in struct.unpack_from('<144d',scratch,6144)):
                raise ValueError('Nonfinite compiled pipeline results')
        return after,{'status':status,'compiled_sha256':self.raw_sha,'compiled_calls':dict(self.calls),
            'inputs_unchanged':True,'unrelated_arena_unchanged':True,'failed_arena_unchanged':True,
            'workspace_guard_unchanged':True,'native_cdecl_preserved':True,
            'shared_animation_arena':self.parent is not None,'client_hook_implemented':False,'game_started':False}
