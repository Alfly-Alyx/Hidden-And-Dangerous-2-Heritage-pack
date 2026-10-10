"""Private native parent changes retire the same compiled hand registry.

Only diagnostic trees and SetParent flags 0/2 (no world-transform preservation,
no immediate refresh) execute. The parent guard itself is independent of flags.
"""
from copy import deepcopy
import struct

from build_modern_equipment_hose import digest
from native_hand_lifecycle_hooks import NativeHandLifecycleHooksOracle,LifecycleRefusal,REGISTERS,BASE as LIFECYCLE_BASE
from native_hand_lifecycle import STATE_SIZE,CONFIGURE
from native_hand_scatter_hook import BASE as HOOK_BASE,ACTIVE

BASE=0x36000000;BINARY_SIZE=2560
BINARY_SHA='17716a5576e4d1a783d8ec9294a0432810240ebace1d606d6186ac1cba821573'
CODE_END=BASE+0x13b7;WATCHED=BASE+0x20b0
EXPORTS={b'Hd2ConfigureParentHooks':0x1013,b'Hd2BeforeHandParentChange':0x10d3,b'Hd2ParentHookEntry':0x1372}
ARGUMENTS={b'Hd2ConfigureParentHooks':2,b'Hd2BeforeHandParentChange':4,b'Hd2ParentHookEntry':0}
PARENT=0x1001d680;ORIGINAL=bytes.fromhex('558bec83e4f0')
ENTRY=BASE+0x1383;TRAP=BASE+0x13a3;REPLAY=BASE+0x13ab
PATCH=b'\xe8'+struct.pack('<i',ENTRY-PARENT-5)+b'\x90'
RANGES=((PARENT,0x1001d6b2),(0x1001d6c2,0x1001d7c3),(0x1001d952,0x1001d970),
        (0x1001d976,0x1001d988),(0x1001dae6,0x1001daf0))


def reference_parent(tree,frame,parent,flags):
    """Independent ordered forest update; no matrix, lifetime or model-vector edit."""
    if (not isinstance(tree,dict) or type(frame) is not int or frame not in tree
            or type(parent) is not int or (parent and parent not in tree)
            or type(flags) is not int or flags not in (0,2)):
        raise ValueError('Unreviewed parent operation')
    for pointer,row in tree.items():
        if (type(pointer) is not int or not 0x1000<=pointer<=0xffffffff or pointer&3
                or not isinstance(row,dict) or set(row)!={'parent','children','flags'}
                or type(row['parent']) is not int or (row['parent'] and row['parent'] not in tree)
                or type(row['flags']) is not int or not 0<=row['flags']<=0xffffffff or row['flags']&0x1c0000
                or not isinstance(row['children'],list) or any(type(c) is not int or c not in tree for c in row['children'])
                or len(row['children'])!=len(set(row['children']))):
            raise ValueError('Invalid diagnostic parent forest')
    for pointer,row in tree.items():
        if any(tree[c]['parent']!=pointer for c in row['children']):raise ValueError('Invalid diagnostic child backlink')
        if row['parent'] and pointer not in tree[row['parent']]['children']:raise ValueError('Missing parent backlink')
        seen={pointer};cursor=row['parent']
        while cursor:
            if cursor in seen:raise ValueError('Cyclic parent forest')
            seen.add(cursor);cursor=tree[cursor]['parent']
    cursor=parent
    while cursor:
        if cursor==frame:raise ValueError('Parent operation would create a cycle')
        cursor=tree[cursor]['parent']
    result=deepcopy(tree);old=result[frame]['parent']
    if old==parent:return result
    for root in (old,parent):
        cursor=root
        while cursor:
            result[cursor]['flags']&=0xfffffeff
            if not flags&2:break
            cursor=result[cursor]['parent']
    if old:result[old]['children'].remove(frame)
    if parent:result[parent]['children'].insert(0,frame)
    result[frame]['parent']=parent
    result[frame]['flags']=(result[frame]['flags']&0xfffffedf)|0x40000000
    return result


