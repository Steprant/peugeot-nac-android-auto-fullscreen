#!/usr/bin/env python3
"""Run only the pinned ARM OpenSSL CLI in QEMU user mode on local metadata.

Does not boot Linux, execute the NAC updater, create an update or access hardware.
QEMU must already be installed on the host. Firmware stays outside this repository.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_media_signature import read_bounded

# Re-acquired from the hash-pinned NAND rootfs; not an installed-unit attestation.
OPENSSL_SHA256 = '5cdeec875409979ff6087c9c41421578fa517be66e22c4fddc3cb9bf9073ab70'
LIBCRYPTO_SHA256 = '8d74fa9d78f6e71febb4fcd0e34fba5e89c079254bae71dbc53e137314400074'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs', required=True, type=Path)
    parser.add_argument('--qemu-arm', default='qemu-arm', help='Host qemu-arm or qemu-arm-static executable')
    parser.add_argument('media_version', type=Path)
    args = parser.parse_args()
    try:
        root = args.rootfs.resolve(strict=True)
        original = read_bounded(root / 'usr/bin/openssl')
        crypto = read_bounded(root / 'lib/libcrypto.so.1.0.0')
        media = read_bounded(args.media_version)
        if hashlib.sha256(original).hexdigest() != OPENSSL_SHA256:
            raise ValueError('Target OpenSSL does not match the reviewed firmware')
        if hashlib.sha256(crypto).hexdigest() != LIBCRYPTO_SHA256:
            raise ValueError('Target libcrypto does not match the reviewed firmware')
        qemu = shutil.which(args.qemu_arm)
        if not qemu:
            raise ValueError('Host qemu-arm executable not found')
        with tempfile.TemporaryDirectory(prefix='nac-target-cms-') as folder:
            target = Path(folder) / 'openssl-arm'
            target.write_bytes(original)
            target.chmod(0o700)
            prefix = [qemu, '-L', str(root), str(target)]
            environment = dict(os.environ, OPENSSL_CONF=os.devnull,
                               RANDFILE=str(Path(folder) / 'random-state'))
            def run(options, data=None):
                return subprocess.run(prefix + options, input=data, capture_output=True,
                                      timeout=30, check=False, env=environment)
            version = run(['version'])
            if version.returncode:
                raise ValueError('Target OpenSSL could not start under host QEMU')
            rows = []
            for mode in ('cms', 'smime'):
                options = [mode, '-verify', '-noverify']
                if mode == 'cms':
                    options += ['-inform', 'SMIME']
                result = run(options, media)
                rows.append({'mode': mode, 'returncode': result.returncode,
                             'content_signature_valid_without_chain': result.returncode == 0,
                             'output_bytes': len(result.stdout),
                             'output_sha256': hashlib.sha256(result.stdout).hexdigest(),
                             'diagnostic': result.stderr.decode(errors='replace')[-2048:]})
            record = {'scope': 'Original ARM OpenSSL CLI under host QEMU user mode only',
                      'input_sha256': hashlib.sha256(media).hexdigest(),
                      'target_openssl': version.stdout.decode().strip(),
                      'target_openssl_sha256': OPENSSL_SHA256,
                      'target_libcrypto_sha256': LIBCRYPTO_SHA256,
                      'openssl_config_disabled': True,
                      'results': rows, 'certificate_chain_verified': False,
                      'nac_updater_executed': False, 'nac_update_acceptance_proved': False}
            print(json.dumps(record, indent=2))
            return 0 if all(row['content_signature_valid_without_chain'] for row in rows) else 1
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
