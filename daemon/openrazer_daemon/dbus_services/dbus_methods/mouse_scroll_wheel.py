# SPDX-License-Identifier: GPL-2.0-or-later

import math
import struct

from openrazer_daemon.dbus_services import endpoint
from openrazer_daemon.misc import hyperscroll


@endpoint('razer.device.scroll', 'setScrollMode', in_sig='y')
def set_scroll_mode(self, mode):
    """
    Set the device's scroll mode

    :param mode: The mode to set (0 = tactile, 1 = free spin)
    :type mode: int
    """
    self.logger.debug("DBus call set_scroll_mode")

    if mode not in (0, 1):
        raise ValueError("mode has to be 0 or 1")

    driver_path = self.get_driver_path('scroll_mode')

    with open(driver_path, 'w') as driver_file:
        driver_file.write(str(int(mode)))


@endpoint('razer.device.scroll', 'getScrollMode', out_sig='y')
def get_scroll_mode(self):
    """
    Get the device's current scroll mode

    :return: The device's current scroll mode (0 = tactile, 1 = free spin)
    :rtype: int
    """
    self.logger.debug("DBus call get_scroll_mode")

    driver_path = self.get_driver_path('scroll_mode')

    with open(driver_path, 'r') as driver_file:
        return int(driver_file.read().strip())


@endpoint('razer.device.scroll', 'setScrollAcceleration', in_sig='b')
def set_scroll_acceleration(self, enabled):
    """
    Set the device's scroll acceleration state

    :param enabled: true to enable acceleration, false to disable it
    :type enabled: bool
    """
    self.logger.debug("DBus call set_scroll_acceleration")

    driver_path = self.get_driver_path('scroll_acceleration')

    with open(driver_path, 'w') as driver_file:
        driver_file.write(str(int(enabled)))


@endpoint('razer.device.scroll', 'getScrollAcceleration', out_sig='b')
def get_scroll_acceleration(self):
    """
    Get the device's scroll acceleration state

    :return: true if acceleration enabled, false otherwise
    :rtype: bool
    """
    self.logger.debug("DBus call get_scroll_acceleration")

    driver_path = self.get_driver_path('scroll_acceleration')

    with open(driver_path, 'r') as driver_file:
        return bool(int(driver_file.read().strip()))


@endpoint('razer.device.scroll', 'setScrollSmartReel', in_sig='b')
def set_scroll_smart_reel(self, enabled):
    """
    Set the device's "smart reel" state

    :param enabled: true to enable smart reel, false to disable it
    :type enabled: bool
    """
    self.logger.debug("DBus call set_scroll_smart_reel")

    driver_path = self.get_driver_path('scroll_smart_reel')

    with open(driver_path, 'w') as driver_file:
        driver_file.write(str(int(enabled)))


@endpoint('razer.device.scroll', 'getScrollSmartReel', out_sig='b')
def get_scroll_smart_reel(self):
    """
    Get the device's "smart reel" state

    :return: true if smart reel enabled, false otherwise
    :rtype: bool
    """
    self.logger.debug("DBus call get_scroll_smart_reel")

    driver_path = self.get_driver_path('scroll_smart_reel')

    with open(driver_path, 'r') as driver_file:
        return bool(int(driver_file.read().strip()))


@endpoint('razer.device.scroll', 'setScrollProfile', in_sig='y')
def set_scroll_profile(self, profile):
    """
    Set the device's HyperScroll profile

    The device rejects a profile that is not enabled, see setScrollProfilesEnabled.

    :param profile: The profile to set (1 = standard, 2 = distinct, 3 = precise, 4 = adaptive, 5 = smooth, 6 = custom)
    :type profile: int
    """
    self.logger.debug("DBus call set_scroll_profile")

    if profile not in range(1, 7):
        raise ValueError("profile has to be between 1 and 6")

    driver_path = self.get_driver_path('scroll_profile')

    with open(driver_path, 'w') as driver_file:
        driver_file.write(str(int(profile)))


