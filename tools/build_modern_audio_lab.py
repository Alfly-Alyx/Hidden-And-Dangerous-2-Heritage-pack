#!/usr/bin/env python3
"""Private disabled modern audio plus reversible ordered sound-definition tails.

No samples are borrowed, no historic FG42 symbols are resolved, no Item is
installed, and the opaque 1050 lookup remains byte-identical. Only direct
numeric bank lookup is checked in a bounded native emulator, never playback.
"""
import argparse
import json
from pathlib import Path,PurePosixPath
import sys

from build_modern_asset import ROOT,output_directory
from build_modern_equipment_hose import digest
from build_modern_weapon_audio import RECIPES,prepare as prepare_audio
from dta_archive import DtaArchive
from reconstruction_sandbox import normal,destination
from sound_definition import parse
from sound_definition_additive import build as append,restore,fingerprint

ORDER=('models.dta','Maps.dta','Sounds.dta','others.DTA','LangEnglish.dta','Patch.dta','SabreSquadron.dta','PatchX01.dta')
DEFINITION='tables/ingamesounds.def'
PIN=('Patch.dta',104700,'ab374c805b6bc663593bfd788f9e437b6998ffe8a3d02e83a393aa201dfd94f3')
ALIASES={f'MOD_{case}_{suffix}'.casefold() for case in RECIPES for suffix in ('F','R')}
TEMPLATES={'shot':(2,0,'G MP40','f_mp40_a.wav',
    {'1410':100,'1420':1084227584,'1430':1120403456,'1440':0,'1450':1065353216,'1470':0}),
    'reload':(3,2,'G MP40 Reload','mp40_r.wav',
    {'1410':100,'1420':1065353216,'1430':1088421888,'1440':0,'1450':1065353216,'1470':0})}


def read_sources(game,*,archives_only=False):
    normal(game);archives=[];providers={};collisions=[];seen=set()
    for path in sorted(game.iterdir(),key=lambda p:p.name.casefold()):
        if path.suffix.casefold()!='.dta':continue
        normal(path)
        if not path.is_file() or path.name.casefold() in seen:raise ValueError('Ambiguous archive source')
        seen.add(path.name.casefold());stamp=(path.stat().st_size,path.stat().st_mtime_ns);index=[];relevant=set()
        with DtaArchive(path) as archive:
            for entry in archive.entries:
                resource=entry.name.replace('\\','/').casefold();index.append([resource,entry.size])
                parts=PurePosixPath(resource).parts
                alias=len(parts)==2 and parts[0]=='sounds' and PurePosixPath(parts[1]).stem in ALIASES
                if not alias and resource!=DEFINITION:continue
                if resource in relevant:raise ValueError('Duplicate relevant audio archive entry')
                relevant.add(resource)
                if alias:collisions.append({'archive':path.name,'path':resource})
                else:providers[path.name]=archive.read(entry)
        if stamp!=(path.stat().st_size,path.stat().st_mtime_ns):raise ValueError('Archive changed during audio inspection')
        archives.append({'archive':path.name,'size':stamp[0],'entry_count':len(index),
            'name_size_index_sha256':digest(json.dumps(index,separators=(',',':')).encode()),'full_archive_hash':False})
    if not archives or not providers or set(providers)-set(ORDER):raise ValueError('Unreviewed sound definition provider set')
    effective=next(name for name in reversed(ORDER) if name in providers);raw=providers[effective]
    if (effective,len(raw),digest(raw))!=PIN:raise ValueError('Changed effective sound definition')
    loose=destination(game,'Sounds')
    if loose.exists():
        if not loose.is_dir():raise ValueError('Invalid loose sound namespace')
        for path in loose.iterdir():
            if path.stem.casefold() in ALIASES:
                normal(path);collisions.append({'archive':None,'path':'Sounds/'+path.name})
    if collisions:raise ValueError('Modern audio alias collision: '+json.dumps(collisions))
    table=destination(game,'Tables/IngameSounds.def');excluded=None
    if table.exists():
        if not archives_only:raise ValueError('Loose sound definition requires explicit archive-only inspection')
        excluded=fingerprint(table.read_bytes())
    return raw,{'archives':archives,'definition_providers':{name:fingerprint(data) for name,data in providers.items()},
        'effective_provider':effective,'excluded_loose_definition':excluded,'candidate_aliases':sorted(ALIASES),
        'archive_and_direct_loose_alias_conflicts':[],'namespace_scope':'all root DTA archives and direct Sounds children',
        'native_search_order_qualified':False,'global_alias_reservation':False}


