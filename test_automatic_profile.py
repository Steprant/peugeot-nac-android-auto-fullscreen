"""Regression tests of the automatic geometry guard, using synthetic memory."""
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import (UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R8,
                               UC_ARM_REG_PC, UC_ARM_REG_SP, UC_ARM_REG_LR)

from patch_fullscreen_lab import load_automatic_profile_spec


class AutomaticProfileGuardTests(unittest.TestCase):
    def evaluate(self, width, height, frame, ecran):
        chunk, = load_automatic_profile_spec()['chunks']
        start = int(chunk['elf_address'], 16)
        complete, forced, get_ecran = 0x37ebd9dc, 0x37ebdbf4, 0x37e273ec
        cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
        cpu.mem_map(0x37ebd000, 0x1000)
        cpu.mem_map(0x37e27000, 0x1000)
        cpu.mem_write(start, bytes.fromhex(chunk['after_hex']))
        obj, stack = 0x10000, 0x20000
        cpu.mem_map(obj, 0x1000)
        cpu.mem_map(stack, 0x1000)

        def put32(address, value):
            cpu.mem_write(address, value.to_bytes(4, 'little'))

        def get32(address):
            return int.from_bytes(cpu.mem_read(address, 4), 'little')

        calls = []

        def hook(uc, address, size, user):
            if address == get_ecran:
                calls.append(address)
                uc.reg_write(UC_ARM_REG_R0, ecran)
                uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            elif address == forced:
                uc.emu_stop()

        put32(obj + 8, 2)
        put32(obj + 12, 1)
        put32(stack + 0x28, width)
        put32(stack + 0x50, frame[0])
        put32(stack + 0x54, frame[1])
        cpu.reg_write(UC_ARM_REG_R4, obj)
        cpu.reg_write(UC_ARM_REG_R8, height)
        cpu.reg_write(UC_ARM_REG_SP, stack)
        cpu.hook_add(UC_HOOK_CODE, hook)
        cpu.emu_start(start, complete, count=100)
        stop = cpu.reg_read(UC_ARM_REG_PC)
        self.assertIn(stop, (complete, forced))
        self.assertEqual((get32(obj + 0x1c), get32(obj + 0x20)), frame)
        self.assertEqual(get32(obj + 0x2c), (abs(height - frame[1]) + 1) & ~1)
        self.assertEqual((get32(obj + 0x18), get32(obj + 0x30)), (2, 1))
        return (80 if stop == forced else get32(obj + 0x28), len(calls))

    def test_exact_wide_geometry_uses_zero_margin(self):
        for ecran in range(7):
            with self.subTest(ecran=ecran):
                margin, calls = self.evaluate(1920, 720, (1920, 1080), ecran)
                self.assertEqual((margin, calls), (0, 0))

    def test_adjacent_geometries_and_fallback_keep_factory_margin(self):
        cases = [(1920, 719, (1920, 1080)), (1920, 721, (1920, 1080)),
                 (1920, 1440, (1920, 1080)), (1919, 720, (1920, 1080)),
                 (1920, 720, (1280, 720)), (1920, 720, (1920, 360)),
                 (1920, 1080, (1920, 1080)), (1280, 720, (1280, 720)),
                 (800, 480, (800, 480))]
        for width, height, frame in cases:
            for ecran in (0, 4, 5, 6):
                with self.subTest(width=width, height=height, frame=frame, ecran=ecran):
                    margin, calls = self.evaluate(width, height, frame, ecran)
                    expected = 80 if ecran in (4, 5) else abs(width - frame[0])
                    self.assertEqual((margin, calls), (expected, 1))
