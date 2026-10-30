#!/usr/bin/env python3
"""Meaningful parser, source-integrity and ORIGINAL ARM control-flow tests.

Requires matching, decrypted local inputs. No tests are silently skipped.
"""
import argparse
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from audit_accesso import audit, newc_entries, pinned_read, selected_users, sha, within_root, PINS
from lzop_verificato import MAGIC, unpack
from prove_firma_arm import Guard, Flags, WrapperArgs, SWL, SECU


def lzop_fixture(payload=b'fixture without executable code'):
    header = struct.pack('>HHHBBIIII', 0x1030, 0x20a0, 0x0940, 1, 3,
                         0x0300000d, 0o100644, 0, 0) + b'\0'
    return (MAGIC + header + struct.pack('>I', zlib.adler32(header)) +
            struct.pack('>III', len(payload), len(payload), zlib.adler32(payload)) + payload + b'\0'*4)


def cpio_member(name, payload=b'', mode=0o100644, uid=0):
    values = (1, mode, uid, 0, 1, 0, len(payload), 0, 0, 0, 0, len(name.encode())+1, 0)
    raw = b'070701' + b''.join(f'{x:08x}'.encode() for x in values) + name.encode() + b'\0'
    raw += b'\0' * (-len(raw) % 4)
    raw += payload
    raw += b'\0' * (-len(raw) % 4)
    return raw


