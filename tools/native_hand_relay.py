"""Private native model-tick relay into the compiled hand adapter.

Only this emulator's pinned image is patched. No file patch, process injection,
Windows loader or game launch. The original recursive Refresh executes on a
supplied joint hierarchy; no loaded scene, skin, bounds or renderer is claimed.
"""
from copy import deepcopy
import struct
import math

from ls3d_animation_stream_oracle import AnimationStreamOracle,validate,reference_step,BOOTSTRAP,ATTACH,WEIGHT,TICK
from ls3d_attach_oracle import AttachOracle,reference_sequence
from native_hand_hook import HandHookOracle,ENTRY
from native_hand_pipeline import WORK_SIZE
from build_native_hand_pipeline import invented_case,compare
from build_native_hand_hook import current_data,EXPECTED_CALLS
from modern_animation import encode_5ds
from native_arm_pose_commit import JOINT_VTABLE,REFRESH,REFRESH_RANGES

MODEL_TICK=0x10034ba0
HOOK_SITE=0x10034bc3
HOOK_ORIGINAL=bytes.fromhex('8b0e56ff5124')
RELAY_END=0x10034bcd
MODEL_VTABLE=0x1009ba50


def reference_model_refresh(arena,parents,model):
    """Independent joint forest under one kind-9 model, separate owning visual."""
    arena=bytearray(arena);model=bytearray(model);children={i:[] for i in range(len(parents))};roots=[]
    for i,parent in enumerate(parents):
        (roots if parent==-1 else children[parent]).append(i)
    def get(data,at):return struct.unpack_from('<I',data,at)[0]
    def put(data,at,value):struct.pack_into('<I',data,at,value&0xffffffff)
    def joint(i):
        at=i*0x200;flag=get(arena,at+0xe0)
        if flag&0x40002000:put(arena,at+0x164,get(arena,at+0x164)&0xffffffe7)
        if flag&0x40000000:
            put(arena,0xf218,get(arena,0xf218)+1)
            put(arena,0xf1d0,get(arena,0xf1d0)&0xfff9ffff)
            put(arena,0xf0e0,(get(arena,0xf0e0)&0xfffffeff)|0x40000000)
    def visit(data,at,rows):
        dirty=get(data,at+0xe0)&0x40002000
        if dirty:put(data,at+0x104,get(data,at+0x104)+1)
        for child in rows:
            ca=child*0x200
            if dirty:put(arena,ca+0xe0,(get(arena,ca+0xe0)&0xfffffedf)|0x2000)
            visit(arena,ca,children[child]);joint(child)
            if get(arena,ca+0xe0)&0x40002000:
                put(arena,ca+0xe0,get(arena,ca+0xe0)&0xbfffdfff)
                put(data,at+0xe0,(get(data,at+0xe0)&0xfffffeff)|0x2000)
    visit(model,0,roots)
    put(model,0xe0,get(model,0xe0)&0xbfffdfff)
    return bytes(arena),bytes(model)


def relay_patch(original,site=HOOK_SITE,target=ENTRY):
    """Six-byte plan only, restricted to the reviewed instruction boundary."""
    if (type(original) is not bytes or original!=HOOK_ORIGINAL or type(site) is not int
            or site!=HOOK_SITE or type(target) is not int or target!=ENTRY):
        raise ValueError('Unreviewed native model relay patch contract')
    return b'\xe8'+struct.pack('<i',target-(site+5))+b'\x90'


def fixture(turned=False):
    data,arena,offsets,roles=invented_case(11,turned)
    names=['N'+str(i) for i in range(11)]
    tracks=[]
    # Only the two independent weapon markers animate. All arm poses must be
    # read from the persistent native arena, never rewritten by the host.
    for i in (1,2):
        p=data['poses'][i][:3]
        tracks.append({'name':names[i],'channels':{'position':{'frames':[0,5,10],
            'values':[p,[p[0]-.01,p[1]+.005,p[2]],p]}}})
    raw=encode_5ds({'provenance':'MODERNE','runtime_status':'pending','frame_end':10,'tracks':tracks})
    initial=[{'position':p[:3],'rotation':p[3:7],'scale':p[7:]} for p in data['poses']]
    return data,arena,offsets,roles,names,{'A':{'data':raw,'mode':1}},initial


