#!/usr/bin/env python3
"""Decode synthetic H.264 and exercise crop, uniform scale and touch on PC only.

Run from the repository root with python -m tools.prove_reference_video.
Requires local FFmpeg with libx264; does not connect to any device or service.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from tools.projection_reference import PANEL, PROFILES, Layout, Profile, TouchRouter


FRAMES = 30
NAMES = ('central-720p', 'whd-1080p', 'wide-720p', 'wide-480p')
COLORS = (('red', (255, 0, 0)), ('lime', (0, 255, 0)),
          ('blue', (0, 0, 255)), ('yellow', (255, 255, 0)))
SQUARE = 40
SQUARE_COLOR = (255, 0, 255)


def run(ffmpeg, *args):
    result = subprocess.run([ffmpeg, '-nostdin', '-hide_banner', *map(str, args)],
                            capture_output=True, check=True, timeout=55)
    return result.stderr.decode('utf-8', errors='replace')


def corners(rect):
    return ((rect.x, rect.y), (rect.right - 1, rect.y),
            (rect.x, rect.bottom - 1), (rect.right - 1, rect.bottom - 1))


def drawbox(x, y, w, h, color, thickness='fill'):
    return f'drawbox=x={x}:y={y}:w={w}:h={h}:color={color}:t={thickness}'


def encode(ffmpeg, layout, output):
    source = layout.profile.source
    width, height = layout.profile.frame
    w, h = source.width, source.height
    marker = 32
    filters = [drawbox(0, 0, w, h, 'white', '4')]
    for (color, _), (x, y) in zip(COLORS, ((0, 0), (w-marker, 0), (0, h-marker), (w-marker, h-marker))):
        filters.append(drawbox(x, y, marker, marker, color))
    # Put a square on a contrasting background to measure the scaling in
    # both axes, not just the resulting canvas dimensions.
    filters.append(drawbox(w//2-28, h//2-28, 56, 56, 'black'))
    filters.append(drawbox(w//2-SQUARE//2, h//2-SQUARE//2, SQUARE, SQUARE, 'magenta'))
    filters.append(f'pad={width}:{height}:{source.x}:{source.y}:black')
    run(ffmpeg, '-v', 'error', '-f', 'lavfi', '-i', f'testsrc2=size={w}x{h}:rate=30',
        '-filter_threads', 1, '-vf', ','.join(filters), '-frames:v', FRAMES,
        '-c:v', 'libx264', '-preset', 'fast', '-crf', 15, '-pix_fmt', 'yuv420p',
        '-threads', 2, '-f', 'h264', output)


def detected_crops(ffmpeg, video, expected):
    log = run(ffmpeg, '-v', 'info', '-nostats', '-threads', 2, '-i', video,
              '-filter_threads', 1, '-vf', 'cropdetect=limit=32:round=2:reset=1:skip=0',
              '-f', 'null', '-')
    found = [tuple(map(int, values)) for values in re.findall(r'\bcrop=(\d+):(\d+):(\d+):(\d+)', log)]
    wanted = (expected.width, expected.height, expected.x, expected.y)
    if len(found) != FRAMES or set(found) != {wanted}:
        raise AssertionError(f'Unexpected decoded crops: {len(found)} frames, {sorted(set(found))}')
    return list(wanted)


def pixel(image, x, y):
    i = (y * PANEL[0] + x) * 3
    return tuple(image[i:i+3])


def matches(rgb, color, tolerance=45):
    return all(abs(a-b) <= tolerance for a, b in zip(rgb, color))


def square_size(image, x, y, axis):
    def in_marker(a, b):
        return (0 <= a < PANEL[0] and 0 <= b < PANEL[1]
                and matches(pixel(image, a, b), SQUARE_COLOR))
    if not in_marker(x, y):
        raise AssertionError('Central square missing')
    length = 1
    for direction in (-1, 1):
        dx, dy = axis[0]*direction, axis[1]*direction
        a, b = x+dx, y+dy
        while in_marker(a, b):
            length += 1
            a, b = a+dx, b+dy
    return length


def mapping_proof(layout):
    source, target = layout.profile.source, layout.destination
    counts = {'panel_pixels_per_axis': [target.width, target.height],
              'source_pixels_per_axis': [source.width, source.height]}
    errors = []
    for src_rect, dst_rect, forward, reverse in (
            (target, source, layout.panel_to_frame, layout.frame_to_panel),
            (source, target, layout.frame_to_panel, layout.panel_to_frame)):
        axis_errors = []
        for axis in (0, 1):
            maximum = 0
            start, length = ((src_rect.x, src_rect.width) if axis == 0 else (src_rect.y, src_rect.height))
            for value in range(start, start+length):
                p = (value, src_rect.y) if axis == 0 else (src_rect.x, value)
                mapped = forward(*p)
                if mapped is None or not dst_rect.contains(*mapped):
                    raise AssertionError('In-bounds pixel mapped outside the destination')
                back = reverse(*mapped)
                maximum = max(maximum, abs(back[axis]-value))
            axis_errors.append(maximum)
        errors.append(axis_errors)
    if max(errors[0]) > 1 or errors[1] != [0, 0]:
        raise AssertionError(f'Unexpected coordinate roundtrip errors: {errors}')
    counts['panel_roundtrip_max_error_xy'] = errors[0]
    counts['source_roundtrip_max_error_xy'] = errors[1]

    router = TouchRouter(layout)
    router.set_focus(True)
    mapped_corners = []
    for i, (point, expected) in enumerate(zip(corners(target), corners(source))):
        down, = router.touch('down', i, *point)
        if down.frame_xy != expected:
            raise AssertionError(f'Wrong touch at {point}: {down.frame_xy}, expected {expected}')
        mapped_corners.append({'panel_xy': list(point), 'frame_xy': list(down.frame_xy)})
    cancelled = router.set_focus(False)
    if len(cancelled) != 4 or router.active or router.touch('move', 0, target.x, target.y):
        raise AssertionError('Lost focus did not release active touches')
    counts['four_corners'] = mapped_corners
    counts['focus_transition_cancelled_pointers'] = len(cancelled)
    return counts


def render_and_measure(ffmpeg, video, output, layout):
    source, dest = layout.profile.source, layout.destination
    filters = (f'crop={source.width}:{source.height}:{source.x}:{source.y},'
               f'scale={dest.width}:{dest.height}:flags=neighbor,'
               f'pad={PANEL[0]}:{PANEL[1]}:{dest.x}:{dest.y}:black,format=rgb24')
    run(ffmpeg, '-v', 'error', '-threads', 2, '-i', video, '-filter_threads', 1, '-vf', filters,
        '-frames:v', FRAMES, '-c:v', 'rawvideo', '-threads', 1, '-f', 'rawvideo', output)
    expected_size = PANEL[0]*PANEL[1]*3
    if output.stat().st_size != expected_size * FRAMES:
        raise AssertionError('Wrong decoded panel frame count or size')
    widths, heights = [], []
    expected_square = int(SQUARE * layout.scale)
    edge_samples = corners(dest)
    black_samples = []
    if dest.x:
        black_samples.extend((x, y) for x in (0, dest.x-1) for y in (0, PANEL[1]//2, PANEL[1]-1))
    if dest.right < PANEL[0]:
        black_samples.extend((x, y) for x in (dest.right, PANEL[0]-1) for y in (0, PANEL[1]//2, PANEL[1]-1))
    with output.open('rb') as frames:
        for i in range(FRAMES):
            image = frames.read(expected_size)
            for point, (_, color) in zip(edge_samples, COLORS):
                if not matches(pixel(image, *point), color):
                    raise AssertionError(f'Corner marker absent in frame {i} at {point}: {pixel(image, *point)}')
            if any(not matches(pixel(image, *point), (0, 0, 0), 8) for point in black_samples):
                raise AssertionError('Unexpected picture in the central-control sidebars')
            x, y = dest.x + dest.width//2, dest.y + dest.height//2
            w, h = square_size(image, x, y, (1, 0)), square_size(image, x, y, (0, 1))
            if abs(w-expected_square) > 2 or abs(h-expected_square) > 2 or abs(w-h) > 2:
                raise AssertionError(f'Unexpected square size in frame {i}: {w}x{h}, expected {expected_square}')
            widths.append(w)
            heights.append(h)
    return {'displayed_frame_size': list(PANEL), 'decoded_frames': FRAMES,
            'corner_markers_observed_in_all_frames': len(edge_samples),
            'black_control_samples_per_frame': len(black_samples),
            'expected_square_width_and_height': expected_square,
            'measured_square_width_range': [min(widths), max(widths)],
            'measured_square_height_range': [min(heights), max(heights)]}


def proof(ffmpeg):
    records = {}
    for name in NAMES:
        path = PROFILES / f'{name}.ini'
        profile = Profile.from_ini(path)
        if name != 'central-720p' and profile != Profile.panoramic(profile.frame):
            raise AssertionError(f'{name} no longer describes an exact panoramic profile')
        layout = Layout.fit(profile)
        with tempfile.TemporaryDirectory(prefix='aa-reference-') as directory:
            video, raw = Path(directory)/'reference.h264', Path(directory)/'panel.rgb'
            encode(ffmpeg, layout, video)
            crop = detected_crops(ffmpeg, video, profile.source)
            measured = render_and_measure(ffmpeg, video, raw, layout)
        records[name] = {'profile_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'geometry': layout.describe(), 'decoded_crop_whxy': crop,
                         'rendering': measured, 'reference_touch': mapping_proof(layout)}
    version = subprocess.run([ffmpeg, '-version'], check=True, capture_output=True, text=True,
                             timeout=10).stdout.splitlines()[0]
    return {'scope': 'PC reference, synthetic H.264, local pixel/touch model; no Android Auto connection',
            'ffmpeg': version, 'profiles': records, 'phone_tested': False,
            'physical_nac_tested': False, 'installation_verified': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    args = parser.parse_args()
    if not args.ffmpeg:
        parser.error('A local FFmpeg executable is required')
    print(json.dumps(proof(args.ffmpeg), indent=2))


if __name__ == '__main__':
    main()