@endpoint('razer.device.scroll', 'getScrollProfile', out_sig='y')
def get_scroll_profile(self):
    """
    Get the device's current HyperScroll profile

    :return: The current profile (1 = standard, 2 = distinct, 3 = precise, 4 = adaptive, 5 = smooth, 6 = custom)
    :rtype: int
    """
    self.logger.debug("DBus call get_scroll_profile")

    driver_path = self.get_driver_path('scroll_profile')

    with open(driver_path, 'r') as driver_file:
        return int(driver_file.read().strip())


@endpoint('razer.device.scroll', 'setScrollProfilesEnabled', in_sig='y')
def set_scroll_profiles_enabled(self, mask):
    """
    Set which HyperScroll profiles are enabled

    :param mask: Bitmask where bit n-1 enables profile n, at least one bit set
    :type mask: int
    """
    self.logger.debug("DBus call set_scroll_profiles_enabled")

    if mask not in range(1, 0x40):
        raise ValueError("mask has to be between 1 and 63")

    driver_path = self.get_driver_path('scroll_profiles_enabled')

    with open(driver_path, 'w') as driver_file:
        driver_file.write(str(int(mask)))


@endpoint('razer.device.scroll', 'getScrollProfilesEnabled', out_sig='y')
def get_scroll_profiles_enabled(self):
    """
    Get which HyperScroll profiles are enabled

    :return: Bitmask where bit n-1 is set if profile n is enabled
    :rtype: int
    """
    self.logger.debug("DBus call get_scroll_profiles_enabled")

    driver_path = self.get_driver_path('scroll_profiles_enabled')

    with open(driver_path, 'r') as driver_file:
        return int(driver_file.read().strip())


SCROLL_NOTCH_STRENGTH_MAX = 0.2  # Synapse's "scroll tension" 100 with the peak at the top of the graph
SCROLL_NOTCH_WIDTH_MIN = 360 / 96  # Synapse's "scroll steps" per turn, 8 to 96
SCROLL_NOTCH_WIDTH_MAX = 360 / 8
SCROLL_CURVE_MAX_POINTS = 80


def _check_scroll_curve(name, points, y_max, notch):
    if len(points) not in range(2, SCROLL_CURVE_MAX_POINTS + 1):
        raise ValueError("{0} curve needs between 2 and {1} points".format(name, SCROLL_CURVE_MAX_POINTS))
    if not all(math.isfinite(x) for x, _ in points):
        raise ValueError("{0} curve x values have to be finite".format(name))
    if any(b[0] <= a[0] for a, b in zip(points, points[1:])):
        raise ValueError("{0} curve x values have to be strictly ascending".format(name))
    if any(not 0 <= y <= y_max for _, y in points):
        raise ValueError("{0} curve y values have to be between 0 and {1}".format(name, y_max))
    if notch and points[0][0] != 0:
        raise ValueError("{0} curve has to start at x = 0".format(name))
    if notch and not SCROLL_NOTCH_WIDTH_MIN <= points[-1][0] <= SCROLL_NOTCH_WIDTH_MAX:
        raise ValueError("{0} curve has to end between {1} and {2} degrees".format(name, SCROLL_NOTCH_WIDTH_MIN, SCROLL_NOTCH_WIDTH_MAX))


@endpoint('razer.device.scroll', 'setScrollCustomProfile', in_sig='a(dd)a(dd)a(dd)')
def set_scroll_custom_profile(self, up, down, speed):
    """
    Set the detent curves of the custom HyperScroll profile (6)

    A notch spans from x = 0 to the last point's x, in degrees of wheel rotation: 360 / 96 to
    360 / 8, matching Synapse's 8 to 96 steps per turn. Up and down should end at the same x.

    :param up: (degrees, strength) points for scrolling up; strength 0 to 0.2
    :type up: list of (float, float)

    :param down: (degrees, strength) points for scrolling down
    :type down: list of (float, float)

    :param speed: (signed wheel speed, multiplier) points; a multiplier of 1 leaves the strength unchanged, 0 removes the notch
    :type speed: list of (float, float)
    """
    self.logger.debug("DBus call set_scroll_custom_profile")

    _write_scroll_custom_profile(self, up, down, speed)


