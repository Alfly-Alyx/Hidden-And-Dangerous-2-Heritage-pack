"""Bounded native model membership transfers with caller-retained references.

Only preallocated vectors and positive reference counts are admitted. No native
allocation, final release, destructor, parent relinking or live client runs.
"""
from copy import deepcopy
import struct

from ls3d_math_oracle import MathOracle,BASE
from native_hand_model_collect import HandModelCollectionOracle
from build_native_hand_model_binding import seed_fixture

ADD=0x100341c0;REMOVE=0x10034260;UNLINK=0x1001c3d0;RELEASE=0x1001c370
RANGES=((ADD,0x100341e6),(0x10034240,0x10034260),(REMOVE,0x100342f0),
        (UNLINK,0x1001c400),(RELEASE,0x1001c38f))
NOT_FOUND=0x80000006
VTABLE=0x1009ba50


def reference_operation(state,kind,model,node):
    """Independent vector swap-removal and separately tracked reference owner."""
    if kind not in ('add','remove') or type(model) is not int or model not in (0,1) or type(node) is not int:
        raise ValueError('Unreviewed membership operation')
    if not 0<=node<len(state['refs']):raise ValueError('Unreviewed membership node')
    result=deepcopy(state)
    def remove(owner):
        vector=result['models'][owner];count=vector['count'];active=vector['slots'][:count]
        if node not in active:return NOT_FOUND
        index=active.index(node);last=count-1
        if index!=last:vector['slots'][index]=vector['slots'][last]
        vector['count']=last;result['owners'][node]=None
        if result['refs'][node]>0:result['refs'][node]-=1
        return 0
    if kind=='remove':return result,remove(model)
    owner=result['owners'][node]
    effective=result['models'][model]['count']-int(owner==model)
    if effective>=128 or not 1<=result['refs'][node]<32767:raise ValueError('Unreviewed allocation or reference boundary')
    result['refs'][node]+=1
    if owner is not None:
        if remove(owner):raise ValueError('Reference owner absent from its vector')
    vector=result['models'][model];vector['slots'][vector['count']]=node;vector['count']+=1;result['owners'][node]=model
    return result,None


