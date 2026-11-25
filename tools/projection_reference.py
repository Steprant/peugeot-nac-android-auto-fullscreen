"""Standalone reference for the video geometry and touch of the DHU profiles.

This module renders no firmware, opens no device and does not implement the
Android Auto input protocol. Its coordinates are local, integer pixel centres.
"""

from configparser import ConfigParser
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path


PROFILES = Path(__file__).resolve().parents[1] / 'docs' / 'validation' / 'dhu'
PANEL = (1920, 720)
VIDEO_MODES = ((800, 480), (1280, 720), (1920, 1080))


@dataclass(frozen=True)
class Rectangle:
    x: int
    y: int
    width: int
    height: int

    def __post_init__(self):
        if any(type(v) is not int for v in (self.x, self.y, self.width, self.height)):
            raise ValueError('Rectangle coordinates must be integers')
        if self.width <= 0 or self.height <= 0:
            raise ValueError('Rectangle must not be empty')

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def ltrb(self):
        return self.x, self.y, self.right, self.bottom

    def contains(self, x, y):
        return self.x <= x < self.right and self.y <= y < self.bottom


@dataclass(frozen=True)
class Profile:
    frame: tuple[int, int]
    width_margin: int = 0
    height_margin: int = 0

    def __post_init__(self):
        if self.frame not in VIDEO_MODES:
            raise ValueError('Unsupported DHU video mode')
        for margin, size in zip((self.width_margin, self.height_margin), self.frame):
            if type(margin) is not int or not 0 <= margin < size or margin % 2:
                raise ValueError('Expected valid, even, symmetric total margins')

    @property
    def source(self):
        width, height = self.frame
        return Rectangle(self.width_margin // 2, self.height_margin // 2,
                         width - self.width_margin, height - self.height_margin)

    @classmethod
    def from_ini(cls, path):
        config = ConfigParser(interpolation=None)
        with Path(path).open(encoding='utf-8') as stream:
            config.read_file(stream)
        general = config['general']
        if general.get('inputmode') != 'touch':
            raise ValueError('This reference requires a touchscreen profile')
        if 'margins' in general:
            raise ValueError('This reference supports symmetric margins only')
        for key in ('contentinsets', 'stablecontentinsets'):
            if key in general and general[key].replace(' ', '') != '0,0,0,0':
                raise ValueError('Nonzero content insets are outside this reference')
        if general.getfloat('pixelaspectratio', 1.0) != 1.0:
            raise ValueError('This reference requires square pixels')
        profile = cls(tuple(map(int, general['resolution'].split('x'))),
                      general.getint('marginwidth', 0), general.getint('marginheight', 0))
        if (profile.width_margin or profile.height_margin) and not general.getboolean('cropmargins', False):
            raise ValueError('Nonzero margins must be removed from the displayed video')
        return profile

    @classmethod
    def panoramic(cls, frame):
        """Full-width, undistorted content for any of the documented DHU modes."""
        width, height = frame
        visible_height = Fraction(width * PANEL[1], PANEL[0])
        if frame not in VIDEO_MODES or visible_height.denominator != 1:
            raise ValueError('Unsupported exact panoramic geometry')
        return cls(frame, 0, height - int(visible_height))


def _integer(value):
    value = Fraction(value)
    if value.denominator != 1:
        raise ValueError('Non-integral reference rectangle: would require rounding')
    return int(value)


def _map_axis(value, start, length, target_start, target_length):
    # Source pixel containing the destination pixel centre. Unlike rounding
    # the endpoint ratio, this never generates the exclusive right/bottom edge.
    return target_start + ((2 * (value - start) + 1) * target_length) // (2 * length)


@dataclass(frozen=True)
class Layout:
    profile: Profile
    destination: Rectangle
    scale: Fraction

    @classmethod
    def fit(cls, profile):
        source = profile.source
        scale = min(Fraction(PANEL[0], source.width), Fraction(PANEL[1], source.height))
        width = _integer(source.width * scale)
        height = _integer(source.height * scale)
        return cls(profile, Rectangle((PANEL[0] - width) // 2, (PANEL[1] - height) // 2,
                                      width, height), scale)

    @property
    def logical_frame(self):
        """Encoded frame represented in panel pixels, including invisible margins."""
        source, destination = self.profile.source, self.destination
        return Rectangle(destination.x - _integer(source.x * self.scale),
                         destination.y - _integer(source.y * self.scale),
                         _integer(self.profile.frame[0] * self.scale),
                         _integer(self.profile.frame[1] * self.scale))

    @staticmethod
    def _map(x, y, src, dst):
        if type(x) is not int or type(y) is not int:
            raise ValueError('Touch coordinates must be integer pixels')
        if not src.contains(x, y):
            return None
        return (_map_axis(x, src.x, src.width, dst.x, dst.width),
                _map_axis(y, src.y, src.height, dst.y, dst.height))

    def panel_to_frame(self, x, y):
        """Coordinates in the original encoded frame, before cropping."""
        return self._map(x, y, self.destination, self.profile.source)

    def panel_to_content(self, x, y):
        """Coordinates relative to the cropped content, distinct from frame coordinates."""
        point = self.panel_to_frame(x, y)
        if point is None:
            return None
        return point[0] - self.profile.source.x, point[1] - self.profile.source.y

    def frame_to_panel(self, x, y):
        return self._map(x, y, self.profile.source, self.destination)

    def describe(self):
        source, destination, logical = self.profile.source, self.destination, self.logical_frame
        return {
            'frame': list(self.profile.frame),
            'total_margins': [self.profile.width_margin, self.profile.height_margin],
            'source_ltrb': list(source.ltrb),
            'destination_ltrb': list(destination.ltrb),
            'scale': [self.scale.numerator, self.scale.denominator],
            'logical_frame_xywh': [logical.x, logical.y, logical.width, logical.height],
            'logical_total_margins': [logical.width - destination.width,
                                      logical.height - destination.height],
        }


@dataclass(frozen=True)
class TouchEvent:
    action: str
    pointer: int
    frame_xy: tuple[int, int]


class TouchRouter:
    """Reference routing rules: a native UI taking focus cancels projection touches.

    The returned events are local data. They are not sent to a phone or NAC.
    """

    def __init__(self, layout):
        self.layout = layout
        self.focused = False
        self.active = {}

    def cancel_all(self):
        events = [TouchEvent('cancel', pointer, point) for pointer, point in sorted(self.active.items())]
        self.active.clear()
        return events

    def set_focus(self, enabled):
        if type(enabled) is not bool:
            raise ValueError('Focus must be explicit')
        self.focused = enabled
        return [] if enabled else self.cancel_all()

    def change_layout(self, layout):
        events = self.cancel_all()
        self.layout = layout
        return events

    def touch(self, action, pointer, x, y):
        if action not in ('down', 'move', 'up', 'cancel') or type(pointer) is not int or pointer < 0:
            raise ValueError('Unknown touch action or pointer')
        if not self.focused:
            return []
        if action == 'cancel':
            return ([TouchEvent(action, pointer, self.active.pop(pointer))]
                    if pointer in self.active else [])
        point = self.layout.panel_to_frame(x, y)
        if action == 'down':
            if point is None or pointer in self.active:
                return []
        elif pointer not in self.active:
            return []
        elif point is None:
            return [TouchEvent('cancel', pointer, self.active.pop(pointer))]

        if action == 'up':
            self.active.pop(pointer)
        else:
            self.active[pointer] = point
        return [TouchEvent(action, pointer, point)]
