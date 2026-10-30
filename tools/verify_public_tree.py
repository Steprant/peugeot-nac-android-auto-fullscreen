#!/usr/bin/env python3
"""Check the distributable file inventory, hashes and common accidental secrets.

A bounded pre-publication check, not a complete legal or secret-scanning guarantee.
Does not execute, contact a device or download any firmware.
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache'}
DENIED_DIRS = {'private', 'originals', 'firmware', 'dumps', 'rootfs_extract', 'rootfs_estratta'}
EXTENSIONS = {'.py', '.json', '.txt', '.md', '.s', '.sh', '.yml', '.yaml', '.svg'}
SPECIAL_FILES = {'LICENSE', '.gitignore', '.gitattributes'}
SECRET_PATTERNS = (
    re.compile(rb'^-----BEGIN (?:[A-Z ]+ )?(?:PRIVATE KEY|CERTIFICATE)-----', re.M),
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{25,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'),
    re.compile(rb'(?<![A-Z0-9])(?:VF3|VR3|VF7)[A-HJ-NPR-Z0-9]{14}(?![A-Z0-9])'),
)


def public_files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file()
                  and not any(x in EXCLUDED_DIRS for x in p.relative_to(ROOT).parts)
                  and p.suffix not in ('.pyc', '.pyo'))


def main():
    failures = []
    files = public_files()
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        data = path.read_bytes()
        if path.is_symlink():
            failures.append(name+': symlink not allowed in distributable tree')
        if any(x in DENIED_DIRS for x in path.relative_to(ROOT).parts):
            failures.append(name+': original/private input directory')
        if path.suffix not in EXTENSIONS and path.name not in SPECIAL_FILES:
            failures.append(name+': unsupported distributable file type')
        if len(data) > 512*1024 or data.startswith(b'\x7fELF') or b'\0' in data:
            failures.append(name+': binary or oversized input')
        try:
            data.decode('utf-8')
        except UnicodeDecodeError:
            failures.append(name+': not UTF-8 text')
        if any(pattern.search(data) for pattern in SECRET_PATTERNS):
            failures.append(name+': possible key, certificate, token or vehicle identifier')
    expected = {}
    for line in (ROOT/'CHECKSUMS_SHA256.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if name in expected or len(digest) != 64:
            failures.append('Invalid checksum entry: '+name)
        expected[name] = digest
    actual = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in files if p.name != 'CHECKSUMS_SHA256.txt'}
    if actual != expected:
        for name in sorted(set(actual)|set(expected)):
            if actual.get(name) != expected.get(name):
                failures.append('Missing, unexpected or modified public file: '+name)
    if failures:
        print('\n'.join(failures))
        return 1
    print(f'Public tree verified: {len(files)} text/source files; all listed SHA256 values match.')
    print('No matched common secret/vehicle-ID pattern. This check is not exhaustive.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