class ParserTests(unittest.TestCase):
    def test_valid_lzop_checksums(self):
        raw, meta = unpack(lzop_fixture())
        self.assertEqual(raw, b'fixture without executable code')
        self.assertTrue(meta['all_checksums_valid'])

    def test_lzop_header_corruption_rejected(self):
        raw = bytearray(lzop_fixture()); raw[23] ^= 1
        with self.assertRaisesRegex(ValueError, 'header checksum'):
            unpack(raw)

    def test_lzop_data_corruption_rejected(self):
        raw = bytearray(lzop_fixture()); raw[-6] ^= 1
        with self.assertRaisesRegex(ValueError, 'block checksum'):
            unpack(raw)

    def test_all_truncated_lzop_prefixes_rejected(self):
        raw = lzop_fixture()
        for end in range(len(raw)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                unpack(raw[:end])

    def test_lzop_expansion_limit(self):
        with self.assertRaisesRegex(ValueError, 'size limit'):
            unpack(lzop_fixture(), max_output=3)

    def test_cpio_metadata_keeps_uid_mode(self):
        entries = list(newc_entries(cpio_member('sbin/init', b'text', 0o100555, 17) + cpio_member('TRAILER!!!')))
        self.assertEqual((entries[0]['uid'], entries[0]['mode']), (17, '0o100555'))

    def test_cpio_traversal_rejected(self):
        for name in ('../etc/passwd', '/etc/passwd', 'a/../../host'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                list(newc_entries(cpio_member(name) + cpio_member('TRAILER!!!')))

    def test_cpio_symlinks_are_not_extracted(self):
        link = cpio_member('safe-link', b'/etc/passwd', 0o120777) + cpio_member('TRAILER!!!')
        self.assertEqual(list(newc_entries(link))[0]['content'], b'/etc/passwd')

    def test_cpio_truncated_member_rejected(self):
        raw = cpio_member('file', b'1234567')
        with self.assertRaises(ValueError):
            list(newc_entries(raw[:-6]))


class RootPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'etc').mkdir()

    def test_absolute_link_stays_in_image(self):
        (self.root/'etc/selected').write_text('image only')
        (self.root/'etc/passwd').symlink_to('/etc/selected')
        self.assertEqual(within_root(self.root, '/etc/passwd').read_text(), 'image only')

    def test_link_escape_rejected(self):
        (self.root/'etc/link').symlink_to('../../host-file')
        with self.assertRaisesRegex(ValueError, 'escapes'):
            within_root(self.root, 'etc/link')

    def test_link_cycle_rejected(self):
        (self.root/'etc/a').symlink_to('b'); (self.root/'etc/b').symlink_to('a')
        with self.assertRaisesRegex(ValueError, 'loop'):
            within_root(self.root, '/etc/a')

    def test_open_unused_passwd_is_not_default(self):
        (self.root/'etc/closed').write_text('root:*:0:0:root:/home/root:/bin/false\n')
        (self.root/'etc/open').write_text('root::0:0:root:/home/root:/bin/sh\n')
        (self.root/'etc/passwd').symlink_to('/etc/closed')
        account = selected_users(self.root)['accounts']['root']
        self.assertTrue(account['password_locked'])
        self.assertFalse(account['password_empty'])
        self.assertEqual(account['shell'], '/bin/false')

    def test_source_wrong_size_rejected(self):
        p = self.root/'file'; p.write_bytes(b'ab')
        with self.assertRaises(ValueError):
            pinned_read(p, {'size': 3, 'sha256': sha(b'ab')})

    def test_source_wrong_hash_rejected(self):
        p = self.root/'file'; p.write_bytes(b'ab')
        with self.assertRaises(ValueError):
            pinned_read(p, {'size': 2, 'sha256': sha(b'ac')})


class FirmwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = audit(INPUT_ROOTFS, INPUT_DECRYPTED)
        cls.swl = within_root(INPUT_ROOTFS, SWL).read_bytes()
        cls.secu = within_root(INPUT_ROOTFS, SECU).read_bytes()

    def test_six_kernel_bodies_and_configs_identical(self):
        kernels = self.report['kernels']
        self.assertEqual(len(kernels), 6)
        streams = [x for k in kernels for x in k['streams'] if x['kind'] == 'kernel']
        self.assertEqual({x['raw_sha256'] for x in streams}, {PINS['raw_kernel_sha256']})
        self.assertEqual({x['config_sha256'] for x in streams}, {PINS['ikconfig_sha256']})
        self.assertTrue(all(x['all_checksums_valid'] and x['config_gzip_checksum_valid'] for x in streams))

    def test_main_init_control_paths_present(self):
        for k in self.report['kernels']:
            if k['module'] != 'kernel':
                continue
            init = next(x['init'] for x in k['streams'] if x['kind'] == 'initramfs')
            self.assertTrue(init['cmdline_init_parsed'] and init['switch_root_uses_init'])
            self.assertTrue(init['rescue_exec_ash_present'] and init['mount_failure_rescue_present'])
            self.assertEqual(init['partition_wait_loop'], k['family'] == 'EMMC')

    def test_production_accounts_are_locked(self):
        accounts = self.report['selected_users']['accounts']
        for name in ('root', 'stdOVIPuser', 'swlman', 'SerGet'):
            self.assertTrue(accounts[name]['password_locked'])
            self.assertEqual(accounts[name]['shell'], '/bin/false')
            self.assertEqual(accounts[name]['uid'], 0)

    def test_unionfs_enable_is_persistent_boot_change(self):
        self.assertTrue(self.report['unionfs']['enable_changes_init_symlink'])
        self.assertFalse(self.report['unionfs']['privileged_entry_provided'])

    def test_arm_only_one_is_success(self):
        for value in (0, -1, 1, 2, 0x7fffffff, -0x80000000):
            with self.subTest(value=value):
                result = Guard(self.swl, value).evaluate()
                self.assertEqual(result['continues_to_next_stage'], value == 1)
                self.assertEqual(result['signature_call']['flags'], '0x2000')

    def test_arm_initialization_failure_prevents_verify(self):
        for value in (0, -1, 2):
            result = Guard(self.swl, 1, value).evaluate()
            self.assertFalse(result['continues_to_next_stage'])
            self.assertIsNone(result['signature_call'])

    def test_arm_production_flags_do_not_skip_verification(self):
        result = Flags(self.secu, 0x2000).evaluate()['observed']
        self.assertEqual(result['flags'], '0x2040')
        for name in ('no_content_verify', 'no_attr_verify', 'no_signer_cert_verify'):
            self.assertFalse(result[name])

    def test_arm_wrapper_passes_production_flags_unchanged(self):
        result = WrapperArgs(self.secu).evaluate()
        self.assertEqual(result['worker_flags_at_offset_0x20'], '0x2000')
        self.assertEqual(result['external_content'], 0)
        self.assertEqual(result['buffer_size'], 0x301)
        self.assertEqual(result['external_calls'], {})

    def test_arm_different_swl_binary_rejected(self):
        data = bytearray(self.swl); data[-1] ^= 1
        with self.assertRaises(ValueError):
            Guard(data, 1)

    def test_arm_different_security_binary_rejected(self):
        data = bytearray(self.secu); data[-1] ^= 1
        with self.assertRaises(ValueError):
            Flags(data, 0x2000)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rootfs', type=Path, required=True)
    p.add_argument('--decrypted', type=Path, required=True)
    args, rest = p.parse_known_args()
    INPUT_ROOTFS, INPUT_DECRYPTED = args.rootfs, args.decrypted
    unittest.main(argv=['test_installazione.py'] + rest, verbosity=2)
