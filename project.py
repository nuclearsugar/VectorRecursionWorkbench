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

import json

from geometry import vec2, polygon


class shape(object):
    def __init__(self, poly, depth, step, inc, clockwise, reverse_colors, disabled, footer, footer_inc, footer_offset):
        # Polygon.
        assert type(poly) == polygon
        self.poly = poly
        # Int >= 1. Max recursion count.
        assert depth >= 1
        self.depth = depth
        # Float (0.0, 1.0). How far to step along the (half) line.
        assert (step > 0.0) and (step < 1.0)
        self.step = step
        # Float [0.0, 1.0). How much to add to step each iteration.
        assert (inc >= 0.0) and (inc < 1.0)
        self.inc = inc
        # Bool. Whether or not recursion appears clockwise.
        assert clockwise in (True, False)
        self.clockwise = clockwise
        # Bool. Whether or not to reverse color sequence.
        assert reverse_colors in (True, False)
        self.reverse_colors = reverse_colors
        # Bool. Whether or not to disable shape.
        assert disabled in (True, False)
        self.disabled = disabled
        # Float [0.0, 1.0). How much to footer to apply each iteration.
        assert (footer >= 0.0) and (footer < 1.0)
        self.footer = footer
        # Float [0.0, 1.0). How much to add each iteration after footer_offset.
        assert (footer_inc >= 0.0) and (footer_inc < 1.0)
        self.footer_inc = footer_inc
        # Int >= 0. What iteration to start applying footer_inc.
        assert footer_offset >= 0
        self.footer_offset = footer_offset


COLOR_NAME_TO_HTML = {
    'black' : "#000000",
    'red'   : "#FF0000",
    'green' : "#00FF00",
    'blue'  : "#0000FF",
    'gray'  : "#7F7F7F",
    'white' : "#FFFFFF",
}

def convert_color_names(colors):
    out = []
    for c in colors:
        out.append(COLOR_NAME_TO_HTML.get(c, c))
    return out

class project(object):
    def __init__(self, canvas, colors, shapes):
        # List. [start_x, start_y, end_x, end_y]
        assert (type(canvas) == list) and (len(canvas) == 4)
        self.canvas = canvas
        # List. HTML color strings
        assert (type(colors) == list)
        self.colors = colors
        self.shapes = shapes

    def to_json(self, filename=None):
        raw_shapes = []
        for s in self.shapes:
            points = []
            for p in s.poly.points:
                points.append((p.x, p.y))
            raw_shapes.append({
                'points': points,
                'depth': s.depth,
                'step': s.step,
                'inc': s.inc,
                'clockwise': s.clockwise,
                'reverse_colors': s.reverse_colors,
                'disabled': s.disabled,
                'footer': s.footer,
                'footer_inc': s.footer_inc,
                'footer_offset': s.footer_offset,
            })
        obj = {
            'canvas': self.canvas,
            'colors': self.colors,
            'shapes': raw_shapes,
        }
        args = { 'sort_keys': True, 'indent': 4, 'separators': (',', ': ') }
        if filename:
            with open(filename, 'w') as f:
                json.dump(obj, f, **args)
            return None
        else:
            return json.dumps(obj, **args)

    def save_file(self, filename):
        self.to_json(filename)

    @classmethod
    def load_file(cls, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
            return cls.load_dict(data)

    @classmethod
    def load_json(cls, json_str):
        data = json.loads(json_str)
        return cls.load_dict(data)

    @classmethod
    def load_dict(cls, data):
        canvas = data['canvas']
        colors = convert_color_names(data['colors'])
        footer_buffer = float(data.get('footer_buffer', 0.0))
        raw_shapes = data.get('shapes', [])
        shapes = []
        for s in raw_shapes:
            points = []
            for p in s['points']:
                points.append(vec2(float(p[0]), float(p[1])))
            shapes.append(
                shape(
                    poly=polygon(points),
                    depth=int(s['depth']),
                    step=float(s['step']),
                    inc=float(s['inc']),
                    clockwise=bool(s['clockwise']),
                    reverse_colors=bool(s.get('reverse_colors', False)),
                    disabled=bool(s.get('disabled', False)),
                    footer=float(s.get('footer', footer_buffer)),
                    footer_inc=float(s.get('footer_inc', 0.0)),
                    footer_offset=float(s.get('footer_offset', 0)),
                )
            )
        return project(canvas, colors, shapes)