def sequence_steps():
    attach=lambda clip:{'kind':'attach','clip':clip,'slot':0,'weight':1,'mode':0}
    tick=lambda delta:{'kind':'tick','delta':delta}
    return [tick(40),attach('A'),tick(0),tick(40),tick(0),tick(80),
            {'kind':'weight','slot':0,'weight':0},tick(40),tick(0),
            {'kind':'weight','slot':0,'weight':1},tick(40),attach(None),tick(0),tick(40),
            attach('A'),tick(0),tick(40),attach(None),tick(40)]


class HandRelayOracle(AnimationStreamOracle):
    STATE_SIZE=0x40000

    def __init__(self,library,compiled):
        self.adapter=None;self.relay_active=False;self.refresh_active=False;self.patched=False
        super().__init__(library)
        self.adapter=HandHookOracle(compiled,self)
        original=bytes(self.uc.mem_read(HOOK_SITE,6))
        self.patch=relay_patch(original)
        if bytes(self.uc.mem_read(0x100be46c,4))!=bytes(4):raise ValueError('Deferred refresh queue must be empty')
        self.native_size=next(b-a+1 for a,b,_ in self.uc.mem_regions() if a==0x10000000)
        self.native_image=bytes(self.uc.mem_read(0x10000000,self.native_size))

    def set_patch(self,enabled):
        if type(enabled) is not bool or self.phase is not None or self.adapter.mode is not None:
            raise ValueError('Invalid or active relay patch change')
        expected=self.patch if self.patched else HOOK_ORIGINAL
        if bytes(self.uc.mem_read(HOOK_SITE,6))!=expected:
            raise ValueError('Emulator relay bytes changed outside patch lifecycle')
        self.uc.mem_write(HOOK_SITE,self.patch if enabled else HOOK_ORIGINAL)
        # Unicorn can otherwise reuse the previous translated native block.
        self.uc.ctl_remove_cache(MODEL_TICK,RELAY_END)
        self.patched=enabled

    def capture_boundary(self):
        h=self.adapter
        self.before_hook=bytes(self.uc.mem_read(h.ARENA,65536))
        self.observed=current_data(h,self.data,self.offsets)
        self.state_at_boundary=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE))

    def on_code(self,uc,address,size,context):
        h=self.adapter
        if h is not None and h.mode in ('configure','fpu_init'):
            return h.on_code(uc,address,size,context)
        if not self.relay_active:return super().on_code(uc,address,size,context)
        if address==HOOK_SITE:self.capture_boundary()
        if address==ENTRY:
            if not self.patched or self.before_hook is None or h.mode is not None:
                raise ValueError('Adapter entered without native post-blend boundary')
            h.mode='hook'
            h.expected_integer={k:h.reg_read(k) for k in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP','EFLAGS')}
            h.expected_fpu=h.fpu_state()
            if h.expected_integer['ESI']!=self.STATE+0x100:raise ValueError('Native relay forwarded another model')
        if address==HOOK_SITE+5 and self.patched:
            if h.mode!='hook' or h.refresh_calls!=1:raise ValueError('Relay did not return through its adapter')
            h.check_fpu();h.mode=None
        if self.refresh_active and (address==ENTRY+40 or address==HOOK_SITE+6):
            self.refresh_active=False
        if address==REFRESH:
            if self.before_hook is None or self.refresh_active:raise ValueError('Unexpected native refresh entry')
            if struct.unpack('<I',uc.mem_read(h.reg_read('ESP')+4,4))[0]!=self.STATE+0x100:
                raise ValueError('Native relay refresh argument differs')
            if self.patched:
                for name,value in h.expected_integer.items():
                    if h.reg_read(name)!=(MODEL_VTABLE if name=='ECX' else value):
                        raise ValueError('Adapter changed integer state before native refresh')
                h.check_fpu()
            h.refresh_calls+=1;h.arena_at_refresh=bytes(uc.mem_read(h.ARENA,65536))
            self.model_at_refresh=bytes(uc.mem_read(self.STATE+0x100,0x170));self.refresh_active=True
        if self.refresh_active:
            if not any(a<=address<address+size<=b for a,b in (*REFRESH_RANGES,(0x100881e0,0x100881e1))):
                raise ValueError(f'Unreviewed model refresh instruction: {address:#x}')
            return
        if h.mode=='hook':return h.on_code(uc,address,size,context)
        if MODEL_TICK<=address<address+size<=RELAY_END:return
        if address==TICK:self.controller_calls+=1
        return super().on_code(uc,address,size,context)

    def on_write(self,uc,access,address,size,value,context):
        if self.refresh_active:
            if not any(a<=address and address+size<=b for a,b in ((self.STACK,self.STACK+65536),*self.refresh_writes)):
                raise ValueError('Native model refresh wrote outside its flags/counters')
            return
        if self.adapter is not None and self.adapter.mode is not None:
            return self.adapter.on_write(uc,access,address,size,value,context)
        return super().on_write(uc,access,address,size,value,context)

    def tick(self,delta,writes):
        h=self.adapter;stack=self.STACK+0xf000
        self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<3I',self.STOP,self.STATE+0x100,delta))
        for name,value in {'EAX':0x11111111,'EBX':0x22222222,'ECX':0x33333333,'EDX':0x44444444,
                'ESI':0x55555555,'EDI':0x66666666,'EBP':0x77777777,'ESP':stack,
                'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.before_hook=self.state_at_boundary=self.observed=None;self.controller_calls=0
        h.calls={};h.refresh_calls=0;h.arena_at_refresh=None
        h.allowed=[(h.CONTEXT+52,h.CONTEXT+64),(h.WORK,h.WORK+WORK_SIZE),(h.POSES,h.POSES+h.count*40)]
        for i in h.roles[5:]:
            at=h.ARENA+h.offsets[i];h.allowed.extend(((at+0xc0,at+0xd0),(at+0xe0,at+0xe4)))
        self.phase='tick';self.writes=tuple(writes);self.visited=set();self.pose_calls=0;self.relay_active=True
        try:
            self.uc.emu_start(MODEL_TICK,self.STOP,count=6_000_000,timeout=20_000_000)
            if h.reg_read('EIP')!=self.STOP or h.reg_read('ESP')!=stack+12:
                raise ValueError('Native model relay budget or stack mismatch')
            for name,value in (('EBX',0x22222222),('ESI',0x55555555),('EDI',0x66666666),('EBP',0x77777777)):
                if h.reg_read(name)!=value:raise ValueError('Native relay changed callee-saved register')
        finally:self.relay_active=False;self.refresh_active=False;self.phase=None;self.writes=();h.mode=None

    def run(self,*,turned=False,patched=True,registered=True,controller_present=True):
        try:return self._run(turned=turned,patched=patched,registered=registered,controller_present=controller_present)
        finally:
            self.set_patch(False)
            if bytes(self.uc.mem_read(0x10000000,self.native_size))!=self.native_image:
                raise ValueError('Native relay image not fully restored')

    def _run(self,*,turned,patched,registered,controller_present):
        if any(type(v) is not bool for v in (turned,patched,registered,controller_present)):
            raise ValueError('Expected explicit relay fixture switches')
        h=self.adapter
        if h.count and h.configure(False):raise ValueError('Previous relay failed unregister')
        self.set_patch(patched)
        data,arena,offsets,roles,names,clips,initial=fixture(turned)
        steps=sequence_steps();parsed,poses,steps=validate(names,clips,initial,steps,9)
        AttachOracle.sequence(self,names,clips,[BOOTSTRAP],9)
        state=reference_sequence(names,clips,[BOOTSTRAP],9)[-1];flags=[8]*len(names)
        model,controller=self.STATE+0x100,self.STATE+0x400
        # The same real diagnostic model object is used by native attachment,
        # model tick, compiled callback and native recursive Refresh.
        self.uc.mem_write(model,struct.pack('<I',MODEL_VTABLE))
        mutable=bytearray(arena);nodes=[h.ARENA+at for at in offsets]
        children={i:[] for i in range(len(nodes))};roots=[]
        for i,node in enumerate(nodes):
            self.uc.mem_write(self.SOURCE+0x400+i*4,struct.pack('<I',node))
            struct.pack_into('<I',mutable,offsets[i]+0xe8,self.SOURCE+0x1000+i*64)
            at=offsets[i];parent=data['parents'][i]
            (roots if parent==-1 else children[parent]).append(i)
            struct.pack_into('<I',mutable,at,JOINT_VTABLE)
            struct.pack_into('<I',mutable,at+0x108,model if parent==-1 else nodes[parent])
            struct.pack_into('<I',mutable,at+0x168,h.ARENA+0xf000)
            struct.pack_into('<I',mutable,at+0x164,0x18)
        for i,rows in children.items():
            if rows:struct.pack_into('<I',mutable,offsets[i]+0x10c,nodes[rows[0]])
        for rows in [roots,*children.values()]:
            for a,b in zip(rows,rows[1:]):struct.pack_into('<I',mutable,offsets[a]+0x110,nodes[b])
        self.uc.mem_write(model+0x10c,struct.pack('<I',nodes[roots[0]]))
        struct.pack_into('<I',mutable,0xf0f8,1);struct.pack_into('<I',mutable,0xf0e0,0x11c)
        struct.pack_into('<I',mutable,0xf1d0,0x60000)
        h.seed(data,bytes(mutable),offsets,roles)
        self.uc.mem_write(h.CONTEXT,struct.pack('<I',model))
        if registered and h.configure():raise ValueError('Relay context registration refused')
        self.data,self.offsets=data,offsets
        pointers={'A':self.STATE+0xa000};data_pointers={'A':self.SOURCE+0x10000}
        source=bytes(self.uc.mem_read(self.SOURCE,0xa0000))
        attach_writes=[(0,4),(controller+4,controller+5),(controller+8,controller+0xe8),
            (controller+0xf0,controller+0xf4),(self.STATE+0x800,self.STATE+0xa00),
            (self.STATE+0x10000,self.STATE+0x18000),(pointers['A']+4,pointers['A']+8)]
        attach_writes.extend((n+0xe0,n+0xe4) for n in nodes)
        tick_writes=[(controller+4,controller+5)]
        for i in range(8):tick_writes.extend(((controller+i*0x1c+0xc,controller+i*0x1c+0xd),
                                            (controller+i*0x1c+0x14,controller+i*0x1c+0x20)))
        for n in nodes:tick_writes.extend(((n+0xb0,n+0xbc),(n+0xc0,n+0xe4)))
        self.refresh_writes=[(n+at,n+at+4) for n in nodes for at in (0xe0,0x104,0x164)]
        self.refresh_writes.extend((h.ARENA+0xf000+at,h.ARENA+0xf000+at+4) for at in (0xe0,0x1d0,0x218))
        self.refresh_writes.extend((model+at,model+at+4) for at in (0xe0,0x104))
        rows=[]
        for step in steps:
            kind=step['kind'];runs=kind=='tick' and controller_present and bool(state['owners'])
            expected=reference_step(state,poses,flags,names,clips,parsed,step) if kind!='tick' or runs else {
                'state':deepcopy(state),'poses':deepcopy(poses),'flags':flags[:],'pose_calls':0}
            before=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE));arena_before=bytes(self.uc.mem_read(h.ARENA,65536))
            if kind=='attach':
                writes=attach_writes
                self._invoke(ATTACH,'attach',[model,pointers.get(step['clip'],0),step['slot'],0x3f800000,step['mode']],writes,controller)
            elif kind=='weight':
                writes=[(controller+4,controller+5),(controller+0x20,controller+0x24)]
                self._invoke(WEIGHT,'stream_weight',[model,0,struct.unpack('<I',struct.pack('<f',step['weight']))[0]],writes,controller)
            else:
                writes=tick_writes
                if not controller_present:self.uc.mem_write(model+0x130,bytes(4))
                try:self.tick(step['delta'],writes)
                finally:
                    if not controller_present:self.uc.mem_write(model+0x130,struct.pack('<I',controller))
            actual=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE));after=bytes(self.uc.mem_read(h.ARENA,65536))
            boundary=self.before_hook if kind=='tick' and runs else after
            observed=[];error=0
            for i,at in enumerate(offsets):
                p={k:list(struct.unpack_from('<'+'f'*w,boundary,at+o)) for k,o,w in
                   (('position',0xb0,3),('rotation',0xc0,4),('scale',0xd0,3))}
                if any(not math.isfinite(v) for row in p.values() for v in row):raise ValueError('Nonfinite relay pose')
                error=max(error,*(abs(a-b) for k in p for a,b in zip(p[k],expected['poses'][i][k])));observed.append(p)
                if struct.unpack_from('<I',boundary,at+0xe0)[0]!=expected['flags'][i]:raise ValueError('Pre-hook native flags differ')
            audit_state=self.state_at_boundary if kind=='tick' and runs else actual
            self.check_state(audit_state,expected['state'],parsed,pointers,data_pointers,nodes,node_flags=expected['flags'])
            all_writes=[*writes,*(self.refresh_writes if runs else [])]
            allowed={i-self.STATE for a,b in all_writes if self.STATE<=a<self.STATE+self.STATE_SIZE for i in range(a,b)}
            if (error>2e-6 or self.pose_calls!=expected['pose_calls']
                    or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,actual)))
                    or bytes(self.uc.mem_read(self.SOURCE,0xa0000))!=source
                    or bytes(self.uc.mem_read(0,4096))!=b'\xff'*4+bytes(4092)):
                raise ValueError('Native relay animation/state differs')
            state,poses,flags=expected['state'],expected['poses'],expected['flags']
            if kind!='tick':continue
            corrected=runs and patched and registered
            expected_calls=EXPECTED_CALLS if corrected else {'Hd2OnModelHandPose':1} if runs and patched else {}
            if (self.controller_calls!=int(runs) or h.refresh_calls!=int(runs) or h.calls!=expected_calls
                    or (not runs and after!=arena_before)):
                raise ValueError('Native relay gate or call ordering differs')
            rotation_error=0
            if corrected:
                if struct.unpack('<2I',self.uc.mem_read(h.CONTEXT+52,8))!=(0,0):raise ValueError('Compiled relay correction failed')
                snapshot=struct.pack('<'+'f'*(h.count*10),*(v for p in self.observed['poses'] for v in p))
                if bytes(self.uc.mem_read(h.POSES,h.count*40))!=snapshot:raise ValueError('Relay did not collect native poses')
                rotation_error=compare(self.observed,boundary,h.arena_at_refresh,offsets,roles)
                # Carry an independent reference, not the C result, between ticks.
                from build_native_hand_targets import reference_inputs
                from build_native_hand_constraints import reference_arm
                from ls3d_math_oracle import f32
                ref=deepcopy(data);ref['poses']=[p['position']+p['rotation']+p['scale'] for p in poses]
                inputs=reference_inputs(ref)
                for side in range(2):
                    for i,q in zip(roles[5+side*3:8+side*3],reference_arm(inputs[side*60:side*60+60],1 if side==0 else -1)):
                        if q[3]<0:q=[-v for v in q]
                        poses[i]['rotation']=[f32(v) for v in q]
                        flags[i]=(flags[i]&0xfffffecb)|0x40000008
            elif runs and h.arena_at_refresh!=boundary:raise ValueError('Disabled correction changed native pose')
            if runs:
                wanted_arena,wanted_model=reference_model_refresh(h.arena_at_refresh,data['parents'],self.model_at_refresh)
                if after!=wanted_arena or bytes(self.uc.mem_read(model,0x170))!=wanted_model:
                    raise ValueError('Native model recursive refresh differs')
                flags=[struct.unpack_from('<I',wanted_arena,at+0xe0)[0] for at in offsets]
            h.check_constants()
            rows.append({'delta':step['delta'],'native_controller_calls':self.controller_calls,'native_pose_calls':self.pose_calls,
                'adapter_calls':h.calls.get('Hd2OnModelHandPose',0),'refresh_calls':h.refresh_calls,'corrected':corrected,
                'max_pose_error':error,'max_rotation_error':rotation_error})
        if h.configure(False):raise ValueError('Relay failed final unregister')
        self.set_patch(False)
        return {'turned':turned,'patched':patched,'registered':registered,'controller_present':controller_present,'ticks':rows,
            'same_cpu_and_node_memory':True,'native_model_tick_executed':True,'native_controller_executed':controller_present,
            'compiled_callback_reached_from_native_relay':any(r['adapter_calls'] for r in rows),
            'emulated_patch_restored':True,'refresh_is_synthetic_stand_in':False,'native_refresh_executed':controller_present,
            'x87_exception_addresses_qualified_in_emulator':not h.emulator_restore_limitations,
            'emulator_restore_limitations':h.emulator_restore_limitations[:],
            'owning_visual_bounds_evaluated':False,'model_lifecycle_is_supplied_fixture':True,
            'client_hook_installed':False,'loaded_scene_qualified':False,'game_started':False}
