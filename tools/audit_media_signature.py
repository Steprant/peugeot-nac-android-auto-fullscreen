#!/usr/bin/env python3
"""Audit local S/MIME/CMS bytes; never skip content or attribute verification.

No firmware download, device access, signing, package creation or installation.
A valid content signature with -noverify does NOT establish certificate trust.
"""
import argparse
from email import policy
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from asn1crypto import cms

MAX_INPUT = 2 * 1024 * 1024
ALGORITHMS = {'sha1', 'sha256', 'sha384', 'sha512'}


def read_bounded(path):
    with Path(path).open('rb') as stream:
        data = stream.read(MAX_INPUT + 1)
    if len(data) > MAX_INPUT:
        raise ValueError('Input exceeds the 2 MiB metadata limit')
    return data


def openssl(args, data=None):
    result = subprocess.run(['openssl', *args], input=data, capture_output=True,
                            timeout=30, check=False)
    return result


def signed_metadata(der):
    info = cms.ContentInfo.load(der, strict=True)
    if info['content_type'].native != 'signed_data':
        raise ValueError('Expected CMS SignedData')
    signed = info['content']
    # This tool deliberately rejects ambiguous multi-signer or attribute layouts.
    if len(signed['signer_infos']) != 1:
        raise ValueError('Expected exactly one CMS signer')
    signer = signed['signer_infos'][0]
    algorithm = signer['digest_algorithm']['algorithm'].native
    if algorithm not in ALGORITHMS:
        raise ValueError('Unsupported digest algorithm: ' + algorithm)
    digests = [attr for attr in signer['signed_attrs']
               if attr['type'].native == 'message_digest']
    if len(digests) != 1 or len(digests[0]['values']) != 1:
        raise ValueError('Expected one signed messageDigest attribute')
    digest = digests[0]['values'][0].native
    if len(digest) != hashlib.new(algorithm).digest_size:
        raise ValueError('messageDigest length differs from its algorithm')
    times = [attr['values'][0].native.isoformat() for attr in signer['signed_attrs']
             if attr['type'].native == 'signing_time' and len(attr['values']) == 1]
    return {'detached': signed['encap_content_info']['content'].native is None,
            'digest_algorithm': algorithm,
            'signature_algorithm': signer['signature_algorithm']['algorithm'].native,
            'signed_message_digest': digest.hex(),
            'signing_time': times[0] if len(times) == 1 else None}


def candidate_probes(content, algorithm, target):
    """A finite, named set of byte transformations, never exhaustive exclusion."""
    candidates = {'openssl_output': content}
    lf = content.replace(b'\r\n', b'\n')
    for name, value in (('lf', lf), ('crlf', lf.replace(b'\n', b'\r\n'))):
        candidates[name] = value
        candidates[name + '_trim_end'] = value.rstrip(b'\r\n\t ')
        candidates[name + '_trim_end_lf'] = value.rstrip(b'\r\n\t ') + b'\n'
        candidates[name + '_trim_end_crlf'] = value.rstrip(b'\r\n\t ') + b'\r\n'
    return {'scope': 'finite named transformations only; no exhaustive preimage claim',
            'candidates': [{'name': name, 'bytes': len(value),
                            'digest': hashlib.new(algorithm, value).hexdigest(),
                            'matches_signed_digest': hashlib.new(algorithm, value).hexdigest() == target}
                           for name, value in candidates.items()]}


def hashlist_link(content, hashlist):
    values = re.findall(rb'^HashListChecksum=([0-9a-fA-F]{64})[ \t]*\r?$', content, re.M)
    if len(values) != 1:
        raise ValueError('Expected one unambiguous SHA256 HashListChecksum')
    actual = hashlib.sha256(hashlist).hexdigest()
    expected = values[0].decode('ascii').lower()
    return {'sha256': actual, 'declared_sha256': expected, 'matches': actual == expected,
            'authenticates_metadata_or_payloads': False}


