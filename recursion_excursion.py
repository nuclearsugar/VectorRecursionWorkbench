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

from project import project
from geometry import polygon

def svg_vec2_str(vec2):
    return "%g,%g" % (vec2.x, vec2.y)

def generate_svg(canvas, recursion_list, output):
    output.write('<?xml version="1.0" standalone="no"?>\n')
    output.write('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
    output.write('<svg viewBox="%s" xmlns="http://www.w3.org/2000/svg" version="1.1">\n' % str(canvas)[1:-1])
    for n,poly_list in enumerate(recursion_list):
        output.write('  <!-- Shape %d -->\n' % (n + 1))
        for c,poly in poly_list:
            output.write('  <polygon fill="%s" points="%s" />\n' % (c, ", ".join(map(svg_vec2_str, poly.points))))
    output.write('</svg>\n')


def generate_recursion(proj):
    """
        Returns list of list of color,polygon tuples:
        [
            [ ('color', poly0_recursion0), ('color', poly1_recursion1), ...],
            [ ('color', poly1_recursion0), ... ]
        ]
    """
    all_output = []
    for n,shape in enumerate(proj.shapes):
        if shape.disabled:
            all_output.append([])
            continue
        if shape.reverse_colors:
            colors = list(proj.colors)
            colors.reverse()
        else:
            colors = proj.colors
        step = shape.step
        inc = shape.inc
        footer_scale = 1.0 - shape.footer
        footer_inc = shape.footer_inc
        footer_offset = shape.footer_offset
        poly = shape.poly
        # real step (0.0,0.5) appears clockwise and (0.5, 1.0) counter-clockwise
        step /= 2.0
        inc /= 2.0
        if not shape.clockwise:
            step = 1.0 - step
            inc = 0.0 - inc
        poly_output = []
        for d in range(shape.depth):
            c = colors[d % len(colors)]
            new_poly = poly.recurse(step)
            if new_poly is None:
                break
            if d >= footer_offset:
                footer_scale -= footer_inc
                if footer_scale < 0:
                    break
            #
            # 0 is poly[0], 0` is new_poly[0], etc:
            #
            # 0...0`....1
            # .         .
            # .         .
            # .         .
            # .         1`
            # 3`        .
            # .         .
            # .         .
            # .         .
            # 3....2`...2
            #
            # Would triangulate as:
            #   [0, 0`, 3`],
            #   [1, 1`, 0`],
            #   [2, 2`, 1`],
            #   [3, 3`, 2`]
            #
            # That is, for i in p:
            #   [i, i`, (i-1)`]
            #
            assert len(poly.points) == len(new_poly.points)
            l = len(poly.points)
            for i in range(l):
                tri = [
                    poly.points[i],
                    new_poly.points[i],
                    new_poly.points[(i-1)%l]
                ]
                # Starting poly clockwise => tri already is
                tri_poly = polygon(tri, make_clockwise=False)
                # Footer shrinks tri to add a gap
                if footer_scale != 1.0:
                    tri_poly = tri_poly.scale(footer_scale)
                poly_output.append((c, tri_poly))
            poly = new_poly
            step += inc
            if (step <= 0.0) or (step >= 1.0):
                print 'Recursion stopped due to step size'
                break
        all_output.append(poly_output)
    return all_output


if __name__ == "__main__":
    import sys
    if len(sys.argv) not in (2,3):
        sys.stderr.write('Usage: %s <project.json> [output.svg]\n' % sys.argv[0])
        sys.exit(1)
    proj = project.load_file(sys.argv[1])
    rec_list = generate_recursion(proj)
    if len(sys.argv) == 3:
        output = open(sys.argv[2], 'w')
    else:
        output = sys.stdout
    generate_svg(proj.canvas, rec_list, output)

