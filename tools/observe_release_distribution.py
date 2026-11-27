#!/usr/bin/env python3
"""Read-only HEAD checks of previously documented public NAC releases.

No firmware is downloaded, no vehicle identifiers are used, and no installation
or device operation is performed. Matching headers are not proof of payload
identity, software compatibility, or acceptance by a head unit.
"""
import argparse
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import format_datetime, parsedate_to_datetime


NAME = 'PSA_ovip-int-firmware-version_{}_NAC_EUR_WAVE4.tar'
CDN = 'https://ds4emloty3shq.cloudfront.net/CONTINENTAL/NAC_EU/ovip-int-firmware-version/'
MIRROR = 'https://majestic-web.mpsa.com/nas/eu/mjb00/PSA/mjbsu/'

# Direct observations of 24–27 November, documented in release-metadata.md.
# The first two ETags were recorded on 27 November. An ETag is not a file hash.
REFERENCES = (
    {'id': 'cdn_44.06_r0', 'version': '44.06.44.22_NAC-r0',
     'url': CDN + NAME.format('44-06-44-22_NAC-r0'),
     'content_length': 6285709824, 'last_modified': 'Mon, 06 Apr 2026 08:19:09 GMT',
     'etag': '"6016b3c39474a03659d3ee4c4790f555-750"'},
    {'id': 'cdn_44.06_r1', 'version': '44.06.44.22_NAC-r1',
     'url': CDN + NAME.format('44-06-44-22_NAC-r1'),
     'content_length': 6285711360, 'last_modified': 'Wed, 14 Oct 2026 14:48:34 GMT',
     'etag': '"2695e31e576cfd8a467abe4ef56fca92-120"'},
    {'id': 'cdn_44.07_r0', 'version': '44.07.33.32_NAC-r0',
     'url': CDN + NAME.format('44-07-33-32_NAC-r0'),
     'content_length': 6312212480, 'last_modified': 'Wed, 21 Oct 2026 15:40:17 GMT',
     'etag': '"10d55f4c74a6c7d8b860d523279afe42-121"'},
    {'id': 'mirror_44.07_r0', 'version': '44.07.33.32_NAC-r0',
     'url': MIRROR + NAME.format('44-07-33-32_NAC-r0'),
     'content_length': 6312212480, 'last_modified': 'Wed, 21 Jan 2026 12:37:21 GMT',
     'etag': 'W/"6312212480-1768999041000"'},
)


def parse_head(raw):
    if len(raw) > 64 * 1024:
        raise ValueError('HEAD response headers are unexpectedly large')
    blocks = [block.splitlines() for block in re.split(rb'\r?\n\r?\n', raw)
              if block.startswith(b'HTTP/')]
    if not blocks:
        raise ValueError('No HTTP response')
    # A proxy CONNECT response may precede the origin response.
    status = re.fullmatch(rb'HTTP/\d+(?:\.\d+)?\s+(\d{3})(?:\s+[^\r\n]*)?', blocks[-1][0])
    if not status or status.group(1) != b'200':
        raise ValueError('Expected a complete HTTP 200 HEAD response')
    fields = {}
    for line in blocks[-1][1:]:
        name, sep, value = line.partition(b':')
        if not sep:
            continue
        name = name.strip().lower()
        if name in (b'content-length', b'last-modified', b'content-type', b'etag'):
            value = value.strip().decode('ascii')
            if name in fields and fields[name] != value:
                raise ValueError('Conflicting origin headers')
            fields[name] = value

    content_type = fields.get(b'content-type', '').split(';', 1)[0].strip().lower()
    if content_type not in ('application/octet-stream', 'application/x-tar', 'application/tar'):
        raise ValueError('Response is not a documented archive media type')
    length = fields.get(b'content-length', '')
    if not re.fullmatch(r'[0-9]{1,12}', length) or int(length) <= 0:
        raise ValueError('Invalid or missing Content-Length')
    date = fields.get(b'last-modified', '')
    try:
        parsed = parsedate_to_datetime(date)
        if parsed.tzinfo is None:
            raise ValueError('Missing Last-Modified timezone')
        modified = format_datetime(parsed.astimezone(timezone.utc), usegmt=True)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('Invalid or missing Last-Modified') from exc
    result = {'content_length': int(length), 'last_modified': modified}
    if fields.get(b'etag'):
        result['etag'] = fields[b'etag']
    return result


def compare_headers(reference, current):
    expected_fields = ('content_length', 'last_modified', 'etag')
    changed = [key for key in expected_fields if key in reference and key in current and
               reference[key] != current[key]]
    missing = [key for key in expected_fields if key in reference and key not in current]
    state = 'headers_changed' if changed else ('inconclusive' if missing else 'headers_match')
    return {'state': state, 'changed_fields': changed, 'missing_fields': missing,
            'payload_identity_verified': False, 'installation_verified': False}


def probe(reference, timeout):
    result = {'reference': reference}
    try:
        # HEAD only; no redirect following, no credentials, no retries or body
        # downloads. All URLs are pinned to the documented public archives.
        response = subprocess.run(['curl', '-q', '-fsS', '--head', '--proto', '=https', '--max-time',
                                   str(timeout), '--', reference['url']],
                                  check=True, capture_output=True, timeout=timeout+2)
        observed = parse_head(response.stdout)
        result['observed'] = observed
        result.update(compare_headers(reference, observed))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result.update({'state': 'unavailable', 'error': type(exc).__name__,
                       'payload_identity_verified': False, 'installation_verified': False})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--timeout', type=int, default=15, choices=range(1, 31),
                        help='Maximum seconds per public HEAD request (default: 15)')
    args = parser.parse_args()
    with ThreadPoolExecutor(max_workers=4) as executor:
        records = list(executor.map(lambda reference: probe(reference, args.timeout), REFERENCES))
    report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
              'scope': 'HTTP HEAD headers of known public distributions; no body or device',
              'archives': records,
              'all_headers_match': all(row['state'] == 'headers_match' for row in records),
              'headers_changed': any(row['state'] == 'headers_changed' for row in records),
              'payload_identity_verified': False, 'installation_verified': False,
              'phone_tested': False, 'physical_nac_tested': False}
    print(json.dumps(report, indent=2))
    return 1 if any(row['state'] in ('unavailable', 'inconclusive') for row in records) else 0


if __name__ == '__main__':
    raise SystemExit(main())
