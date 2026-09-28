"""Native clip stream and compiled arm commit on the same private joint records.

No client hook, loaded scene, renderer or operating-system library loading.
The numerical arm solver uses its own bounded CPU; joint memory does not move
between animation, pose commit, recursive refresh and palette calculation.
"""
from copy import deepcopy
import math
import struct

from animation_tick_audit import model_poses
from build_equipment_hand_animation import IDENTITY,HAND_NAMES
from fpv_contact_constraints import correct as reference_correct,ARM_NAMES,targets,world,wrist_errors
from hand_pose_ik import pinned_skin
from ls3d_animation_stream_oracle import AnimationStreamOracle,validate,reference_step,BOOTSTRAP,WEIGHT,TICK,ATTACH
from ls3d_attach_oracle import AttachOracle,reference_sequence
from ls3d_math_oracle import unit
from ls3d_palette_oracle import START as PALETTE_START,STOP as PALETTE_STOP,PALETTE,reference as reference_palette,TOLERANCE
from model_transform import native_affine
from native_arm_pose_commit import (PersistentArmCommitOracle,BINARY_SHA,BINARY_SIZE,BASE,
                                   JOINT_VTABLE,REFRESH,reference_refresh)
from build_modern_equipment_hose import digest
from native_hand_constraints import correct_compiled


def canonical(q):
    q=unit(q)
    return [-v for v in q] if q[3]<0 else q


