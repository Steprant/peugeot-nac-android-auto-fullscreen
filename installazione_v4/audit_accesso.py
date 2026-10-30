#!/usr/bin/env python3
"""Audit offline dei file originali. Non apre dispositivi, rete o firmware in scrittura.

python audit_accesso.py --rootfs ROOT_ESTRATTA --decrypted DIRECTORY_CON_AUTO
L'output JSON va a stdout; nessun percorso dell'immagine viene eseguito.
"""
import argparse
import gzip
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath

from lzop_verificato import unpack

HERE = Path(__file__).parent
PINS = json.loads((HERE / 'firmware_pins.json').read_text())
OPTIONS = ('MODULE_SIG', 'SECCOMP', 'DEVKMEM', 'STRICT_DEVMEM', 'SECURITY',
           'SECURITYFS', 'DEFAULT_SECURITY', 'UNION_FS', 'FUSE_FS', 'IKCONFIG_PROC')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def within_root(root, name):
    """Resolve target absolute symlinks inside the extracted root, never the host.

    For stable, trusted local extractions only; not a defense against concurrent
    modification of the filesystem during an audit. Reject escapes and loops.
    """
    root = Path(root).resolve(strict=True)
    pending = list(PurePosixPath(str(name)).parts)
    done = []
    hops = 0
    while pending:
        part = pending.pop(0)
        if part in ('/', '.', ''):
            continue
        if part == '..':
            if not done:
                raise ValueError('Path escapes extracted root')
            done.pop()
            continue
        candidate = root.joinpath(*done, part)
        if candidate.is_symlink():
            hops += 1
            if hops > 40:
                raise ValueError('Symlink loop or excessive depth')
            target = os.readlink(candidate)
            if target.startswith('/'):
                done = []
            pending = list(PurePosixPath(target).parts) + pending
        else:
            done.append(part)
    return root.joinpath(*done)


def pinned_read(path, pin):
    data = Path(path).read_bytes()
    if len(data) != pin['size'] or sha(data) != pin['sha256']:
        raise ValueError('Source does not match pinned firmware: ' + str(path))
    return data


def newc_entries(data):
    """Parse metadata and byte slices; never extract a CPIO member or symlink."""
    at = 0
    names = set()
    while True:
        if at + 110 > len(data) or data[at:at+6] != b'070701':
            raise ValueError('Truncated or unsupported newc archive')
        try:
            values = [int(data[at+6+i*8:at+14+i*8], 16) for i in range(13)]
        except ValueError as exc:
            raise ValueError('Invalid newc header') from exc
        mode, uid, gid, length, nlen = values[1], values[2], values[3], values[6], values[11]
        at += 110
        if not 1 <= nlen <= 4096 or at+nlen > len(data) or data[at+nlen-1] != 0:
            raise ValueError('Invalid newc name')
        name = data[at:at+nlen-1].decode('utf-8', errors='strict')
        at = (at+nlen+3) & ~3
        if at+length > len(data):
            raise ValueError('Truncated newc member')
        content = data[at:at+length]
        at = (at+length+3) & ~3
        if name == 'TRAILER!!!':
            return
        p = PurePosixPath(name)
        if p.is_absolute() or '..' in p.parts or '\x00' in name:
            raise ValueError('Unsafe newc member name')
        name = str(p)
        if name in names:
            raise ValueError('Duplicate newc member')
        names.add(name)
        yield {'name': name, 'mode': oct(mode), 'uid': uid, 'gid': gid,
               'size': length, 'content': content}


def selected_users(root):
    path = within_root(root, '/etc/passwd')
    records = {}
    for line in path.read_text().splitlines():
        fields = line.split(':')
        if len(fields) == 7 and fields[0] in ('root', 'stdOVIPuser', 'secOVIPuser', 'swlman', 'SerGet'):
            name, password, uid, gid, _, _, shell = fields
            records[name] = {'uid': int(uid), 'gid': int(gid), 'shell': shell,
                             'password_locked': password.startswith(('*', '!')),
                             'password_empty': password == ''}
    return {'selected_file': '/' + path.relative_to(Path(root).resolve()).as_posix(),
            'accounts': records,
            'note': 'Selected archive configuration, not the live unit. No password hashes exported.'}


