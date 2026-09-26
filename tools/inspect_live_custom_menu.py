"""Read-only inspection of the known H&D2 test process's menu structures.

Does not inject code, write memory, send input, capture screens or modify files.
"""
from pathlib import Path
import argparse
import ctypes as c
from ctypes import wintypes as w
import json
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.research/binary-patch-deps'))
import pefile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('pid',type=int)
p.add_argument('--module-base',type=lambda s:int(s,0),required=True)
args=p.parse_args()
k=c.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
k.ReadProcessMemory.argtypes=[w.HANDLE,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)]
k.QueryFullProcessImageNameW.argtypes=[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)]
k.CloseHandle.argtypes=[w.HANDLE]
h=k.OpenProcess(0x1010,False,args.pid)
if not h: raise c.WinError(c.get_last_error())
try:
    path=c.create_unicode_buffer(32768);length=w.DWORD(len(path))
    if not k.QueryFullProcessImageNameW(h,0,path,c.byref(length)): raise c.WinError(c.get_last_error())
    expected=Path(r'D:\Games\Hidden and Dangerous 2 - Test Menu Personnalise\HD2_SabreSquadron.exe')
    if str(expected).casefold()!=path.value.casefold(): raise ValueError('Not the authorized test game')
    def read(at,n):
        buf=c.create_string_buffer(n);got=c.c_size_t()
        if not k.ReadProcessMemory(h,at,buf,n,c.byref(got)) or got.value!=n:
            raise ValueError('Unreadable game address %08X'%at)
        return buf.raw
    def word(at):return struct.unpack('<I',read(at,4))[0]
    def words(at,n):return [hex(x) for x in struct.unpack('<%dI'%n,read(at,n*4))]
    pe=pefile.PE(str(expected.parent/'Scripts/HD2.CustomMenu.asi'))
    exports={s.name.decode():args.module_base+s.address for s in pe.DIRECTORY_ENTRY_EXPORT.symbols}
    out={'process':path.value,'exports':{name:hex(word(exports[name])) for name in (
        'MenuView','MenuMissionScreen','MenuMissionScene','MenuSavedVisibility','MenuCustomVisibility')}}
    manager=word(0x8aea10)
    out['manager']=words(manager,4)
    # Build-time definitions are released by the engine; never dereference them.
    if 'MenuCategoryIds' in exports:
        out['category_ids']=words(exports['MenuCategoryIds'],3)
    current=0
    if word(0x8ae5f0):
        stack=0x8ae5c4+0x14
        begin,cur,block=word(stack),word(stack+8)-4,word(stack+12)
        offset=(cur-begin)//4
        page=offset//1024
        cell=cur if page==0 else word(block+page*4)+(offset-page*1024)*4
        current=word(cell)
    out['runtime_root']=hex(current)
    visited=set()
    def runtime(obj,depth=0):
        if not obj or obj in visited or depth>4:return None
        visited.add(obj)
        begin,end=word(obj+8),word(obj+12)
        children=[]
        if begin and begin<=end<=begin+2048:
            children=[runtime(word(slot),depth+1) for slot in range(begin,end,4)]
        result={'address':hex(obj),'vtable':hex(word(obj)),
            'id':hex(word(obj+0x60)),'visible':read(obj+0x65,1)[0],
            'scene':hex(word(obj+0x50)),
            'children':children}
        if word(obj)==0x814a08:
            begin,end=word(obj+0xa4),word(obj+0xa8)
            result['first_visible']=word(obj+0x98)
            result['last_visible']=word(obj+0x9c)
            if begin and begin<=end<=begin+2048:
                result['inactive_rows']=[{'id':hex(word(word(slot)+0x60)),
                    'visible':read(word(slot)+0x65,1)[0]} for slot in range(begin,end,4)]
        return result
    if current:out['runtime']=runtime(current)
    print(json.dumps(out,indent=2))
finally:k.CloseHandle(h)
