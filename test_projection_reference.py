"""Tests for the independent PC layout, no firmware or device required."""
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from tools.projection_reference import PANEL, PROFILES, Layout, Profile, Rectangle, TouchEvent, TouchRouter
from tools.prove_reference_video import mapping_proof


class ProjectionReferenceTests(unittest.TestCase):
    def test_panoramic_modes(self):
        cases = (
            ('whd-1080p', (1920, 1080), 360, (1920, 720), Fraction(1), (0, -180, 1920, 1080)),
            ('wide-720p', (1280, 720), 240, (1280, 480), Fraction(3, 2), (0, -180, 1920, 1080)),
            ('wide-480p', (800, 480), 180, (800, 300), Fraction(12, 5), (0, -216, 1920, 1152)),
        )
        for name, frame, margin, content, scale, logical in cases:
            with self.subTest(name=name):
                p = Profile.from_ini(PROFILES / f'{name}.ini')
                self.assertEqual(p, Profile.panoramic(frame))
                self.assertEqual((p.width_margin, p.height_margin), (0, margin))
                self.assertEqual((p.source.width, p.source.height), content)
                layout = Layout.fit(p)
                self.assertEqual(layout.destination, Rectangle(0, 0, *PANEL))
                self.assertEqual(layout.scale, scale)
                self.assertEqual(layout.logical_frame, Rectangle(*logical))

    def test_central_control_does_not_claim_sidebars(self):
        layout = Layout.fit(Profile.from_ini(PROFILES / 'central-720p.ini'))
        self.assertEqual(layout.destination, Rectangle(320, 0, 1280, 720))
        for x in (-1, 0, 319, 1600, 1919, 1920):
            self.assertIsNone(layout.panel_to_frame(x, 360))
        self.assertEqual(layout.panel_to_frame(320, 0), (0, 0))
        self.assertEqual(layout.panel_to_frame(1599, 719), (1279, 719))

    def test_touch_on_the_exclusive_edges_and_margins(self):
        for frame in ((1920, 1080), (1280, 720), (800, 480)):
            with self.subTest(frame=frame):
                layout = Layout.fit(Profile.panoramic(frame))
                source = layout.profile.source
                self.assertEqual(layout.panel_to_frame(0, 0), (0, source.y))
                self.assertEqual(layout.panel_to_frame(1919, 719), (source.right-1, source.bottom-1))
                self.assertEqual(layout.panel_to_content(1919, 719), (source.width-1, source.height-1))
                for x, y in ((1920, 0), (0, 720), (-1, 0), (0, -1)):
                    self.assertIsNone(layout.panel_to_frame(x, y))
                for x, y in ((0, source.y-1), (0, source.bottom), (source.right, source.y)):
                    self.assertIsNone(layout.frame_to_panel(x, y))

    def test_all_positions_on_both_axes_of_the_four_profiles(self):
        for path in sorted(PROFILES.glob('*.ini')):
            with self.subTest(profile=path.name):
                result = mapping_proof(Layout.fit(Profile.from_ini(path)))
                self.assertEqual(result['source_roundtrip_max_error_xy'], [0, 0])
                self.assertLessEqual(max(result['panel_roundtrip_max_error_xy']), 1)
                self.assertEqual(len(result['four_corners']), 4)

    def test_old_480_margin_cannot_be_mistaken_for_the_correct_geometry(self):
        incorrect = Layout.fit(Profile((800, 480), 0, 240))
        self.assertEqual(incorrect.destination, Rectangle(0, 72, 1920, 576))
        self.assertNotEqual(incorrect.destination, Rectangle(0, 0, *PANEL))

    def test_invalid_geometry_is_rejected(self):
        for frame, width_margin, height_margin in (
                ((1920, 720), 0, 0), ((1280, 720), -2, 0), ((1280, 720), 0, 720),
                ((800, 480), 1, 0), ((800, 480), 0, 181)):
            with self.subTest(frame=frame, margins=(width_margin, height_margin)):
                with self.assertRaises(ValueError):
                    Profile(frame, width_margin, height_margin)

    def test_parser_does_not_silently_ignore_unsupported_options(self):
        base = '[general]\ninputmode = touch\nresolution = 800x480\n'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'profile.ini'
            for tail in ('margins=90,90,0,0\n', 'marginheight=180\n',
                         'pixelaspectratio=1.5\n', 'contentinsets=5,0,0,0\n'):
                with self.subTest(tail=tail):
                    path.write_text(base+tail)
                    with self.assertRaises(ValueError):
                        Profile.from_ini(path)

    def test_two_fingers_move_and_release(self):
        router = TouchRouter(Layout.fit(Profile.panoramic((1280, 720))))
        self.assertEqual(router.touch('down', 1, 0, 0), [])
        router.set_focus(True)
        self.assertEqual(router.touch('down', 1, 0, 0), [TouchEvent('down', 1, (0, 120))])
        self.assertEqual(router.touch('down', 2, 1919, 719), [TouchEvent('down', 2, (1279, 599))])
        self.assertEqual(router.touch('down', 1, 0, 0), [])
        self.assertEqual(router.touch('move', 1, 1919, 0), [TouchEvent('move', 1, (1279, 120))])
        self.assertEqual(router.touch('up', 2, 0, 719), [TouchEvent('up', 2, (0, 599))])
        self.assertEqual(router.touch('up', 1, 1919, 719), [TouchEvent('up', 1, (1279, 599))])
        self.assertFalse(router.active)

    def test_native_focus_and_resolution_change_cancel_active_pointers(self):
        router = TouchRouter(Layout.fit(Profile.panoramic((1920, 1080))))
        router.set_focus(True)
        router.touch('down', 1, 0, 0)
        router.touch('down', 2, 1919, 719)
        self.assertEqual([e.pointer for e in router.set_focus(False)], [1, 2])
        self.assertEqual(router.touch('down', 3, 10, 10), [])
        router.set_focus(True)
        self.assertEqual(router.touch('up', 2, 1919, 719), [])
        router.touch('down', 1, 0, 0)
        new = Layout.fit(Profile.panoramic((800, 480)))
        self.assertEqual(router.change_layout(new), [TouchEvent('cancel', 1, (0, 180))])
        self.assertEqual(router.touch('move', 1, 0, 0), [])
        self.assertEqual(router.touch('down', 1, 0, 0), [TouchEvent('down', 1, (0, 90))])

    def test_touches_outside_the_visible_content_do_not_clamp(self):
        router = TouchRouter(Layout.fit(Profile((1280, 720))))
        router.set_focus(True)
        self.assertEqual(router.touch('down', 1, 0, 0), [])
        self.assertEqual(router.touch('down', 1, 320, 0), [TouchEvent('down', 1, (0, 0))])
        self.assertEqual(router.touch('move', 1, 319, 0), [TouchEvent('cancel', 1, (0, 0))])
        self.assertEqual(router.touch('up', 1, 320, 0), [])


if __name__ == '__main__':
    unittest.main()
