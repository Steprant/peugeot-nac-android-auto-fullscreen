#!/usr/bin/env python3
"""Bounded static CarPlay cross-check on pinned local files; no device access.

Inline immediates include structure offsets and unrelated constants. Their presence
is not a geometry clamp, and their absence would not exclude pools/tables/callees.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from capstone.arm import ARM_OP_IMM, ARM_INS_CMP, ARM_INS_MOV, ARM_INS_MOVW, ARM_INS_ADD, ARM_INS_SUB, ARM_INS_RSB
from elftools.elf.elffile import ELFFile

PINS = {
    'usr/lib/ovip/Conn/libCarPlayAL.so.1.0.0':
        'd413022b0a324ac14c890c90892cc3ba246786a1d2e7e36a366f03d4d7c18377',
    'usr/share/ovip/CarPlayHMILib/libCarPlayHMILib.so.1.0.0':
        '6841e16cdba3536285cbc9f2ebaaed29dffe1567aa2b7b9b72217464b6288245',
}
UI_SHA256 = '4ea4167a3a3155aa9db3ea89586e2dfc07d4a6f93b95b1a3584b368b489459a1'
KINDS = {ARM_INS_CMP, ARM_INS_MOV, ARM_INS_MOVW, ARM_INS_ADD, ARM_INS_SUB, ARM_INS_RSB}
VALUES = {320, 640, 1280, 1600, 1920}


def review_library(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('CarPlay library SHA256 differs from reviewed firmware')
    elf = ELFFile(io.BytesIO(data))
    if elf['e_machine'] != 'EM_ARM' or elf.elfclass != 32 or not elf.little_endian:
        raise ValueError('Expected little-endian ARM32 ELF')
    symbols = [s for s in elf.get_section_by_name('.dynsym').iter_symbols()
               if s['st_info']['type'] == 'STT_FUNC' and s['st_value'] and s['st_size']]
    decoder = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    decoder.detail = True
    decoder.skipdata = True
    hits = []
    count = 0
    section = elf.get_section_by_name('.text')
    for instruction in decoder.disasm(section.data(), section['sh_addr']):
        if not instruction.id:
            continue
        count += 1
        if instruction.id not in KINDS:
            continue
        immediates = [op.imm for op in instruction.operands if op.type == ARM_OP_IMM and op.imm in VALUES]
        if immediates:
            owners = [s.name for s in symbols if s['st_value'] <= instruction.address < s['st_value'] + s['st_size']]
            hits.append({'address': hex(instruction.address),
                         'instruction': instruction.mnemonic + ' ' + instruction.op_str,
                         'immediates_decimal': immediates, 'containing_dynamic_functions': owners})
    selected = [{'name': s.name, 'address': hex(s['st_value']), 'size': s['st_size']}
                for s in symbols if any(token in s.name for token in
                                       ('getVisibleArea', 'identifyDisplayType', 'setVideoConfiguration', 'setScreenSize'))]
    return {'sha256': expected, 'bytes': len(data), 'decoded_text_instructions': count,
            'inline_immediate_hits': hits, 'selected_symbols': selected,
            'geometry_clamp_proved_or_excluded': False}


def review_ui(path):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != UI_SHA256:
        raise ValueError('UI module SHA256 differs from reviewed firmware')
    rows = []
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        for member in archive:
            if not member.isfile() or '/CarPlay/' not in member.name or not member.name.endswith('.qml'):
                continue
            if member.size > 1024 * 1024:
                raise ValueError('Oversized CarPlay QML')
            data = archive.extractfile(member).read()
            text = data.decode('utf-8')
            rows.append({'path': member.name.removeprefix('./'),
                         'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                         'fullscreen_content_screen': bool(re.search(r'^FullscreenContentScreen\s*\{', text, re.M)),
                         'uses_mirroring_start_x': 'CarPlayApi.mirroringStartX' in text,
                         'uses_mirroring_width': 'CarPlayApi.mirroringWidth' in text,
                         'uses_mirroring_height': 'CarPlayApi.mirroringHeight' in text})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs', required=True, type=Path)
    parser.add_argument('--ui-module', type=Path)
    args = parser.parse_args()
    try:
        rows = [dict(file=name, **review_library((args.rootfs / name).read_bytes(), expected))
                for name, expected in PINS.items()]
        result = {'scope': 'static ARM32 text scan and dynamic-symbol cross-check only',
                  'firmware': '44.07.33.32_NAC-r0', 'libraries': rows,
                  'warning': 'Text decoding can include literal data; hit semantics require function review. No inference from an immediate alone.',
                  'hardware_tested': False, 'carplay_patch_produced': False}
        if args.ui_module:
            result['carplay_qml'] = review_ui(args.ui_module)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    main()
