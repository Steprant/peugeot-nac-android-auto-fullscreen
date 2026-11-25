"""Run the firmware's video rectangle calculation through the call to a stand-in graphics receiver."""
import argparse
import configparser
import hashlib
import json
import struct
from pathlib import Path

from unicorn.arm_const import UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_R0, UC_ARM_REG_S0, UC_ARM_REG_SP

from patch_fullscreen_lab import load_projection_spec, patch_bytes
from prove_arm import RETURN
from prove_native_fullscreen import Native, configure_touch, wayland_touch

PROFILES = Path(__file__).resolve().parent / 'docs' / 'validation' / 'dhu'
VIDEO_ENUM = {'800x480': 1, '1280x720': 2, '1920x1080': 3}
START = 0x76ec8
GET_GRAPHICS_SERVICE = 0x489dc
MOCK_GET_SETTINGS = RETURN + 0x100
MOCK_APPLY_SETTINGS = RETURN + 0x104
MOCK_TOUCH = RETURN + 0x108


class VideoLab(Native):
    def stub(self, name):
        if name == 'memcpy':
            dest, source, count = (self.r(i) for i in range(3))
            self.uc.mem_write(dest, bytes(self.uc.mem_read(source, count)))
            return dest
        if name == 'memset':
            dest, value, count = (self.r(i) for i in range(3))
            self.uc.mem_write(dest, bytes([value & 255]) * count)
            return dest
        if name == 'dlt_user_log_write_start':
            return 1
        if name in ('dlt_user_log_write_uint', 'dlt_user_log_write_string'):
            value = self.r(1)
            if name.endswith('_string'):
                value = self.cstr(value)
            self.messages.append(value)
            return 0
        if name == 'dlt_user_log_write_float32':
            self.messages.append(('float32', self.uc.reg_read(UC_ARM_REG_S0)))
            return 0
        if name == 'dlt_user_log_write_finish':
            self.messages.append(None)
            return 0
        return super().stub(name)

    def hook(self, uc, address, size, user):
        if address == GET_GRAPHICS_SERVICE:
            uc.reg_write(UC_ARM_REG_R0, self.service)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            return
        if address == MOCK_TOUCH:
            count = self.r(2)
            if count not in (1, 2):
                raise AssertionError(('Unexpected contact count', count))
            points = list(struct.iter_unpack('<3I', uc.mem_read(self.r(1), count * 12)))
            self.events.append((self.r(3), self.get32(uc.reg_read(UC_ARM_REG_SP)), points))
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            return
        if address == MOCK_APPLY_SETTINGS:
            if self.r(1) != self.service + 0x20:
                raise AssertionError('Unexpected settings address at graphics receiver.')
            self.submissions.append(bytes(uc.mem_read(self.r(1), 0x24c)))
            uc.reg_write(UC_ARM_REG_R0, 0)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            return
        if address == MOCK_GET_SETTINGS:
            # The graphics service normally fills this settings structure.
            # Keep the initial zeroed settings for both sides of the comparison.
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
            return
        super().hook(uc, address, size, user)

    def evaluate(self, mode, horizontal, vertical, log_level):
        self.messages = []
        obj, graphics, vtable, input_state = (self.alloc(256) for _ in range(4))
        self.put32(obj + 4, graphics)
        self.put32(graphics, vtable)
        self.put32(vtable + 0x30, MOCK_GET_SETTINGS)
        self.put32(vtable + 0x2c, MOCK_APPLY_SETTINGS)
        self.service = self.alloc(0x270)
        self.put32(self.service + 4, graphics)
        self.submissions = []
        # Other graphics state, including per-unit offsets, is zero in this fixture.
        self.put32(obj + 0x40, input_state)
        self.put32(input_state + 0x84, {1: 800, 2: 1280, 3: 1920}.get(mode, 1920))

        # Original PC-relative GOT loads used by the DLT level check.
        got_base = (0x76f0c + self.get32(0x77a20)) & 0xffffffff
        context_slot = got_base + self.get32(0x77a28)
        ctx = self.alloc(64)
        self.put32(context_slot, ctx)
        if log_level is not None:
            level = self.alloc(4)
            self.put32(level, log_level)
            self.put32(ctx + 8, level)

        self.run(START, (obj, mode, horizontal, vertical))
        if len(self.submissions) != 1:
            raise AssertionError('Expected one graphics submission per configuration.')
        settings = self.submissions[0]
        coords = struct.unpack_from('<8I', settings, 0x12c)
        return list(coords[:4]), list(coords[4:]), self.messages, settings


