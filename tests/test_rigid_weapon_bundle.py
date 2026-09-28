"""Invented tables and animations only; no commercial bytes in fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import rigid_weapon_bundle as bundle
import build_rigid_weapon_bundle_lab as lab
from item_ammo_descriptor import build_ammunition
from item_weapon_descriptor import build_weapon
from items_sav import parse
from fpv_table import parse as parse_fpv
from build_rigid_weapon_resource_lab import group
from build_modern_animation_bank import ALIASES
from animation_attach_audit import invented
from build_benelli_table_lab import write_lab
from test_items_sav import table
from test_fpv_table import table as fpv_table
from test_item_table_additive import group as old_group
from test_item_weapon_descriptor import fixture as weapon_spec
from test_item_ammo_descriptor import fixture as ammo_spec
from test_mg34_table_lab import Both
from test_item_table_oracle import SyntheticMachine
from test_benelli_table_lab import Machine as StateMachine


def fixture(*,hand='H',layer='PatchX01.dta',base_weight=.2):
    slots=[None]*500
    for i in (196,201):
        spec=ammo_spec();spec['text_id']=1000+i;spec['names']['internal']='MODERN_Base'+str(i);spec['weight']=base_weight
        slots[i]=build_ammunition(spec)
    original={'items':table(slots),'fpv':fpv_table(old_group(109))};labs={}
    for case in bundle.CASES:
        spec=weapon_spec();spec['text_id']={'FG42':21502,'MG34':21501,'ZK383':21503}[case]
        spec['names']['internal']='MODERN_'+case
        spec['weapon_members_raw'][0x54]={'FG42':196,'MG34':201,'ZK383':365}[case]
        weapon=build_weapon(spec);fragment=group(case,hand)[0]
        files={f'PROTOTYPE_{case}.item.disabled':weapon,
               f'PROTOTYPE_{bundle.SHORT[case]}P{hand}.fpvgroup.disabled':fragment,
               'Text/french/TEXTY_DD.txt.disabled':b'invented common labels'}
        for alias in ALIASES.values():
            files[f'PROTOTYPE_{bundle.SHORT[case]}P{hand}{alias}.5ds.disabled']=invented(['Invented'])
        if case=='ZK383':
            ammo=build_ammunition(ammo_spec());files['PROTOTYPE_ZK3MAG.item.disabled']=ammo
            current,proof=bundle.build_pair(original['items'],original['fpv'],weapon,fragment,ammo,weapon_slot=364,ammo_slot=365)
        else:current,proof=bundle.add_weapon(original['items'],original['fpv'],weapon,fragment,slot=bundle.SLOTS[case])
        files.update({bundle.CENTRAL[k]:v for k,v in current.items()})
        report={'schema_version':1,'scope':bundle.SCOPES[case],'runtime_status':'pending','hand_variant':hand,'item_layer':layer,
                'transaction':proof,'reverse_verified_in_memory':True,'pending_requirements':['gameplay'],
                'files':{k:bundle.fingerprint(v) for k,v in files.items()},
                'game_started':False,'game_modified':False,'installation_allowed':False,'playable_weapon':False}
        labs[case]=(files,report)
    return labs,original


class Loader:
    def load(self,raw,name):
        return {'animation_sha256':bundle.fingerprint(raw)['sha256'],'native_animation_open_and_relocation_executed':True,
                'relocated_body_and_name_match':True,'requested_memory_filename':name[:-4]+'.5ds'}


class CombinedRigidWeaponTests(unittest.TestCase):
    def test_four_hand_layer_combinations_preserve_old_records_and_reverse_all_four_additions(self):
        for hand in ('H','R'):
            for layer in ('SabreSquadron.dta','PatchX01.dta'):
                labs,original=fixture(hand=hand,layer=layer);saved=deepcopy(labs)
                files,report=bundle.build(labs);current={k:files[n] for k,n in bundle.CENTRAL.items()}
                self.assertEqual(labs,saved);self.assertEqual(parse(current['items'])['present_slots'],6)
                self.assertEqual(parse(current['items'])['allocation_tail_size'],parse(original['items'])['allocation_tail_size']-2016)
                self.assertEqual([g['id'] for g in parse_fpv(current['fpv'])['groups']],[109,462,463,464])
                self.assertEqual(bundle.restore(current,json.loads(json.dumps(report['transaction']))),original)
                for old,new in zip(parse(original['items'])['slots'],parse(current['items'])['slots']):
                    if old['slot'] not in (362,363,364,365):self.assertEqual(old['sha256'],new['sha256'])
                self.assertEqual(report['identical_shared_resources'][0]['owners'],list(bundle.CASES))
                self.assertFalse(report['installation_allowed']);self.assertFalse(report['playable_weapons'])

    def test_different_source_snapshots_hands_or_archive_layers_never_merge(self):
        for change,message in [({'base_weight':.3},'source table'),({'hand':'R'},'hand variants'),
                               ({'layer':'SabreSquadron.dta'},'archive layers')]:
            labs,_=fixture();labs['MG34']=fixture(**change)[0]['MG34']
            with self.assertRaisesRegex(ValueError,message):bundle.build(labs)

    def test_conflicting_shared_bytes_or_windows_case_refused_without_mutating_inputs(self):
        name='Text/french/TEXTY_DD.txt.disabled'
        for alternate,raw in [(name,b'changed'),(name.lower(),b'invented common labels')]:
            labs,_=fixture();files,report=labs['MG34'];files.pop(name);report['files'].pop(name)
            files[alternate]=raw;report['files'][alternate]=bundle.fingerprint(raw);saved=deepcopy(labs)
            with self.assertRaisesRegex(ValueError,'Conflicting shared'):bundle.build(labs)
            self.assertEqual(labs,saved)

    def test_changed_payloads_active_names_scope_and_waived_safety_flags_are_rejected(self):
        for mutate in (lambda f,r:f.update({'PROTOTYPE_MG34.item.disabled':b'changed'}),
                       lambda f,r:r.update(scope='other'),lambda f,r:r.update(installation_allowed=True),
                       lambda f,r:r.update(game_started=0),lambda f,r:r.update(reverse_verified_in_memory=False),
                       lambda f,r:r.update(schema_version=True)):
            labs,_=fixture();mutate(*labs['MG34'])
            with self.assertRaises(ValueError):bundle.build(labs)
        for name in ('../outside.disabled','Maps/active.bmp','C:/escape.disabled','AUX.disabled'):
            labs,_=fixture();files,report=labs['MG34'];files[name]=b'x';report['files'][name]=bundle.fingerprint(b'x')
            with self.assertRaises(ValueError):bundle.build(labs)
        with self.assertRaises(ValueError):bundle.build({})

    def test_later_edits_or_changed_nested_receipts_refuse_whole_rollback(self):
        labs,_=fixture();files,report=bundle.build(labs);current={k:files[n] for k,n in bundle.CENTRAL.items()}
        for key in current:
            changed=dict(current);changed[key]+=b'later'
            with self.assertRaises(ValueError):bundle.restore(changed,report['transaction'])
        for mutate in (lambda p:p.update(allocation_bytes_consumed=2016.0),lambda p:p.update(installation_allowed=0),
                       lambda p:p['transactions'].reverse(),lambda p:p['transactions'][0]['transaction'].update(slot=363),
                       lambda p:p['transactions'][2]['transaction']['ammo'].update(slot=365.0),
                       lambda p:p.update(extra='unknown')):
            proof=deepcopy(report['transaction']);mutate(proof)
            with self.assertRaises(ValueError):bundle.restore(current,proof)

    def test_native_orchestration_checks_joint_tables_and_each_weapons_nine_clips(self):
        labs,_=fixture();files,report=bundle.build(labs)
        result=lab.inspect(files,report,StateMachine(),SyntheticMachine(),Both(),Loader())
        self.assertEqual(result['native_descriptor_records_checked'],6)
        self.assertEqual(sum(map(len,result['native_animation_resource_requests'].values())),117)
        self.assertEqual(sum(map(len,result['native_animation_loads'].values())),27)
        self.assertFalse(result['simultaneous_runtime_use_qualified'])
        class BadLoader:
            def load(self,*args):return {}
        with self.assertRaisesRegex(ValueError,'animation load'):
            lab.inspect(files,report,StateMachine(),SyntheticMachine(),Both(),BadLoader())

    def test_private_reader_refuses_traversal_unlisted_files_or_payload_changes(self):
        labs,_=fixture();files,report=labs['FG42']
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);folder=root/'.analysis/item-table-labs/Invented'
            write_lab(folder,files,report)
            self.assertEqual(lab.load_lab('Invented',root=root),(files,report))
            for name in ('../Invented','Invented/child','C:Invented','CON'):
                with self.assertRaises(ValueError):lab.load_lab(name,root=root)
            extra=folder/'unlisted.disabled';extra.write_bytes(b'invented')
            with self.assertRaisesRegex(ValueError,'Unlisted'):lab.load_lab('Invented',root=root)
            extra.unlink();(folder/'Text/french/TEXTY_DD.txt.disabled').write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'differs'):lab.load_lab('Invented',root=root)


if __name__=='__main__':unittest.main()
