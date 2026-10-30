import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from patch_fullscreen_lab import load_plan,patch_bytes,patch_qml,restore_qml,prepare,PROFILE

ROOT=os.environ.get('NAC_LAB_ROOTFS')
UI=os.environ.get('NAC_LAB_UI_FILE')

class PlanTests(unittest.TestCase):
    def test_plan_is_pinned_and_not_installable(self):
        plan=load_plan();self.assertEqual(plan['revision'],3)
        self.assertFalse(plan['vehicle_tested']);self.assertFalse(plan['installability_verified'])
        self.assertEqual(len(plan['files']),2)

    def test_modified_plan_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'plan.json';p.write_text(json.dumps(load_plan())+' ')
            with self.assertRaises(ValueError):load_plan(p)

    def test_incompatible_binary_refused(self):
        with self.assertRaises(ValueError):patch_bytes(b'bad',load_plan()['files'][0])

@unittest.skipUnless(ROOT,'Need NAC_LAB_ROOTFS and the exact external firmware files.')
class CoordinatedNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import prove_native_fullscreen as n
        cls.n=n;cls.root=Path(ROOT)

    def test_complete_aa_visible_area_function(self):
        result=self.n.visible_area(self.root)
        self.assertEqual({k:result[k] for k in ('x','y','width','height')},{'x':0,'y':0,'width':1920,'height':720})
        self.assertTrue(result['returned_pointer_correct'])

    def test_original_screen_status_selection_preserved(self):
        for flag,expected in [(True,1),(False,2)]:
            self.assertEqual(self.n.visible_area(self.root,climate=flag)['native_screen_status'],expected)

    def test_other_rectangles_pass_through(self):
        for rect in [(0,0,800,480),(0,0,1280,720),(320,0,1280,768),(320,1,1280,720),(321,0,1280,720)]:
            r=self.n.visible_area(self.root,rect)
            self.assertEqual(tuple(r[k] for k in ('x','y','width','height')),rect)

    def test_preserved_stack_canary_detects_corruption(self):
        with self.assertRaisesRegex(RuntimeError,'stack_chk_fail'):
            self.n.visible_area(self.root,corrupt_canary=True)

    def test_native_sidebars_hide_for_exact_aa_names_only(self):
        for name in ['INTERNET_0033','INTERNET_0033Skin','INTERNET_0033SkinLogic']:
            r=self.n.sidebar_allowed(self.root,name=name)
            self.assertFalse(r['allowed']);self.assertFalse(r['stored'])
        for name in ['AUDIO_0001Skin','CLIMATE_0151SkinLogic','CAMERA','INTERNET_0033Evil','internet_0033','INTERNET_0033SkinLogicX','']:
            r=self.n.sidebar_allowed(self.root,name=name,previous=False)
            self.assertTrue(r['allowed']);self.assertTrue(r['stored'])

    def test_native_focus_loss_restores_allowed_state(self):
        r=self.n.sidebar_allowed(self.root,focused=False,previous=False)
        self.assertTrue(r['allowed']);self.assertTrue(r['stored'])

    def test_invalid_monitor_or_index_retains_factory_state(self):
        for kwargs in [{'monitor_present':False},{'index':0xffffffff},{'index':1,'count':1},{'count':0}]:
            r=self.n.sidebar_allowed(self.root,previous=False,**kwargs)
            self.assertTrue(r['allowed'])

    def test_sd_hd_factory_state_matrix(self):
        for state in range(10):
            for previous in (False,True):
                for climate in (False,True):
                    expected=climate if state==6 else previous if state in (4,7) else True
                    r=self.n.sidebar_allowed(self.root,whd=False,state=state,previous=previous,climate_allowed=climate)
                    self.assertEqual(r['allowed'],expected,(state,previous,climate))
                    self.assertEqual(r['trace'],[])

    def test_native_requests_for_both_bars_and_restoration(self):
        rows=self.n.sidebar_transition(self.root)
        self.assertEqual([r['sidebars_shown_in_stub'] for r in rows],[True,False,True,False,True])
        self.assertEqual(rows[0]['native_requests'],[])
        for row,action in zip(rows[1:],['hide','show','hide','show']):
            self.assertEqual(row['native_requests'],[{'action':action,'screen_id':111},{'action':action,'screen_id':222}])

    def test_exact_profile_crop_alignment(self):
        r=self.n.crop_offset(self.root)
        self.assertEqual(r['factory_arithmetic_y'],-178)
        self.assertEqual(r['candidate_y'],-180)

    def test_other_crop_cases_keep_factory_arithmetic(self):
        for kwargs in [{'rect':(320,0,1280,720)},{'frame':(1280,720)},
                       {'rect':(0,88,1920,632)},{'margin':0},{'margin':362},{'xmargin':20}]:
            r=self.n.crop_offset(self.root,**kwargs)
            self.assertEqual(r['candidate_y'],r['factory_arithmetic_y'])

    def test_native_wayland_down_and_motion_at_edges_and_both_fingers(self):
        for action in ('down','motion'):
            for finger in (0,1):
                for x,y in [(0,0),(319,359),(320,719),(1599,0),(1600,359),(1919,719)]:
                    r=self.n.native_touch(self.root,x,y+180,action,finger)
                    self.assertEqual((r['x'],r['y']),(x,y),(action,finger,x,y))

    def test_native_wayland_fractional_pixel_conversion(self):
        r=self.n.native_touch(self.root,1919.75,899.75)
        self.assertEqual((r['x'],r['y']),(1919,719))

    def test_default_surface_manager_accepts_full_video_geometry(self):
        self.assertEqual(self.n.surface_default(self.root),{'x':0,'y':-180,'width':1920,'height':1080})

    def test_fullscreen_config_is_read_by_original_parser(self):
        from prove_arm import ConfigLab
        from config_laboratorio import render_cfg
        cfg=ConfigLab((self.root/self.n.APP).read_bytes(),render_cfg(PROFILE));cfg.parse()
        r=cfg.override()
        self.assertTrue(r['ramo_file'])
        self.assertEqual(r['campi_oggetto_18_40'][1:7],[1920,1080,3,0,360,1])

    def test_unwind_sections_and_critical_functions_unmodified(self):
        from elftools.elf.elffile import ELFFile
        import io
        for row in self.n.unchanged_unwind(self.root):self.assertTrue(row['unchanged'])
        checked=[]
        for spec in load_plan()['files']:
            source=(self.root/spec['source_path']).read_bytes();new=patch_bytes(source,spec)
            elf=ELFFile(io.BytesIO(source))
            for symbol in elf.get_section_by_name('.dynsym').iter_symbols():
                if symbol['st_size'] and any(n in symbol.name for n in ('sltFocusLost','sltFocusGained','showWHDStatusBar')):
                    for seg in elf.iter_segments():
                        if seg['p_type']=='PT_LOAD' and seg['p_vaddr']<=symbol['st_value']<seg['p_vaddr']+seg['p_filesz']:
                            off=seg['p_offset']+symbol['st_value']-seg['p_vaddr'];size=symbol['st_size']
                            self.assertEqual(source[off:off+size],new[off:off+size]);checked.append(symbol.name);break
        self.assertGreaterEqual(len(checked),3)

    def test_byte_exact_restore_and_repeat_application_refused(self):
        for spec in load_plan()['files']:
            original=(self.root/spec['source_path']).read_bytes();new=patch_bytes(original,spec)
            self.assertEqual(patch_bytes(new,spec,True),original)
            with self.assertRaises(ValueError):patch_bytes(new,spec)

