"""Real host CMS tests with ephemeral synthetic data, keys and certificates only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.audit_media_signature import audit, hashlist_link, MAX_INPUT


class MediaSignatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='nac-cms-tests-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.key = cls.root / 'test.key'
        cls.cert = cls.root / 'test.crt'
        subprocess.run(['openssl', 'req', '-new', '-x509', '-newkey', 'rsa:2048',
                        '-nodes', '-subj', '/CN=Synthetic NAC unit test only',
                        '-days', '1', '-keyout', str(cls.key), '-out', str(cls.cert)],
                       capture_output=True, check=True, timeout=30)
        cls.hashlist = b'synthetic hash list, no firmware\n'
        cls.content = (b'[MediaHeader]\r\nDescription=synthetic\r\nHashListChecksum=' +
                       hashlib.sha256(cls.hashlist).hexdigest().encode() + b'\r\n')
        result = subprocess.run(['openssl', 'cms', '-sign', '-binary', '-md', 'sha256',
                                 '-signer', str(cls.cert), '-inkey', str(cls.key),
                                 '-outform', 'SMIME'], input=cls.content,
                                capture_output=True, check=True, timeout=30)
        cls.signed = result.stdout

    def test_valid_detached_signature_uses_embedded_mime_bytes(self):
        r = audit(self.signed, self.hashlist)
        self.assertTrue(r['detached'])
        self.assertTrue(r['embedded_content_signature_valid_without_chain'])
        self.assertEqual(r['certificate_chain_verification'], 'not_attempted')
        self.assertTrue(r['hashlist_link']['matches'])
        self.assertFalse(r['nac_update_acceptance_proved'])
        self.assertFalse(r['installable'])

    def test_content_tampering_fails_real_digest_check(self):
        r = audit(self.signed.replace(b'Description=synthetic', b'Description=modified!'))
        self.assertFalse(r['embedded_content_signature_valid_without_chain'])
        self.assertFalse(r['openssl_output_authenticated'])

    def test_micalg_header_does_not_select_the_cms_digest(self):
        self.assertIn(b'micalg="sha-256"', self.signed)
        r = audit(self.signed.replace(b'micalg="sha-256"', b'micalg="sha1"'))
        self.assertEqual(r['digest_algorithm'], 'sha256')
        self.assertFalse(r['micalg_matches_cms'])
        self.assertTrue(r['embedded_content_signature_valid_without_chain'])

    def test_exact_external_preimage_and_signature_verified(self):
        r = audit(self.signed, detached_content=self.content)
        self.assertTrue(r['supplied_detached_content']['matches_signed_digest'])
        self.assertTrue(r['supplied_detached_content']['signature_valid_without_chain'])

    def test_wrong_external_preimage_rejected(self):
        r = audit(self.signed, detached_content=self.content + b'changed')
        self.assertFalse(r['supplied_detached_content']['matches_signed_digest'])
        self.assertFalse(r['supplied_detached_content']['signature_valid_without_chain'])

    def test_external_content_trust_and_hashlist_use_the_same_bytes(self):
        tampered = self.signed.replace(b'Description=synthetic', b'Description=modified!')
        r = audit(tampered, self.hashlist, self.content, self.cert)
        self.assertFalse(r['embedded_content_signature_valid_without_chain'])
        self.assertTrue(r['supplied_detached_content']['signature_valid_without_chain'])
        self.assertTrue(r['certificate_chain_verification']['host_verification_valid'])
        self.assertEqual(r['hashlist_link']['content_source'], 'supplied_detached_content')
        self.assertTrue(r['hashlist_link']['matches'])

    def test_supplied_synthetic_trust_anchor_validates_chain(self):
        r = audit(self.signed, ca_file=self.cert)
        self.assertTrue(r['certificate_chain_verification']['host_verification_valid'])
        self.assertFalse(r['certificate_chain_verification']['nac_trust_policy_reproduced'])

    def test_hashlist_mismatch_does_not_authenticate_payload(self):
        r = audit(self.signed, hashlist=b'changed hash list')
        self.assertTrue(r['embedded_content_signature_valid_without_chain'])
        self.assertFalse(r['hashlist_link']['matches'])
        self.assertFalse(r['hashlist_link']['authenticates_metadata_or_payloads'])

    def test_ambiguous_hashlist_checksum_rejected(self):
        with self.assertRaises(ValueError):
            hashlist_link(self.content + self.content, self.hashlist)

    def test_invalid_or_oversized_smime_rejected(self):
        for raw in (b'', b'not signed', b'x' * (MAX_INPUT + 1)):
            with self.subTest(raw_size=len(raw)), self.assertRaises(ValueError):
                audit(raw)

    def test_cli_bad_signature_reports_failure(self):
        source = self.root / 'tampered.ini'
        source.write_bytes(self.signed.replace(b'Description=synthetic', b'Description=modified!'))
        run = subprocess.run([sys.executable, str(Path(__file__).parent / 'tools/audit_media_signature.py'),
                              str(source)], capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 1)
        self.assertFalse(json.loads(run.stdout)['embedded_content_signature_valid_without_chain'])


if __name__ == '__main__':
    unittest.main()
