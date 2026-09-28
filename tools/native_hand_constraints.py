"""Bounded x86 execution of our original compiled arm solver, no OS loading.

This is NOT a client hook. Source skeletons stay private; only caller-owned
synthetic buffers are touched. All six rotations are committed together.
"""
import math
import struct

from animation_tick_audit import model_poses
from build_equipment_hand_animation import HAND_NAMES
from build_modern_equipment_hose import digest
from fpv_contact_constraints import (world,targets,wrist_errors,observed_elbow_hints,replace_arm_rotations)
from fpv_contact_constraints import correct as correct_reference,ARM_NAMES
from hand_pose_ik import pinned_skin,validate_basis,vector
from model_transform import native_affine

CODE_SHA='be596ddb17eb8d1fdc15253f18c826713e0b80ae90a0fcac1d1b42a063b84f62'
CODE_SIZE=6240
ENTRY_RVA=8100
BINARY_SHA='d3ff9aa8bf18b947ad369e8ccc79809c773da9f9b8c102ae17b7ed1527e934bf'
BINARY_SIZE=8192
SECTION_PINS={b'.text':(0x1000,CODE_SIZE,CODE_SHA),
    b'.data':(0x3000,384,'58c1f4c33fbafb1a81c9535b61b9943f2471123dd261699fb0a6e29592320988'),
    b'.reloc':(0x4000,88,'17393442c0a7d59629622bbb39fecd73311b0b9ba79f0f52e1c43888b8664d10')}


def arm_input(skin,side,wanted):
    if side not in ('L','R') or set(wanted)!={'position','rotation','pole'}:
        raise ValueError('Invalid compiled arm target')
    by_name={n['name']:n for n in skin['nodes']}
    nodes=[by_name[f'Bip01 {side} '+part] for part in ('UpperArm','Forearm','Hand')]
    clavicle=by_name[f'Bip01 {side} Clavicle']
    if (by_name['a']['index']!=clavicle['parent_id'] or clavicle['index']!=nodes[0]['parent_id']
            or nodes[1]['parent_id']!=nodes[0]['index']
            or nodes[2]['parent_id']!=nodes[1]['index']):raise ValueError('Unreviewed compiled arm hierarchy')
    values=[]
    for node in nodes:
        basis,position=skin['rest_world'][node['index']]
        validate_basis(basis);vector(position)
        values.extend(v for row in basis for v in row);values.extend(position)
    parent=skin['rest_world'][nodes[0]['parent_id']][0];validate_basis(parent)
    values.extend(v for row in parent for v in row)
    values.extend(vector(wanted['position']))
    values.extend(v for row in validate_basis(wanted['rotation']) for v in row)
    values.extend(vector(wanted['pole']))
    if len(values)!=60:raise ValueError('Compiled arm ABI size differs')
    return values


