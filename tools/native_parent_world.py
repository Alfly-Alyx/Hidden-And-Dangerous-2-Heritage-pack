"""Native SetParent world-preserving paths on owned diagnostic uniform-scale trees.

Uses the compiled parent guard unchanged. No scene notifications, immediate
Refresh, allocator, destructor, renderer or game process is admitted.
"""
from copy import deepcopy
import math
import struct

from ls3d_math_oracle import f32
from ls3d_palette_oracle import local_matrix,product
from native_hand_parent_hooks import NativeHandParentHooksOracle,reference_parent,PARENT,BASE as PARENT_BASE
from native_hand_lifecycle import STATE_SIZE

WORLD=0x1001e390
RANGES=((0x1001d686,0x1001d7d5),(0x1001d821,0x1001d970),(0x1001d976,0x1001d988),
    (0x1001dae6,0x1001daf0),(WORLD,0x1001e543),(0x1002d450,0x1002d57d),
    (0x1002c620,0x1002c791),(0x1002d830,0x1002d9b0),(0x1002db20,0x1002dc85),
    (0x1002cf10,0x1002d25f),(0x10005a60,0x10005a79),(0x10010960,0x10010a8e),
    (0x1002ec40,0x1002ec79),(0x1002ff30,0x1002ff47),(0x10011d80,0x10011d9f))
TOLERANCE=5e-5


def inverse_uniform(matrix):
    if (not isinstance(matrix,list) or len(matrix)!=16 or any(type(v) not in (int,float) or not math.isfinite(v) for v in matrix)
            or any(matrix[i]!=v for i,v in ((3,0),(7,0),(11,0),(15,1)))):raise ValueError('Expected finite affine uniform matrix')
    square=sum(matrix[i]**2 for i in (0,1,2))
    if not .01<=square<=100:raise ValueError('Unreviewed uniform scale')
    for a in range(3):
        for b in range(3):
            dot=sum(matrix[a*4+k]*matrix[b*4+k] for k in range(3))
            if abs(dot-(square if a==b else 0))>2e-5*max(1,square):raise ValueError('Nonuniform or sheared matrix')
    determinant=(matrix[0]*(matrix[5]*matrix[10]-matrix[6]*matrix[9])
                 -matrix[1]*(matrix[4]*matrix[10]-matrix[6]*matrix[8])
                 +matrix[2]*(matrix[4]*matrix[9]-matrix[5]*matrix[8]))
    if determinant<=0:raise ValueError('Reflected uniform matrix')
    result=[0.0]*16;result[15]=1.0
    for a in range(3):
        for b in range(3):result[a*4+b]=matrix[b*4+a]/square
    for b in range(3):result[12+b]=-sum(matrix[12+k]*result[k*4+b] for k in range(3))
    return result


def world_matrices(tree,locals):
    if set(tree)!=set(locals):raise ValueError('Tree/local identity mismatch')
    # Reuse bounded forest validation without introducing a structural mutation.
    first=next(iter(tree),None)
    if first is None:raise ValueError('Empty parent world forest')
    reference_parent(tree,first,tree[first]['parent'],0)
    for matrix in locals.values():inverse_uniform(matrix)
    result={}
    def world(pointer):
        if pointer not in result:
            parent=tree[pointer]['parent'];result[pointer]=product(locals[pointer],world(parent)) if parent else list(locals[pointer])
        return result[pointer]
    for pointer in tree:world(pointer)
    return result


def world_target(tree,locals,frame,parent):
    updated=reference_parent(tree,frame,parent,0);world=world_matrices(tree,locals)
    target=product(world[frame],inverse_uniform(world[parent])) if parent else world[frame]
    return updated,target,world


