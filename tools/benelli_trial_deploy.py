#!/usr/bin/env python3
"""Reversible Benelli FILESYSTEM rehearsal in a verified independent copy.

No game launch, personal-game write, executable patch or save migration. This
checks deployment mechanics, not whether the prototype is playable. The shared
active.json marker prevents overlap with existing mission-file experiments.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import uuid

import benelli_trial_payload as payload
from benelli_asset_preflight import audit as asset_audit
from reconstruction_runtime_audit import file_hash,fingerprint
from reconstruction_sandbox import (ROOT,load_session,idle_game,operation,destination,
    write_new,json_data,atomic_json,relative,verify as verify_clone)
from reconstruction_trial_deploy import put_blob,blob,supported_client,check_environment,re_transaction

PRESET='BENELLI_TRIAL.json'
KIND='benelli_trial_transaction'


def prepare(session,lab,*,root=ROOT):
    session,ready,manifest=load_session(session,root);idle_game();supported_client(session)
    with operation(session):
        if destination(session,'active.json').exists():raise ValueError('Restore the active experiment before Benelli preparation')
        if destination(session,PRESET).exists():raise ValueError('Benelli preset already exists; not overwritten')
        check_environment(session,ready,manifest)
        files,lab_manifest,mapping=payload.load_lab(lab)
        assets=asset_audit(session/'game')
        if not assets['no_candidate_collisions']:raise ValueError('Unresolved asset collisions in independent copy')
        before=payload.read_targets(session/'game',mapping)
        after,plan=payload.prepare(files,lab_manifest,before)
        stored={name:put_blob(session,raw) for name,raw in files.items()}
        for raw in before.values():
            if raw is not None:put_blob(session,raw)
        if payload.read_targets(session/'game',mapping)!=before:raise ValueError('Targets changed while storing Benelli preset')
        preset={'schema_version':1,'kind':'disabled_benelli_trial_preset','environment_sha256':ready['manifest_sha256'],
                'lab_manifest':lab_manifest,'lab_files':stored,'plan':plan,'asset_preflight':assets,
                'game_launched':False,'payloads_activated':False}
        write_new(destination(session,PRESET),json_data(preset))
        load_preset(session,ready)
        return {'status':'disabled_benelli_preset_prepared','files':len(after),
                'game_launched':False,'payloads_activated':False,'playable_weapon':False}


def load_preset(session,ready):
    preset=json.loads(destination(session,PRESET).read_text(encoding='utf-8'))
    if (preset.get('schema_version')!=1 or preset.get('kind')!='disabled_benelli_trial_preset'
            or preset.get('environment_sha256')!=ready['manifest_sha256']):raise ValueError('Invalid Benelli preset identity')
    mapping=payload.target_map(preset['lab_files'])
    files={name:blob(session,proof) for name,proof in preset['lab_files'].items()}
    rows=preset['plan']['files']
    if (len(rows)!=len(mapping) or {row['path'] for row in rows}!=set(mapping.values())
            or len({row['path'].casefold() for row in rows})!=len(rows)):
        raise ValueError('Invalid Benelli target set')
    before={row['path']:blob(session,row['before']) if row['before'] is not None else None for row in rows}
    after,plan=payload.prepare(files,preset['lab_manifest'],before)
    if json_data(plan)!=json_data(preset['plan']):raise ValueError('Benelli file plan no longer matches checked payloads')
    if preset['asset_preflight'].get('no_candidate_collisions') is not True:raise ValueError('Unqualified preset resource preflight')
    return preset,before,after


def current(session,name):
    path=destination(session/'game',name)
    if not path.exists():return None
    if not path.is_file():raise ValueError('Non-file Benelli trial target')
    return {'size':path.stat().st_size,'sha256':file_hash(path)}


def replace_file(session,name,proof):
    raw=blob(session,proof);target=destination(session/'game',name)
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.parent/('.benelli-'+uuid.uuid4().hex+'.disabled')
    write_new(temporary,raw)
    try:
        destination(session/'game',name)
        os.replace(temporary,target)
        if current(session,name)!=proof:raise ValueError('Benelli payload read-back mismatch')
    finally:
        # Only this call's uninstalled temporary copy, never a game/user file.
        if temporary.exists():temporary.unlink()


def created_directories(session,rows):
    directories=set()
    for row in rows:
        parts=relative(row['path'])
        for count in range(1,len(parts)):
            name='/'.join(parts[:count])
            if not destination(session/'game',name).exists():directories.add(name)
    return sorted(directories)


def restore_locked(session,ready):
    preset,_,_=load_preset(session,ready)
    journal=json.loads(destination(session,'active.json').read_text(encoding='utf-8'))
    if (journal.get('schema_version')!=1 or journal.get('kind')!=KIND
            or not isinstance(journal.get('transaction'),str) or not re_transaction(journal['transaction'])
            or journal.get('preset_sha256')!=fingerprint(preset)
            or json_data(journal.get('files'))!=json_data(preset['plan']['files'])):
        raise ValueError('Invalid Benelli restoration journal or changed preset')
    rows=journal['files'];allowed_directories=set()
    for row in rows:
        parts=row['path'].split('/')
        allowed_directories.update('/'.join(parts[:count]) for count in range(1,len(parts)))
    directories=journal.get('created_directories')
    if (not isinstance(directories,list) or any(not isinstance(n,str) for n in directories)
            or len(directories)!=len(set(directories)) or not set(directories)<=allowed_directories):
        raise ValueError('Invalid Benelli created-directory list')
    # Preflight ALL targets and backups before restoring the first file.
    for row in rows:
        blob(session,row['after'])
        if row['before'] is not None:blob(session,row['before'])
        if current(session,row['path']) not in (row['before'],row['after']):
            raise ValueError('Later edit preserved; Benelli restoration refused: '+row['path'])
    journal['phase']='restoring';atomic_json(session,'active.json',journal);retired=[]
    for row in rows:
        name=row['path'];now=current(session,name)
        if now==row['before']:continue
        if now!=row['after']:raise ValueError('Target changed during Benelli restoration')
        if row['before'] is None:
            saved=destination(session,'retired/'+journal['transaction']+'/benelli/'+name+'.disabled')
            saved.parent.mkdir(parents=True,exist_ok=True)
            if saved.exists():raise FileExistsError('Retired Benelli model already exists')
            os.rename(destination(session/'game',name),saved);retired.append(name)
        else:replace_file(session,name,row['before'])
    if any(current(session,row['path'])!=row['before'] for row in rows):raise ValueError('Benelli restoration verification failed')
    preserved=[]
    for name in sorted(directories,key=lambda n:(-n.count('/'),n)):
        directory=destination(session/'game',name)
        if directory.is_dir():
            if any(directory.iterdir()):preserved.append(name)
            else:directory.rmdir() # Verified empty and recorded as created by this transaction.
    journal.update(phase='restored',retired_files=retired,preserved_nonempty_directories=preserved,game_launched=False)
    atomic_json(session,'active.json',journal)
    history=destination(session,'history/'+journal['transaction']+'.json');history.parent.mkdir(parents=True,exist_ok=True)
    if history.exists():raise FileExistsError('Benelli restoration history collision')
    os.rename(session/'active.json',history)
    return {'status':'restored','files':len(rows),'retired_files':retired,'history':str(history),'game_launched':False}


def apply(session,*,root=ROOT):
    session,ready,manifest=load_session(session,root);idle_game();supported_client(session)
    with operation(session):
        if destination(session,'active.json').exists():raise ValueError('Restore the active experiment first')
        preset,_,_=load_preset(session,ready);check_environment(session,ready,manifest)
        assets=asset_audit(session/'game')
        if not assets['no_candidate_collisions'] or json_data(assets)!=json_data(preset['asset_preflight']):
            raise ValueError('Asset environment changed since Benelli preparation')
        rows=preset['plan']['files']
        if any(current(session,row['path'])!=row['before'] for row in rows):
            raise ValueError('A Benelli trial target changed since preparation')
        idle_game() # Recheck after the potentially lengthy archive preflight.
        journal={'schema_version':1,'kind':KIND,'transaction':uuid.uuid4().hex,'preset_sha256':fingerprint(preset),
                 'phase':'applying','files':rows,'created_directories':created_directories(session,rows),'game_launched':False}
        atomic_json(session,'active.json',journal)
        try:
            for row in rows:
                if current(session,row['path'])!=row['before']:raise ValueError('Target changed during Benelli application')
                replace_file(session,row['path'],row['after'])
            journal['phase']='applied_not_run';atomic_json(session,'active.json',journal)
        except (OSError,ValueError):
            restore_locked(session,ready)
            raise
        return {'status':'applied_not_run','files':len(rows),'game_launched':False,'playable_weapon':False}


def restore(session,*,root=ROOT):
    session,ready,_=load_session(session,root);idle_game()
    with operation(session):return restore_locked(session,ready)


def rehearse(session,*,root=ROOT):
    session,_,_=load_session(session,root);idle_game()
    output=destination(session,'BENELLI_OFFLINE_REHEARSAL.json')
    if output.exists():raise FileExistsError('Benelli rehearsal report already exists')
    if not verify_clone(session,root=root)['ok']:raise ValueError('Benelli rehearsal requires the unmodified initial copy')
    applied=apply(session,root=root);restored=restore(session,root=root)
    final=verify_clone(session,root=root)
    if not final['ok']:raise ValueError('Whole-copy comparison failed after Benelli rehearsal')
    report={'schema_version':1,'scope':'benelli_offline_filesystem_rehearsal','applied':applied,'restored':restored,
            'final_copy_check':final,'initial_copy_restored':True,'game_launched':False,
            'runtime_tests_performed':0,'runtime_register_modified':False,'playable_weapon':False}
    write_new(output,json_data(report))
    return {key:report[key] for key in ('scope','applied','restored','initial_copy_restored','runtime_tests_performed','game_launched')}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','apply','restore','rehearse'))
    parser.add_argument('--session',type=Path,required=True)
    parser.add_argument('--lab',type=Path)
    args=parser.parse_args(argv)
    if (args.action=='prepare')!=(args.lab is not None):parser.error('--lab is required only for prepare')
    try:
        result=prepare(args.session,args.lab) if args.action=='prepare' else globals()[args.action](args.session)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print('Benelli isolated trial refused: '+str(error),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
