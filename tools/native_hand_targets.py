"""Original compiled target preparation on private detached pose buffers."""
import math
import struct

from build_modern_equipment_hose import digest
from fpv_contact_constraints import world,targets,observed_elbow_hints
from native_hand_constraints import arm_input

BINARY_SHA='21ff73f49a776611b353b72f643d25bfb09d22a06e9239c2050cc1969e71718f'
BINARY_SIZE=6144
BASE=0x24000000
ENTRY=BASE+0x166c
CODE_END=BASE+0x1000+4472


def validate_receipt(receipt):
    if (not isinstance(receipt,dict) or type(receipt.get('status')) is not int or receipt['status']!=0
            or receipt.get('compiled_sha256')!=BINARY_SHA
            or any(receipt.get(k) is not True for k in ('input_unchanged','output_and_scratch_guards_unchanged',
                'failed_output_unchanged','native_cdecl_preserved'))
            or any(receipt.get(k) is not False for k in ('game_started','client_hook_implemented'))):
        raise ValueError('Incomplete compiled target preparation receipt')
    error=receipt.get('max_input_error')
    if type(error) not in (int,float) or not math.isfinite(error) or not 0<=error<=2e-6:
        raise ValueError('Invalid compiled target preparation comparison')
    return error


def checked_prepare(machine,data,reference):
    actual,receipt=machine.prepare(data)
    for row in (actual,reference):
        if (not isinstance(row,list) or len(row)!=120
                or any(type(v) not in (int,float) or not math.isfinite(v) for v in row)):
            raise ValueError('Compiled target preparation refused or returned invalid inputs')
    receipt={**receipt,'max_input_error':max(abs(a-b) for a,b in zip(actual,reference))}
    validate_receipt(receipt)
    return actual,receipt


def preparation_inputs(skin,equipment_nodes,poses,grips):
    hand_nodes=skin['nodes'];names=[n['name'] for n in [*hand_nodes,*equipment_nodes]]
    if len(set(names))!=len(names) or set(names)!=set(poses) or not 5<=len(names)<=128:
        raise ValueError('Ambiguous target preparation poses')
    index={name:i for i,name in enumerate(names)}
    parents=[n['parent_id']-1 for n in hand_nodes]+[
        -1 if n['parent_id']==0 else len(hand_nodes)+n['parent_id']-1 for n in equipment_nodes]
    if any(type(p) is not int or not -1<=p<i for i,p in enumerate(parents)):
        raise ValueError('Target preparation requires parent-first trees')
    roles=[index[n] for n in ('fpv_weapon','MOD_left_hand','MOD_right_hand','Bip01 L Forearm','Bip01 R Forearm')]
    expected=observed_elbow_hints(targets(world(equipment_nodes,poses),grips,root_name='fpv_weapon'),world(hand_nodes,poses))
    arm_values=[arm_input(skin,side,expected[side]) for side in ('L','R')]
    data={'poses':[[*poses[n]['position'],*poses[n]['rotation'],*poses[n]['scale']] for n in names],
          'parents':parents,'roles':roles,'rest':[v for a in arm_values for v in a[:45]],
          'grips':[v for side in ('L','R') for v in [*grips[side]['contact_offset'],
              *(v for row in grips[side]['rest_to_equipment_rotation'] for v in row),*grips[side]['wrist_to_contact_in_rest']]]}
    return data,[v for arm in arm_values for v in arm]


def encode_inputs(data):
    if (not isinstance(data,dict) or set(data)!={'poses','parents','roles','rest','grips'}
            or not isinstance(data['poses'],list) or not 5<=len(data['poses'])<=128):
        raise ValueError('Invalid target preparation input shape')
    count=len(data['poses'])
    for row in data['poses']:
        if not isinstance(row,list) or len(row)!=10 or any(type(v) not in (int,float) for v in row):
            raise ValueError('Invalid target preparation pose buffer')
    for key,size in (('parents',count),('roles',5),('rest',90),('grips',30)):
        if not isinstance(data[key],list) or len(data[key])!=size:raise ValueError('Invalid target preparation '+key)
    if (any(type(v) is not int or not -1<=v<=128 for v in data['parents'])
            or any(type(v) is not int or not 0<=v<=0xffff for v in data['roles'])
            or any(type(v) not in (int,float) for v in data['rest']+data['grips'])):
        raise ValueError('Invalid target preparation scalar')
    source=bytearray(0x3000)
    try:
        struct.pack_into('<'+'f'*(count*10),source,0,*(v for row in data['poses'] for v in row))
        struct.pack_into('<'+'i'*count,source,0x1800,*data['parents'])
        struct.pack_into('<5I',source,0x1b00,*data['roles'])
        struct.pack_into('<90d',source,0x1c00,*data['rest'])
        struct.pack_into('<30d',source,0x2000,*data['grips'])
    except (OverflowError,struct.error) as error:raise ValueError('Target preparation scalar cannot be encoded') from error
    return count,bytes(source)


