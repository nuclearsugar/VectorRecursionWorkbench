#
# Vector Recursion Workbench
# Copyright (c) 2014-2016 Nathan Williams, Jason Fletcher
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import math


class vec2(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "(%g,%g)" % (self.x, self.y)

    def __eq__(self, rhs):
        return (self.x == rhs.x) and (self.y == rhs.y)

    def __sub__(self, rhs):
        return vec2(self.x - rhs.x, self.y - rhs.y)

    def __add__(self, rhs):
        return vec2(self.x + rhs.x, self.y + rhs.y)

    def __mul__(self, s):
        return vec2(self.x * s, self.y * s)

    def __div__(self, s):
        return vec2(self.x / s, self.y / s)

    def dot(self, rhs):
        return (self.x * rhs.x) + (self.y * rhs.y)

    def cross(self, rhs):
        # u x v = ( u.y * v.z - u.z * v.y,
        #           u.z * v.x - u.x * v.z,
        #           u.x * v.y - u.y * v.x)
        # Treat this vec2 as vec3 with 0 for z components
        return (self.x * rhs.y) - (self.y * rhs.x)

    def dist_sq(self, rhs):
        a = (rhs.x - self.x) ** 2
        b = (rhs.y - self.y) ** 2
        return a + b

    def dist(self, rhs):
        return math.sqrt(self.dist_sq(rhs))

    def rot(self, deg):
        rad = math.radians(deg)
        c = math.cos(rad)
        s = math.sin(rad)
        return vec2(self.x * c - self.y * s, self.x * s + self.y * c)

    def project_onto_line(self, a, b):
        """ Project this vec2 on the line segment defined by a and b """
        ab = b - a
        ab_dist_sq = ab.dot(ab)
        if ab_dist_sq == 0:
            # a and b are equal
            return a
        else:
            # Line parameterized as a + t(b - a)
            ap = self - a
            t = ap.dot(ab) / ab_dist_sq
            if t < 0.0:
                # before a
                return a
            elif t > 1:
                # before b
                return b
            else:
                # between
                return a + (ab * t)


class polygon(object):
    def __init__(self, points, make_clockwise=True):
        self.points = []
        self.points.extend(points)
        if make_clockwise:
            self.make_clockwise()

    def __repr__(self):
        return str(self.points)

    @classmethod
    def aabb(cls, x, y, w, h):
        return polygon([
            vec2(x, y),
            vec2(x, y+h),
            vec2(x+w, y+h),
            vec2(x+w, y)
        ])

    def make_clockwise(self):
        # Get into clockwise order
        c = self.center()
        if c is None:
            return None
        a = {}
        for p in self.points:
            # Angle between vertex and center
            a[p] = math.atan2(p.y - c.y, p.x - c.x)
        self.points.sort(key=lambda p: a[p])
        return self

    def is_concave(self):
        # All consecutive line segments must have cross products of same sign
        n = len(self.points)
        prev_sign = None
        for i,a in enumerate(self.points):
            b = self.points[(i+1) % n]
            c = self.points[(i+2) % n]
            ab = b - a
            bc = c - b
            sign = ab.cross(bc) >= 0.0
            if prev_sign is None:
                prev_sign = sign
            elif prev_sign != sign:
                return False
        return True

    def center(self):
        a = 0.0
        cx = 0.0
        cy = 0.0
        p = self.points + [ self.points[0] ]
        for i in range(0, len(p)-1):
            tmp = p[i].x * p[i+1].y - p[i+1].x * p[i].y
            a += tmp
            cx += ( (p[i].x + p[i+1].x) * tmp)
            cy += ( (p[i].y + p[i+1].y) * tmp)
        a = 0.5 * a
        if a == 0.0:
            return None
        tmp = (1.0 / (6.0 * a))
        return vec2( tmp * cx, tmp * cy )

    def contains(self, p):
        # self.points sorted clockwise so pointer must
        # be on right (inner) side of all segments
        for i,a in enumerate(self.points):
            b = self.points[(i+1)%len(self.points)]
            ab = b - a
            ap = p - a
            if ab.cross(ap) < 0:
                return False
        return True

    def rotate(self, deg):
        c = self.center()
        if c is None:
            return None
        out = []
        for p in self.points:
            x = p - c
            x = x.rot(deg)
            x = x + c
            out.append(x)
        return polygon(out)

    def scale(self, s):
        c = self.center()
        if c is None:
            return None
        out = []
        for p in self.points:
            x = (p.x - c.x) * s + c.x
            y = (p.y - c.y) * s + c.y
            out.append(vec2(x, y))
        p = polygon(out, make_clockwise=False)
        return p.make_clockwise()

    def recurse(self, s):
        p = []
        l = len(self.points)
        for i in range(0, l):
            p.append(self.points[i] + (self.points[(i+1)%l] - self.points[i]) * s)
        # Input polygon already clockwise => recurse is clockwise
        return polygon(p, make_clockwise=False)