@unittest.skipUnless(ROOT and UI,'Need NAC_LAB_ROOTFS and NAC_LAB_UI_FILE.')
class BundleTests(unittest.TestCase):
    def test_qml_exact_restore_and_incompatible_input_refused(self):
        source=Path(UI).read_bytes();new=patch_qml(source)
        self.assertEqual(restore_qml(new),source)
        self.assertEqual(new.count(b'nacLabWHD:'),1)
        with self.assertRaises(ValueError):patch_qml(new)
        with self.assertRaises(ValueError):patch_qml(source+b' ')

    def test_bundle_is_local_candidate_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'candidate'
            manifest=prepare(ROOT,UI,out)
            self.assertFalse(manifest['installable']);self.assertFalse(manifest['vehicle_tested'])
            self.assertTrue((out/'cfg.candidate').exists())
            self.assertFalse((out/'SWL').exists())
            with self.assertRaises(FileExistsError):prepare(ROOT,UI,out)

@unittest.skipUnless(ROOT and UI and importlib.util.find_spec('PyQt5'),'Need firmware inputs and desktop PyQt5.')
class DesktopQtTests(unittest.TestCase):
    def test_real_desktop_qt_bindings_and_original_parent_layout(self):
        from prove_qml_fullscreen import run_layout
        result=run_layout(ROOT,UI);rows=result['cases']
        r=rows[0]
        self.assertEqual((r['original']['x'],r['original']['width']),(320,1280))
        self.assertEqual((r['candidate']['x'],r['candidate']['width']),(0,1920))
        self.assertEqual(r['candidate']['content_width'],1920)
        self.assertTrue(r['candidate']['clip']);self.assertEqual(r['candidate']['mask_width'],1920)
        for row in rows[1:5]:self.assertEqual(row['original'],row['candidate'])
        for row in rows[5:]:self.assertEqual(row['candidate']['mask_width'],0)
        self.assertFalse(result['nac_qt_5_5_executed'])

if __name__=='__main__':unittest.main()
