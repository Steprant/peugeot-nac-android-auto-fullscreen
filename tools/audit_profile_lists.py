#!/usr/bin/env python3
"""Read-only regression audit for the existing offline graphics candidate.

Reuses the project's ARM graphics test fixture without creating a firmware
package, communicating with a device, or changing any original files.
Run as python -m tools.audit_profile_lists --rootfs PATH.
"""
import argparse
import json
from pathlib import Path

from unicorn import UcError

from patch_fullscreen_lab import load_automatic_profile_spec, patch_bytes
from prove_automatic_profile import APP_SHA256, DIMENSIONS, AutomaticProfileLab
from tools.projection_reference import Layout, Profile


# These are synthetic calls to the graphics configuration routine. The screen
# enum inputs are controls; they do not identify a different physical car.
CASES = (
    ('SD_control', (800, 480), 0, False, None),
    ('720p_control_enum_0', (1280, 720), 0, False, None),
    ('720p_control_enum_4', (1280, 720), 4, False, None),
    ('720p_control_enum_5', (1280, 720), 5, False, None),
    ('1080p_control', (1920, 1080), 0, False, None),
    ('1080p_horizontal_margin_control', (1920, 1080), 4, False, None),
    ('adjacent_width_control', (1840, 720), 5, False, None),
    ('adjacent_height_control', (1920, 719), 4, False, None),
    ('exact_WHD_enum_4', (1920, 720), 4, True, None),
    ('exact_WHD_enum_5', (1920, 720), 5, True, None),
    ('exact_WHD_without_1080p', (1920, 720), 4, True, DIMENSIONS[:2]),
)


def collect(data, digest, visible, ecran, frames):
    lab = AutomaticProfileLab(data, digest, frames=frames)
    parameters = lab.parameters(*visible, ecran)['native_parameters']
    outcome = {'parameters': parameters, 'list_returned': False}
    try:
        configurations = lab.video_configurations()
    except (UcError, RuntimeError) as error:
        outcome.update({'emulator_error': type(error).__name__, 'error_summary': str(error),
                        'append_count_before_error': len(lab.advertised),
                        'records_observed_before_error': lab.advertised[:3]})
        return outcome
    outcome.update({'list_returned': True, 'records': configurations})
    try:
        outcome['hmi_sizes'] = [lab.hmi_screen_size(properties) for properties in configurations]
    except (UcError, RuntimeError) as error:
        outcome['hmi_error'] = type(error).__name__
    return outcome


def expected_geometry(frames):
    result = []
    for frame in reversed(frames):
        mode = DIMENSIONS.index(frame) + 1
        profile = Profile.panoramic(frame)
        layout = Layout.fit(profile)
        logical = layout.logical_frame
        result.append({'geometry_fields': [mode, profile.width_margin, profile.height_margin],
                       'hmi_size_reference': {'width_margin': logical.width-layout.destination.width,
                                              'height_margin': logical.height-layout.destination.height,
                                              'frame_width': logical.width, 'frame_height': logical.height}})
    return result


def evaluate_case(original, candidate, spec, name, visible, ecran, panoramic, frames):
    stock = collect(original, APP_SHA256, visible, ecran, frames)
    new = collect(candidate, spec['candidate_sha256'], visible, ecran, frames)
    if not stock['list_returned'] or 'hmi_error' in stock:
        raise AssertionError(f'Unusable original control: {name}')
    record = {'case': name, 'visible_size': list(visible), 'screen_enum': ecran,
              'original': stock, 'candidate': new}
    if panoramic:
        record['reference'] = expected_geometry(frames or DIMENSIONS)
    if not new['list_returned']:
        record.update({'pass': False, 'reason': 'candidate did not return a configuration list'})
    elif not panoramic:
        record['pass'] = stock == new
        record['reason'] = 'unchanged control' if record['pass'] else 'unexpected change outside the target geometry'
    else:
        expected = record['reference']
        list_ok = [r[:3] for r in new['records']] == [r['geometry_fields'] for r in expected]
        hmi_ok = new.get('hmi_sizes') == [r['hmi_size_reference'] for r in expected]
        record.update({'list_geometry_matches': list_ok, 'hmi_geometry_matches': hmi_ok,
                       'pass': list_ok and hmi_ok,
                       'reason': 'matches standalone reference' if list_ok and hmi_ok else 'incomplete panoramic geometry'})
    return record


def audit(rootfs):
    spec = load_automatic_profile_spec()
    original = (rootfs / spec['source_path']).read_bytes()
    candidate = patch_bytes(original, spec)
    records = [evaluate_case(original, candidate, spec, *case) for case in CASES]
    return {'scope': 'PC ARM display-code regression; Qt and screen type simulated; no device connection',
            'original_sha256': spec['original_sha256'], 'candidate_sha256': spec['candidate_sha256'],
            'case_count': len(records), 'passed': sum(case['pass'] for case in records),
            'candidate_passes_pc_audit': all(case['pass'] for case in records), 'cases': records,
            'physical_nac_tested': False, 'phone_tested': False, 'installation_verified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rootfs', required=True, type=Path)
    result = audit(parser.parse_args().rootfs)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['candidate_passes_pc_audit'] else 1)
