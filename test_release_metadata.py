import io
import tarfile
import tempfile
import unittest
from pathlib import Path

from tools.compare_release_metadata import DISPLAY_COMPONENTS, compare, read_metadata


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.components = {'AUTO/' + path: 'a' * 64 for path in DISPLAY_COMPONENTS.values()}
        self.components['FirmwareList.ini'] = 'b' * 64

    def write_metadata(self, update_id, version, components, *, manifest_id=None):
        update = (
            '<UpdateInfo><UpdateType>ovip-int-firmware-version</UpdateType>'
            f'<UpdateID>{update_id}</UpdateID><UpdateVersion>{version}</UpdateVersion>'
            '<UpdateProvider>CONTINENTAL</UpdateProvider><UpdateSize>1234</UpdateSize>'
            '<EcuCompatibilityList><EcuType>NAC_EUR_WAVE4</EcuType></EcuCompatibilityList>'
            '</UpdateInfo>'
        )
        manifest_id = manifest_id or update_id
        sections = ''.join(
            f'[$(MEDIA_ROOT)/SWL/{manifest_id}/Firmware/{name}]\nHash = {digest}\n\n'
            for name, digest in components.items()
        )
        archive = self.directory / f'{update_id}.tar'
        with tarfile.open(archive, 'w') as writer:
            for name, value in (('UpdateInfo.xml', update),
                                (f'SWL/{manifest_id}/HashList.ini', sections)):
                data = value.encode()
                member = tarfile.TarInfo(name)
                member.size = len(data)
                writer.addfile(member, io.BytesIO(data))
        return archive

    def test_same_components_under_two_update_ids(self):
        old = self.write_metadata('111', '44.06.44.22_NAC-r0', self.components)
        new_components = dict(self.components, **{'FirmwareList.ini': 'c' * 64})
        new = self.write_metadata('222', '44.06.44.22_NAC-r1', new_components)
        result = compare(read_metadata([old]), read_metadata([new]))
        self.assertTrue(result['firmware_list_only_change'])
        self.assertEqual(result['declared_components']['identical'], 4)
        self.assertFalse(result['installation_verified'])
        self.assertFalse(result['physical_fullscreen_verified'])

    def test_missing_or_changed_graphics_is_not_a_manifest_only_change(self):
        old = read_metadata([self.write_metadata('111', '44.06.44.22_NAC-r0', self.components)])
        ui_name = 'AUTO/' + DISPLAY_COMPONENTS['ui_resources']
        for missing in (False, True):
            with self.subTest(missing=missing):
                components = dict(self.components, **{'FirmwareList.ini': 'c' * 64})
                if missing:
                    del components[ui_name]
                else:
                    components[ui_name] = 'd' * 64
                new = read_metadata([self.write_metadata('222', '44.06.44.22_NAC-r1', components)])
                result = compare(old, new)
                self.assertFalse(result['firmware_list_only_change'])
                self.assertEqual(result['display_components']['ui_resources'],
                                 'missing' if missing else 'changed')

    def test_metadata_must_belong_to_the_same_update(self):
        path = self.write_metadata('111', '44.06.44.22_NAC-r0', self.components, manifest_id='222')
        with self.assertRaisesRegex(ValueError, 'another update'):
            read_metadata([path])

    def test_truncated_manifest_is_rejected(self):
        archive = self.write_metadata('111', '44.06.44.22_NAC-r0', self.components)
        partial = self.directory / 'partial.tar'
        partial.write_bytes(archive.read_bytes()[:1536])
        with self.assertRaisesRegex(ValueError, 'HashList.ini'):
            read_metadata([partial])