class TargetPreparationOracle:
    STOP=0x3000000;STACK=0x3100000;INPUT=0x3300000;WORK=0x3400000;OUTPUT=0x3500000

    def __init__(self,raw):
        if type(raw) is not bytes or len(raw)!=BINARY_SIZE or digest(raw)!=BINARY_SHA:
            raise ValueError('Unreviewed target preparation image')
        import pefile
        import unicorn as uni
        from unicorn import x86_const as reg
        pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
        if (pe.OPTIONAL_HEADER.ImageBase!=BASE or pe.FILE_HEADER.Machine!=0x14c
                or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!={b'Hd2PrepareArms':ENTRY-BASE}):
            raise ValueError('Unreviewed target preparation PE contract')
        self.uni,self.reg=uni,reg;self.raw_sha=digest(raw);self.active=False;self.work_size=0
        self.uc=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32)
        for at,size,permissions in ((BASE,(len(mapped)+4095)&~4095,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.STOP,4096,uni.UC_PROT_READ|uni.UC_PROT_EXEC),(self.STACK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.INPUT,0x3000,uni.UC_PROT_READ),(self.WORK,8192,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.OUTPUT,4096,uni.UC_PROT_READ|uni.UC_PROT_WRITE)):
            self.uc.mem_map(at,size,permissions)
        self.uc.mem_write(BASE,mapped)
        self.uc.hook_add(uni.UC_HOOK_CODE,self.on_code);self.uc.hook_add(uni.UC_HOOK_MEM_WRITE,self.on_write)

    def on_code(self,uc,address,size,context):
        if not self.active or not BASE+0x1000<address<address+size<=CODE_END:
            raise ValueError('Target preparation instruction outside reviewed code')

    def on_write(self,uc,access,address,size,value,context):
        if not self.active or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),(self.WORK,self.WORK+self.work_size),(self.OUTPUT,self.OUTPUT+960))):
            raise ValueError('Target preparation write outside scratch, output or stack')

    def prepare(self,data,*,capacity=120,short_workspace=False,invalid_count=False):
        if (self.active or type(capacity) is not int or capacity not in (0,119,120)
                or type(short_workspace) is not bool or type(invalid_count) is not bool):
            raise ValueError('Unreviewed target preparation ABI')
        count,source=encode_inputs(data);workspace=count*12
        self.uc.mem_write(self.INPUT,source);self.uc.mem_write(self.WORK,b'Z'*8192);self.uc.mem_write(self.OUTPUT,b'Z'*4096)
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        args=[self.INPUT,self.INPUT+0x1800,129 if invalid_count else count,self.INPUT+0x1b00,
              self.INPUT+0x1c00,self.INPUT+0x2000,self.WORK,workspace-int(short_workspace),self.OUTPUT,capacity]
        self.uc.mem_write(stack,struct.pack('<11I',self.STOP,*args))
        preserved={'EBX':0x12345678,'ESI':0x34567812,'EDI':0x56781234,'EBP':0x78123456}
        for name,value in {**preserved,'EAX':0,'ECX':0,'EDX':0,'ESP':stack,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.active=True;self.work_size=count*48
        try:
            self.uc.emu_start(ENTRY,self.STOP,count=1000000,timeout=3_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+4
                    or any(self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+n))!=v for n,v in preserved.items())):
                raise ValueError('Target preparation budget or calling convention differs')
        finally:self.active=False
        status=self.uc.reg_read(self.reg.UC_X86_REG_EAX)
        output=bytes(self.uc.mem_read(self.OUTPUT,4096));scratch=bytes(self.uc.mem_read(self.WORK,8192))
        if (status not in range(6) or bytes(self.uc.mem_read(self.INPUT,0x3000))!=source
                or output[960:]!=b'Z'*(4096-960) or (status and output!=b'Z'*4096)
                or scratch[count*48:]!=b'Z'*(8192-count*48)):
            raise ValueError('Target preparation changed inputs, guards or failed output')
        values=list(struct.unpack('<120d',output[:960])) if status==0 else None
        if values is not None and any(not math.isfinite(v) for v in values):raise ValueError('Nonfinite prepared arm input')
        return values,{'status':status,'compiled_sha256':self.raw_sha,'input_unchanged':True,
            'output_and_scratch_guards_unchanged':True,'failed_output_unchanged':True,
            'native_cdecl_preserved':True,'game_started':False,'client_hook_implemented':False}
