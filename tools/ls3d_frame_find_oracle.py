"""Pinned native frame lookup and direct-child enumeration on synthetic trees.

No scene/model load, cloning, animation, renderer, allocation or OS calls.
Only ASCII exact-name matching (optionally case-insensitive) is qualified.
"""
import struct
from ls3d_math_oracle import MathOracle

START=0x1001ded0
ENUM=0x1001de40
COUNT=0x1001db80
CHILD=0x1001dba0
GLOBAL=0x100be440
RANGES=((START,0x1001deff),(ENUM,0x1001dea7),(0x1001dbd0,0x1001ddfa),
    (0x1001deb0,0x1001dec2),(0x10098740,0x10098793),(0x1009880b,0x10098810),
    (COUNT,0x1001dbc8))
TYPE_MASK={1:1,6:0x20,9:0x80,10:0x400}


def name_bytes(name):
    if not isinstance(name,str) or not 1<=len(name)<=63:raise ValueError('Unreviewed scene query/name')
    try:raw=name.encode('ascii')
    except UnicodeEncodeError as error:raise ValueError('Only ASCII scene names reviewed') from error
    if any(v<32 or v==127 for v in raw) or '*' in name or '?' in name:
        raise ValueError('Unreviewed control character or wildcard')
    return raw+b'\0'


def validate(nodes,query,flags):
    name_bytes(query)
    if type(flags) is not int or flags not in (1,0x21,0xffff,0x20001,0x20021,0x2ffff):
        raise ValueError('Unreviewed scene search flags')
    if not isinstance(nodes,list) or not 1<=len(nodes)<=128:raise ValueError('Unreviewed scene tree size')
    for index,node in enumerate(nodes):
        if not isinstance(node,dict) or set(node)!={'name','frame_type','parent'}:
            raise ValueError('Unexpected scene node fields')
        name_bytes(node['name'])
        if type(node['frame_type']) is not int or node['frame_type'] not in TYPE_MASK:
            raise ValueError('Unreviewed scene frame kind')
        if type(node['parent']) is not int or not -1<=node['parent']<index:
            raise ValueError('Scene tree must be acyclic and parent-first')


def reference(nodes,query,flags=1):
    validate(nodes,query,flags);children={i:[] for i in range(-1,len(nodes))}
    for i,node in enumerate(nodes):children[node['parent']].append(i)
    def visit(index):
        node=nodes[index];match=node['name']==query if flags&0x20000 else node['name'].lower()==query.lower()
        if flags&TYPE_MASK[node['frame_type']] and match:return index
        for child in children[index]:
            found=visit(child)
            if found is not None:return found
        return None
    for root in children[-1]:
        found=visit(root)
        if found is not None:return {'index':found,'direct_children':children[found]}
    return {'index':None,'direct_children':[]}


