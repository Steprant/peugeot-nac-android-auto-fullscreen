import os
import tempfile
import unittest
from pathlib import Path

from patch_laboratorio import candidate, HMI_SHA256, PATCHED_SHA256, OFFSET, digest, write_new
from config_laboratorio import validate_cfg, render_cfg

TEXT='readFromFile=true\nscreenWidth=1920\nscreenHeight=720\nwidthMargin=0\nheigthMargin=360\nvideoDPI=240\nvideoResolution=1080p\n'

class GuardTests(unittest.TestCase):
    def test_cfg_roundtrip(self):
        self.assertEqual(render_cfg(validate_cfg(TEXT)),TEXT)
    def test_cfg_rejects_unrecognised_or_hazardous_syntax(self):
        cases=[TEXT.replace('heigthMargin','heightMargin'),TEXT+'\n',TEXT+'# comment\n',
               TEXT.replace('=1920','= 1920'),TEXT.replace('true','True'),
               TEXT.replace('1920','-1'),TEXT.replace('1920','2147483648'),
               TEXT+'screenWidth=1920\n',TEXT.replace('videoDPI=240','videoDPI=0'),
               TEXT.replace('1080p','2160p'),TEXT.replace('widthMargin=0\n','')]
        for case in cases:
            with self.subTest(case=repr(case)),self.assertRaises(ValueError):validate_cfg(case)
    def test_no_incompatible_binary_patch(self):
        with self.assertRaises(ValueError):candidate(b'not firmware')
    def test_never_overwrites_existing_destination(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'candidate.offline.so';p.write_bytes(b'keep')
            with self.assertRaises(FileExistsError):write_new(p,b'new')
            self.assertEqual(p.read_bytes(),b'keep')
    def test_refuses_live_library_filename(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'libAAutoHMILib.so.1.0.0'
            with self.assertRaises(ValueError):write_new(p,b'new')
            self.assertFalse(p.exists())

@unittest.skipUnless(os.environ.get('NAC_LAB_ROOTFS'),'Servono gli ELF reali esterni e NAC_LAB_ROOTFS.')
class FirmwareArmTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from prove_arm import ConfigLab,geometry
        cls.lab_type=ConfigLab;cls.geom=staticmethod(geometry)
        root=Path(os.environ['NAC_LAB_ROOTFS'])
        cls.root=root
        cls.app=(root/'usr/lib/ovip/Android/libAndroidAutoAppLogic.so').read_bytes()
        cls.hmi=(root/'usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0').read_bytes()

    def make(self,text=TEXT):
        lab=self.lab_type(self.app,text);parsed=lab.parse();return lab,parsed

    def test_parser_reads_real_path_and_exact_keys(self):
        lab,result=self.make()
        self.assertEqual(lab.filename,'/home/root/cfg')
        self.assertEqual(result,{'flag':True,'mappa':validate_cfg(TEXT),'righe_lette':7})

    def test_actual_getters_and_hmi_override_branch(self):
        lab,_=self.make()
        expected={'screenWidth':1920,'screenHeight':720,'widthMargin':0,'heigthMargin':360,'videoDPI':240,'videoResolution':3}
        for k,v in expected.items():self.assertEqual(lab.getter(k),{'return':0,'value':v})
        self.assertEqual(lab.override(),{'ramo_file':True,'campi_oggetto_18_40':[2,1920,720,3,0,360,1,240,0,0,0]})

    def test_without_file_no_override(self):
        lab,result=self.make(None)
        self.assertFalse(result['flag'])
        self.assertEqual(lab.getter('screenWidth'),{'return':6,'value':0xa5a5a5a5})
        self.assertFalse(lab.override()['ramo_file'])

    def test_false_flag_stops_parser_before_later_values(self):
        lab,result=self.make(TEXT.replace('readFromFile=true','readFromFile=false'))
        self.assertFalse(result['flag']);self.assertEqual(result['righe_lette'],1)
        self.assertEqual(result['mappa'],{'readFromFile':'false'})

    def test_flag_requires_exact_case_and_no_key_space(self):
        for text in [TEXT.replace('true','True'),TEXT.replace('readFromFile=','readFromFile =')]:
            _,result=self.make(text);self.assertFalse(result['flag'])

    def test_correct_english_height_spelling_does_not_supply_firmware_key(self):
        lab,_=self.make(TEXT.replace('heigthMargin','heightMargin'))
        self.assertEqual(lab.getter('heigthMargin'),{'return':0,'value':0})

    def test_unknown_resolution_silently_falls_back(self):
        lab,_=self.make(TEXT.replace('1080p','2160p'))
        self.assertEqual(lab.getter('videoResolution'),{'return':0,'value':1})

    def test_resolution_enum_values(self):
        for text,val in [('480p',1),('720p',2),('1080p',3)]:
            lab,_=self.make(TEXT.replace('1080p',text))
            self.assertEqual(lab.getter('videoResolution'),{'return':0,'value':val})

    def test_one_byte_difference_and_byte_exact_restore(self):
        b=candidate(self.hmi)
        self.assertEqual(digest(b),PATCHED_SHA256)
        self.assertEqual([i for i,(x,y) in enumerate(zip(self.hmi,b)) if x!=y],[OFFSET+3])
        self.assertEqual(candidate(b,restore=True),self.hmi)
        self.assertEqual(digest(candidate(b,restore=True)),HMI_SHA256)

    def test_modified_original_and_twice_patched_rejected(self):
        changed=bytearray(self.hmi);changed[-1]^=1
        with self.assertRaises(ValueError):candidate(bytes(changed))
        with self.assertRaises(ValueError):candidate(candidate(self.hmi))

    def test_unpatched_actual_tail_clamps_large_area(self):
        self.assertEqual(self.geom(self.hmi,(0,0,1920,720)),{'x':320,'y':0,'width':1280,'height':720})

    def test_candidate_actual_tail_accepts_large_area(self):
        self.assertEqual(self.geom(self.hmi,(0,0,1920,720),True),{'x':0,'y':0,'width':1920,'height':720})

    def test_candidate_alone_does_not_change_original_central_geometry(self):
        for changed in (False,True):
            self.assertEqual(self.geom(self.hmi,(320,0,1280,720),changed),{'x':320,'y':0,'width':1280,'height':720})

    def test_boundary_and_other_geometries(self):
        cases=[(0,0,1,1),(0,20,800,480),(0,88,1280,632),(37,11,1279,720),(0,0,1281,720),(0,0,1600,720),(0,0,1920,1080)]
        for rect in cases:
            x,y,w,h=rect
            before={'x':x+(w-1280)//2 if w>1280 else x,'y':y,'width':min(w,1280),'height':h}
            after={'x':x,'y':y,'width':w,'height':h}
            with self.subTest(rect=rect):
                self.assertEqual(self.geom(self.hmi,rect),before)
                self.assertEqual(self.geom(self.hmi,rect,True),after)

    def test_qrc_resources_from_real_hash_pinned_plugins(self):
        from audit_qrc import audit
        result=audit(self.root)
        self.assertEqual(len(result['componenti']),2)
        first,second=result['componenti']
        self.assertTrue(first['binding_WHD_x_320'])
        self.assertTrue(first['binding_WHD_larghezza_meno_640'])
        self.assertTrue(second['compressione_zlib'])
        self.assertTrue(second['clip_condizionale_WHD'])

if __name__=='__main__':unittest.main()