class ArmSolverOracle:
    BASE=0x10000000;STOP=0x3000000;STACK=0x3100000;INPUT=0x3300000;OUTPUT=0x3400000

    def __init__(self,raw):
        # The complete image is pinned too: section hashes alone do not bind
        # PE headers, overlapping raw offsets, imports or allocation sizes.
        if type(raw) is not bytes or len(raw)!=BINARY_SIZE or digest(raw)!=BINARY_SHA:
            raise ValueError('Unreviewed original compiled arm image')
        import pefile
        import unicorn as uni
        from unicorn import x86_const as reg
        pe=pefile.PE(data=raw);mapped=pe.get_memory_mapped_image()
        exports={s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}
        code=[s for s in pe.sections if s.Name.rstrip(b'\0')==b'.text']
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=self.BASE
                or pe.OPTIONAL_HEADER.Magic!=0x10b or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or set(exports)!={b'Hd2SolveArm'} or len(code)!=1
                or code[0].VirtualAddress!=0x1000 or code[0].Misc_VirtualSize!=CODE_SIZE
                or exports[b'Hd2SolveArm']!=ENTRY_RVA
                or digest(mapped[0x1000:0x1000+CODE_SIZE])!=CODE_SHA):
            raise ValueError('Unreviewed original compiled arm solver')
        if (pe.OPTIONAL_HEADER.AddressOfEntryPoint!=0x1000
                or len(pe.sections)!=3 or {s.Name.rstrip(b'\0') for s in pe.sections}!=set(SECTION_PINS)):
            raise ValueError('Unreviewed compiled arm section set')
        for section in pe.sections:
            rva,size,sha=SECTION_PINS[section.Name.rstrip(b'\0')]
            if (section.VirtualAddress!=rva or section.Misc_VirtualSize!=size
                    or digest(mapped[rva:rva+size])!=sha):raise ValueError('Changed compiled arm section')
        self.uni,self.reg=uni,reg;self.raw_sha=digest(raw);self.entry=self.BASE+exports[b'Hd2SolveArm']
        self.uc=uni.Uc(uni.UC_ARCH_X86,uni.UC_MODE_32)
        for start,size,permissions in ((self.BASE,(len(mapped)+4095)&~4095,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.STOP,4096,uni.UC_PROT_READ|uni.UC_PROT_EXEC),
                (self.STACK,65536,uni.UC_PROT_READ|uni.UC_PROT_WRITE),
                (self.INPUT,4096,uni.UC_PROT_READ),(self.OUTPUT,4096,uni.UC_PROT_READ|uni.UC_PROT_WRITE)):
            self.uc.mem_map(start,size,permissions)
        self.uc.mem_write(self.BASE,mapped);self.active=False;self.visited=set()
        self.uc.hook_add(uni.UC_HOOK_CODE,self.on_code);self.uc.hook_add(uni.UC_HOOK_MEM_WRITE,self.on_write)

    def on_code(self,uc,address,size,_):
        if not self.active or not self.BASE+0x1000<=address<address+size<=self.BASE+0x1000+CODE_SIZE:
            raise ValueError('Compiled arm instruction outside reviewed code')
        if address==self.BASE+0x1000:raise ValueError('Diagnostic DLL startup must never be called')
        self.visited.add(address)

    def on_write(self,uc,access,address,size,value,_):
        if not self.active or not any(a<=address and address+size<=b for a,b in
                ((self.STACK,self.STACK+65536),(self.OUTPUT,self.OUTPUT+96))):
            raise ValueError('Compiled arm write outside output or stack')

    def solve(self,values,side,*,count=60,capacity=12):
        if (self.active or not isinstance(values,list) or len(values)!=60
                or any(type(v) not in (int,float) for v in values)
                or type(side) is not int or not -2<=side<=2
                or type(count) is not int or not 0<=count<=64
                or type(capacity) is not int or not 0<=capacity<=16):
            raise ValueError('Unreviewed compiled arm ABI input')
        data=struct.pack('<60d',*values);source=data+bytes(4096-len(data));sentinel=b'\xa5'*4096
        self.uc.mem_write(self.INPUT,source);self.uc.mem_write(self.OUTPUT,sentinel)
        self.uc.mem_write(self.STACK,bytes(65536));stack=self.STACK+0xf000
        self.uc.mem_write(stack,struct.pack('<6I',self.STOP,self.INPUT,count,side&0xffffffff,self.OUTPUT,capacity))
        preserved={'EBX':0x12345678,'ESI':0x34567812,'EDI':0x56781234,'EBP':0x78123456}
        for name,value in {**preserved,'EAX':0,'ECX':0,'EDX':0,'ESP':stack,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.active=True;self.visited=set()
        try:
            self.uc.emu_start(self.entry,self.STOP,count=500000,timeout=3_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+4
                    or any(self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+n))!=v for n,v in preserved.items())):
                raise ValueError('Compiled arm calling convention or instruction budget differs')
        finally:self.active=False
        status=self.uc.reg_read(self.reg.UC_X86_REG_EAX);after=bytes(self.uc.mem_read(self.OUTPUT,4096))
        if (status not in range(6) or bytes(self.uc.mem_read(self.INPUT,4096))!=source
                or after[96:]!=sentinel[96:] or (status and after!=sentinel)):
            raise ValueError('Compiled arm changed inputs or wrote partial failed output')
        values=list(struct.unpack('<12d',after[:96])) if status==0 else None
        if values is not None and any(not math.isfinite(v) for v in values):raise ValueError('Nonfinite compiled arm output')
        return values,{'status':status,'compiled_sha256':self.raw_sha,'code_sha256':CODE_SHA,
            'native_cdecl_preserved':True,'input_unchanged':True,'failure_output_unchanged':True,
            'output_guard_unchanged':True,'instructions_visited':len(self.visited),
            'operating_system_or_game_called':False,'engine_hook_implemented':False}