class ModelMembershipOracle(MathOracle):
    MODELS=(0x5700000,0x5900000);VECTORS=(0x5800000,0x5a00000)

    def __init__(self,library,compiled_collection):
        self.collector=None
        super().__init__(library)
        self.collector=HandModelCollectionOracle(compiled_collection,self)
        for at in (*self.MODELS,*self.VECTORS,*(self.collector.NODES+i*0x2000 for i in range(128))):
            self.uc.mem_map(at,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        self.native_size=next(b-a+1 for a,b,_ in self.uc.mem_regions() if a==BASE)
        self.native_image=bytes(self.uc.mem_read(BASE,self.native_size))

    def on_code(self,uc,address,size,context):
        if self.collector is not None and self.collector.active:return self.collector.on_code(uc,address,size,context)
        if self.phase!='membership' or not any(a<=address<address+size<=b for a,b in RANGES):
            raise ValueError(f'Unreviewed native membership instruction or allocation/final-release path: {address:#x}')
        for entry,label in ((ADD,'add'),(REMOVE,'remove'),(UNLINK,'unlink_previous_owner'),(RELEASE,'release_positive_reference')):
            if address==entry:self.calls[label]=self.calls.get(label,0)+1

    def on_write(self,uc,access,address,size,value,context):
        if self.collector is not None and self.collector.active:return self.collector.on_write(uc,access,address,size,value,context)
        if self.phase!='membership' or not any(a<=address and address+size<=b for a,b in ((self.STACK,self.STACK+65536),*self.writes)):
            raise ValueError('Native membership write outside reviewed counters, vectors or reference ownership')

    def seed(self,count):
        if count not in (11,128) or self.phase is not None:raise ValueError('Unreviewed membership fixture')
        self.records,_,blocks=seed_fixture(self.collector,count,'ordered',4)
        self.pages={};self.pointers=[r['pointer'] for r in self.records]
        for row,(page,block) in zip(self.records,blocks):
            data=bytearray(block);at=row['pointer']-page
            struct.pack_into('<I',data,at,VTABLE);struct.pack_into('<H',data,at+0xe4,1)
            struct.pack_into('<I',data,at+0x100,0);self.pages[page]=data
        for model,vector in zip(self.MODELS,self.VECTORS):
            data=bytearray(b'Z'*4096);data[:0x170]=bytes(0x170)
            struct.pack_into('<I',data,0,VTABLE);struct.pack_into('<I',data,0xf8,9)
            struct.pack_into('<4I',data,0x120,vector,128,0,128);self.pages[model]=data
            data=bytearray(b'Z'*4096);data[:512]=bytes(512);self.pages[vector]=data
        for page,data in self.pages.items():self.uc.mem_write(page,bytes(data))
        self.state={'models':[{'slots':[None]*128,'count':0} for _ in range(2)],'owners':[None]*count,'refs':[1]*count}
        self.operation_count=0;self.total_calls={};self.collections=[]

    def expected_pages(self,state):
        pages={p:bytearray(v) for p,v in self.pages.items()}
        for i,(model,vector) in enumerate(zip(self.MODELS,self.VECTORS)):
            description=state['models'][i];struct.pack_into('<I',pages[model],0x128,description['count'])
            for j,node in enumerate(description['slots']):struct.pack_into('<I',pages[vector],j*4,0 if node is None else self.pointers[node])
        for i,pointer in enumerate(self.pointers):
            page=pointer&~4095;offset=pointer-page;owner=state['owners'][i]
            struct.pack_into('<I',pages[page],offset+0x100,0 if owner is None else self.MODELS[owner])
            struct.pack_into('<H',pages[page],offset+0xe4,state['refs'][i])
        return pages

    def check_pages(self,state):
        if any(bytes(self.uc.mem_read(at,4096))!=bytes(data) for at,data in self.expected_pages(state).items()):
            raise ValueError('Native membership changed hierarchy, names, transforms, guards or reference state')
        if bytes(self.uc.mem_read(BASE,self.native_size))!=self.native_image:raise ValueError('Native membership changed library image')

    def operation(self,kind,model,node):
        if self.phase is not None or self.collector.active:raise ValueError('Nested native membership operation')
        expected,status=reference_operation(self.state,kind,model,node)
        # Retain at least one caller reference so no destructor/error path can execute.
        if min(expected['refs'])<1:raise ValueError('Final native release is outside the reviewed membership domain')
        self.check_pages(self.state);stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<3I',self.STOP,self.MODELS[model],self.pointers[node]))
        for name,value in {'ESP':stack,'EAX':0,'ECX':0,'EDX':0,'EBX':0x12345678,'ESI':0x23456781,
                           'EDI':0x34567812,'EBP':0x45678123,'EFLAGS':2}.items():
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+name),value)
        self.phase='membership';self.calls={}
        self.writes=[*( (v,v+512) for v in self.VECTORS),*((m+0x128,m+0x12c) for m in self.MODELS)]
        self.writes.extend((p+offset,p+offset+size) for p in self.pointers for offset,size in ((0xe4,2),(0x100,4)))
        try:
            self.uc.emu_start(ADD if kind=='add' else REMOVE,self.STOP,count=100000,timeout=1_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP or self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+12:
                raise ValueError('Native membership budget or stack mismatch')
            for name,value in (('EBX',0x12345678),('ESI',0x23456781),('EDI',0x34567812),('EBP',0x45678123)):
                if self.uc.reg_read(getattr(self.reg,'UC_X86_REG_'+name))!=value:raise ValueError('Native membership callee-saved register differs')
            if status is not None and self.uc.reg_read(self.reg.UC_X86_REG_EAX)!=status:raise ValueError('Native removal status differs')
        finally:self.phase=None;self.writes=()
        self.check_pages(expected);self.state=expected;self.operation_count+=1
        for key,value in self.calls.items():self.total_calls[key]=self.total_calls.get(key,0)+value
        return status

    def collect(self,model,status):
        raw,order,receipt=self.collector.collect(self.MODELS[model],0x170,self.VECTORS[model],512,list(reversed(self.records)))
        if receipt['status']!=status:raise ValueError('Collection disagrees after native membership transfer')
        self.check_pages(self.state);self.collections.append(receipt)
        return raw,order

    def scenario(self,count):
        self.seed(count)
        for node in range(count):self.operation('add',0,node)
        self.collect(0,0)
        self.operation('add',0,count//2);self.collect(0,0)
        self.operation('remove',1,count//2)
        for node in range(3):self.operation('add',1,node)
        self.collect(0,2)
        for node in range(3,count):self.operation('add',1,node)
        # Membership transfer does NOT rewrite parent links (+108). The old
        # roots still name model A, so binding all of model B must be refused.
        self.collect(1,13)
        for node in reversed(range(count)):self.operation('add',0,node)
        self.collect(0,0)
        for node in range(count):self.operation('remove',0,node)
        self.collect(0,2);self.operation('remove',0,0)
        if self.state['refs']!=[1]*count or self.state['owners']!=[None]*count:
            raise ValueError('Caller-retained references not restored')
        return {'nodes':count,'operations':self.operation_count,'native_calls':self.total_calls,'collections':self.collections,
            'model_vectors_and_reference_counts_match':True,'hierarchy_names_transforms_and_guards_unchanged':True,
            'all_caller_references_retained':True,'membership_transfer_is_not_parent_relinking':True,
            'native_allocator_executed':False,'native_destructor_executed':False,'live_lifetime_qualified':False,
            'game_started':False,'windows_library_loaded':False,'game_modified':False}
