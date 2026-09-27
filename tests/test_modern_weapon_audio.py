"""Entirely invented/generated audio; no recordings or game installation."""
from copy import deepcopy
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_modern_weapon_audio as audio


class ModernWeaponAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipes={case:json.loads(path.read_text(encoding='utf-8')) for case,path in audio.RECIPES.items()}

    def test_four_original_effects_have_bounded_pcm_and_explicit_limits(self):
        hashes=set()
        for case,recipe in self.recipes.items():
            before=deepcopy(recipe);files,report=audio.prepare(recipe)
            self.assertEqual(recipe,before);self.assertEqual(len(files),2)
            self.assertEqual(report['case'],case);self.assertFalse(report['source_audio_samples_read'])
            self.assertFalse(report['historical_fg42_symbols_resolved']);self.assertFalse(report['listened'])
            self.assertFalse(report['game_modified']);self.assertFalse(report['sound_bank_indices_allocated'])
            for kind,effect in report['effects'].items():
                name=effect['filename'];raw=files[name];metadata=effect['metadata']
                self.assertTrue(name.endswith('.wav.disabled'));self.assertLessEqual(len(effect['intended_stem']),19)
                self.assertEqual(metadata['sample_rate_hz'],22050);self.assertEqual(metadata['sample_width_bytes'],2)
                self.assertEqual(metadata['channels'],1)
                self.assertEqual(metadata['sample_frames'],round(recipe['effects'][kind]['duration_seconds']*22050))
                self.assertEqual(metadata['first_last_pcm'],[0,0]);self.assertEqual(metadata['clipped_samples'],0)
                self.assertGreater(metadata['peak_pcm'],0);self.assertLessEqual(metadata['peak_pcm'],16384)
                self.assertEqual(report['files'][name],{'size':len(raw),'sha256':audio.digest(raw)})
                hashes.add(audio.digest(raw))
        self.assertEqual(len(hashes),4)

    def test_deterministic_bytes_and_seed_is_local_to_one_effect(self):
        recipe=self.recipes['FG42'];a,_=audio.prepare(recipe);b,_=audio.prepare(recipe)
        self.assertEqual(a,b)
        changed=deepcopy(recipe);changed['effects']['shot']['seed']+=1;c,_=audio.prepare(changed)
        self.assertNotEqual(a['MOD_FG42_F.wav.disabled'],c['MOD_FG42_F.wav.disabled'])
        self.assertEqual(a['MOD_FG42_R.wav.disabled'],c['MOD_FG42_R.wav.disabled'])

    def test_headroom_scaling_handles_maximum_coincident_layers(self):
        recipe=deepcopy(self.recipes['FG42']);layer=recipe['effects']['shot']['layers'][1]
        layer.update(gain=.5,noise_mix=0)
        recipe['effects']['shot']['layers']=[deepcopy(layer) for _ in range(24)]
        files,report=audio.prepare(recipe);metadata=report['effects']['shot']['metadata']
        self.assertLess(metadata['headroom_gain_applied'],1);self.assertLessEqual(metadata['peak_pcm'],16384)
        with wave.open(io.BytesIO(files['MOD_FG42_F.wav.disabled']),'rb') as source:
            values=struct.unpack('<'+str(source.getnframes())+'h',source.readframes(source.getnframes()))
        self.assertGreater(min(values),-32768);self.assertLess(max(values),32767)

    def test_invalid_provenance_alias_seed_and_effect_shapes_refused(self):
        mutations=(lambda p:p.update(schema_version=True),lambda p:p.update(provenance='HISTORIQUE'),
            lambda p:p.update(sample_rate_hz=True),lambda p:p.update(sample_rate_hz=44100),
            lambda p:p.update(case='Other'),lambda p:p.update(description=''),lambda p:p.update(source_file='borrowed.wav'),
            lambda p:p['effects'].pop('reload'),lambda p:p['effects']['shot'].update(stem='../wrong'),
            lambda p:p['effects']['shot'].update(seed=True),lambda p:p['effects']['shot'].update(seed=0),
            lambda p:p['effects']['shot'].update(duration_seconds=6),lambda p:p['effects']['shot'].update(layers=[]))
        for mutate in mutations:
            bad=deepcopy(self.recipes['FG42']);mutate(bad)
            with self.assertRaises(ValueError):audio.prepare(bad)

    def test_invalid_layers_are_rejected_before_generation(self):
        for key,value in (('at',-.01),('at',.59),('length',.001),('gain',.51),('gain',True),
                          ('attack',0),('attack',.04),('decay',float('nan')),('tone_hz',[0,100]),
                          ('tone_hz',[100]),('noise_mix',2),('noise_smoothing',0),('source','sample.wav')):
            bad=deepcopy(self.recipes['FG42']);bad['effects']['shot']['layers'][0][key]=value
            with self.assertRaises(ValueError):audio.prepare(bad)

    def test_fresh_output_is_disabled_and_existing_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'fresh';report=audio.build(self.recipes['ZK383'],output)
            self.assertEqual(set(p.name for p in output.iterdir()),{'MANIFEST.json','MOD_ZK383_F.wav.disabled','MOD_ZK383_R.wav.disabled'})
            self.assertEqual(json.loads((output/'MANIFEST.json').read_text(encoding='utf-8')),report)
            before={p.name:p.read_bytes() for p in output.iterdir()}
            with self.assertRaises(FileExistsError):audio.build(self.recipes['ZK383'],output)
            self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()},before)


if __name__=='__main__':unittest.main()