def audit(root, decrypted):
    root = Path(root).resolve(strict=True)
    verified = {}
    for name, pin in PINS['rootfs_files'].items():
        data = pinned_read(within_root(root, name), pin)
        verified[name] = {'size': len(data), 'sha256': sha(data)}
    kernels = []
    for record in PINS['kernels']:
        nbx = pinned_read(within_root(decrypted, record['file']), record)
        streams = []
        for entry in record['streams']:
            raw, metadata = unpack(nbx, entry['input_offset'])
            if len(raw) != entry['raw_size'] or sha(raw) != entry['raw_sha256']:
                raise ValueError('Unexpected decompressed stream')
            item = {**metadata, 'kind': entry['kind'], 'raw_size': len(raw), 'raw_sha256': sha(raw)}
            if entry['kind'] == 'kernel':
                begin = raw.index(b'IKCFG_ST') + 8
                end = raw.index(b'IKCFG_ED', begin)
                config = gzip.decompress(raw[begin:end])  # verifies gzip CRC and size
                if sha(config) != PINS['ikconfig_sha256']:
                    raise ValueError('Unexpected IKCONFIG')
                lines = config.decode().splitlines()
                item['config_sha256'] = sha(config)
                item['config_gzip_checksum_valid'] = True
                item['security_options'] = [x for x in lines if any(
                    x.startswith('CONFIG_'+o+'=') or x == '# CONFIG_'+o+' is not set' for o in OPTIONS)]
                item['kernel_versions'] = [x.decode() for x in re.findall(rb'Linux version [^\0\n]+', raw)]
            else:
                count = 0
                init = None
                for member in newc_entries(raw):
                    count += 1
                    if member['name'] == 'sbin/init' and stat.S_ISREG(int(member['mode'], 8)):
                        init = member
                item['cpio_members'] = count
                if init:
                    script = init['content'].decode()
                    # Facts about source code, not proof of console reachability.
                    item['init'] = {k: init[k] for k in ('name', 'mode', 'uid', 'gid', 'size')}
                    item['init'].update({'sha256': sha(init['content']),
                        'rescue_exec_ash_present': bool(re.search(r'rescue_shell\(\).*?exec ash', script, re.S)),
                        'mount_failure_rescue_present': '|| rescue_shell' in script,
                        'cmdline_init_parsed': 'INIT=$(sed' in script and '/proc/cmdline' in script,
                        'switch_root_uses_init': 'exec switch_root /mnt/root $INIT' in script,
                        'partition_wait_loop': 'while $(eval $RETRY)' in script})
            streams.append(item)
        kernels.append({k: record[k] for k in ('file', 'size', 'sha256', 'module', 'family')} | {'streams': streams})
    target = within_root(root, '/etc/systemd/system/ovip-sys-debug.target').read_text()
    wants = next(line.split('=', 1)[1].split() for line in target.splitlines() if line.startswith('Wants='))
    checks = {p: within_root(root, p).is_file() for p in (
        '/usr/sbin/sshd', '/usr/bin/sshd', '/sbin/sshd',
        '/etc/systemd/system/sshd.service', '/lib/systemd/system/sshd.service',
        '/etc/systemd/system/ovip-sys-ethernet.service',
        '/usr/bin/sem_dm_server', '/lib/systemd/system/serial-getty@.service')}
    enable = within_root(root, '/etc/enable_unionfs.sh').read_text()
    union = within_root(root, '/etc/init_unionfs.sh').read_text()
    hab = within_root(root, '/usr/bin/HABInfo').read_bytes()
    return {'firmware': PINS['firmware'], 'audit': 'local files only', 'installable': False,
        'vehicle_tested': False, 'rootfs_files_verified': verified, 'kernels': kernels,
        'selected_users': selected_users(root), 'debug_target_wants': wants,
        'debug_files_present': checks,
        'unionfs': {'enable_changes_init_symlink': 'rm -f /sbin/init' in enable and 'ln -s /etc/init_unionfs.sh init' in enable,
                    'uses_tmpfs': '-t tmpfs' in union, 'uses_pivot_root': 'pivot_root .' in union,
                    'privileged_entry_provided': False},
        'hab': {'device_tree_reference_present': b'/proc/device-tree/chosen/secure-boot_info' in hab,
                'ocotp_reference_present': b'/sys/fsl_otp/HW_OCOTP_' in hab,
                'actual_fuse_state': 'UNKNOWN; no live hardware read'},
        'limitations': ['Pinned archive is not proof of installed hardware identity or successful secure update.',
                        'No UART login, controlled boot arguments, root access or fullscreen proved on a NAC.',
                        'Module signing configuration does not grant module-loading privileges or exclude userspace checks.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs', required=True, type=Path)
    parser.add_argument('--decrypted', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.rootfs, args.decrypted), indent=2))
