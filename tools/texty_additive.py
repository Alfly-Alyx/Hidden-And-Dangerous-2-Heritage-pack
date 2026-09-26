"""Byte-preserving modern TEXTY additions, not a general commercial text parser.

Existing multiline text, duplicate IDs, comments and encoding bytes stay opaque
and unchanged. A conservative numeric-token scan may reject false positives;
it never claims to parse every legacy text construct or prove global freedom.
"""
import hashlib
import re

ENCODINGS={'czech':'cp1250','english':'cp1252','englishus':'cp1252','french':'cp1252',
           'german':'cp1252','italian':'cp1252','japan':'utf-8','spanish':'cp1252'}
RESERVED=(21500,21531)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def validate(catalogue,*,mission_range):
    if (not isinstance(catalogue,dict) or set(catalogue)!={'schema_version','provenance','status','project_reservation','labels'}
            or type(catalogue['schema_version']) is not int or catalogue['schema_version']!=1
            or catalogue['provenance']!='MODERNE_ORIGINAL' or catalogue['status']!='prototype_disabled'
            or catalogue['project_reservation']!=list(RESERVED)
            or any(type(n) is not int for n in catalogue['project_reservation'])):
        raise ValueError('Unexpected disabled modern text catalogue')
    if (not isinstance(mission_range,(tuple,list)) or len(mission_range)!=2
            or any(type(n) is not int or not 0<=n<=0x7fffffff for n in mission_range)
            or mission_range[0]>mission_range[1]):raise ValueError('Invalid creator text reservation')
    if max(RESERVED[0],mission_range[0])<=min(RESERVED[1],mission_range[1]):
        raise ValueError('Modern inventory range overlaps creator mission reservation')
    labels=catalogue['labels'];ids=set();keys=set()
    if not isinstance(labels,list) or not 1<=len(labels)<=32:raise ValueError('Invalid modern label set')
    for row in labels:
        if not isinstance(row,dict) or set(row)!={'key','text_id','values'}:raise ValueError('Invalid modern label row')
        number=row['text_id'];key=row['key']
        if (type(number) is not int or not RESERVED[0]<=number<=RESERVED[1] or number in ids
                or not isinstance(key,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,47}',key) or key in keys):
            raise ValueError('Invalid or duplicate modern label identity')
        ids.add(number);keys.add(key);values=row['values']
        if not isinstance(values,dict) or set(values)!=set(ENCODINGS):raise ValueError('Incomplete modern label languages')
        for language,value in values.items():
            if (not isinstance(value,str) or not value or any(ord(c)<32 for c in value)
                    or any(c in value for c in ('"','\\')) or '[MODERN' not in value or not value.endswith(']')):
                raise ValueError('Invalid or unmarked modern inventory label')
            try:encoded=value.encode(ENCODINGS[language])
            except UnicodeEncodeError as error:raise ValueError('Modern label is not encodable') from error
            if len(encoded)>80:raise ValueError('Modern inventory label too long')
    return labels


def collision_check(sources,ids):
    if not isinstance(sources,dict) or not sources:raise ValueError('No text sources audited')
    collisions=[]
    for name,raw in sources.items():
        if not isinstance(raw,bytes) or b'\0' in raw:raise ValueError('Unsupported binary/UTF16 text source')
        for number in ids:
            if type(number) is not int or not 0<=number<=0x7fffffff:raise ValueError('Invalid text candidate')
            pattern=rb'(?<![0-9])'+str(number).encode('ascii')+rb'(?![0-9])'
            if re.search(pattern,raw):collisions.append({'source':name,'text_id':number})
    if collisions:raise ValueError('Text ID token already present: '+str(collisions))


def append_labels(raw,labels,language):
    if not isinstance(raw,bytes) or b'\0' in raw or language not in ENCODINGS:
        raise ValueError('Unsupported text source or language')
    if not labels:raise ValueError('No modern labels to append')
    ids=[row['text_id'] for row in labels]
    if len(set(ids))!=len(ids) or any(type(n) is not int or not RESERVED[0]<=n<=RESERVED[1] for n in ids):
        raise ValueError('Invalid or duplicate modern inventory ID')
    collision_check({'target':raw},[row['text_id'] for row in labels])
    content=raw[3:] if raw.startswith(b'\xef\xbb\xbf') else raw
    last=next((line.strip() for line in reversed(content.splitlines()) if line.strip()),b'')
    if (last and not last.startswith((b';',b'//'))
            and not re.fullmatch(rb'[0-9]+[ \t]+"[^\r\n]*"[ \t]*(?:;.*)?',last)):
        raise ValueError('Unreviewed final text boundary; refusing blind append')
    separator=b'\r\n' if b'\r\n' in raw else b'\r' if b'\r' in raw and b'\n' not in raw else b'\n'
    addition=(separator if raw and not raw.endswith((b'\r',b'\n')) else b'')
    addition+=b'; HERITAGE - MODERN INVENTORY - DISABLED LABORATORY'+separator
    for row in labels:
        value=row['values'][language]
        # Revalidate the serialization boundary even when the caller did not
        # validate the whole catalogue. No quote/backslash/control injection.
        if (not isinstance(value,str) or any(ord(c)<32 for c in value)
                or '"' in value or '\\' in value or '[MODERN' not in value or not value.endswith(']')):
            raise ValueError('Invalid modern label serialization')
        try:line=f'{row["text_id"]}\t"{value}"'.encode(ENCODINGS[language])
        except UnicodeEncodeError as error:raise ValueError('Unencodable modern label') from error
        if len(value.encode(ENCODINGS[language]))>80:raise ValueError('Modern inventory label too long')
        addition+=line+separator
    result=raw+addition
    return result,{'original_size':len(raw),'original_sha256':sha(raw),'result_size':len(result),
                   'result_sha256':sha(result),'addition_size':len(addition),'addition_sha256':sha(addition),
                   'existing_bytes_preserved':result[:len(raw)]==raw,'encoding':ENCODINGS[language],
                   'newline_hex':separator.hex(),'native_text_loader_qualified':False}


def remove_append(current,proof):
    if (not isinstance(proof,dict) or any(type(proof.get(k)) is not int or proof[k]<0
            for k in ('original_size','result_size','addition_size'))
            or proof['original_size']+proof['addition_size']!=proof['result_size']):
        raise ValueError('Invalid text append sizes')
    if not isinstance(current,bytes) or len(current)!=proof['result_size'] or sha(current)!=proof['result_sha256']:
        raise ValueError('Changed text output; refusing reversal')
    original=current[:proof['original_size']];addition=current[proof['original_size']:]
    if (sha(original)!=proof['original_sha256'] or len(addition)!=proof['addition_size']
            or sha(addition)!=proof['addition_sha256']):raise ValueError('Inconsistent text append proof')
    return original