class SharedPoseMemory(PersistentArmCommitOracle):
    """Delegated CPU hooks; not a second emulator or a copied pose arena."""
    def __init__(self,parent,compiled):
        if type(compiled) is not bytes or len(compiled)!=BINARY_SIZE or digest(compiled)!=BINARY_SHA:
            raise ValueError('Unreviewed original arm commit image')
        import pefile
        mapped=pefile.PE(data=compiled).get_memory_mapped_image()
        self.uc,self.uni,self.reg=parent.uc,parent.uni,parent.reg
        self.NODES=parent.STATE+0x20000;self.NODES_SIZE=0x10000
        self.phase=None;self.writes=();self.visited=set();self.joints=0;self.calls={}
        self.uc.mem_map(BASE,(len(mapped)+4095)&~4095,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC)
        self.uc.mem_write(BASE,mapped)
        self.uc.mem_map(self.SOURCE,self.SOURCE_SIZE,self.uni.UC_PROT_READ)
        self.uc.mem_protect(0x100bf000,0x2000,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        if bytes(self.uc.mem_read(0x100be46c,4))!=bytes(4):raise ValueError('Deferred refresh queue is not empty')

    def seed(self,hand_nodes):
        self.parents=[n['parent_id']-1 for n in hand_nodes];self.count=len(hand_nodes)
        self.indices=[i for i,n in enumerate(hand_nodes) if n['name'] in ARM_NAMES]
        if (self.count!=37 or len(self.indices)!=6 or [n['index'] for n in hand_nodes]!=list(range(1,38))
                or any(not -1<=p<i for i,p in enumerate(self.parents))):
            raise ValueError('Unreviewed shared hand hierarchy')
        source=bytearray(self.SOURCE_SIZE);arena=bytearray(self.uc.mem_read(self.NODES,self.NODES_SIZE))
        owner=0xf000;children={i:[] for i in range(self.count)};self.roots=[]
        struct.pack_into('<II',source,0x210,self.count,self.SOURCE+0x900)
        for i,parent in enumerate(self.parents):
            at=i*0x200;pointer=self.NODES+at
            (self.roots if parent==-1 else children[parent]).append(i)
            struct.pack_into('<I',source,0x900+i*4,pointer)
            struct.pack_into('<16f',source,0x1000+i*96,*IDENTITY)
            struct.pack_into('<I',arena,at,JOINT_VTABLE)
            struct.pack_into('<I',arena,at+0xf8,10)
            struct.pack_into('<f',arena,at+0xbc,1)
            struct.pack_into('<I',arena,at+0x108,self.NODES+(owner if parent==-1 else parent*0x200))
            struct.pack_into('<I',arena,at+0x168,self.NODES+owner)
        for i,rows in children.items():
            if rows:struct.pack_into('<I',arena,i*0x200+0x10c,self.NODES+rows[0]*0x200)
            for a,b in zip(rows,rows[1:]):struct.pack_into('<I',arena,a*0x200+0x110,self.NODES+b*0x200)
        struct.pack_into('<I',arena,owner+0xf8,1)
        struct.pack_into('<I',arena,owner+0xe0,0x11c)
        struct.pack_into('<I',arena,owner+0x1d0,0x60000)
        self.uc.mem_write(self.SOURCE,bytes(source));self.uc.mem_write(self.NODES,bytes(arena))
        self.source=bytes(source)

    def apply_and_refresh(self,poses,replacements):
        before=bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))
        indices=self.indices;offsets=[i*0x200 for i in indices]
        snapshots=[list(struct.unpack_from('<4f',before,at+0xc0)) for at in offsets]
        flags=[struct.unpack_from('<I',before,at+0xe0)[0] for at in offsets]
        if self.commit(offsets,snapshots,replacements,flags)!=0:raise ValueError('Shared arm commit refused')
        before_refresh=bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))
        expected_refresh=reference_refresh(before_refresh,self.parents)
        writes=[(self.NODES+i*0x200+at,self.NODES+i*0x200+at+4)
                for i in range(self.count) for at in (0xe0,0x104,0x164)]
        writes.extend((self.NODES+0xf000+at,self.NODES+0xf000+at+4) for at in (0xe0,0x1d0,0x218))
        for root in self.roots:self.invoke(REFRESH,[self.NODES+root*0x200],'joint_refresh',writes)
        if bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE))!=expected_refresh:
            raise ValueError('Shared native refresh disagrees')
        updated=deepcopy(poses)
        for i,q in zip(indices,replacements):updated[i]['rotation']=q
        expected=reference_palette([{**p,'parent':parent} for p,parent in zip(updated[:self.count],self.parents)],
                                   [IDENTITY]*self.count)
        self.uc.mem_write(PALETTE,b'Z'*4096);stack=self.STACK+0xf000
        self.uc.mem_write(self.STACK,bytes(65536))
        for at,value in ((0x38,self.SOURCE+0x1000),(0x3c,self.SOURCE)):
            self.uc.mem_write(stack+at,struct.pack('<I',value))
        for name,value in {'EAX':0,'EBX':0,'ECX':0,'EDX':0,'ESI':0,'EDI':self.SOURCE,
                'EBP':stack+0x400,'ESP':stack,'EFLAGS':2,'FPCW':0x27f,'FPSW':0,'FPTAG':0xffff}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase='palette';self.joints=self.count;self.calls={}
        try:
            self.uc.emu_start(PALETTE_START,PALETTE_STOP,count=4096+800*self.count**2,timeout=5_000_000)
            if (self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=PALETTE_STOP
                    or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack):raise ValueError('Shared palette did not finish')
        finally:self.phase=None;self.joints=0
        actual=bytes(self.uc.mem_read(self.NODES,self.NODES_SIZE));pal=bytes(self.uc.mem_read(PALETTE,4096))
        error=0;allowed=set();matrices=[]
        for i in range(self.count):
            for key,at in (('local_matrices',0x80),('world_matrices',0x120)):
                row=list(struct.unpack_from('<16f',actual,i*0x200+at))
                if any(not math.isfinite(v) for v in row):raise ValueError('Nonfinite shared matrix')
                error=max(error,*(abs(a-b) for a,b in zip(row,expected[key][i])))
                if key=='world_matrices':matrices.append(row)
            row=struct.unpack_from('<16f',pal,i*64)
            if any(not math.isfinite(v) for v in row):raise ValueError('Nonfinite shared palette')
            error=max(error,*(abs(a-b) for a,b in zip(row,expected['palette'][i])))
            for a,b in ((0x80,0x8c),(0x90,0x9c),(0xa0,0xac),(0xe0,0xe4),(0x120,0x160),(0x164,0x168)):
                allowed.update(range(i*0x200+a,i*0x200+b))
        if (error>TOLERANCE or pal[self.count*64:]!=b'Z'*(4096-self.count*64)
                or bytes(self.uc.mem_read(self.SOURCE,self.SOURCE_SIZE))!=self.source
                or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(expected_refresh,actual)))):
            raise ValueError('Shared palette changed protected state or differs')
        return updated,matrices,{'max_matrix_error':error,'local_rebuilds':self.calls.get(0x1002d450,0),
            'owner_change_counter':struct.unpack_from('<I',actual,0xf000+0x218)[0]}


