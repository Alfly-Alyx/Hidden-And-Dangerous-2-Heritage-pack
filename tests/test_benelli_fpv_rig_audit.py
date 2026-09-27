import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import benelli_fpv_rig_audit as audit
from test_fpv_rig_binding import rigs
from test_benelli_fpv_lab import MemoryArchive
from test_items_sav import invented_slot,table as item_table


def fake_hands():return {name:('invented:'+name).encode() for name in audit.HAND_PINS}


def fake_pins(data):
    return {name:(audit.HAND_PINS[name][0],len(raw),audit.sha(raw)) for name,raw in data.items()}


class BenelliHandsAuditTests(unittest.TestCase):
    def prepare(self,*,changed=False,missing_texture=False):
        hands=fake_hands();pins=fake_pins(hands)
        if changed:hands[audit.HAND_MODELS[0]]+=b'changed'
        hand_nodes,weapon_nodes,animated_nodes=rigs(36)
        def model(raw):
            if raw==b'static':nodes=weapon_nodes;animated=False
            elif raw.startswith(b'invented:models/'):nodes=hand_nodes;animated=False
            else:nodes=animated_nodes;animated=True
            return {'nodes':copy.deepcopy(nodes),'node_count':len(nodes),'has_animation':animated}
        def textures(raw):
            if missing_texture:return ['missing.bmp']
            return ['e_br_bdarm.bmp','la_ruka01.bmp'] if b'fpv_hands_r' in raw else ['la_ruka01.bmp','la_ruka02.bmp']
        sources={'models/#fpvbeneli'+state+'.'+suffix:b'animation' for state in audit.STATES for suffix in ('4ds','5ds')}
        slots=[None]*500
        for slot,kind,name in ((114,2,'Uniform'),(270,1,'Anomalous owner')):
            raw=bytearray(invented_slot(name=name,kind=kind));raw[8:28]=b'FPV_hands_r'.ljust(20,b'\0');slots[slot]=bytes(raw)
        with patch.object(audit,'HAND_PINS',pins),patch.object(audit,'derive',return_value=(b'static',{'invented':True})),\
             patch.object(audit,'parse_4ds_nodes',side_effect=model),patch.object(audit,'world_transforms'),\
             patch.object(audit,'textures',side_effect=textures),patch.object(audit,'parse_5ds',return_value={
                 'frame_end':60,'track_count':45,'tracks':[{'name':node['name']} for node in animated_nodes]}):
            return audit.audit(sources,hands,{('SabreSquadron.dta','tables/items.sav'):item_table(slots)})

    def test_two_variants_nine_pairs_and_unusual_item_class_are_reported_without_normalization(self):
        report=self.prepare()
        self.assertEqual(len(report['hands_variants']),2)
        for variant in report['hands_variants'].values():
            self.assertEqual(len(variant['clips']),9)
            for clip in variant['clips'].values():
                self.assertEqual(clip['assembled_target_count'],45)
                self.assertEqual((clip['hand_track_count'],clip['weapon_track_count']),(37,8))
        self.assertEqual(report['non_class2_reference_slots'],{'SabreSquadron.dta':[270]})
        self.assertEqual(report['commercial_item_references']['SabreSquadron.dta'][1]['kind'],1)
        sleeve=report['hands_variants']['models/fpv_hands_r.4ds']
        self.assertEqual(sleeve['material_texture_sources']['e_br_bdarm.bmp'],'maps_u/e_br_bdarm.bmp')
        for key in ('native_binding_execution_qualified','skin_deformation_qualified','camera_and_animation_events_qualified',
                    'game_started','game_modified','playable_weapon','geometry_or_animation_keys_exported'):
            self.assertFalse(report[key])

    def test_changed_model_and_unresolved_texture_are_refused(self):
        with self.assertRaisesRegex(ValueError,'Changed pinned'):self.prepare(changed=True)
        with self.assertRaisesRegex(ValueError,'texture source'):self.prepare(missing_texture=True)

    def read(self,game,mutation=None,**kwargs):
        data=fake_hands();pins=fake_pins(data);archives={name:[] for name in audit.HAND_ARCHIVES}
        for name,raw in data.items():archives[pins[name][0]].append((name,raw))
        if mutation:mutation(archives)
        with patch.object(audit,'HAND_PINS',pins),\
             patch.object(audit,'DtaArchive',side_effect=lambda path:MemoryArchive(path,archives)):
            return audit.read_hands(game,**kwargs)

    def test_uniform_texture_namespace_is_read_without_copying_any_resource(self):
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);sources,excluded=self.read(game)
            self.assertEqual(sources,fake_hands());self.assertEqual(excluded,{})
            self.assertEqual(list(game.iterdir()),[])

    def test_loose_aliases_are_refused_or_explicitly_excluded_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            game=Path(temp);(game/'maps').mkdir();alias=game/'maps/e_br_bdarm.bmp';alias.write_bytes(b'user texture')
            with self.assertRaisesRegex(ValueError,'Loose'):self.read(game)
            _,excluded=self.read(game,archives_only=True)
            self.assertIn('maps/e_br_bdarm.bmp',excluded);self.assertEqual(alias.read_bytes(),b'user texture')

    def test_duplicate_missing_changed_and_later_shadowing_sources_are_refused(self):
        def duplicate(arcs):arcs['models.dta'].append(arcs['models.dta'][0])
        def missing(arcs):arcs['Maps_U.dta'].clear()
        def changed(arcs):name,_=arcs['models.dta'][0];arcs['models.dta'][0]=(name,b'changed')
        def shadow(arcs):arcs['Patch.dta'].append(arcs['models.dta'][0])
        with tempfile.TemporaryDirectory() as temp:
            for mutation in (duplicate,missing,changed,shadow):
                with self.subTest(mutation=mutation.__name__),self.assertRaises(ValueError):self.read(Path(temp),mutation)


if __name__=='__main__':unittest.main()
