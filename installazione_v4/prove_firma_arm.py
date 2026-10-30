#!/usr/bin/env python3
"""Execute two ORIGINAL, pinned ARM fragments in Unicorn.

secInit, secVerifySignature, the logger and CMS_verify are explicit stubs.
This proves branch decisions and arguments, NOT cryptography or NAC acceptance.
No patch, signature bypass, Linux boot, network, ECU or installation is executed.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from prove_arm import Arm, STACK
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R7, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_SP
from audit_accesso import PINS, within_root

SWL = 'usr/lib/libswlprodext.so'
SECU = 'usr/lib/libsecuUtils.so'


class Guard(Arm):
    def __init__(self, data, verify_result, init_result=1):
        super().__init__(data, PINS['rootfs_files'][SWL]['sha256'])
        self.verify_result = verify_result
        self.init_result = init_result
        self.observed = None

    def stub(self, name):
        if name == 'secInit':
            return self.init_result
        if name == 'secVerifySignature':
            sp = self.uc.reg_read(UC_ARM_REG_SP)
            self.observed = {'media': self.cstr(self.r(0)), 'external_content': self.r(1),
                'buffer_size': self.get32(sp+4), 'flags': hex(self.get32(sp+8))}
            return self.verify_result
        if name == 'SwlProdPrintOnUART':
            return 0
        raise RuntimeError('Unexpected external call: ' + name)

    def evaluate(self):
        for reg in (UC_ARM_REG_R4, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11):
            self.uc.reg_write(reg, self.alloc(8192))
        media = self.uc.reg_read(UC_ARM_REG_R10)
        self.uc.mem_write(media, b'/local/MediaVersion.ini\0')
        self.uc.reg_write(UC_ARM_REG_R7, 1)
        self.run(0x12480, stops=(0x11f68, 0x124ec, 0x12934))
        return {'secInit_stub_return': self.init_result, 'secVerifySignature_stub_return': self.verify_result,
                'stop': hex(self.last_stop), 'continues_to_next_stage': self.last_stop == 0x12934,
                'signature_call': self.observed, 'external_calls': dict(self.calls)}


class Flags(Arm):
    def __init__(self, data, flags):
        super().__init__(data, PINS['rootfs_files'][SECU]['sha256'])
        self.input_flags = flags
        self.observed = None

    def stub(self, name):
        if name != 'CMS_verify':
            raise RuntimeError('Unexpected external call: ' + name)
        sp = self.uc.reg_read(UC_ARM_REG_SP)
        self.observed = {'flags': hex(self.get32(sp+4)), 'signer_stack': self.r(1),
                         'no_content_verify': bool(self.get32(sp+4) & 4),
                         'no_attr_verify': bool(self.get32(sp+4) & 8),
                         'no_signer_cert_verify': bool(self.get32(sp+4) & 0x20)}
        return 1  # explicitly mocked; never evidence of valid signature

    def evaluate(self):
        params = self.alloc(128)
        self.put32(params+0x20, self.input_flags)
        for reg in (UC_ARM_REG_R0, UC_ARM_REG_R7, UC_ARM_REG_R9):
            self.uc.reg_write(reg, self.alloc(128))
        self.uc.reg_write(UC_ARM_REG_R4, params)
        self.run(0x3776f84c, stops=(0x3776f878,))
        return {'input_flags': hex(self.input_flags), 'CMS_verify_stub': True,
                'observed': self.observed, 'stop': hex(self.last_stop)}


class WrapperArgs(Arm):
    """Original wrapper prologue, stopped before globals or any function call."""
    def __init__(self, data):
        super().__init__(data, PINS['rootfs_files'][SECU]['sha256'])

    def evaluate(self):
        incoming_sp = STACK + 0x18000
        self.put32(incoming_sp, 0x11111111)  # output path placeholder
        self.put32(incoming_sp+4, 0x301)
        self.put32(incoming_sp+8, 0x2000)
        self.run(0x377757b0, args=(0x22222222, 0, 0x33333333, 0x44444444), stops=(0x3777581c,))
        params = self.uc.reg_read(UC_ARM_REG_SP) + 0x10
        return {'media': hex(self.get32(params)), 'external_content': self.get32(params+8),
                'output_path': hex(self.get32(params+0x14)), 'buffer_size': self.get32(params+0x18),
                'worker_flags_at_offset_0x20': hex(self.get32(params+0x20)),
                'external_calls': dict(self.calls), 'stop': hex(self.last_stop)}


def run(root):
    swl = within_root(root, SWL).read_bytes()
    secu = within_root(root, SECU).read_bytes()
    guards = [Guard(swl, value).evaluate() for value in (0, -1, 1, 2, 0x7fffffff)]
    guards += [Guard(swl, 1, value).evaluate() for value in (0, -1, 2)]
    for case in guards:
        expected = case['secInit_stub_return'] == 1 and case['secVerifySignature_stub_return'] == 1
        if case['continues_to_next_stage'] != expected:
            raise AssertionError('Unexpected verification guard branch')
    flags = Flags(secu, 0x2000).evaluate()
    if flags['observed']['flags'] != '0x2040' or any(flags['observed'][k] for k in ('no_content_verify', 'no_attr_verify', 'no_signer_cert_verify')):
        raise AssertionError('Unexpected production CMS flags')
    wrapper = WrapperArgs(secu).evaluate()
    if wrapper['worker_flags_at_offset_0x20'] != '0x2000':
        raise AssertionError('Unexpected original wrapper argument layout')
    return {'firmware': PINS['firmware'], 'vehicle_tested': False, 'cryptographic_verification_executed': False,
            'guards': guards, 'wrapper_arguments': wrapper, 'production_CMS_flags': flags,
            'meaning': 'Original control flow rejects simulated failures; real production flags do not disable content, signed-attribute or signer-certificate verification.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.rootfs), indent=2))
