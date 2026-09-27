"""In-memory append-only modern sound entries with exact reversal.

Existing ordered banks, empty slots, variant bytes and opaque lookup payload
are preserved. New direct numeric references are NOT historic symbol resolution.
No source/game file writes, playback or global identifier reservation.
"""
import hashlib
import re
import struct

from sound_definition import parse,chunks,VARIANT_FIELDS

BANKS={2:'Weapon Shooting',3:'Weapon Manipulation'}


def fingerprint(raw):return {'size':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def chunk(kind,payload):return struct.pack('<HI',kind,len(payload)+6)+payload


def encode_entry(spec):
    if (not isinstance(spec,dict) or set(spec)!={'bank','label','flag_raw','variant'}
            or type(spec['bank']) is not int or spec['bank'] not in BANKS
            or not isinstance(spec['label'],str) or not re.fullmatch(r'MODERN [A-Z0-9 _-]{1,48}',spec['label'])
            or type(spec['flag_raw']) is not int or spec['flag_raw'] not in (0,1)):
        raise ValueError('Unreviewed modern sound entry')
    variant=spec['variant']
    if (not isinstance(variant,dict) or set(variant)!={'filename','parameters_raw'}
            or not isinstance(variant['filename'],str)
            or not re.fullmatch(r'MOD_[A-Z0-9_]{1,15}\.wav',variant['filename'])
            or not isinstance(variant['parameters_raw'],dict)
            or set(variant['parameters_raw'])!={str(k) for k in VARIANT_FIELDS[1:]}
            or any(type(v) is not int or not 0<=v<=0xffffffff for v in variant['parameters_raw'].values())):
        raise ValueError('Unreviewed modern sound variant')
    payload=chunk(1400,variant['filename'].encode('ascii')+b'\0')
    payload+=b''.join(chunk(tag,struct.pack('<I',variant['parameters_raw'][str(tag)])) for tag in VARIANT_FIELDS[1:])
    return chunk(1200,chunk(1210,spec['label'].encode('ascii')+b'\0')+chunk(1310,bytes([spec['flag_raw']]))+chunk(1300,payload))


def rebuild(data,parsed,tails,*,remove=False):
    banks={b['offset']:b for b in parsed['banks']};parts=[]
    for kind,start,end in chunks(data,6,len(data)):
        if kind!=1100 or banks[start]['index'] not in tails:
            parts.append(data[start:end]);continue
        bank=banks[start];tail=tails[bank['index']]
        if remove:
            last=len(bank['entries'])-len(tail)
            if last<0:raise ValueError('Missing appended sound entries')
            boundary=bank['entries'][last]['offset'] if tail else end
            parts.append(chunk(1100,data[start+6:boundary]))
        else:parts.append(chunk(1100,data[start+6:end]+b''.join(tail)))
    return chunk(1000,b''.join(parts))


def restore(current,receipt):
    if (not isinstance(receipt,dict) or set(receipt)!={'schema_version','scope','before','after','additions',
            'original_entry_count','original_variant_count','opaque_lookup_preserved','existing_entries_preserved',
            'global_indices_reserved','historical_symbols_resolved'}
            or type(receipt['schema_version']) is not int or receipt['schema_version']!=1
            or receipt['scope']!='disabled_modern_sound_append'
            or receipt['after']!=fingerprint(current)
            or receipt['opaque_lookup_preserved'] is not True or receipt['existing_entries_preserved'] is not True
            or receipt['global_indices_reserved'] is not False or receipt['historical_symbols_resolved'] is not False
            or not isinstance(receipt['additions'],list) or not 1<=len(receipt['additions'])<=8):
        raise ValueError('Changed sound append receipt or output')
    parsed=parse(current);tails={}
    for row in receipt['additions']:
        if (not isinstance(row,dict) or set(row)!={'bank','index','label','filename','size','sha256'}
                or type(row['bank']) is not int or row['bank'] not in BANKS
                or type(row['index']) is not int or row['index']<0):raise ValueError('Invalid appended sound row')
        if row['bank']>=len(parsed['banks']):raise ValueError('Missing appended sound bank')
        bank=parsed['banks'][row['bank']]
        if bank['label']!=BANKS[row['bank']] or row['index']>=len(bank['entries']):raise ValueError('Changed sound bank owner')
        entry=bank['entries'][row['index']]
        if (entry['sha256']!=row['sha256'] or entry['size']!=row['size'] or entry['label']!=row['label']
                or len(entry['variants'])!=1 or entry['variants'][0]['filename']!=row['filename']):
            raise ValueError('Changed appended sound entry')
        tails.setdefault(row['bank'],[]).append(row)
    for bank,rows in tails.items():
        count=len(parsed['banks'][bank]['entries'])
        if [r['index'] for r in rows]!=list(range(count-len(rows),count)):
            raise ValueError('Sound append rows are not an ordered tail')
    original=rebuild(current,parsed,tails,remove=True)
    restored=parse(original)
    if (fingerprint(original)!=receipt['before'] or restored['entry_count']!=receipt['original_entry_count']
            or restored['variant_count']!=receipt['original_variant_count']):
        raise ValueError('Restored sound definition differs from its original fingerprint')
    return original


def build(data,additions):
    parsed=parse(data)
    if not isinstance(additions,list) or not 1<=len(additions)<=8:raise ValueError('Unreviewed sound append count')
    labels={e['label'].casefold() for b in parsed['banks'] for e in b['entries']}
    filenames={v['filename'].casefold() for b in parsed['banks'] for e in b['entries'] for v in e['variants']}
    tails={};rows=[]
    for spec in additions:
        raw=encode_entry(spec);index=spec['bank']
        if index>=len(parsed['banks']) or parsed['banks'][index]['label']!=BANKS[index]:
            raise ValueError('Changed sound bank owner')
        label=spec['label'].casefold();filename=spec['variant']['filename'].casefold()
        if label in labels or filename in filenames:raise ValueError('Modern sound alias collision')
        labels.add(label);filenames.add(filename)
        ordinal=len(parsed['banks'][index]['entries'])+len(tails.get(index,[]))
        if ordinal>=256:raise ValueError('Sound bank exceeds reviewed lookup capacity')
        tails.setdefault(index,[]).append(raw)
        rows.append({'bank':index,'index':ordinal,'label':spec['label'],'filename':spec['variant']['filename'],**fingerprint(raw)})
    current=rebuild(data,parsed,tails);after=parse(current)
    for old,new in zip(parsed['banks'],after['banks']):
        if old['label']!=new['label'] or [e['sha256'] for e in old['entries']]!=[e['sha256'] for e in new['entries'][:len(old['entries'])]]:
            raise ValueError('Existing sound entry changed')
    old_lookup=parsed['opaque_lookup'];new_lookup=after['opaque_lookup']
    if (old_lookup is None)!=(new_lookup is None):raise ValueError('Sound lookup presence changed')
    if old_lookup and data[old_lookup['offset']:old_lookup['offset']+old_lookup['size']]!=current[new_lookup['offset']:new_lookup['offset']+new_lookup['size']]:
        raise ValueError('Opaque sound lookup changed')
    receipt={'schema_version':1,'scope':'disabled_modern_sound_append','before':fingerprint(data),'after':fingerprint(current),
        'additions':rows,'original_entry_count':parsed['entry_count'],'original_variant_count':parsed['variant_count'],
        'opaque_lookup_preserved':True,'existing_entries_preserved':True,'global_indices_reserved':False,
        'historical_symbols_resolved':False}
    if restore(current,receipt)!=data:raise ValueError('Sound append reversal failed')
    return current,receipt
