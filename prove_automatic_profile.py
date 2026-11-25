#!/usr/bin/env python3
"""Exercise the original registration, sizing and native no-file video path on PC."""
import argparse
import configparser
import copy
import json
import re
import struct
from pathlib import Path

from unicorn.arm_const import (UC_ARM_REG_PC, UC_ARM_REG_R4, UC_ARM_REG_R6, UC_ARM_REG_R8,
                               UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC)

from audit_statico import ROOT_FILES, digest
from config_laboratorio import render_cfg
from patch_fullscreen_lab import PROFILE, load_automatic_profile_spec, load_projection_spec, patch_bytes
from prove_arm import APP_SHA256, OVERRIDE_START, OVERRIDE_END, STACK, ConfigLab
from prove_native_fullscreen import visible_area, crop_offset
from prove_projection_whd import VideoLab, replay_touch


DIMENSIONS = ((800, 480), (1280, 720), (1920, 1080))
FIELDS = ('screen_type', 'frame_width', 'frame_height', 'resolution', 'width_margin',
          'height_margin', 'frame_rate', 'dpi', 'field_38', 'real_dpi_mock_result', 'field_40')


class AutomaticProfileLab(ConfigLab):
    def __init__(self, data, expected, *, cfg=None, frames=None):
        super().__init__(data, cfg, expected=expected)
        self.uc.reg_write(UC_ARM_REG_C1_C0_2, 0x00f00000)
        self.uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)
        self.screen = self.alloc(0x80)
        self.screen_type = self.alloc(0x40)
        self.dimension_map = self.alloc(32)
        self.enum_map = self.alloc(32)
        self.put32(self.dimension_map, 1)
        self.put32(self.enum_map, 1)
        self.put32(self.screen + 0x10, self.dimension_map)
        self.put32(self.screen + 0x14, self.enum_map)
        self.put32(self.screen + 0x44, self.obj)
        self.put32(self.screen + 0x50, self.screen_type)
        self.real_dpi_calls = []
        self.advertised = []

        # Constructor's original height-to-resolution enum registration.
        self.uc.reg_write(UC_ARM_REG_R4, self.screen)
        self.run(0x37ebe020, stops=(0x37ebe180,))
        if frames is None:
            # The original caller registers all three device resolutions.
            owner = self.alloc(64)
            self.put32(owner + 0x2c, self.screen)
            self.uc.reg_write(UC_ARM_REG_R4, owner)
            self.uc.reg_write(UC_ARM_REG_R6, self.screen)
            self.run(0x37eba790, stops=(0x37eba7c0,))
        else:
            # Reduced capability table for fallback controls only.
            for width, height in frames:
                self.run(0x37ebb24c, (self.screen, width, height))

    def nodes(self, map_data):
        result = []
        visited = set()

        def visit(node):
            if not node:
                return
            if node in visited or len(visited) >= 16:
                raise ValueError('Invalid simulated Qt map')
            visited.add(node)
            visit(self.get32(node + 4))
            result.append(node)
            visit(self.get32(node + 8))

        visit(self.get32(map_data + 12))
        return result

    def registrations(self):
        return {
            'dimensions': [[self.get32(node + 16), self.get32(node + 12)]
                           for node in self.nodes(self.dimension_map)],
            'height_to_resolution': [[self.get32(node + 12), self.get32(node + 16)]
                                     for node in self.nodes(self.enum_map)],
        }

    def hook(self, uc, address, size, user):
        name = self.plt.get(address, '')
        if name in self.symbols and any(symbol in name for symbol in (
                'addSupportedDeviceResolutions', 'getVideoDensity', 'CAAPVideoScreenSize8mapValue',
                'CAAPVideoScreenSize16isVideoPropEqual')):
            self.calls[name] += 1
            uc.reg_write(UC_ARM_REG_PC, self.symbols[name])
            return
        super().hook(uc, address, size, user)

    def stub(self, name):
        if name in ('_ZNK12QMapNodeBase8nextNodeEv', '_ZNK12QMapNodeBase12previousNodeEv'):
            nodes = self.nodes(self.dimension_map)
            node = self.r(0)
            sentinel = self.dimension_map + 8
            if node == sentinel and name.endswith('previousNodeEv'):
                return nodes[-1]
            index = nodes.index(node) + (1 if name.endswith('nextNodeEv') else -1)
            return nodes[index] if 0 <= index < len(nodes) else sentinel
        if name == '_ZN7connsvc11androidauto2al14CAAPScreenType12getEcranTypeEv':
            return self.get32(self.r(0) + 0x28)
        if name == '_ZN7connsvc11androidauto2al19CAAPVideoScreenSize16calculateRealDPIENS0_23CE_CONF_VideoResolutionEjNS0_10eEcranTypeE':
            self.real_dpi_calls.append([self.r(1), self.r(2), self.r(3)])
            return 250
        if name == '_ZN5QListIN7connsvc11androidauto23CE_CONF_VideoPropertiesEE6appendERKS2_':
            self.advertised.append(list(struct.unpack('<8I', self.uc.mem_read(self.r(1), 32))))
            return None
        if name == '_ZN5QListIN7connsvc11androidauto23CE_CONF_VideoPropertiesEEC1ERKS3_':
            self.put32(self.r(0), self.get32(self.r(1)))
            return None
        if name == '_ZN5QListIN7connsvc11androidauto23CE_CONF_VideoPropertiesEED1Ev':
            return None
        return super().stub(name)

    def choose_frame(self, width, height):
        out = self.alloc(16)
        self.put32(STACK + 0x18000, self.screen + 0x10)
        self.run(0x37ebb33c, (out, self.screen, width, height))
        _, frame_width, frame_height = struct.unpack('<3I', self.uc.mem_read(out, 12))
        return frame_width, frame_height

    def parameters(self, width, height, ecran_type, *, screen_type=2, frame_rate=1):
        parsed = self.parse()
        frame_width, frame_height = self.choose_frame(width, height)
        self.put32(self.screen + 8, screen_type)
        self.put32(self.screen + 12, frame_rate)
        self.put32(self.screen_type + 0x28, ecran_type)
        self.uc.reg_write(UC_ARM_REG_R4, self.screen)
        self.uc.reg_write(UC_ARM_REG_R8, height)
        sp = STACK + 0x18000
        self.put32(sp + 0x28, width)
        self.put32(sp + 0x50, frame_width)
        self.put32(sp + 0x54, frame_height)
        self.run(OVERRIDE_START, stops=(OVERRIDE_END,))
        if self.last_stop != OVERRIDE_END:
            raise RuntimeError('Unexpected automatic configuration exit')
        return {
            'configuration_file_enabled': parsed['flag'],
            'mapped_frame': [frame_width, frame_height],
            'native_parameters': dict(zip(FIELDS, (self.get32(self.screen + offset)
                                                  for offset in range(0x18, 0x44, 4)))),
            'real_dpi_call_arguments': list(self.real_dpi_calls),
        }

    def video_configurations(self):
        # Capture the actual native list append operations. The Qt container
        # and real DPI return are simulated; Android Auto is not connected.
        self.advertised.clear()
        self.put32(self.screen + 0x48, self.import_data['_ZN9QListData11shared_nullE'])
        self.run(0x37ebc870, (self.alloc(4), self.screen))
        # Provide the captured records through a minimal QList data layout,
        # so getHMIScreenSize can take its original configuration-list path.
        data = self.alloc(16 + 4 * len(self.advertised))
        self.put32(data, 1)
        self.put32(data + 4, len(self.advertised))
        self.put32(data + 12, len(self.advertised))
        for index, properties in enumerate(self.advertised):
            fields = self.alloc(32)
            self.uc.mem_write(fields, struct.pack('<8I', *properties))
            self.put32(data + 16 + 4 * index, fields)
        self.put32(self.screen + 0x48, data)
        return list(self.advertised)

    def hmi_screen_size(self, properties):
        # Run original equality/selection and dimension arithmetic, stopping
        # before the diagnostic logging that follows the four output stores.
        outputs = tuple(self.alloc(4) for _ in range(4))
        sp = STACK + 0x18000
        for index, value in enumerate([*properties[3:], *outputs]):
            self.put32(sp + 4 * index, value)
        self.run(0x37ebcacc, (self.screen, *properties[:3]), stops=(0x37ebcbc4,))
        if self.last_stop != 0x37ebcbc4:
            raise RuntimeError('Unexpected HMI screen-size exit')
        return dict(zip(('width_margin', 'height_margin', 'frame_width', 'frame_height'),
                        (self.get32(out) for out in outputs)))


