"""No live network or device needed for these header-comparison controls."""
import unittest
from unittest.mock import patch
import subprocess

from tools.observe_release_distribution import REFERENCES, compare_headers, parse_head, probe


GOOD = (b'HTTP/1.1 200 Connection established\r\n\r\nHTTP/2 200 \r\n'
        b'content-type: application/x-tar\r\ncontent-length: 6312212480\r\n'
        b'last-modified: Wed, 21 Jan 2026 12:37:21 GMT\r\n'
        b'etag: W/"6312212480-1768999041000"\r\n\r\n')


class ReleaseDistributionTests(unittest.TestCase):
    def test_proxy_header_is_not_the_origin_response(self):
        value = parse_head(GOOD)
        self.assertEqual(value['content_length'], 6312212480)
        self.assertEqual(value['last_modified'], 'Wed, 21 Jan 2026 12:37:21 GMT')
        self.assertEqual(value['etag'], 'W/"6312212480-1768999041000"')

    def test_matching_headers_do_not_verify_content_or_installation(self):
        value = compare_headers(REFERENCES[-1], parse_head(GOOD))
        self.assertEqual(value['state'], 'headers_match')
        self.assertFalse(value['payload_identity_verified'])
        self.assertFalse(value['installation_verified'])

    def test_changed_headers_only_require_review(self):
        for changed in ({'content_length': 123}, {'last_modified': 'Thu, 26 Nov 2026 09:00:00 GMT'},
                        {'etag': '"another"'}):
            with self.subTest(changed=changed):
                result = compare_headers(REFERENCES[-1], dict(parse_head(GOOD), **changed))
                self.assertEqual(result['state'], 'headers_changed')
                self.assertEqual(result['changed_fields'], list(changed))
                self.assertFalse(result['installation_verified'])

    def test_known_etag_missing_is_inconclusive(self):
        value = parse_head(GOOD)
        value.pop('etag')
        result = compare_headers(REFERENCES[-1], value)
        self.assertEqual(result['state'], 'inconclusive')
        self.assertEqual(result['missing_fields'], ['etag'])

    def test_non_archive_unavailable_or_partial_response_is_rejected(self):
        for raw in (GOOD.replace(b'HTTP/2 200', b'HTTP/2 404'),
                    GOOD.replace(b'HTTP/2 200', b'HTTP/2 206'),
                    GOOD.replace(b'application/x-tar', b'text/html'),
                    GOOD.replace(b'6312212480\r\nlast-modified', b'0\r\nlast-modified'),
                    GOOD.replace(b'Wed, 21 Jan 2026 12:37:21 GMT', b'not a date'),
                    GOOD.replace(b'content-length: 6312212480\r\n', b'')):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_head(raw)

    def test_conflicting_duplicate_header_is_rejected(self):
        raw = GOOD.replace(b'content-length: 6312212480\r\n',
                           b'content-length: 6312212480\r\nContent-Length: 1\r\n')
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            parse_head(raw)

    def test_probe_uses_head_only_and_does_not_follow_redirects(self):
        with patch('tools.observe_release_distribution.subprocess.run') as execute:
            execute.return_value.stdout = GOOD
            result = probe(REFERENCES[-1], 8)
        self.assertEqual(result['state'], 'headers_match')
        command = execute.call_args.args[0]
        self.assertEqual(command[:2], ['curl', '-q'])
        self.assertIn('--head', command)
        self.assertNotIn('--location', command)
        self.assertEqual(command[-1], REFERENCES[-1]['url'])

    def test_failed_live_probe_is_not_reported_as_unchanged(self):
        with patch('tools.observe_release_distribution.subprocess.run',
                   side_effect=subprocess.TimeoutExpired('curl', 8)):
            result = probe(REFERENCES[-1], 8)
        self.assertEqual(result['state'], 'unavailable')
        self.assertFalse(result['installation_verified'])


if __name__ == '__main__':
    unittest.main()