def audit(raw, hashlist=None, detached_content=None, ca_file=None):
    if not raw or len(raw) > MAX_INPUT:
        raise ValueError('Missing or oversized S/MIME input')
    version = openssl(['version'])
    if version.returncode:
        raise ValueError('OpenSSL version command failed')
    encoded = openssl(['cms', '-cmsout', '-inform', 'SMIME', '-outform', 'DER'], raw)
    if encoded.returncode:
        raise ValueError('OpenSSL could not parse S/MIME SignedData')
    metadata = signed_metadata(encoded.stdout)
    headers = BytesParser(policy=policy.default).parsebytes(raw, headersonly=True)
    declared = str(headers.get_param('micalg') or '').lower()
    result = {'scope': 'host metadata audit only',
              'input_sha256': hashlib.sha256(raw).hexdigest(),
              'input_bytes': len(raw), 'openssl': version.stdout.decode().strip(),
              **metadata, 'mime_micalg': declared,
              'micalg_matches_cms': declared.replace('-', '') == metadata['digest_algorithm'],
              'certificate_chain_verification': 'not_attempted',
              'nac_update_acceptance_proved': False, 'installable': False}
    # -noverify skips ONLY certificate-chain verification, not the content digest
    # or signed-attribute signature. Never use -nosigs/-no_content_verify here.
    verified = openssl(['cms', '-verify', '-noverify', '-inform', 'SMIME'], raw)
    result['embedded_content_signature_valid_without_chain'] = verified.returncode == 0
    result['embedded_verify_returncode'] = verified.returncode
    result['embedded_verify_diagnostic'] = verified.stderr.decode(errors='replace')[-2048:]
    # OpenSSL may emit unverified content before a digest failure. It is diagnostic
    # data, never trusted metadata. An empty output does not prove an empty preimage.
    content = verified.stdout
    result['openssl_output_bytes'] = len(content)
    result['openssl_output_sha256'] = hashlib.sha256(content).hexdigest()
    result['openssl_output_authenticated'] = verified.returncode == 0
    result['probes'] = candidate_probes(content, metadata['digest_algorithm'],
                                      metadata['signed_message_digest'])
    with tempfile.TemporaryDirectory(prefix='nac-cms-audit-') as folder:
        folder = Path(folder)
        if detached_content is not None:
            if not metadata['detached']:
                raise ValueError('External content is accepted only for detached CMS')
            if len(detached_content) > MAX_INPUT:
                raise ValueError('Oversized detached content')
            source = folder / 'content.bin'
            source.write_bytes(detached_content)
            check = openssl(['cms', '-verify', '-noverify', '-binary', '-inform', 'DER',
                             '-content', str(source)], encoded.stdout)
            observed = hashlib.new(metadata['digest_algorithm'], detached_content).hexdigest()
            result['supplied_detached_content'] = {
                'bytes': len(detached_content), 'digest': observed,
                'matches_signed_digest': observed == metadata['signed_message_digest'],
                'signature_valid_without_chain': check.returncode == 0,
                'verify_returncode': check.returncode}
        if ca_file is not None:
            # Full host verification against caller-supplied trust material.
            # OEM trust policy, CRLs, time and target acceptance are separate gates.
            args = ['cms', '-verify', '-CAfile', str(Path(ca_file).resolve())]
            if detached_content is None:
                full = openssl(args + ['-inform', 'SMIME'], raw)
            else:
                full = openssl(args + ['-binary', '-inform', 'DER', '-content', str(source)],
                               encoded.stdout)
            result['certificate_chain_verification'] = {
                'host_verification_valid': full.returncode == 0,
                'returncode': full.returncode,
                'ca_file_sha256': hashlib.sha256(read_bounded(ca_file)).hexdigest(),
                'nac_trust_policy_reproduced': False}
    if hashlist is not None:
        if len(hashlist) > MAX_INPUT:
            raise ValueError('Oversized HashList input')
        selected = content if detached_content is None else detached_content
        result['hashlist_link'] = hashlist_link(selected, hashlist)
        result['hashlist_link']['content_source'] = ('openssl_output' if detached_content is None
                                                   else 'supplied_detached_content')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('media_version', type=Path)
    parser.add_argument('--hashlist', type=Path)
    parser.add_argument('--detached-content', type=Path,
                        help='Exact candidate bytes; verified in binary DER mode without chain trust')
    parser.add_argument('--ca-file', type=Path, help='Optional independently acquired host trust anchors')
    args = parser.parse_args()
    try:
        result = audit(read_bounded(args.media_version),
                       read_bounded(args.hashlist) if args.hashlist else None,
                       read_bounded(args.detached_content) if args.detached_content else None,
                       args.ca_file)
        print(json.dumps(result, indent=2))
        # A diagnostic report is useful on failure, but a bad signature must not
        # produce a successful shell status in scripts/CI.
        good = result['embedded_content_signature_valid_without_chain']
        if args.detached_content:
            good = result['supplied_detached_content']['signature_valid_without_chain']
        if args.hashlist:
            good = good and result['hashlist_link']['matches']
        if args.ca_file:
            good = good and result['certificate_chain_verification']['host_verification_valid']
        return 0 if good else 1
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