def correct_compiled(hand,equipment_nodes,poses,grips,machine,*,root_name='fpv_weapon',preserve_observed_elbow_plane=True,target_preparer=None):
    if root_name!='fpv_weapon' or preserve_observed_elbow_plane is not True:
        raise ValueError('Unreviewed compiled correction policy')
    source,skin=pinned_skin(hand);names,initial=model_poses(hand);seeds=dict(zip(names,initial))
    gear_names={n['name'] for n in equipment_nodes}
    if (set(names)!=HAND_NAMES or gear_names&HAND_NAMES or set(poses)!=HAND_NAMES|gear_names
            or poses['a']!=seeds['a']
            or any(poses[n][k]!=seeds[n][k] for n in names for k in ('position','scale'))):
        raise ValueError('Compiled correction would alter source rest or root')
    # Serialized/native quaternion normalization can change one float32 bit.
    # Compare the represented rotations, not signs or raw quaternion bytes.
    for side in ('L','R'):
        name=f'Bip01 {side} Clavicle'
        a=native_affine([0,0,0],poses[name]['rotation'],[1,1,1])[0]
        b=native_affine([0,0,0],seeds[name]['rotation'],[1,1,1])[0]
        if max(abs(a[i][j]-b[i][j]) for i in range(3) for j in range(3))>2e-6:
            raise ValueError('Compiled correction requires resting clavicles')
    hand_world=world(skin['nodes'],poses)
    wanted=observed_elbow_hints(targets(world(equipment_nodes,poses),grips,root_name='fpv_weapon'),hand_world)
    before=wrist_errors(hand_world,wanted);authored={};receipts={}
    prepared=None;preparation_receipt=None
    if target_preparer is not None:
        from native_hand_targets import preparation_inputs,checked_prepare
        data,reference=preparation_inputs(skin,equipment_nodes,poses,grips)
        prepared,preparation_receipt=checked_prepare(target_preparer,data,reference)
    for index,side in enumerate(('L','R')):
        inputs=prepared[60*index:60*(index+1)] if prepared is not None else arm_input(skin,side,wanted[side])
        values,receipt=machine.solve(inputs,1 if side=='L' else -1)
        if receipt['status']!=0:raise ValueError(f"Compiled arm solver refused {side} correction: status {receipt['status']}")
        receipts[side]=receipt
        for i,part in enumerate(('UpperArm','Forearm','Hand')):
            name=f'Bip01 {side} '+part
            authored[name]={**poses[name],'rotation':values[4*i:4*i+4]}
    result=replace_arm_rotations(poses,authored);after=wrist_errors(world(skin['nodes'],result),wanted)
    if max(after.values())>5e-6:raise ValueError('Compiled correction missed wrist target')
    return result,{'hand_source':source,'before':before,'after':after,'changed_channels':'six_arm_rotations_only',
        'finger_poses_preserved':True,'equipment_poses_preserved':True,'source_rest_transforms_preserved':True,
        'compiled_arm_receipts':receipts,'correction_is_compiled_x86':True,
        'compiled_target_preparation':preparation_receipt,
        'engine_hook_implemented':False,'runtime_status':'pending'}


class ComparedCorrector:
    """Offline comparison wrapper; the compiled implementation is independent."""
    def __init__(self,machine):
        self.machine=machine;self.poses=0;self.arms=0;self.max_rotation_matrix_error=0

    def __call__(self,hand,nodes,poses,grips,**policy):
        result,receipt=correct_compiled(hand,nodes,poses,grips,self.machine,**policy)
        expected,_=correct_reference(hand,nodes,poses,grips,**policy)
        error=0
        for name in poses:
            if name not in ARM_NAMES:
                if result[name]!=expected[name]:raise ValueError('Compiled correction changed an unrelated pose')
                continue
            a=native_affine([0,0,0],result[name]['rotation'],[1,1,1])[0]
            b=native_affine([0,0,0],expected[name]['rotation'],[1,1,1])[0]
            error=max(error,*(abs(a[i][j]-b[i][j]) for i in range(3) for j in range(3)))
        if error>2e-6:raise ValueError('Compiled arm rotations differ from Python reference')
        self.max_rotation_matrix_error=max(self.max_rotation_matrix_error,error);self.poses+=1;self.arms+=2
        return result,receipt

    def report(self):
        return {'compiled_sha256':self.machine.raw_sha,'code_sha256':CODE_SHA,'corrected_poses':self.poses,
                'compiled_arm_calls':self.arms,'max_rotation_matrix_error':self.max_rotation_matrix_error,
                'six_rotations_compared_to_independent_python':True,'runtime_hook_implemented':False}