class FrameFindOracle(MathOracle):
    TREE=0x3a00000
    TREE_SIZE=0x20000

    def __init__(self,raw):
        super().__init__(raw)
        self.uc.mem_map(self.TREE,self.TREE_SIZE,self.uni.UC_PROT_READ)
        self.uc.mem_protect(GLOBAL&~4095,4096,self.uni.UC_PROT_READ|self.uni.UC_PROT_WRITE)
        # Only the native ASCII/C-locale fast path is in the reviewed domain.
        if struct.unpack('<I',self.uc.mem_read(0x100d743c,4))[0]:
            raise ValueError('Unexpected native locale state')

    def on_code(self,uc,address,size,context):
        if self.phase!='frame_find':return super().on_code(uc,address,size,context)
        if not any(a<=address and address+size<=b for a,b in RANGES):
            raise ValueError('Unreviewed scene lookup instruction, locale or callback')

    def on_write(self,uc,access,address,size,value,context):
        if self.phase!='frame_find':return super().on_write(uc,access,address,size,value,context)
        if self.STACK<=address and address+size<=self.STACK+65536:return
        if address==GLOBAL and size==4 and value==0:return
        raise ValueError('Scene lookup wrote outside stack/zero enumeration sentinel')

    def execute(self,start,arguments):
        stack=self.STACK+0xf000;self.uc.mem_write(self.STACK,bytes(65536))
        self.uc.mem_write(stack,struct.pack('<'+'I'*(len(arguments)+1),self.STOP,*arguments))
        for register in ('EAX','EBX','ECX','EDX','ESI','EDI','EBP'):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+register),0)
        for register,value in (('ESP',stack),('EFLAGS',2)):
            self.uc.reg_write(getattr(self.reg,'UC_X86_REG_'+register),value)
        self.phase='frame_find'
        try:
            self.uc.emu_start(start,self.STOP,count=1_000_000,timeout=5_000_000)
            if self.uc.reg_read(self.reg.UC_X86_REG_EIP)!=self.STOP:raise ValueError('Scene lookup budget exhausted')
            if self.uc.reg_read(self.reg.UC_X86_REG_ESP)!=stack+4*(len(arguments)+1):
                raise ValueError('Scene lookup calling convention differs')
            return self.uc.reg_read(self.reg.UC_X86_REG_EAX)
        finally:self.phase=None

    def find(self,nodes,query,flags=1):
        if self.phase is not None:raise ValueError('Nested frame lookup')
        expected=reference(nodes,query,flags);source=bytearray(self.TREE_SIZE)
        pointers=[self.TREE+0x1000+(i+1)*0x180 for i in range(len(nodes))];container=self.TREE+0x1000
        table=self.TREE+0x100;struct.pack_into('<I',source,0x144,ENUM)
        children={i:[] for i in range(-1,len(nodes))}
        for i,node in enumerate(nodes):children[node['parent']].append(i)
        for index in range(-1,len(nodes)):
            pointer=container if index==-1 else pointers[index];offset=pointer-self.TREE
            struct.pack_into('<I',source,offset,table)
            struct.pack_into('<H',source,offset+0xf8,9 if index==-1 else nodes[index]['frame_type'])
            if index!=-1:
                string_at=0x14000+index*64;value=name_bytes(nodes[index]['name'])
                source[string_at:string_at+len(value)]=value
                struct.pack_into('<I',source,offset+0xe8,self.TREE+string_at)
            if children[index]:
                struct.pack_into('<I',source,offset+0x10c,pointers[children[index][0]])
                for left,right in zip(children[index],children[index][1:]):
                    struct.pack_into('<I',source,pointers[left]-self.TREE+0x110,pointers[right])
        encoded=name_bytes(query);source[0x1f000:0x1f000+len(encoded)]=encoded
        self.uc.mem_write(self.TREE,bytes(source))
        result=self.execute(START,[container,self.TREE+0x1f000,flags])
        expected_pointer=0 if expected['index'] is None else pointers[expected['index']]
        if result!=expected_pointer:raise ValueError('Native scene frame lookup differs')
        actual_children=[]
        if result:
            count=self.execute(COUNT,[result])
            if count!=len(expected['direct_children']):raise ValueError('Native direct child count differs')
            for i in range(count+1):
                child=self.execute(CHILD,[result,i])
                wanted=0 if i==count else pointers[expected['direct_children'][i]]
                if child!=wanted:raise ValueError('Native child enumeration differs')
                if child:actual_children.append(pointers.index(child))
        if bytes(self.uc.mem_read(self.TREE,self.TREE_SIZE))!=bytes(source):
            raise ValueError('Native lookup changed source tree or names')
        return {**expected,'direct_children':actual_children,'flags':flags,
            'native_frame_find_and_direct_children_match':True,'source_tree_preserved':True,
            'case_sensitive':bool(flags&0x20000),'synthetic_tree_order_is_explicit':True,
            'native_loader_executed':False,'clone_or_model_add_executed':False,
            'animation_or_renderer_called':False,'library_loaded':False,'game_started':False}
