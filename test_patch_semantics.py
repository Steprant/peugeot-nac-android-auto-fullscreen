"""Execute published patch intervals only; no OEM ELF or crypto substitutions.

These bounded tests exercise instruction semantics, not complete NAC functions,
Qt, compositor, physical display, exception handling or installation.
"""
import struct
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5,
                               UC_ARM_REG_R9, UC_ARM_REG_SP, UC_ARM_REG_CPSR)
from patch_fullscreen_lab import load_plan

MEMORY = 0x10000000
STACK = 0x10001000


def execute(chunk, stop, setup, cpsr=None):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    start = int(chunk['elf_address'], 0)
    first = start & ~4095
    uc.mem_map(first, ((max(start + chunk['length'], stop + 4) - first + 4095) // 4096) * 4096)
    uc.mem_map(MEMORY, 8192)
    uc.mem_write(start, bytes.fromhex(chunk['after_hex']))
    uc.reg_write(UC_ARM_REG_SP, STACK)
    if cpsr is not None:
        uc.reg_write(UC_ARM_REG_CPSR, cpsr)
    setup(uc)
    observed = []
    def hook(engine, address, size, user):
        if address == stop:
            observed.append(address)
            engine.emu_stop()
    uc.hook_add(UC_HOOK_CODE, hook)
    uc.emu_start(start, stop + 4, count=200)
    if observed != [stop]:
        raise AssertionError('Published patch did not reach its common exit')
    return uc


class PatchSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chunks = {c['label']: c for f in load_plan()['files'] for c in f['chunks']}

    def geometry(self, rect):
        chunk = self.chunks['AA-only WHD visible rectangle']
        def setup(uc):
            uc.reg_write(UC_ARM_REG_R5, MEMORY)
            uc.reg_write(UC_ARM_REG_R4, 0x12345678)
            uc.mem_write(MEMORY, struct.pack('<4i', *rect))
        uc = execute(chunk, 0x37da6e14, setup)
        self.assertEqual(uc.reg_read(UC_ARM_REG_R4), 0x12345678)
        self.assertEqual(uc.reg_read(UC_ARM_REG_R5), MEMORY)
        return struct.unpack('<4i', uc.mem_read(MEMORY, 16))

    def test_whd_inclusive_rectangle_expands(self):
        self.assertEqual(self.geometry((320, 0, 1599, 719)), (0, 0, 1919, 719))

    def test_hd9_full_width_is_unchanged(self):
        self.assertEqual(self.geometry((0, 0, 1279, 719)), (0, 0, 1279, 719))

    def test_each_nonmatching_rectangle_field_preserves_input(self):
        original = [320, 0, 1599, 719]
        for index in range(4):
            for delta in (-1, 1):
                value = original.copy(); value[index] += delta
                with self.subTest(value=value):
                    self.assertEqual(self.geometry(value), tuple(value))

    def crop(self, values, margin=360):
        chunk = self.chunks['Exact 1080p crop alignment']
        def setup(uc):
            uc.reg_write(UC_ARM_REG_R9, MEMORY)
            for offset, value in values.items():
                uc.mem_write(MEMORY + offset, struct.pack('<i', value))
            uc.mem_write(STACK + 0x3c, struct.pack('<i', margin))
        uc = execute(chunk, 0x37d8f240, setup)
        self.assertEqual(uc.reg_read(UC_ARM_REG_R9), MEMORY)
        return struct.unpack('<i', uc.mem_read(MEMORY + 0x38, 4))[0]

    def profile(self):
        return {0x24: 0, 0x28: 0, 0x2c: 1920, 0x30: 720, 0x34: 0,
                0x38: -178, 0x3c: 1920, 0x40: 1080}

    def test_exact_video_profile_aligns_crop(self):
        self.assertEqual(self.crop(self.profile()), -180)

    def test_each_nonmatching_video_field_keeps_factory_crop(self):
        for offset in (0x24, 0x28, 0x2c, 0x30, 0x34, 0x3c, 0x40):
            values = self.profile(); values[offset] += 1
            with self.subTest(offset=hex(offset)):
                self.assertEqual(self.crop(values), -178)
        self.assertEqual(self.crop(self.profile(), margin=362), -178)

    def test_width_clamp_branch_is_unconditional_with_same_destination(self):
        chunk = self.chunks['Remove the AA-only 1280 width clamp']
        # Exercise all four carry/zero combinations: the replacement ignores LS.
        for carry in (0, 1):
            for zero in (0, 1):
                uc = execute(chunk, 0x37d8c678, lambda uc: None,
                             cpsr=0x10 | (carry << 29) | (zero << 30))
                self.assertIsInstance(uc, Uc)


if __name__ == '__main__':
    unittest.main()
