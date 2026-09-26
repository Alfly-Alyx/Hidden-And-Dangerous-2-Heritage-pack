"""Strict read-only codec for the reviewed ordered IngameSounds.def shape.

Empty entries/banks retain their ordinal. Numeric variant parameters and the
top-level 1050 lookup payload remain opaque; no sound is played or exported.
"""
import hashlib
import struct

VARIANT_FIELDS=(1400,1410,1420,1430,1440,1450,1470)


def chunks(data,start,end):
    result=[]
    while start<end:
        if end-start<6:raise ValueError('Truncated sound definition chunk')
        kind,size=struct.unpack_from('<HI',data,start)
        if size<6 or start+size>end:raise ValueError('Invalid sound definition bounds')
        result.append((kind,start,start+size));start+=size
    return result


def text(data,start,end,*,allow_empty=False):
    raw=data[start:end]
    if not raw or raw[-1]!=0 or b'\0' in raw[:-1] or any(b<32 for b in raw[:-1]):
        raise ValueError('Invalid terminated sound text')
    try:value=raw[:-1].decode('cp1252')
    except UnicodeDecodeError as error:raise ValueError('Invalid sound text encoding') from error
    if not value and not allow_empty:raise ValueError('Empty sound resource text')
    return value


def parse(data):
    if not isinstance(data,bytes):raise ValueError('Expected immutable sound definition')
    roots=chunks(data,0,len(data))
    if len(roots)!=1 or roots[0][0]!=1000:raise ValueError('Expected single sound definition root')
    banks=[];lookup=None
    for kind,start,end in chunks(data,6,len(data)):
        if kind==1050:
            if lookup is not None or (end-start-6)%8:raise ValueError('Invalid opaque sound lookup shape')
            raw=data[start+6:end]
            lookup={'offset':start,'size':end-start,'pair_count':len(raw)//8,
                    'sha256':hashlib.sha256(raw).hexdigest(),'semantics_qualified':False}
            continue
        if kind!=1100 or lookup is not None:raise ValueError('Unexpected sound bank order/type')
        children=chunks(data,start+6,end)
        if not children or children[0][0]!=1110 or any(c[0]!=1200 for c in children[1:]):
            raise ValueError('Unexpected sound bank shape')
        label=text(data,children[0][1]+6,children[0][2],allow_empty=True);entries=[]
        for _,a,b in children[1:]:
            fields=chunks(data,a+6,b)
            if ([c[0] for c in fields[:2]]!=[1210,1310]
                    or any(c[0]!=1300 for c in fields[2:])):
                raise ValueError('Unexpected sound entry shape')
            name=text(data,fields[0][1]+6,fields[0][2],allow_empty=True)
            flag=data[fields[1][1]+6:fields[1][2]]
            if flag not in (b'\0',b'\1'):raise ValueError('Unreviewed sound entry flag')
            variants=[]
            for _,va,vb in fields[2:]:
                properties=chunks(data,va+6,vb)
                if tuple(c[0] for c in properties)!=VARIANT_FIELDS or any(c[2]-c[1]!=10 for c in properties[1:]):
                    raise ValueError('Unexpected sound variant properties')
                filename=text(data,properties[0][1]+6,properties[0][2])
                variants.append({'filename':filename,'parameters_raw':{
                    str(tag):struct.unpack_from('<I',data,pa+6)[0] for tag,pa,pb in properties[1:]}})
            entries.append({'index':len(entries),'label':name,'flag_raw':flag[0],
                            'offset':a,'size':b-a,'sha256':hashlib.sha256(data[a:b]).hexdigest(),
                            'variants':variants})
        banks.append({'index':len(banks),'label':label,'offset':start,'size':end-start,'entries':entries})
    return {'size':len(data),'sha256':hashlib.sha256(data).hexdigest(),'banks':banks,
            'entry_count':sum(len(b['entries']) for b in banks),
            'variant_count':sum(len(e['variants']) for b in banks for e in b['entries']),
            'opaque_lookup':lookup,'playback_qualified':False}


def resolve(parsed,bank,index):
    if type(bank) is not int or not 0<=bank<len(parsed['banks']):raise ValueError('Unknown sound bank')
    if type(index) is not int or not 0<=index<=0xffffffff:raise ValueError('Invalid sound index')
    if index==0xffffffff:return None
    entries=parsed['banks'][bank]['entries']
    if index>=len(entries):raise ValueError('Sound index outside its bank')
    return entries[index]
