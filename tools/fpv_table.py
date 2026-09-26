"""Read structured FPV resource associations, leaving event semantics opaque."""
import hashlib
import struct


def chunks(data,start,end):
    result=[]
    while start<end:
        if end-start<6: raise ValueError('Truncated FPV chunk header')
        kind,size=struct.unpack_from('<HI',data,start)
        if size<6 or start+size>end: raise ValueError('Invalid FPV chunk bounds')
        result.append((kind,start,start+size));start+=size
    return result


def unique(items,label):
    if len({x[0] for x in items})!=len(items): raise ValueError('Duplicate FPV '+label)


def parse(data):
    roots=chunks(data,0,len(data))
    if len(roots)!=1 or roots[0][0]!=12345: raise ValueError('Invalid FPV root')
    group_chunks=chunks(data,6,len(data));unique(group_chunks,'group')
    groups=[]
    for group_id,start,end in group_chunks:
        state_chunks=chunks(data,start+6,end);unique(state_chunks,'state')
        states=[]
        for state_id,sa,sb in state_chunks:
            channel_chunks=chunks(data,sa+6,sb);unique(channel_chunks,'channel')
            if {c[0] for c in channel_chunks}!={3000,3001,3002,3003}:
                raise ValueError('Unexpected FPV channel set')
            channels=[]
            for channel_id,ca,cb in channel_chunks:
                position=ca+6;variants=[]
                while position<cb:
                    if cb-position<10: raise ValueError('Truncated FPV variant')
                    kind,size=struct.unpack_from('<HI',data,position)
                    if kind!=1000 or size<8 or position+size+4>cb:
                        raise ValueError('Invalid FPV resource entry')
                    raw=data[position+6:position+size]
                    if raw[-1]!=0 or b'\0' in raw[:-1]: raise ValueError('Invalid FPV resource name')
                    name=raw[:-1].decode('cp1252')
                    if any(ord(c)<32 for c in name): raise ValueError('Control character in FPV resource name')
                    value=struct.unpack_from('<I',data,position+size)[0]
                    variants.append({'name':name,'value_raw':value});position+=size+4
                channels.append({'id':channel_id,'variants':variants})
            states.append({'id':state_id,'channels':channels})
        groups.append({'id':group_id,'offset':start,'size':end-start,
                       'sha256':hashlib.sha256(data[start:end]).hexdigest(),'states':states})
    return {'groups':groups,'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'event_semantics_qualified':False,'weapon_binding_qualified':False}