def replay_touch(candidate, digest, *, properties=None, surface_y=-180):
    lab = VideoLab(candidate, digest)
    user, _, _ = configure_touch(lab, properties=properties)
    lab.service = lab.alloc(0x2c0)
    receiver, vtable = lab.alloc(64), lab.alloc(128)
    lab.put32(lab.service + 0x1c, 1)
    lab.put32(lab.service + 0x2b0, receiver)
    lab.put32(receiver, vtable)
    lab.put32(vtable + 0x30, MOCK_TOUCH)
    lab.events = []
    # Two contacts cross opposite edges, then release separately.
    sequence = [('down', 0, 0, 0, 0), ('down', 1, 1919, 719, 5),
                ('motion', 0, 1919, 0, 2), ('motion', 1, 0, 719, 2),
                ('up', 1, 0, 719, 6), ('up', 0, 1919, 0, 1)]
    active = {}
    records = []
    for step, (action, finger, x, y, code) in enumerate(sequence, 1):
        active[finger] = (finger, x, y)
        wayland_touch(lab, user, x, y - surface_y, action, finger)
        if len(lab.events) != step:
            raise AssertionError(('Expected one dispatched event', step, lab.events))
        event, index, points = lab.events[-1]
        if (event, points) != (code, list(active.values())) or points[index][0] != finger:
            raise AssertionError((action, finger, code, event, index, points))
        records.append({'action': action, 'finger': finger, 'event': event, 'index': index,
                        'contacts_id_x_y': points})
        if action == 'up':
            del active[finger]
    return records


def run_comparison(root):
    spec = load_projection_spec()
    stock = (root / spec['source_path']).read_bytes()
    candidate = patch_bytes(stock, spec)
    cases = {}
    for name in ('central-720p', 'whd-1080p', 'wide-720p'):
        ini = configparser.ConfigParser()
        with (PROFILES / (name + '.ini')).open() as stream:
            ini.read_file(stream)
        general = ini['general']
        cases[name] = (VIDEO_ENUM[general['resolution']], general.getint('marginwidth', 0),
                       general.getint('marginheight', 0))
    cases.update({'480p': (1, 0, 0), '480p-margins': (1, 80, 60), '1080p-no-margin': (3, 0, 0),
                  '1080p-width-margin': (3, 1, 360), '1080p-height-361': (3, 0, 361),
                  '1080p-height-359': (3, 0, 359), 'unknown-mode': (4, 0, 360)})
    records = []
    for name, args in cases.items():
        for log_level in (None, 0, 3, 4):
            old = VideoLab(stock, spec['original_sha256']).evaluate(*args, log_level)
            new = VideoLab(candidate, spec['candidate_sha256']).evaluate(*args, log_level)
            if args == (3, 0, 360):
                target = [0, 180, 1920, 900]
                if old[3][:0x12c] + old[3][0x14c:] != new[3][:0x12c] + new[3][0x14c:]:
                    raise AssertionError('Unrelated graphics settings changed.')
                if new[:2] != (target, target) or old[:2] == new[:2]:
                    raise AssertionError((name, log_level, old[:2], new[:2]))
            elif old != new:
                raise AssertionError((name, log_level, old, new))
            if log_level is None:
                records.append({'profile': name, 'mode_widthMargin_heightMargin': list(args),
                                'original_source': old[0], 'original_target': old[1],
                                'candidate_source': new[0], 'candidate_target': new[1]})
    touch_events = replay_touch(candidate, spec['candidate_sha256'])
    return {'firmware': '44.07.33.32_NAC-r0', 'scope': 'ARM emulation through submission to a mock graphics receiver',
            'original_sha256': hashlib.sha256(stock).hexdigest(),
            'candidate_sha256': hashlib.sha256(candidate).hexdigest(),
            'log_levels': [None, 0, 3, 4], 'comparisons': len(cases) * 4, 'rectangles_ltrb': records,
            'touch_events': touch_events,
            'touch_receiver': 'mock, records contacts at the native projection interface',
            'graphics_settings_provider': 'mocked, zero initial settings',
            'native_graphics_submission_executed': True, 'graphics_receiver': 'mock', 'native_touch_dispatch_executed': True,
            'physical_nac_tested': False, 'phone_tested': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs', type=Path, required=True)
    print(json.dumps(run_comparison(parser.parse_args().rootfs), indent=2))