class NativeParentWorldOracle(NativeHandParentHooksOracle):
    def __init__(self,*args):
        self.world_running=False;self.world_calls={};self.world_nodes=set()
        super().__init__(*args)

    def on_code(self,uc,address,size,context):
        if self.world_running and address not in (PARENT,PARENT+6) and any(a<=address<address+size<=b for a,b in RANGES):
            self.parent_executing=False
            if address==0x1001d8e4:
                # The native vector helper writes three components. SetParent
                # also copies its fourth stack slot; it is padding, not scale.
                self.scale_padding=bytes(uc.mem_read(self.adapter.reg_read('EAX')+12,4))
            if address==WORLD:
                pointer=self.adapter.reg_read('ECX')
                if pointer not in self.tree:raise ValueError('Native world calculation escaped owned forest')
                self.world_nodes.add(pointer)
            for entry,label in ((WORLD,'world_cache'),(0x1002d450,'quaternion_matrix'),(0x1002c620,'inverse_matrix'),
                                (0x1002d830,'matrix_product'),(0x1002db20,'scale_extract'),(0x1002cf10,'orientation_rebuild')):
                if address==entry:self.world_calls[label]=self.world_calls.get(label,0)+1
            return
        return super().on_code(uc,address,size,context)

    def seed_world(self,turned):
        if type(turned) is not bool:raise ValueError('Expected explicit world orientation fixture')
        self.seed_tree(11);self.locals={};self.local_scales={}
        for i,(pointer,row) in enumerate(self.tree.items()):
            scale=1.0 if i>1 else (1.125 if i==0 else .875)
            angle=(.09*(i+1) if turned else 0);axis=(0,0,1) if i%2 else (0,1,0)
            q=[f32(v*math.sin(angle/2)) for v in axis]+[f32(math.cos(angle/2))]
            pose={'rotation':q,'position':[f32(.02*(i+1)),f32(.01*(i%3-1)),f32(-.015*(i+2))],'scale':[scale]*3}
            self.locals[pointer]=local_matrix(pose);self.local_scales[pointer]=scale
            page=pointer&~4095;at=pointer-page;data=self.pages[page]
            data[at+0x40:at+0xb0]=bytes(0x70)
            struct.pack_into('<4f',data,at+0xb0,*pose['position'],1)
            struct.pack_into('<4f',data,at+0xc0,*q);struct.pack_into('<4f',data,at+0xd0,scale,scale,scale,1)
            struct.pack_into('<I',data,at+0xe0,8);struct.pack_into('<f',data,at+0xfc,1)
            row['flags']=8
        for page,data in self.pages.items():self.uc.mem_write(page,bytes(data))
        for node in range(11):self.operation('add',0,node)
        self.uc.mem_write(self.STATE,bytes(STATE_SIZE)+b'Z'*(4096-STATE_SIZE))
        if self.setup_parent(b'Hd2ConfigureParentHooks',[self.STATE,STATE_SIZE]):raise ValueError('World parent hook setup failed')
        self.watch_model(11)

    def world_reparent(self,frame,parent,flags):
        if self.phase is not None or type(flags) is not int or flags not in (1,3):raise ValueError('Unreviewed world parent operation')
        expected_tree,target,old_world=world_target(self.tree,self.locals,frame,parent)
        before=self.expected_pages(self.state);self.check_pages(self.state)
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<4I',self.STOP,frame,parent,flags))
        preserved={'EBX':0x12345678,'ESI':0x23456781,'EDI':0x34567812,'EBP':0x45678123}
        for key,value in {**preserved,'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+key),value)
        self.world_calls={};self.world_nodes=set();self.scale_padding=None;self.phase='membership';self.parent_running=True;self.world_running=True
        self.writes=tuple((p+a,p+b) for p in self.tree for a,b in ((0x40,0x80),(0x80,0x8c),(0x90,0x9c),(0xa0,0xac),
                          (0xe0,0xe4),(0xfc,0x100),(0x108,0x114)))+((frame+0xb0,frame+0xbc),(frame+0xd0,frame+0xe0))
        try:
            self.uc.emu_start(PARENT,self.STOP,count=200000,timeout=3_000_000)
            if (self.adapter.reg_read('EIP')!=self.STOP or self.adapter.reg_read('ESP')!=stack+16 or self.adapter.reg_read('EAX')
                    or self.parent_saved is not None or any(self.adapter.reg_read(k)!=v for k,v in preserved.items())):
                raise ValueError('World parent ABI differs')
            if self.adapter.reg_read('FPTAG')!=0xffff or self.adapter.reg_read('FPCW')!=0x27f:raise ValueError('Native world routine left floating stack/control changed')
        finally:self.phase=None;self.parent_running=False;self.world_running=False;self.parent_executing=False;self.parent_saved=None;self.writes=()
        actual={page:bytes(self.uc.mem_read(page,4096)) for page in self.pages}
        changed=self.tree[frame]['parent']!=parent
        errors={'world_caches':0.0,'local_matrices':0.0,'scales':0.0,'preserved_world':0.0}
        after_locals=deepcopy(self.locals);allowed={page:set() for page in self.pages}
        def permit(pointer,start,end):allowed[pointer&~4095].update(range(pointer%4096+start,pointer%4096+end))
        def floats(pointer,at,count):return list(struct.unpack_from('<'+'f'*count,actual[pointer&~4095],pointer%4096+at))
        def compare(key,values,wanted):
            if any(not math.isfinite(v) for v in values):raise ValueError('Nonfinite native world result')
            error=max(abs(a-b) for a,b in zip(values,wanted));errors[key]=max(errors[key],error)
            if error>TOLERANCE:raise ValueError(f'Native world {key} differs: {error}')
        for pointer,row in self.tree.items():
            at=pointer%4096;data=actual[pointer&~4095];new=expected_tree[pointer]
            children=new['children'];siblings=expected_tree[new['parent']]['children'] if new['parent'] else []
            position=siblings.index(pointer) if new['parent'] else -1
            following=siblings[position+1] if position>=0 and position+1<len(siblings) else 0
            if struct.unpack_from('<3I',data,at+0x108)!=(new['parent'],children[0] if children else 0,following):
                raise ValueError('World parent links differ')
            permit(pointer,0x108,0x114)
            wanted_flags=0x40000010 if changed and pointer==frame else (0x3c if pointer in self.world_nodes else 8)
            if struct.unpack_from('<I',data,at+0xe0)[0]!=wanted_flags:raise ValueError('World parent cache flags differ')
            permit(pointer,0xe0,0xe4)
            if pointer in self.world_nodes:
                compare('world_caches',floats(pointer,0x40,16),old_world[pointer]);permit(pointer,0x40,0x80)
                scale=self.local_scales[pointer];cursor=row['parent']
                while cursor:scale*=self.local_scales[cursor];cursor=self.tree[cursor]['parent']
                compare('scales',floats(pointer,0xfc,1),[scale]);permit(pointer,0xfc,0x100)
                if pointer!=frame or not changed:
                    compare('local_matrices',floats(pointer,0x80,16),self.locals[pointer])
                    for lo,hi in ((0x80,0x8c),(0x90,0x9c),(0xa0,0xac)):permit(pointer,lo,hi)
            if pointer==frame and changed:
                scale=floats(pointer,0xd0,3);orientation=floats(pointer,0x80,16)
                local=orientation[:]
                for a in range(3):
                    for b in range(3):local[a*4+b]=f32(orientation[a*4+b]*scale[a])
                compare('local_matrices',local,target);after_locals[pointer]=local
                compare('scales',scale,[math.sqrt(sum(target[a*4+b]**2 for b in range(3))) for a in range(3)])
                if data[at+0xdc:at+0xe0]!=self.scale_padding:raise ValueError('Native copied scale padding differs')
                for lo,hi in ((0x80,0x8c),(0x90,0x9c),(0xa0,0xac),(0xb0,0xbc),(0xd0,0xe0)):permit(pointer,lo,hi)
        for page,raw in actual.items():
            if any(a!=b and i not in allowed[page] for i,(a,b) in enumerate(zip(before[page],raw))):
                raise ValueError('World parent changed unrelated object/vector/guard bytes')
        new_world=world_matrices(expected_tree,after_locals)
        for pointer in self.tree:compare('preserved_world',new_world[pointer],old_world[pointer])
        if bytes(self.uc.mem_read(0x10000000,self.native_size))!=self.native_image:raise ValueError('World parent changed native image')
        return {'changed':changed,'flags':flags,'max_errors':errors,'native_calls':dict(self.world_calls),
                'native_world_cache_objects':len(self.world_nodes),'all_world_transforms_preserved':True,
                'unrelated_bytes_and_membership_unchanged':True,'moved_quaternion_left_stale_by_native_matrix_path':changed,
                'fourth_scale_slot_is_nonsemantic_copied_padding':changed}

    def scenario_world(self,case,turned,patched,flags):
        if case not in ('move_leaf','detach_leaf','move_model','same_parent') or type(patched) is not bool:raise ValueError('Unreviewed world case')
        self.seed_world(turned);frame=self.MODELS[0] if case=='move_model' else self.pointers[-1]
        parent=0 if case=='detach_leaf' else self.tree[frame]['parent'] if case=='same_parent' else self.MODELS[1]
        self.parent_checks=0;self.parent_calls={};self.set_parent_patch(patched)
        try:
            result=self.world_reparent(frame,parent,flags)
            if (patched and self.guard_state()!=(0,0,1,4,1)) or (not patched and self.guard_state()[0]!=self.adapter.CONTEXT):
                raise ValueError('World parent correction registry gate differs')
            if not patched:
                if self.setup_call(b'Hd2BeforeHandModelChange',[self.STATE,STATE_SIZE,self.MODELS[0],0,3])!=1:
                    raise ValueError('Unpatched world cleanup failed')
        finally:self.set_parent_patch(False)
        if bytes(self.uc.mem_read(0x10000000,self.native_size))!=self.pristine_image:raise ValueError('World parent image not restored')
        if self.setup_parent(b'Hd2ConfigureParentHooks',[0,0]):raise ValueError('World parent hook disconnect failed')
        if bytes(self.uc.mem_read(PARENT_BASE+0x2000,4096))!=self.parent_data:raise ValueError('World parent global not restored')
        self.adapter.check_constants()
        return {**result,'case':case,'turned':turned,'patched':patched,'parent_prologue_checks':self.parent_checks,
            'compiled_parent_notifications':self.parent_calls.get('Hd2BeforeHandParentChange',0),'native_image_fully_restored':True,
            'native_immediate_refresh_executed':False,'scene_notifications_executed':False,'native_allocator_or_destructor_executed':False,
            'game_started':False,'game_modified':False,'hand_correction_executed':False,'live_model_lifetime_qualified':False}
