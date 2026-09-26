"""Invented local fixtures only; never ship commercial mesh/keyframe data."""
import copy
import io
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
import wave
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import build_benelli_fpv_lab as lab
from test_benelli_fpv_static import source,anchor
from test_model_instance import model,mesh
from test_five_ds import invented_clip
from menu_gui_audit import parse_4ds_nodes


def sound_definitions():
    def chunk(kind,raw): return struct.pack('<HI',kind,len(raw)+6)+raw
    return b''.join(chunk(0x4b0,chunk(0x4ba,label.encode()+b'\0')+chunk(0x51e,b'\0')
                          +chunk(0x514,chunk(0x578,name.encode()+b'\0')+chunk(0x582,bytes(4))))
                    for label,name in lab.SOUNDS.items())


def audio(samples=(0,32767,-32768),rate=22050):
    out=io.BytesIO()
    with wave.open(out,'wb') as wav:
        wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
        wav.writeframes(struct.pack('<'+'h'*len(samples),*samples))
    return out.getvalue()


class MemoryArchive:
    def __init__(self,path,archives):
        self.rows=archives[path.name]
        self.entries=[SimpleNamespace(name=n,index=i) for i,(n,_) in enumerate(self.rows)]
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,entry): return self.rows[entry.index][1]


def sources():
    archives={a:[] for a in lab.ARCHIVES}
    pins={}
    for i,name in enumerate(sorted(lab.REQUIRED)):
        raw=('invented '+name).encode(); archive=lab.ARCHIVES[i%len(lab.ARCHIVES)]
        archives[archive].append((name,raw))
        pins[name]={'archive':archive,'size':len(raw),'sha256':lab.sha(raw)}
    return archives,{'schema_version':1,'sources':pins}


def skeleton():
    raw=source(); parsed=parse_4ds_nodes(raw)
    # 37 invented joints, after the eight fabricated weapon records.
    joints=[]
    for i in range(37):
        name=f'joint{i}'.encode()
        joints.append(struct.pack('<BH3f4f3f',10,0,0,0,0,0,0,0,1,1,1,1)
                      +bytes(5)+bytes([len(name)])+name+b'\0'+bytes(4))
    return (raw[:parsed['node_count_offset']]+struct.pack('<H',45)
            +raw[parsed['node_count_offset']+2:-1]+b''.join(joints)+b'\1')


class FpvLabTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def read(self,archives,manifest,**kwargs):
        with patch.object(lab,'DtaArchive',side_effect=lambda path:MemoryArchive(path,archives)):
            return lab.read_sources(self.root,manifest,**kwargs)

    def test_all_exact_sources_read_without_extraction(self):
        archives,manifest=sources()
        data,excluded=self.read(archives,manifest)
        self.assertEqual(set(data),lab.REQUIRED); self.assertEqual(excluded,{})
        self.assertEqual(list(self.root.iterdir()),[])

    def test_late_archive_shadow_and_duplicate_refused(self):
        archives,manifest=sources(); name=next(n for n,p in manifest['sources'].items() if p['archive']=='models.dta')
        archives['Patch.dta'].append((name,b'replacement'))
        with self.assertRaisesRegex(ValueError,'shadowed'): self.read(archives,manifest)
        archives['Patch.dta'].clear()
        # Test duplicates in the same layer, including spelling/case differences.
        archives['models.dta'].append((name.upper().replace('/','\\'),b'other'))
        with self.assertRaisesRegex(ValueError,'Ambiguous'): self.read(archives,manifest)

    def test_patchx_relevant_override_refused_even_with_archive_only(self):
        archives,manifest=sources(); (self.root/'PatchX01.dta').touch()
        archives['PatchX01.dta']=[(next(iter(lab.REQUIRED)),b'changed')]
        with self.assertRaisesRegex(ValueError,'PatchX01'): self.read(archives,manifest,archives_only=True)

    def test_loose_file_never_silently_used(self):
        archives,manifest=sources(); name=next(iter(lab.REQUIRED))
        loose=self.root/name; loose.parent.mkdir(); loose.write_bytes(b'private override')
        with self.assertRaisesRegex(ValueError,'Loose'): self.read(archives,manifest)
        data,excluded=self.read(archives,manifest,archives_only=True)
        self.assertNotEqual(data[name],loose.read_bytes())
        self.assertEqual(excluded[name],{'size':16,'sha256':lab.sha(b'private override')})
        self.assertEqual(loose.read_bytes(),b'private override')

    def test_missing_mutated_or_malformed_pin_refused(self):
        archives,manifest=sources(); name=next(iter(manifest['sources']))
        changed=copy.deepcopy(manifest); changed['sources'][name]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'changed'): self.read(archives,changed)
        for bad in (None,[],{}, {'schema_version':1,'sources':[]},
                    {'schema_version':1,'sources':{}}):
            with self.subTest(bad=bad),self.assertRaises(ValueError): self.read(archives,bad)
        for key,value in (('size',True),('sha256','not-a-hash'),('archive','other.dta')):
            bad=copy.deepcopy(manifest); bad['sources'][name][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): self.read(archives,bad)
        owner=manifest['sources'][name]['archive']
        archives[owner]=[(n,d) for n,d in archives[owner] if n!=name]
        with self.assertRaisesRegex(ValueError,'Missing'): self.read(archives,manifest)

    def test_pair_requires_all_tracks_resolved_and_complete_skeleton(self):
        raw=skeleton(); clip=invented_clip([('fpv_weapon',{'position':([0,10],[(0,0,0),(1,0,0)])})])
        proof=lab.inspect_pair(raw,clip)
        self.assertEqual(proof['joint_nodes'],37); self.assertEqual(proof['key_count'],2)
        self.assertFalse(proof['engine_validated']); self.assertIsNone(proof['frame_rate'])
        self.assertEqual(proof['unresolved_track_names'],[])
        with self.assertRaisesRegex(ValueError,'missing from'):
            lab.inspect_pair(raw,invented_clip())
        with self.assertRaisesRegex(ValueError,'skeleton'): lab.inspect_pair(source(),clip)

    def test_output_names_and_existing_directory_refused(self):
        for name in ('../escape','a/b','a\\b','C:foo','CON','lpt1','a.','a '*32,'',None):
            with self.subTest(name=name),self.assertRaises(ValueError): lab.output_directory(name,self.root)
        out=lab.output_directory('Benelli_v1',self.root); out.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'already exists'): lab.output_directory('Benelli_v1',self.root)

    def test_sound_reference_is_owned_not_merely_near_another_label(self):
        raw=sound_definitions(); proof=lab.sound_references(raw)
        self.assertEqual(proof['I Benelli M4']['filename'],'f_bene_a.wav')
        self.assertFalse(proof['I Benelli M4']['event_binding_qualified'])
        for bad in (raw+raw,raw.replace(b'f_bene_a.wav',b'wrong___.wav'),raw[6:],raw[:-1]):
            with self.subTest(size=len(bad)),self.assertRaises(ValueError): lab.sound_references(bad)

    def test_audio_measurements_do_not_claim_listening_or_synchronization(self):
        result=lab.audio_metadata(audio())
        self.assertEqual(result['peak_abs_pcm16'],32768)
        self.assertAlmostEqual(result['rms_dbfs'],-1.761045,places=5)
        self.assertFalse(result['listened']); self.assertFalse(result['synchronized_to_animation'])
        self.assertIsNone(lab.audio_metadata(audio((0,0)))['rms_dbfs'])
        for raw in (audio(rate=8000),audio(())):
            with self.assertRaises(ValueError): lab.audio_metadata(raw)

    def audit_fixture(self):
        raw=skeleton(); clip=invented_clip([('fpv_weapon',{'position':([0],[(0,0,0)])})])
        data={f'models/#fpvbeneli{s}.{ext}':value for s in lab.STATES for ext,value in [('4ds',raw),('5ds',clip)]}
        data.update({'models/w_garandfpv.4ds':model(mesh('fpv_weapon')),
                     'tables/fpvanims.sav':b'\0'.join(('#FPVBeneli'+s).encode() for s in lab.STATES),
                     'tables/item_shoot.tbl':b'fixture','tables/ingamesounds.def':sound_definitions(),
                     **{'sounds/'+n:audio() for n in lab.SOUNDS.values()}})
        return data

    def test_audit_rejects_wrong_reference_rotation_or_changed_table_names(self):
        data=self.audit_fixture()
        evidence={'header_ok':True,'sha256':'56A60C8F6846A86E24137BAE21877935EA4F0D113F94F73B0CE6750F951ED7E7'}
        with patch.object(lab,'benelli_shoot_evidence',return_value=evidence):
            report=lab.audit(data,{'sources':{}},{})
            self.assertEqual(len(report['pairs']),9); self.assertEqual(len(report['audio']),2)
            self.assertFalse(report['playable_weapon']); self.assertFalse(report['item_slot_allocated'])
            bad=dict(data); bad['tables/fpvanims.sav']+=b'\0#FPVBeneliOther'
            with self.assertRaisesRegex(ValueError,'state references'): lab.audit(bad,{'sources':{}},{})
            bad=dict(data); raw=bytearray(bad['models/w_garandfpv.4ds'])
            root=parse_4ds_nodes(raw)['nodes'][0]
            struct.pack_into('<4f',raw,root['position_offset']+12,0,1,0,0)
            bad['models/w_garandfpv.4ds']=bytes(raw)
            with self.assertRaisesRegex(ValueError,'neutral'): lab.audit(bad,{'sources':{}},{})

    def test_build_is_disabled_hashed_private_and_non_overwriting(self):
        output=lab.output_directory('Invented',self.root)
        with patch('model_wireframe.projection_png',side_effect=lambda v,f,n,p:p.write_bytes(b'fixture PNG')):
            report=lab.build({'models/#fpvbeneliaim.4ds':source()}, {'playable_weapon':False},output)
        self.assertEqual(len(list(output.iterdir())),4)
        self.assertTrue((output/'PROTOTYPE_HERITAGE_BenelliFPV.4ds.disabled').is_file())
        self.assertFalse(report['playable_weapon'])
        for name,digest in report['files'].items(): self.assertEqual(lab.sha((output/name).read_bytes()),digest)
        self.assertIn('LIRE_AVANT_ESSAI.txt',report['files'])
        self.assertEqual(json.loads((output/'MANIFEST.json').read_text(encoding='utf-8')),report)
        before={p.name:p.read_bytes() for p in output.iterdir()}
        with self.assertRaises(FileExistsError): lab.build({'models/#fpvbeneliaim.4ds':source()}, {},output)
        self.assertEqual({p.name:p.read_bytes() for p in output.iterdir()},before)


if __name__=='__main__': unittest.main()