def _write_scroll_custom_profile(self, up, down, speed):
    up = [(float(x), float(y)) for x, y in up]
    down = [(float(x), float(y)) for x, y in down]
    speed = [(float(x), float(y)) for x, y in speed]

    _check_scroll_curve('up', up, SCROLL_NOTCH_STRENGTH_MAX, True)
    _check_scroll_curve('down', down, SCROLL_NOTCH_STRENGTH_MAX, True)
    _check_scroll_curve('speed', speed, 1.0, False)
    if up[-1][0] != down[-1][0]:
        raise ValueError("up and down curves have to end at the same x")

    payload = struct.pack('<BBB', len(up), len(down), len(speed))
    for x, y in up + down + speed:
        payload += struct.pack('<ff', x, y)

    driver_path = self.get_driver_path('scroll_custom_profile')

    with open(driver_path, 'wb') as driver_file:
        driver_file.write(payload)


def _check_scroll_slider_points(name, points):
    if len(points) != 5 or any(len(p) != 2 for p in points):
        raise ValueError("{0} needs five (x, y) points: start, left handle, peak, right handle, end".format(name))
    if any(v not in range(0, 101) for p in points for v in p):
        raise ValueError("{0} points have to be between 0 and 100".format(name))
    xs = [x for x, _ in points]
    if xs[0] != 0 or xs[4] != 100 or not 0 < xs[2] < 100 or xs != sorted(xs):
        raise ValueError("{0} x values have to run 0 <= left <= peak <= right <= 100 with the peak strictly inside".format(name))


@endpoint('razer.device.scroll', 'setScrollCustomSliders', in_sig='byya(yy)ya(yy)')
def set_scroll_custom_sliders(self, linked, steps, up_tension, up_points, down_tension, down_points):
    """
    Set the custom HyperScroll profile (6) the way Synapse's curve editor does

    Builds the same curves Synapse would and stores the editor state, so Synapse shows matching sliders.

    :param linked: Whether Synapse's editor shows up and down as linked
    :type linked: bool

    :param steps: Notches per wheel turn, 8 to 96
    :type steps: int

    :param up_tension: Strength of the scroll up curve, 0 to 100
    :type up_tension: int

    :param up_points: Five (x, y) percent points for scrolling up: start (x 0), left handle, peak, right handle, end (x 100)
    :type up_points: list of (int, int)

    :param down_tension: Strength of the scroll down curve, 0 to 100
    :type down_tension: int

    :param down_points: Five (x, y) percent points for scrolling down
    :type down_points: list of (int, int)
    """
    self.logger.debug("DBus call set_scroll_custom_sliders")

    up_points = [tuple(int(v) for v in p) for p in up_points]
    down_points = [tuple(int(v) for v in p) for p in down_points]

    if steps not in range(8, 97):
        raise ValueError("steps has to be between 8 and 96")
    if up_tension not in range(0, 101) or down_tension not in range(0, 101):
        raise ValueError("tension has to be between 0 and 100")
    _check_scroll_slider_points('up', up_points)
    _check_scroll_slider_points('down', down_points)

    _write_scroll_custom_profile(self, hyperscroll.notch_curve(up_points, steps, up_tension),
                                 hyperscroll.notch_curve(down_points, steps, down_tension), hyperscroll.SPEED_CURVE)

    payload = bytes([int(bool(linked)), steps, up_tension, steps, down_tension])
    payload += bytes(v for p in up_points + down_points for v in p)

    driver_path = self.get_driver_path('scroll_custom_sliders')

    with open(driver_path, 'wb') as driver_file:
        driver_file.write(payload)


@endpoint('razer.device.scroll', 'getScrollCustomSliders', out_sig='byya(yy)ya(yy)')
def get_scroll_custom_sliders(self):
    """
    Get the custom HyperScroll profile's settings as last saved by Synapse or setScrollCustomSliders

    :return: linked, steps, up tension, up points, down tension, down points, as for setScrollCustomSliders
    :rtype: tuple
    """
    self.logger.debug("DBus call get_scroll_custom_sliders")

    driver_path = self.get_driver_path('scroll_custom_sliders')

    with open(driver_path, 'rb') as driver_file:
        data = driver_file.read()

    points = [(data[i], data[i + 1]) for i in range(5, 25, 2)]

    return bool(data[0]), data[1], data[2], points[:5], data[4], points[5:]
