# SPDX-License-Identifier: GPL-2.0-or-later

"""
Builds HyperScroll custom curves from Synapse's curve editor settings

Each direction is two quadratic Bezier curves in percent space: start -> peak with the left
handle as control point, and peak -> end with the right handle. Synapse samples both at
t = k/50 and keeps only the samples needed to stay within 0.2 percent of the curve. The
sample selection runs in float32 and the kept values in double; matching both reproduces
Synapse's points byte for byte.
"""

import struct

TOLERANCE = 0.2
SAMPLES = 50
SPEED_CURVE = [(-720.0, 1.0), (0.0, 1.0), (720.0, 1.0)]


def _f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def _casteljau_f32(p0, c, p1, t):
    q0 = [_f32(a + _f32(_f32(b - a) * t)) for a, b in zip(p0, c)]
    q1 = [_f32(a + _f32(_f32(b - a) * t)) for a, b in zip(c, p1)]
    return tuple(_f32(a + _f32(_f32(b - a) * t)) for a, b in zip(q0, q1))


def _polynomial(p0, c, p1, t):
    return tuple((1 - t) ** 2 * a + 2 * t * (1 - t) * b + t * t * d for a, b, d in zip(p0, c, p1))


def _samples(bezier, points, ts):
    start, left, peak, right, end = points
    return [bezier(start, left, peak, t) for t in ts] + [bezier(peak, right, end, t) for t in ts[1:]]


def _error_f32(samples, i, j):
    (ax, ay), (bx, by) = samples[i], samples[j]
    slope = _f32(by - ay)
    width = _f32(bx - ax)
    return max((abs(_f32(_f32(ay + _f32(slope * _f32(_f32(x - ax) / width))) - y)) for x, y in samples[i + 1:j]), default=0.0)


def _kept_samples(samples):
    tolerance = _f32(TOLERANCE)
    kept, last = [0], 0
    for j in range(1, len(samples) - 2):
        if _error_f32(samples, last, j + 1) > tolerance:
            kept.append(j)
            last = j
    return kept + [len(samples) - 1]


def notch_curve(points, steps, tension):
    """
    Build one direction's notch curve

    :param points: (x, y) percent points: start, left handle, peak, right handle, end
    :param steps: notches per wheel turn, 8 to 96
    :param tension: 0 to 100
    :return: (degrees, strength) points
    """
    points = [tuple(float(v) for v in p) for p in points]
    kept = _kept_samples(_samples(_casteljau_f32, points, [_f32(k / SAMPLES) for k in range(SAMPLES + 1)]))
    samples = _samples(_polynomial, points, [k / SAMPLES for k in range(SAMPLES + 1)])
    return [(samples[k][0] / 100 * 360 / steps, samples[k][1] / 100 * tension * 0.002) for k in kept]
