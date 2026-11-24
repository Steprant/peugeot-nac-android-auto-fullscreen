#!/usr/bin/env python3
"""Compare the published version and display-component digests in aligned TAR slices."""
import argparse
import configparser
import hashlib
import json
import re
import tarfile
import xml.etree.ElementTree as ET
from pathlib import Path


MAX_SLICE = 1024 * 1024
DISPLAY_COMPONENTS = {
    'nand_rootfs': '1010103/NAC_EU/NAND/rootfs.fsn',
    'emmc_rootfs': '1010103/NAC_EU/EMMC/rootfs-emmc.fsn',
    'ui_resources': 'Universes/ui-app-data-resource.tar.gz',
    'pixel_hd': 'Universes/ui-pixel-hd.tar.gz',
}


def read_metadata(slices):
    """Read only UpdateInfo and HashList from 512-byte-aligned slices."""
    records = {}
    for path in slices:
        with path.open('rb') as stream:
            data = stream.read(MAX_SLICE + 1)
        if len(data) > MAX_SLICE or len(data) % 512:
            raise ValueError(f'{path.name}: expected an aligned slice of at most 1 MiB')
        for offset in range(0, len(data), 512):
            block = data[offset:offset + 512]
            if b'UpdateInfo.xml' not in block[:100] and b'HashList.ini' not in block[:100]:
                continue
            try:
                member = tarfile.TarInfo.frombuf(block, 'utf-8', 'strict')
            except tarfile.TarError:
                continue
            if member.name != 'UpdateInfo.xml' and not re.fullmatch(
                    r'SWL/[0-9]+/HashList\.ini', member.name):
                continue
            if not member.isfile() or not 0 < member.size <= 64 * 1024:
                raise ValueError(f'{path.name}: invalid metadata member')
            start = offset + 512
            end = start + member.size
            if end > len(data):
                continue
            payload = data[start:end]
            if member.name in records and records[member.name] != payload:
                raise ValueError('Conflicting metadata members')
            records[member.name] = payload

    if 'UpdateInfo.xml' not in records:
        raise ValueError('UpdateInfo.xml missing or truncated')
    info = ET.fromstring(records['UpdateInfo.xml'])
    version = info.findtext('UpdateVersion', '')
    update_id = info.findtext('UpdateID', '')
    ecus = sorted(el.text for el in info.findall('EcuCompatibilityList/EcuType') if el.text)
    declared_size = int(info.findtext('UpdateSize', '0'))
    if (info.tag != 'UpdateInfo' or info.findtext('UpdateType') != 'ovip-int-firmware-version'
            or info.findtext('UpdateProvider') != 'CONTINENTAL'
            or 'NAC_EUR_WAVE4' not in ecus or not re.fullmatch(r'[0-9]+', update_id)
            or not re.fullmatch(r'[0-9]+(?:\.[0-9]+){3}_NAC-r[0-9]+', version)
            or declared_size <= 0):
        raise ValueError('Expected Continental NAC European Wave 4 firmware metadata')
    hash_path = f'SWL/{update_id}/HashList.ini'
    if set(records) != {'UpdateInfo.xml', hash_path}:
        raise ValueError('HashList.ini missing or associated with another update')
    manifest = records[hash_path]
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(manifest.decode('utf-8-sig'))
    prefix = f'$(MEDIA_ROOT)/SWL/{update_id}/Firmware/'
    components = {}
    for section in config.sections():
        if not section.startswith(prefix):
            raise ValueError('Unexpected component path')
        digest = config[section].get('Hash', '').lower()
        if not re.fullmatch(r'[a-f0-9]{64}', digest):
            raise ValueError('Missing or invalid SHA-256 field')
        components[section.removeprefix(prefix)] = digest
    if not components:
        raise ValueError('Empty component manifest')
    return {
        'version': version,
        'update_id': update_id,
        'declared_update_size': declared_size,
        'ecu_types': ecus,
        'hashlist_sha256': hashlib.sha256(manifest).hexdigest(),
        'components': components,
    }


def compare(baseline, candidate):
    old, new = baseline['components'], candidate['components']
    common = old.keys() & new.keys()
    changed = {name for name in common if old[name] != new[name]}
    added, removed = new.keys() - old.keys(), old.keys() - new.keys()

    def display_result(path):
        if path not in old or path not in new:
            return 'missing'
        return 'identical' if old[path] == new[path] else 'changed'

    display = {name: display_result('AUTO/' + path) for name, path in DISPLAY_COMPONENTS.items()}
    return {
        'scope': 'comparison of SHA-256 values declared in official TAR metadata',
        'baseline': {k: v for k, v in baseline.items() if k != 'components'},
        'candidate': {k: v for k, v in candidate.items() if k != 'components'},
        'declared_components': {
            'baseline': len(old),
            'candidate': len(new),
            'identical': len(common) - len(changed),
            'changed': len(changed),
            'added': len(added),
            'removed': len(removed),
        },
        'display_components': display,
        'firmware_list_only_change': (
            changed == {'FirmwareList.ini'} and not added and not removed
            and all(value == 'identical' for value in display.values())
        ),
        'payload_bytes_verified': False,
        'installation_verified': False,
        'physical_fullscreen_verified': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', required=True, type=Path, nargs='+')
    parser.add_argument('--candidate', required=True, type=Path, nargs='+')
    args = parser.parse_args()
    try:
        result = compare(read_metadata(args.baseline), read_metadata(args.candidate))
    except (OSError, ValueError, ET.ParseError, configparser.Error) as exc:
        parser.exit(2, f'{exc}\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
