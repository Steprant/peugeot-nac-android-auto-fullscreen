"""Public ARM regression for the exact profile gate, with no firmware fixture."""
import struct
import unittest

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import (UC_ARM_REG_CPSR, UC_ARM_REG_PC, UC_ARM_REG_R8,
                               UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_SP)
from patch_fullscreen_lab import load_projection_spec


class ProjectionGateTests(unittest.TestCase):
    def test_only_exact_nonlegacy_format_replaces_rectangles(self):
        for mode, width_margin, height_margin in ((3, 0, 360), (3, 0, 359), (3, 0, 361),
                                                  (3, 1, 360), (3, 0, 0), (0, 0, 360), (4, 0, 360)):
            with self.subTest(mode=mode, margins=(width_margin, height_margin)):
                cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
                cpu.mem_map(0x76000, 0x2000)
                stack = 0x10000
                cpu.mem_map(stack, 0x1000)
                initial = bytes([0xA5]) * 0x1000
                cpu.mem_write(stack, initial)
                for chunk in load_projection_spec()['chunks']:
                    cpu.mem_write(int(chunk['elf_address'], 16), bytes.fromhex(chunk['after_hex']))
                cpu.reg_write(UC_ARM_REG_SP, stack)
                cpu.reg_write(UC_ARM_REG_R10, mode)
                cpu.reg_write(UC_ARM_REG_R9, width_margin)
                cpu.reg_write(UC_ARM_REG_R8, height_margin)
                # The 480p path has branched out. The preceding CMP with 2 set Z=0.
                cpu.reg_write(UC_ARM_REG_CPSR, cpu.reg_read(UC_ARM_REG_CPSR) & ~(1 << 30))
                selected = (mode, width_margin, height_margin) == (3, 0, 360)
                stop = 0x76ff0 if selected else 0x77040
                cpu.emu_start(0x76fa0, stop, count=30)
                self.assertEqual(cpu.reg_read(UC_ARM_REG_PC), stop)
                expected = bytearray(initial)
                if selected:
                    struct.pack_into('<8I', expected, 0x39c, *((0, 180, 1920, 900) * 2))
                self.assertEqual(cpu.mem_read(stack, 0x1000), expected)