class NativeHandParentHooksOracle(NativeHandLifecycleHooksOracle):
    FOREIGN=0x5b00000

    def __init__(self,library,collection,hook,lifecycle,parent):
        if type(parent) is not bytes or len(parent)!=BINARY_SIZE or digest(parent)!=BINARY_SHA:
            raise ValueError('Unreviewed parent interception image')
        self.parent_setup=False;self.parent_running=False;self.parent_executing=False
        self.parent_patched=False;self.parent_saved=None;self.parent_calls={};self.parent_checks=0
        super().__init__(library,collection,hook,lifecycle)
        import pefile
        pe=pefile.PE(data=parent);mapped=pe.get_memory_mapped_image()
        if (pe.FILE_HEADER.Machine!=0x14c or pe.OPTIONAL_HEADER.ImageBase!=BASE or hasattr(pe,'DIRECTORY_ENTRY_IMPORT')
                or {s.name:s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}!=EXPORTS):
            raise ValueError('Unreviewed parent PE contract')
        self.uc.mem_map(BASE,(len(mapped)+4095)&~4095,self.uni.UC_PROT_READ|self.uni.UC_PROT_EXEC);self.uc.mem_write(BASE,mapped)
        self.uc.mem_protect(BASE+0x2000,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.uc.mem_map(self.FOREIGN,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.parent_data=bytes(self.uc.mem_read(BASE+0x2000,4096))
        if bytes(self.uc.mem_read(PARENT,6))!=ORIGINAL:raise ValueError('Native parent entry differs')

    def set_parent_patch(self,enabled):
        if (type(enabled) is not bool or self.phase is not None or self.setup_active or self.parent_setup
                or self.parent_saved is not None or self.entries):raise ValueError('Active parent patch change')
        if bytes(self.uc.mem_read(0x10000000,self.native_size))!=self.native_image:raise ValueError('Native image differs before parent patch')
        if bytes(self.uc.mem_read(PARENT,6))!=(PATCH if self.parent_patched else ORIGINAL):raise ValueError('Parent patch bytes differ')
        self.uc.mem_write(PARENT,PATCH if enabled else ORIGINAL);self.uc.ctl_remove_cache(PARENT,PARENT+0x100)
        self.parent_patched=enabled;self.native_image=bytes(self.uc.mem_read(0x10000000,self.native_size))

    def on_code(self,uc,address,size,context):
        if self.collector is not None and self.collector.active:return self.collector.on_code(uc,address,size,context)
        if self.adapter is not None and self.adapter.mode is not None:return self.adapter.on_code(uc,address,size,context)
        if address==TRAP:
            if not self.parent_running or self.parent_saved is None or bytes(uc.mem_read(address,2))!=b'\x0f\x0b':
                raise ValueError('Unexpected parent diagnostic trap')
            raise LifecycleRefusal('Parent change stopped before native mutation')
        own=BASE+0x1000<address<address+size<=CODE_END
        registry=HOOK_BASE+0x5314<=address<address+size<=HOOK_BASE+0x54b1
        if own or (registry and (self.parent_setup or self.parent_running)):
            if not self.parent_setup and not self.parent_running:raise ValueError('Parent guard outside explicit phase')
            self.parent_executing=True
            for name,rva in EXPORTS.items():
                if address==BASE+rva:self.parent_calls[name.decode()]=self.parent_calls.get(name.decode(),0)+1
            if address==REPLAY:
                saved=self.parent_saved
                if (saved is None or any(self.adapter.reg_read(k)!=v for k,v in saved['registers'].items())
                        or self.adapter.fpu_state()!=saved['fpu']):raise ValueError('Parent shim changed pre-prologue CPU state')
                self.check_retired(saved)
            return
        self.parent_executing=False
        if self.parent_running:
            if not any(a<=address<address+size<=b for a,b in RANGES):
                raise ValueError(f'Unreviewed parent instruction, world-preservation or scene callback: {address:#x}')
            if self.parent_patched and address==PARENT:
                stack=self.adapter.reg_read('ESP');frame,parent=struct.unpack('<2I',uc.mem_read(stack+4,8))
                state=self.guard_state();owned={self.MODELS[0],*self.watched_nodes}
                self.parent_saved={'registers':{k:self.adapter.reg_read(k) for k in REGISTERS},
                    'fpu':self.adapter.fpu_state(),'state':state,'matched':bool(state[0] and (frame in owned or parent in owned))}
            elif self.parent_patched and address==PARENT+6:
                saved=self.parent_saved
                if saved is None:raise ValueError('Missing parent prologue snapshot')
                wanted=dict(saved['registers']);old_stack=wanted['ESP'];wanted['EBP']=old_stack-4;wanted['ESP']=(old_stack-4)&~15
                # AND clears CF/OF and sets SF/ZF/PF. AF is architecturally undefined.
                value=wanted['ESP'];bits=(0x80 if value&0x80000000 else 0)|(0x40 if not value else 0)|(4 if (value&255).bit_count()%2==0 else 0)
                wanted['EFLAGS']=(wanted['EFLAGS']&~0x8d5)|bits
                if any((self.adapter.reg_read(k)&(~0x10 if k=='EFLAGS' else 0xffffffff))!=v for k,v in wanted.items()):
                    raise ValueError('Parent original prologue replay differs')
                if struct.unpack('<I',uc.mem_read(old_stack-4,4))[0]!=saved['registers']['EBP'] or self.adapter.fpu_state()!=saved['fpu']:
                    raise ValueError('Parent prologue stack or x87 differs')
                self.check_retired(saved);self.parent_checks+=1;self.parent_saved=None
            return
        return super().on_code(uc,address,size,context)

    def check_retired(self,saved):
        old=saved['state']
        expected=(0,0,old[2],4,min(old[4]+1,0xffffffff)) if saved['matched'] else old
        if self.guard_state()!=expected or (saved['matched'] and struct.unpack('<I',self.uc.mem_read(ACTIVE,4))[0]):
            raise ValueError('Parent change not retired before original prologue')
        self.check_pages(self.state)

    def on_write(self,uc,access,address,size,value,context):
        if self.collector is not None and self.collector.active:return self.collector.on_write(uc,access,address,size,value,context)
        if self.adapter is not None and self.adapter.mode is not None:return self.adapter.on_write(uc,access,address,size,value,context)
        if self.parent_executing or self.parent_setup:
            if not any(a<=address and address+size<=b for a,b in ((self.STACK,self.STACK+65536),
                    (self.STATE,self.STATE+STATE_SIZE),(WATCHED,WATCHED+4),(ACTIVE,ACTIVE+4),
                    (self.adapter.CONTEXT+44,self.adapter.CONTEXT+52))):raise ValueError('Parent guard wrote outside metadata')
            return
        return super().on_write(uc,access,address,size,value,context)

    def setup_parent(self,name,args):
        if (self.parent_setup or self.phase is not None or self.setup_active or name not in ARGUMENTS
                or not isinstance(args,list) or len(args)!=ARGUMENTS[name]
                or any(type(v) is not int or not 0<=v<=0xffffffff for v in args)):raise ValueError('Invalid parent setup invocation')
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(1+len(args)),self.STOP,*args))
        preserved={'EBX':0x12345678,'ESI':0x23456781,'EDI':0x34567812,'EBP':0x45678123}
        for key,value in {**preserved,'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EFLAGS':2}.items():self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+key),value)
        self.parent_setup=True
        try:
            self.uc.emu_start(BASE+EXPORTS[name],self.STOP,count=100000,timeout=1_000_000)
            if (self.adapter.reg_read('EIP')!=self.STOP or self.adapter.reg_read('ESP')!=stack+4
                    or any(self.adapter.reg_read(k)!=v for k,v in preserved.items())):raise ValueError('Parent setup ABI differs')
            return self.adapter.reg_read('EAX')
        finally:self.parent_setup=False;self.parent_executing=False

    def seed_tree(self,count):
        self.seed(count);self.tree={}
        pointers=[*self.MODELS,*self.pointers,self.FOREIGN+4]
        extra=bytearray(b'Z'*4096);extra[4:4+0x170]=bytes(0x170)
        struct.pack_into('<I',extra,4+0xf8,10);struct.pack_into('<H',extra,4+0xe4,1)
        struct.pack_into('<I',extra,4+0x108,self.MODELS[1]);self.pages[self.FOREIGN]=extra
        for pointer in pointers:
            page=pointer&~4095;offset=pointer-page;data=self.pages[page]
            self.tree[pointer]={'parent':struct.unpack_from('<I',data,offset+0x108)[0],'children':[],'flags':0x11c}
        for pointer,row in self.tree.items():
            if row['parent']:self.tree[row['parent']]['children'].append(pointer)
        self.pages=self.tree_pages(self.tree)
        for page,data in self.pages.items():self.uc.mem_write(page,bytes(data))
        self.check_pages(self.state)

    def tree_pages(self,tree):
        pages={p:bytearray(raw) for p,raw in self.pages.items()}
        for pointer,row in tree.items():
            at=pointer-(pointer&~4095);data=pages[pointer&~4095]
            siblings=tree[row['parent']]['children'] if row['parent'] else []
            position=siblings.index(pointer) if row['parent'] else -1
            following=siblings[position+1] if position>=0 and position+1<len(siblings) else 0
            struct.pack_into('<I',data,at+0xe0,row['flags'])
            struct.pack_into('<3I',data,at+0x108,row['parent'],row['children'][0] if row['children'] else 0,following)
        return pages

    def reparent(self,frame,parent,flags=0):
        if self.phase is not None or self.setup_active or self.parent_setup:raise ValueError('Nested parent operation')
        expected=reference_parent(self.tree,frame,parent,flags);expected_pages=self.tree_pages(expected)
        self.check_pages(self.state);stack=self.STACK+0xf000
        self.uc.mem_write(self.STACK,bytes(65536));self.uc.mem_write(stack,struct.pack('<4I',self.STOP,frame,parent,flags))
        preserved={'EBX':0x12345678,'ESI':0x23456781,'EDI':0x34567812,'EBP':0x45678123}
        for key,value in {**preserved,'ESP':stack,'EAX':0x11111111,'ECX':0x22222222,'EDX':0x33333333,'EFLAGS':0x402}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+key),value)
        self.phase='membership';self.parent_running=True
        self.writes=tuple((p+at,p+at+4) for p in self.tree for at in (0xe0,0x108,0x10c,0x110))
        try:
            self.uc.emu_start(PARENT,self.STOP,count=100000,timeout=1_000_000)
            if (self.adapter.reg_read('EIP')!=self.STOP or self.adapter.reg_read('ESP')!=stack+16 or self.adapter.reg_read('EAX')
                    or self.parent_saved is not None or any(self.adapter.reg_read(k)!=v for k,v in preserved.items())):
                raise ValueError('Parent native return ABI differs')
        finally:self.phase=None;self.parent_running=False;self.parent_executing=False;self.parent_saved=None;self.writes=()
        old=self.pages;self.pages=expected_pages
        try:self.check_pages(self.state)
        except Exception:self.pages=old;raise
        self.tree=expected

    def watch_existing(self,count):
        self.watch_model(count)

    def scenario_parent(self,count):
        self.seed_tree(count);self.parent_calls={};self.parent_checks=0
        self.uc.mem_write(self.STATE,bytes(STATE_SIZE)+b'Z'*(4096-STATE_SIZE))
        for node in range(count):self.operation('add',0,node)
        for name,call in ((b'Hd2ConfigureLifecycleHooks',self.setup_call),(b'Hd2ConfigureParentHooks',self.setup_parent)):
            if call(name,[self.STATE,STATE_SIZE]):raise ValueError('Shared parent guard setup failed')
        self.watch_existing(count);self.set_patches(True);self.set_parent_patch(True);rows=[]
        try:
            if self.setup_parent(b'Hd2ConfigureParentHooks',[0,0])!=1:raise ValueError('Active parent guard replaced')
            self.adapter.mode='fpu_init'
            try:self.uc.emu_start(self.adapter.FPU_INIT,self.adapter.FPU_INIT+6,count=3)
            finally:self.adapter.mode=None
            # An unrelated frame may detach while the registered model stays watched.
            self.reparent(self.FOREIGN+4,0,2)
            if self.guard_state()[0]!=self.adapter.CONTEXT:raise ValueError('Foreign parent change retired the context')
            rows.append({'operation':'foreign_detach','retired':False})
            # Attaching an uncollected frame beneath an owned frame still retires.
            self.reparent(self.FOREIGN+4,self.pointers[0],2)
            if self.guard_state()[3]!=4:raise ValueError('Destination membership did not retire parent guard')
            rows.append({'operation':'foreign_attach_under_owned','retired':True})
            self.reparent(self.FOREIGN+4,self.MODELS[1],2);self.watch_existing(count)
            self.uc.mem_write(self.adapter.CONTEXT+40,struct.pack('<I',1));before=self.guard_state()
            try:self.reparent(self.pointers[-1],0)
            except LifecycleRefusal:pass
            else:raise ValueError('Busy parent guard forwarded mutation')
            if self.guard_state()!=before:raise ValueError('Busy parent guard changed watched state')
            self.check_pages(self.state);self.uc.mem_write(self.adapter.CONTEXT+40,bytes(4))
            rows.append({'operation':'busy_detach','native_operation_stopped':True})
            # Non-head child removal, null destination, restoration, then no-op.
            old_parent=self.tree[self.pointers[-1]]['parent'];self.reparent(self.pointers[-1],0,2)
            rows.append({'operation':'owned_detach','retired':True})
            self.reparent(self.pointers[-1],old_parent,2);self.watch_existing(count)
            self.reparent(self.pointers[-1],old_parent,0)
            rows.append({'operation':'same_parent_noop','retired':True})
            self.watch_existing(count);self.reparent(self.MODELS[0],self.MODELS[1],2)
            rows.append({'operation':'watched_model_reparent','retired':True})
            self.reparent(self.MODELS[0],0,2)
            # Same shared guard remains usable by the previously built native hooks.
            self.watch_existing(count);self.operation('add',0,count//2)
            if self.guard_state()!=(0,0,5,1,5):raise ValueError('Membership and parent hooks do not share guard generation')
            rows.append({'operation':'membership_add_after_parent_rearm','retired':True})
            self.check_pages(self.state)
        finally:
            self.parent_saved=None;self.set_parent_patch(False);self.set_patches(False)
        if self.setup_parent(b'Hd2ConfigureParentHooks',[0,0]) or self.setup_call(b'Hd2ConfigureLifecycleHooks',[0,0]):
            raise ValueError('Parent final disconnection failed')
        if (bytes(self.uc.mem_read(BASE+0x2000,4096))!=self.parent_data
                or bytes(self.uc.mem_read(LIFECYCLE_BASE+0x2000,4096))!=self.delivery_data
                or struct.unpack('<I',self.uc.mem_read(ACTIVE,4))[0]
                or bytes(self.uc.mem_read(self.STATE+STATE_SIZE,4096-STATE_SIZE))!=b'Z'*(4096-STATE_SIZE)):
            raise ValueError('Parent data or state guards changed')
        self.adapter.check_constants()
        return {'nodes':count,'operations':rows,'parent_calls':self.parent_calls,'parent_prologue_checks':self.parent_checks,
            'shared_guard_generations':5,'native_parent_flags':[0,2],'hierarchy_and_flags_match_independent_reference':True,
            'model_membership_references_names_and_poses_unchanged_by_reparent':True,'native_image_fully_restored':True,
            'integer_flags_and_x87_preserved_before_native_prologue':True,'world_transform_preservation_executed':False,
            'hand_correction_executed':False,'native_allocator_or_destructor_executed':False,'game_started':False,
            'production_client_refusal_handling_qualified':False,'live_model_lifetime_qualified':False}