def prepare(definition,recipes,machine):
    if (len(definition),digest(definition))!=PIN[1:]:raise ValueError('Changed pinned audio definition')
    if not isinstance(recipes,dict) or set(recipes)!=set(RECIPES):raise ValueError('Both explicit modern audio recipes are required')
    source=parse(definition);choices={};additions=[];files={};audio_reports={}
    for kind,(bank,index,label,filename,parameters) in TEMPLATES.items():
        row=source['banks'][bank]['entries'][index]
        if (row['label']!=label or row['flag_raw']!=0 or row['variants']!=[{'filename':filename,'parameters_raw':parameters}]):
            raise ValueError('Changed explicit numeric audio category baseline')
        choices[kind]={'bank':bank,'index':index,'label':label,'entry_sha256':row['sha256'],
            'parameters_raw':parameters,'flag_raw':0,'only_numeric_settings_adopted':True,
            'parameter_units_or_playback_meanings_qualified':False,'source_sample_read':False}
    for case in RECIPES:
        if recipes[case].get('case')!=case:raise ValueError('Modern audio recipe owner differs')
        generated,audio_report=prepare_audio(recipes[case]);audio_reports[case]=audio_report
        for kind,row in audio_report['effects'].items():
            name=row['filename'];files['Sounds/'+name]=generated[name]
            bank=TEMPLATES[kind][0]
            additions.append({'bank':bank,'label':f'MODERN {case} '+kind.upper(),'flag_raw':0,
                'variant':{'filename':row['intended_stem']+'.wav','parameters_raw':dict(TEMPLATES[kind][4])}})
    current,receipt=append(definition,additions)
    if restore(current,receipt)!=definition:raise ValueError('Modern sound definition reversal differs')
    parsed=parse(current);counts=[len(b['entries']) for b in parsed['banks']];lookups=[]
    for row in receipt['additions']:
        result=machine.lookup(row['bank'],row['index'],counts)
        if result.get('native_synthetic_lookup_matches') is not True or result.get('entry_present') is not True:
            raise ValueError('Incomplete modern audio numeric lookup receipt')
        lookups.append(result)
    append_receipt=machine.append_order()
    if len(append_receipt.get('checks',[]))!=12 or any(r.get('native_append_matches') is not True for r in append_receipt['checks']):
        raise ValueError('Incomplete ordered append receipt')
    files['Tables/IngameSounds.def.disabled']=current
    return files,{'schema_version':1,'scope':'private_disabled_modern_audio_lab','runtime_status':'pending',
        'provenance':'MODERN_AUDIO_AND_EXPLICIT_CATEGORY_SETTINGS','transaction':receipt,
        'audio_recipes':audio_reports,'modern_category_choices':choices,'native_numeric_lookup':lookups,
        'native_ordered_append':append_receipt,'after_bank_counts':counts,'reversal_verified_in_memory':True,
        'files':{name:fingerprint(raw) for name,raw in files.items()},'existing_audio_entries_preserved':True,
        'opaque_1050_lookup_preserved':True,'new_symbolic_lookup_entries_added':False,'historic_fg42_symbols_resolved':False,
        'new_audio_is_originally_synthesized':True,'commercial_audio_exported':False,
        'source_definition_is_commercial_private_only':True,'native_complete_definition_loader_executed':False,
        'playback_executed':False,'listened':False,'item_descriptors_built':False,'global_indices_reserved':False,
        'installation_allowed':False,'game_started':False,'game_modified':False,'engine_validated':False,
        'pending_requirements':['listening_and_mix','full_native_sound_definition_load','symbolic_lookup_policy',
            'modern_item_sound_bindings','animation_and_gameplay_event_timing','loose_definition_overlay_composition',
            'isolated_file_deployment','native_audio_playback']}


def main(argv=None):
    from item_native_contract import SOURCE_SHA,IMAGE_SHA
    from item_sound_oracle import SoundOracle
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game',type=Path,required=True)
    parser.add_argument('--archives-only',action='store_true');parser.add_argument('--output-name',required=True)
    parser.add_argument('--image',type=Path,default=ROOT/'tmp/stock-menu-analysis.bin');args=parser.parse_args(argv)
    try:
        output=output_directory(ROOT,args.output_name)
        if output.exists():raise FileExistsError('Use a fresh disabled audio lab')
        if digest((args.game/'HD2_SabreSquadron.exe').read_bytes())!=SOURCE_SHA:raise ValueError('Unreviewed client')
        definition,preflight=read_sources(args.game,archives_only=args.archives_only)
        recipes={case:json.loads(path.read_text(encoding='utf-8')) for case,path in RECIPES.items()}
        files,report=prepare(definition,recipes,SoundOracle(args.image.read_bytes()))
        report.update(preflight=preflight,source_executable_sha256=SOURCE_SHA,private_image_sha256=IMAGE_SHA)
        output.mkdir(parents=True,exist_ok=False)
        for name,raw in files.items():
            path=output.joinpath(*name.split('/'));path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(raw)
            if path.read_bytes()!=raw:raise ValueError('Disabled audio lab readback differs')
        with (output/'MANIFEST.json').open('x',encoding='utf-8') as stream:json.dump(report,stream,indent=2);stream.write('\n')
        with (output/'PRIVATE_DISABLED.txt').open('x',encoding='utf-8') as stream:
            stream.write('PRIVATE / DISABLED / MODERN AUDIO\nCommercial sound-definition bytes: do not redistribute.\n'
                         'No installation, playback or historical FG42 symbol resolution.\n')
        print(json.dumps({'output':str(output),'files':len(files)+2,'additions':report['transaction']['additions'],
            'reversal_verified':True,'archives_inspected':len(preflight['archives']),'engine_validated':False},indent=2));return 0
    except (OSError,ValueError,KeyError,ImportError) as error:
        print('Private modern audio lab refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