def factory_rectangles(root):
    name = 'usr/share/ovip/ScreenManager/ScreenAreas.ini'
    if digest(root / name) != ROOT_FILES[name]:
        raise ValueError('Unrecognized factory geometry')
    config = configparser.ConfigParser(interpolation=None)
    with (root / name).open() as stream:
        config.read_file(stream)
    result = {}
    for category in config.sections():
        match = re.fullmatch(r'@Rect\((\d+) (\d+) (\d+) (\d+)\)', config[category]['FULLSCREEN'])
        if not match:
            raise ValueError('Unexpected factory rectangle')
        result[category] = tuple(map(int, match.groups()))
    return result


def comparisons(root):
    spec = load_automatic_profile_spec()
    original = (root / spec['source_path']).read_bytes()
    candidate = patch_bytes(original, spec)
    registration = AutomaticProfileLab(original, APP_SHA256).registrations()
    if registration != {'dimensions': [list(pair) for pair in DIMENSIONS],
                        'height_to_resolution': [[480, 1], [720, 2], [1080, 3]]}:
        raise AssertionError(registration)

    factory = factory_rectangles(root)
    requests = {f'factory_{name}': rect[2:] for name, rect in factory.items()}
    requests.update({
        'WHD_full': (1920, 720), 'WHD_height_719': (1920, 719),
        'WHD_height_721': (1920, 721), 'WHD_height_1440': (1920, 1440),
        'width_1919': (1919, 720), 'width_1921': (1921, 720),
        'unmargined_1080p': (1920, 1080), 'panoramic_720p': (1280, 480),
    })
    records = []
    for name, request in requests.items():
        for ecran in range(7):
            old = AutomaticProfileLab(original, APP_SHA256).parameters(*request, ecran)
            new = AutomaticProfileLab(candidate, spec['candidate_sha256']).parameters(*request, ecran)
            expected = copy.deepcopy(old)
            if name == 'WHD_full' and ecran in (4, 5):
                if old['native_parameters']['width_margin'] != 80:
                    raise AssertionError(old)
                expected['native_parameters']['width_margin'] = 0
            if new != expected:
                raise AssertionError((name, ecran, old, new))
            records.append({'request': name, 'visible': list(request), 'screen_enum': ecran,
                            'original': old, 'candidate': new})

    fallback = DIMENSIONS[:2]
    old = AutomaticProfileLab(original, APP_SHA256, frames=fallback).parameters(1920, 720, 4)
    new = AutomaticProfileLab(candidate, spec['candidate_sha256'], frames=fallback).parameters(1920, 720, 4)
    if old != new or new['native_parameters']['resolution'] != 2:
        raise AssertionError(('720p fallback', old, new))

    cfg = render_cfg(PROFILE)
    explicit_old = AutomaticProfileLab(original, APP_SHA256, cfg=cfg).parameters(1280, 720, 4)
    explicit_new = AutomaticProfileLab(candidate, spec['candidate_sha256'], cfg=cfg).parameters(1280, 720, 4)
    if explicit_old != explicit_new or not explicit_new['configuration_file_enabled']:
        raise AssertionError('Original explicit file configuration behavior changed')

    # Feed the HMI's actual candidate rectangle into the automatic native path
    # and then forward those exact parameters to the revision 5 video proof.
    hmi_area = visible_area(root, factory['WHD'])
    lab = AutomaticProfileLab(candidate, spec['candidate_sha256'])
    linked = lab.parameters(hmi_area['width'], hmi_area['height'], 4)
    video = linked['native_parameters']
    advertised = lab.video_configurations()
    if len(advertised) != 3 or advertised[0] != [video[field] for field in FIELDS[3:]]:
        raise AssertionError(('Primary configuration differs from automatic selection', advertised))
    original_lab = AutomaticProfileLab(original, APP_SHA256)
    original_lab.parameters(hmi_area['width'], hmi_area['height'], 4)
    original_advertised = original_lab.video_configurations()
    if [entry[2] for entry in original_advertised] != [360, 360, 360]:
        raise AssertionError(('Original fallback margins', original_advertised))
    if [entry[2] for entry in advertised] != [360, 240, 240]:
        raise AssertionError(('Candidate fallback margins', advertised))

    # A normal unmargined 1080p request must retain the original list.
    neutral_old = AutomaticProfileLab(original, APP_SHA256)
    neutral_old.parameters(1920, 1080, 4)
    neutral_new = AutomaticProfileLab(candidate, spec['candidate_sha256'])
    neutral_new.parameters(1920, 1080, 4)
    if neutral_old.video_configurations() != neutral_new.video_configurations():
        raise AssertionError('Fallback guard changed an unmargined 1080p profile')
    hmi_size = lab.hmi_screen_size(advertised[0])
    expected_hmi_size = {field: video[field] for field in hmi_size}
    if hmi_size != expected_hmi_size:
        raise AssertionError(('1080p HMI parameters', expected_hmi_size, hmi_size))
    offset = crop_offset(root, (hmi_area['x'], hmi_area['y'], hmi_area['width'], hmi_area['height']),
                         (hmi_size['frame_width'], hmi_size['frame_height']),
                         hmi_size['height_margin'], hmi_size['width_margin'])
    if offset['candidate_y'] != -180:
        raise AssertionError(('HMI crop offset', offset))
    proj = load_projection_spec()
    graphics = patch_bytes((root / proj['source_path']).read_bytes(), proj)
    source, target, _, _ = VideoLab(graphics, proj['candidate_sha256']).evaluate(
        video['resolution'], video['width_margin'], video['height_margin'], None)
    if source != [0, 180, 1920, 900] or target != source:
        raise AssertionError(('End-to-end virtual crop', source, target))
    configurations = []
    for properties in advertised:
        mode, horizontal, vertical = properties[:3]
        frame_width, frame_height = DIMENSIONS[mode - 1]
        fallback_source, fallback_target, _, _ = VideoLab(
            graphics, proj['candidate_sha256']).evaluate(mode, horizontal, vertical, None)
        configurations.append({
            'properties': dict(zip(FIELDS[3:], properties)),
            'visible_content': [frame_width - horizontal, frame_height - vertical],
            'native_hmi_size': lab.hmi_screen_size(properties),
            'projection_source_ltrb': fallback_source,
            'projection_target_ltrb': fallback_target,
        })
    if configurations[1]['projection_source_ltrb'] != [0, 120, 1280, 600]:
        raise AssertionError(('720p projection crop', configurations[1]))
    touch_events = replay_touch(graphics, proj['candidate_sha256'], properties=advertised[0],
                                surface_y=offset['candidate_y'])

    return {
        'firmware': '44.07.33.32_NAC-r0',
        'scope': 'ARM emulation using Qt map, file, screen-type and graphics substitutes',
        'registrations_executed_in_native_code': registration,
        'factory_rectangles': factory,
        'comparisons': records,
        'fallback_720p': new,
        'explicit_file_behavior_preserved': explicit_new,
        'linked_hmi_and_projection': {'hmi': hmi_area, 'automatic_video': linked,
                                      'original_fallback_margins': [entry[2] for entry in original_advertised],
                                      'native_configuration_list': configurations,
                                      'crop_offset': offset,
                                      'source_ltrb': source, 'target_ltrb': target,
                                      'touch_events': touch_events},
        'real_dpi_calculation': 'arguments checked; return value simulated',
        'phone_tested': False,
        'physical_nac_tested': False,
        'installation_verified': False,
    }


if __name__ == '__main__':
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--rootfs', required=True, type=Path)
    print(json.dumps(comparisons(args.parse_args().rootfs), indent=2))