class UnifiedHandPoseOracle(AnimationStreamOracle):
    STATE_SIZE=0x40000

    def __init__(self,library,compiled_commit,solver):
        self.bridge=None
        super().__init__(library)
        self.bridge=SharedPoseMemory(self,compiled_commit);self.solver=solver

    def on_code(self,uc,address,size,context):
        if self.bridge is not None and self.bridge.phase is not None:
            return self.bridge.on_code(uc,address,size,context)
        return super().on_code(uc,address,size,context)

    def on_write(self,uc,access,address,size,value,context):
        if self.bridge is not None and self.bridge.phase is not None:
            return self.bridge.on_write(uc,access,address,size,value,context)
        return super().on_write(uc,access,address,size,value,context)

    def run(self,hand,gear_nodes,names,clips,initial,steps,grips):
        _,skin=pinned_skin(hand);hand_nodes=skin['nodes'];hn=[n['name'] for n in hand_nodes]
        if (set(hn)!=HAND_NAMES or names[:37]!=hn or names[37:]!=[n['name'] for n in gear_nodes]
                or len(names)>=120 or len(set(names))!=len(names)):
            raise ValueError('Unreviewed unified target identities')
        parsed,poses,steps=validate(names,clips,initial,steps,9)
        bootstrap=AttachOracle.sequence(self,names,clips,[BOOTSTRAP],9)
        state=reference_sequence(names,clips,[BOOTSTRAP],9)[-1];flags=[8]*len(names)
        model,controller=self.STATE+0x100,self.STATE+0x400
        nodes=[self.bridge.NODES+i*0x200 for i in range(len(names))]
        pointers={k:self.STATE+0xa000+i*0x100 for i,k in enumerate(clips)}
        data_pointers={k:self.SOURCE+0x10000+i*0x10000 for i,k in enumerate(clips)}
        # Pre-execution fixture construction only. No live or previously bound
        # target is moved: bootstrap has no attached clips and no pose owners.
        for i,(node,pose) in enumerate(zip(nodes,poses)):
            record=bytes(self.uc.mem_read(self.STATE+0x1000+i*0x100,0x100))
            self.uc.mem_write(node,record)
            self.uc.mem_write(self.SOURCE+0x400+i*4,struct.pack('<I',node))
            for channel,offset in (('position',0xb0),('rotation',0xc0),('scale',0xd0)):
                self.uc.mem_write(node+offset,struct.pack('<'+'f'*len(pose[channel]),*pose[channel]))
        self.bridge.seed(hand_nodes)
        source=bytes(self.uc.mem_read(self.SOURCE,0xa0000));samples=[];max_pose_error=0;max_rotation_error=0
        attach_writes=[(0,4),(controller+4,controller+5),(controller+8,controller+0xe8),
            (controller+0xf0,controller+0xf4),(self.STATE+0x800,self.STATE+0xa00),
            (self.STATE+0x10000,self.STATE+0x18000)]
        attach_writes.extend((n+0xe0,n+0xe4) for n in nodes)
        attach_writes.extend((p+4,p+8) for p in pointers.values())
        tick_writes=[(controller+4,controller+5)]
        for i in range(8):tick_writes.extend(((controller+i*0x1c+0xc,controller+i*0x1c+0xd),
                                             (controller+i*0x1c+0x14,controller+i*0x1c+0x20)))
        for node in nodes:tick_writes.extend(((node+0xb0,node+0xbc),(node+0xc0,node+0xe4)))
        for index,step in enumerate(steps):
            expected=reference_step(state,poses,flags,names,clips,parsed,step)
            before=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE));kind=step['kind']
            if kind=='attach':
                writes=attach_writes;weight=struct.unpack('<I',struct.pack('<f',step['weight']))[0]
                self._invoke(ATTACH,'attach',[model,pointers.get(step['clip'],0),step['slot'],weight,step['mode']],writes,controller)
            elif kind=='weight':
                slot=step['slot'];weight=struct.unpack('<I',struct.pack('<f',step['weight']))[0]
                writes=[(controller+4,controller+5),(controller+0x20+slot*0x1c,controller+0x24+slot*0x1c)]
                self._invoke(WEIGHT,'stream_weight',[model,slot,weight],writes,controller)
            else:
                writes=tick_writes;self._invoke(TICK,'tick',[step['delta']],writes,controller)
            actual=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE))
            self.check_state(actual,expected['state'],parsed,pointers,data_pointers,nodes,node_flags=expected['flags'])
            observed=[];error=0
            for i,node in enumerate(nodes):
                pose={}
                for channel,offset,width in (('position',0xb0,3),('rotation',0xc0,4),('scale',0xd0,3)):
                    row=list(struct.unpack_from('<'+'f'*width,actual,node-self.STATE+offset))
                    if any(not math.isfinite(v) for v in row):raise ValueError('Nonfinite unified native pose')
                    error=max(error,*(abs(a-b) for a,b in zip(row,expected['poses'][i][channel])))
                    pose[channel]=row
                observed.append(pose)
            allowed={i-self.STATE for a,b in writes if a>=self.STATE for i in range(a,b)}
            if (error>2e-6 or self.pose_calls!=expected['pose_calls']
                    or bytes(self.uc.mem_read(0,4096))!=b'\xff'*4+bytes(4092)
                    or bytes(self.uc.mem_read(self.SOURCE,0xa0000))!=source
                    or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,actual)))):
                raise ValueError('Unified native stream changed unrelated state or differs')
            state,poses,flags=expected['state'],expected['poses'],expected['flags'];max_pose_error=max(max_pose_error,error)
            if kind!='tick':continue
            raw=dict(zip(names,observed));reference_raw=dict(zip(names,poses))
            corrected,receipt=correct_compiled(hand,gear_nodes,raw,grips,self.solver,
                root_name='fpv_weapon',preserve_observed_elbow_plane=True)
            reference_result,_=reference_correct(hand,gear_nodes,reference_raw,grips,
                root_name='fpv_weapon',preserve_observed_elbow_plane=True)
            replacements=[]
            for i in self.bridge.indices:
                name=names[i];q=canonical(corrected[name]['rotation']);ref=canonical(reference_result[name]['rotation'])
                a=native_affine([0,0,0],q,[1,1,1])[0];b=native_affine([0,0,0],ref,[1,1,1])[0]
                difference=max(abs(a[r][c]-b[r][c]) for r in range(3) for c in range(3))
                if difference>2e-6:raise ValueError(f'Unified solver differs at step {index}, {name}: matrix error {difference:.12g}')
                max_rotation_error=max(max_rotation_error,difference);replacements.append(q)
                poses[i]={**poses[i],'rotation':ref}
            updated,matrices,chain=self.bridge.apply_and_refresh(observed,replacements)
            # The next native call observes these same objects. Reference
            # rotations are carried independently, never replaced by C output.
            arena=bytes(self.uc.mem_read(self.STATE,self.STATE_SIZE))
            flags=[struct.unpack_from('<I',arena,node-self.STATE+0xe0)[0] for node in nodes]
            wanted=targets(world(gear_nodes,raw),grips,root_name='fpv_weapon')
            wrists=wrist_errors(dict(zip(hn,matrices)),wanted)
            if max(wrists.values())>5e-6:raise ValueError('Unified corrected wrist target missed')
            samples.append({'step':index,'delta':step['delta'],'native_pose_calls':self.pose_calls,
                'before':receipt['before'],'after':wrists,**chain})
        return {'steps':len(steps),'samples':samples,'max_native_pose_error':max_pose_error,
                'max_solver_rotation_error':max_rotation_error,'ticks':len(samples),
                'bootstrap':bootstrap,'owner_allocations':self.alloc_count,'owner_releases':self.free_count,
                'native_animation_compiled_commit_refresh_palette_same_memory':True,
                'poses_seeded_only_before_first_operation':True,'reference_corrected_poses_carried_independently':True,
                'solver_cpu_separate':True,'client_hook_implemented':False,'loaded_scene_qualified':False,
                'owning_visual_bounds_evaluated':False,'game_started':False}
