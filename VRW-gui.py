#!/usr/bin/env python
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

POINT_SNAP_PIXEL_DIST = 25

import copy
import os
import time

import wx

from recursion_excursion import generate_recursion, generate_svg
from project import project, shape, polygon, vec2

# File menu
ID_EXPORT_FULL = wx.NewId()
ID_EXPORT_INDIVIDUAL = wx.NewId()
# Control panel
ID_BTN_ADD_LINE = wx.NewId()
ID_BTN_DEL_LINE = wx.NewId()
ID_CHK_SNAP = wx.NewId()
ID_CHK_HIDE_GUIDE = wx.NewId()
ID_CHK_HIDE_NUM = wx.NewId()
ID_RAD_PREVIEW = wx.NewId()
ID_RAD_ASPECT_RATIO = wx.NewId()
# Attributes panel
## Shape
ID_RA_SHAPE_DIR = wx.NewId()
ID_TXT_SHAPE_ATTRS = wx.NewId()
ID_SL_SHAPE_DEPTH = wx.NewId()
ID_SP_SHAPE_DEPTH = wx.NewId()
ID_SL_SHAPE_STEP = wx.NewId()
ID_SP_SHAPE_STEP = wx.NewId()
ID_SL_SHAPE_INNER = wx.NewId()
ID_SP_SHAPE_INNER = wx.NewId()
ID_CHK_REVERSE_COLORS = wx.NewId()
ID_CHK_DISABLED = wx.NewId()
ID_SL_SHAPE_FOOTER = wx.NewId()
ID_SP_SHAPE_FOOTER = wx.NewId()
ID_SL_SHAPE_FOOTER_BUFFER = wx.NewId()
ID_SP_SHAPE_FOOTER_BUFFER = wx.NewId()
ID_SL_SHAPE_FOOTER_OFFSET = wx.NewId()
ID_SP_SHAPE_FOOTER_OFFSET = wx.NewId()
## Global
ID_SL_GLOBAL_STEP = wx.NewId()
ID_SP_GLOBAL_STEP = wx.NewId()
ID_CP_GLOBAL_COLOR1 = wx.NewId()
ID_CP_GLOBAL_COLOR2 = wx.NewId()
ID_SP_GLOBAL_CANVAS_WIDTH = wx.NewId()
ID_SP_GLOBAL_CANVAS_HEIGHT = wx.NewId()
ID_BTN_GLOBAL_BG_IMAGE = wx.NewId()


class ProjectDefaults(object):
    depth = 50
    step = 0.20
    inc = 0.0
    footer = 0.0
    clockwise = True
    colors = [ '#000000', '#FFFFFF' ]
    # 16:9 Default
    canvas = [ 0, 0, 896, 504 ]
    reverse_colors=False


class ControlsState(object):
    json_save_filename = None
    # Controls
    do_point_snapping = True
    do_hide_guide_lines = False
    do_hide_shape_numbers = False
    do_draw_recursion = False
    aspect_ratio_fit = True
    bg_bitmap = None


class AppState(object):
    project = None
    rec_list = None
    canvas_w = None
    canvas_h = None
    # Shape selection
    do_num_hotkey = True
    selected_shape = None
    # Guide line addition
    add_line_proposed = None        # vec2 from projection onto existing line
    add_line_proposed_info = None   # (shape, index) of where proposed was projected
    add_line_stage = None           # list of accepted proposed
    add_line_stage_info = None      # list of accepted proposed infos
    # Guide line deletion
    del_line_stage = None           # [vec2,vec2] of proposed line to delete


class UndoStack(object):
    def __init__(self):
        self._callback = None
        self.reset()

    def __repr__(self):
        return 'UndoStack(%d,%s)' % (self._pos, str(self._stack))

    def do_callback(self):
        if self._callback:
            self._callback(self)

    def set_callback(self, cb):
        self._callback = cb

    def reset(self):
        self._pos = -1
        self._stack = []
        self.do_callback()

    def do(self, x):
        del self._stack[(self._pos + 1):]
        self._stack.append(x)
        self._pos = len(self._stack) - 1
        self.do_callback()

    def can_undo(self):
        return (self._pos > 0)

    def undo(self):
        self._pos -= 1
        self.do_callback()
        return self._stack[self._pos]

    def can_redo(self):
        return ((self._pos + 1) < len(self._stack))

    def redo(self):
        self._pos += 1
        self.do_callback()
        return self._stack[self._pos]


g_project_defaults = ProjectDefaults()

g_app = None
g_state = AppState()
g_controls = ControlsState()
g_undo_stack = UndoStack()


def get_scale(view_xy):
    canvas_x = g_state.project.canvas[2] - g_state.project.canvas[0]
    canvas_y = g_state.project.canvas[3] - g_state.project.canvas[1]
    # Default stretch
    xs = view_xy[0] / float(canvas_x)
    ys = view_xy[1] / float(canvas_y)
    if g_controls.aspect_ratio_fit:
        if xs < ys:
            ys = xs
        else:
            xs = ys
    return xs,ys


def colour_from_name(color_name):
    c = wx.Colour()
    c.SetFromName(color_name)
    return c

def post_project_modification():
    p_copy = copy.deepcopy(g_state.project)
    g_undo_stack.do(p_copy)

def state_from_project(orig_proj, with_undo_reset=True):
    global g_state
    try:
        proj = copy.deepcopy(orig_proj)
        cw = proj.canvas[2] - proj.canvas[0]
        ch = proj.canvas[3] - proj.canvas[1]
        rl = generate_recursion(proj)
        g_state = AppState()
        g_state.project = proj
        g_state.rec_list = rl
        g_state.canvas_w = cw
        g_state.canvas_h = ch
        g_app.set_global_ui()
        g_app.force_redraw()
        if with_undo_reset:
            g_undo_stack.reset()
            post_project_modification()
    except Exception as e:
        print 'Failed, keeping old project:', e

def new_project():
    # Simple empty project
    d = g_project_defaults
    p1 = d.canvas[0:2]
    p2 = d.canvas[2:4]
    s = shape(
        poly=polygon([vec2(p1[0], p1[1]),
                      vec2(p2[0], p1[1]),
                      vec2(p2[0], p2[1]),
                      vec2(p1[0], p2[1])]),
        depth=d.depth,
        step=d.step,
        inc=d.inc,
        clockwise=d.clockwise,
        reverse_colors=d.reverse_colors,
        disabled=False,
        footer=d.footer,
        footer_inc=0.0,
        footer_offset=0,
    )
    p = project(d.canvas, d.colors, [s])
    g_controls.json_save_filename = None
    state_from_project(p)

def load_project(filename):
    print 'Loading project file:', filename
    try:
        tmp_p = project.load_file(filename)
        state_from_project(tmp_p)
        g_controls.json_save_filename = filename
    except Exception as e:
        print 'Failed, keeping old project:', e

def save_project(filename, keep_filename):
    if g_state is None:
        print 'Nothing to save!'
        return
    print 'Saving project file:', filename
    try:
        p_copy = copy.deepcopy(g_state.project)
        p_copy.save_file(filename)
        if keep_filename:
            g_controls.json_save_filename = filename
    except Exception as e:
        print 'Failed:', e

def export_full(filename):
    if g_state is None:
        print 'Nothing to export!'
        return
    print 'Exporting SVG file:', filename
    try:
        p_copy = copy.deepcopy(g_state.project)
        rl = generate_recursion(p_copy)
        with open(filename, 'w') as f:
            generate_svg(p_copy.canvas, rl, f)
    except Exception as e:
        print 'Failed:', e

def export_individual(directory):
    if g_state is None:
        print 'Nothing to export!'
        return
    print 'Exporting individual SVG files to:', directory
    try:
        p_copy = copy.deepcopy(g_state.project)
        rl = generate_recursion(p_copy)
        for i,r in enumerate(rl):
            if r:
                filename = '%02d.svg' % (i + 1)
                with open(os.path.join(directory, filename), 'w') as f:
                    generate_svg(p_copy.canvas, [r], f)
    except Exception as e:
        print 'Failed:', e

def unique_list(l):
    out = []
    for x in l:
        if x not in out:
            out.append(x)
    return out

class BaseDrawPanel(wx.Panel):
    def __init__(self, parent, style=wx.TAB_TRAVERSAL):
        wx.Panel.__init__(self, parent=parent, style=style)

    def bind_events(self, target):
        target.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        target.Bind(wx.EVT_MOTION, self.OnMotion)

    #
    # Events
    #

    def OnLeftUp(target, evt):
        if g_state.add_line_stage is not None:
            # May not have proposed yet if keyboard shotcut was used
            if not g_state.add_line_proposed:
                evt.Skip()
                return
            g_state.add_line_stage.append(g_state.add_line_proposed)
            g_state.add_line_stage_info.append(g_state.add_line_proposed_info)
            g_state.add_line_proposed = None
            g_state.add_line_proposed_info = None
            if len(g_state.add_line_stage) == 2:
                # Check
                assert len(g_state.add_line_stage_info) == 2
                stage = g_state.add_line_stage
                info = g_state.add_line_stage_info
                s_shape= info[0][0]
                assert s_shape == info[1][0]
                if s_shape == g_state.selected_shape:
                    g_state.selected_shape = None
                # Order clockwise
                if info[0][1] > info[1][1]:
                    stage = [ stage[1], stage[0] ]
                    info = [ info[1], info[0] ]
                # Clear out
                g_state.rec_list = None
                g_state.project.shapes.remove(s_shape)
                # Split the shape
                points = s_shape.poly.points
                s_a_p = []
                for i in range(0, info[0][1]+1):
                    s_a_p.append(points[i])
                s_a_p.append(stage[0])
                s_a_p.append(stage[1])
                for i in range(info[1][1]+1, len(points)):
                    s_a_p.append(points[i])
                s_b_p = []
                s_b_p.append(stage[0])
                for i in range(info[0][1]+1, info[1][1]+1):
                    s_b_p.append(points[i])
                s_b_p.append(stage[1])
                s_a_p = unique_list(s_a_p)
                s_b_p = unique_list(s_b_p)
                new_footer = s_shape.footer
                s_a = shape(
                    poly=polygon(s_a_p),
                    depth=s_shape.depth,
                    step=s_shape.step,
                    inc=s_shape.inc,
                    clockwise=s_shape.clockwise,
                    reverse_colors=s_shape.reverse_colors,
                    disabled=False,
                    footer=new_footer,
                    footer_inc=s_shape.footer_inc,
                    footer_offset=s_shape.footer_offset,
                )
                s_b = shape(
                    poly=polygon(s_b_p),
                    depth=s_shape.depth,
                    step=s_shape.step,
                    inc=s_shape.inc,
                    clockwise=s_shape.clockwise,
                    reverse_colors=s_shape.reverse_colors,
                    disabled=False,
                    footer=new_footer,
                    footer_inc=s_shape.footer_inc,
                    footer_offset=s_shape.footer_offset,
                )
                g_state.project.shapes.extend([s_a, s_b])
                # Generate
                g_state.rec_list = generate_recursion(g_state.project)
                post_project_modification()
                # Clear
                g_state.add_line_stage = None
                g_state.add_line_stage_info = None
            g_app.force_redraw()
        elif g_state.del_line_stage is not None:
            # May not have proposed yet if keyboard shortcut was used
            if not g_state.del_line_stage:
                evt.Skip()
                return
            line = g_state.del_line_stage
            g_state.del_line_stage = None
            shapes = []
            error_msg = None
            for s in g_state.project.shapes:
                if (line[0] in s.poly.points) and (line[1] in s.poly.points):
                    shapes.append(s)
            if len(shapes) == 0:
                error_msg = 'Found no shapes with line segment!'
            elif len(shapes) == 1:
                # Remove line[0] from shape
                t_poly = polygon(shapes[0].poly.points)
                t_poly.points.remove(line[0])
                if len(t_poly.points) < 3:
                    g_state.project.shapes.remove(shapes[0])
                elif t_poly.is_concave():
                    shapes[0].poly = t_poly
                else:
                    error_msg = 'Combined shape is convex!'
            elif len(shapes) == 2:
                points = []
                # Collect all points
                for s in shapes:
                    points.extend(s.poly.points)
                # Contains 2 copies of line[0] and line[1]. Remove one copy.
                for p in line:
                    points.remove(p)
                # Get them clockwise
                t_poly = polygon(points)
                points = t_poly.points
                # Remove any points that are on a line segment instead of being a corner.
                # For points A, B, C, if AB and BC are co-linear (cross of 0), remove B.
                repeat = True
                while repeat:
                    repeat = False
                    n = len(points)
                    for i,a in enumerate(points):
                        b = points[(i+1)%n]
                        c = points[(i+2)%n]
                        ab = b - a
                        bc = c - b
                        if abs(ab.cross(bc)) < 0.001:
                            points.remove(b)
                            repeat = True
                            break
                t_poly = polygon(points)
                if t_poly.is_concave():
                    shapes[0].poly = t_poly
                    g_state.project.shapes.remove(shapes[1])
                else:
                    error_msg = 'Combined shape is convex!'
            else:
                error_msg = 'Found more than two shapes with line segment!'
            if error_msg:
                wx.MessageBox(error_msg, 'Deletion error', wx.OK|wx.ICON_ERROR)
            else:
                g_state.rec_list = generate_recursion(g_state.project)
                post_project_modification()
            g_app.force_redraw()
        else:
            # [De]Select shape
            sp = wx.GetMousePosition() - target.GetScreenPosition()
            w,h = target.GetClientSize()
            xs,ys = get_scale((w, h))
            inv_xs,inv_ys = (1.0/xs), (1.0/ys)
            # Scale to canvas coordinates
            p = vec2(sp.x * inv_xs, sp.y * inv_ys)
            for i,s in enumerate(g_state.project.shapes):
                if s.poly.contains(p):
                    if g_state.selected_shape == s:
                        g_state.selected_shape = None
                    else:
                        g_state.selected_shape = s
                    break
            g_app.force_redraw()
        evt.Skip()

    def OnMotion(target, evt):
        w,h = target.GetClientSize()
        xs,ys = get_scale((w, h))
        inv_xs,inv_ys = (1.0/xs), (1.0/ys)
        if g_state.add_line_stage is not None:
            sp = evt.GetPosition()
            # Scale to canvas coordinates
            p = vec2(sp.x * inv_xs, sp.y * inv_ys)
            # Snap current point to closest if close enough to existing.
            if g_controls.do_point_snapping:
                closest = None
                for shape in g_state.project.shapes:
                    for point in shape.poly.points:
                        if (closest is None) or (p.dist_sq(point) < p.dist_sq(closest)):
                            closest = point
                # Back to screen coordinates, closer dist^2?
                screen_p = vec2(p.x * xs, p.y * ys)
                screen_c = vec2(closest.x * xs, closest.y * ys)
                if screen_p.dist_sq(screen_c) <= (POINT_SNAP_PIXEL_DIST**2):
                    p = closest
            # Project onto all shape lines
            closest = None
            closest_info = None
            last_info = (None,None)
            if g_state.add_line_stage_info:
                last_info = g_state.add_line_stage_info[0]
            for shape in g_state.project.shapes:
                if (g_state.selected_shape is not None) and (g_state.selected_shape != shape):
                    continue
                # TODO: Restricted to current shape for poly split simplicity
                if last_info[0] and last_info[0] != shape:
                    continue
                cnt = len(shape.poly.points)
                for i in range(cnt):
                    # Skip current line segment
                    if (shape, i) == last_info:
                        continue
                    a = shape.poly.points[i]
                    b = shape.poly.points[(i+1)%cnt]
                    pp = p.project_onto_line(a, b)
                    pp.x = round(pp.x, 8)
                    pp.y = round(pp.y, 8)
                    if (closest is None) or (p.dist_sq(pp) < p.dist_sq(closest)):
                        closest = pp
                        closest_info = (shape, i)
            g_state.add_line_proposed = closest
            g_state.add_line_proposed_info = closest_info
            g_app.force_redraw()
        elif g_state.del_line_stage is not None:
            sp = evt.GetPosition()
            # Scale to canvas coordinates
            p = vec2(sp.x * inv_xs, sp.y * inv_ys)
            # Find closest line segment
            closest = None
            closest_info = None
            for shape in g_state.project.shapes:
                if (g_state.selected_shape is not None) and (g_state.selected_shape != shape):
                    continue
                cnt = len(shape.poly.points)
                for i,a in enumerate(shape.poly.points):
                    b = shape.poly.points[(i+1)%cnt]
                    pp = p.project_onto_line(a, b)
                    if (closest is None) or (p.dist_sq(pp) < p.dist_sq(closest)):
                        closest = pp
                        closest_info = [a,b]
            g_state.del_line_stage = closest_info
            g_app.force_redraw()
        evt.Skip()


class GraphicsContextDrawPanel(BaseDrawPanel):
    def __init__(self, parent):
        BaseDrawPanel.__init__(self, parent=parent, style=wx.FULL_REPAINT_ON_RESIZE)

        self._bg_color = wx.Brush(True and 'white' or self.GetBackgroundColour())

        # Manual buffer on Windows to prevent resize flicker
        self._use_buffer = ('wxMSW' in wx.PlatformInfo)
        if self._use_buffer:
            self._buffer = None
            self.Bind(wx.EVT_SIZE, self.OnSize)
            self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnErase)

        # Events
        self.bind_events(self)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    #
    # Internal
    #

    def init_buffer(self):
        sz = self.GetClientSize()
        sz.width = max(1, sz.width)
        sz.height = max(1, sz.height)
        self._buffer = wx.EmptyBitmap(sz.width, sz.height, 32)
        dc = wx.MemoryDC(self._buffer)
        dc.SetBackground(self._bg_color)
        dc.Clear()
        self.draw_gc(dc)

    def draw_gc(self, dc):
        if g_state.rec_list is None:
            return

        gc = wx.GraphicsContext.Create(dc)
        xs,ys = get_scale(gc.GetSize())

        if g_controls.do_draw_recursion:
            brush_map = {}
            brushes = []
            paths = []
            for tlist in g_state.rec_list:
                for c,poly in tlist:
                    path = gc.CreatePath()
                    for n,point in enumerate(poly.points):
                        x = point.x * xs
                        y = point.y * ys
                        if n == 0:
                            path.MoveToPoint(x, y)
                        else:
                            path.AddLineToPoint(x, y)
                    path.CloseSubpath()
                    b = brush_map.get(c, None)
                    if b == None:
                        brush_map[c] = b = wx.Brush(colour_from_name(c))
                    brushes.append(b)
                    paths.append(path)

            for b,p in zip(brushes, paths):
                gc.SetBrush(b)
                gc.FillPath(p)
        else:
            if g_controls.bg_bitmap:
                bgw = (g_state.project.canvas[2] - g_state.project.canvas[0]) * xs
                bgh = (g_state.project.canvas[3] - g_state.project.canvas[1]) * ys
                gc.DrawBitmap(g_controls.bg_bitmap, 0, 0, bgw, bgh)

        if not g_controls.do_hide_guide_lines:
            gc.SetPen(wx.Pen('black', 3))
            for s in g_state.project.shapes:
                path = gc.CreatePath()
                for n,point in enumerate(s.poly.points):
                    x = point.x * xs
                    y = point.y * ys
                    if n == 0:
                        path.MoveToPoint(x, y)
                    else:
                        path.AddLineToPoint(x, y)
                path.CloseSubpath()
                gc.StrokePath(path)

        if not g_controls.do_hide_shape_numbers:
            f = wx.Font(pointSize=18, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD)
            bg = gc.CreateBrush(wx.Brush('white'))
            for i,s in enumerate(g_state.project.shapes):
                gc.SetFont(f, (g_state.selected_shape == s) and wx.RED or wx.BLACK)
                c = s.poly.center()
                gc.DrawText(str(i+1), c.x*xs - 9, c.y*ys - 9, bg)

        # Draw in-progress guide line
        points = []
        line_color = 'gray'
        line_size = 3
        if g_state.add_line_proposed:
            points.append(g_state.add_line_proposed)
        if g_state.add_line_stage:
            points.extend(g_state.add_line_stage)
        if g_state.del_line_stage:
            line_color = 'red'
            line_size = 5
            points.extend(g_state.del_line_stage)
        if points:
            gc.SetPen(wx.Pen(line_color, 1))
            gc.SetBrush(wx.Brush(line_color))
            path = gc.CreatePath()
            for p in points:
                path.AddCircle(p.x * xs, p.y * ys, 7)
            gc.SetPen(wx.Pen(line_color, line_size))
            if len(points) == 2:
                path.MoveToPoint(points[0].x * xs, points[0].y * ys)
                path.AddLineToPoint(points[1].x * xs, points[1].y * ys)
            path.CloseSubpath()
            gc.DrawPath(path)

    #
    # Events
    #

    def OnErase(self, evt):
        # Prevent flicker
        pass

    def OnPaint(self, evt):
        if self._use_buffer:
            if self._buffer is None:
                self.init_buffer()
            dc = wx.BufferedPaintDC(self, self._buffer)
        else:
            dc = wx.PaintDC(self)
            dc.SetBackground(self._bg_color)
            dc.Clear()
            self.draw_gc(dc)

    def OnSize(self, evt):
        self.init_buffer()
        evt.Skip()


class ControlsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)

        btn1 = wx.Button(parent=self, id=ID_BTN_ADD_LINE, label='Draw Guide Line (d)')
        btn2 = wx.Button(parent=self, id=ID_BTN_DEL_LINE, label='Delete Guide Line (x)')
        chk1 = wx.CheckBox(parent=self, id=ID_CHK_SNAP, label='Snapping')
        chk2 = wx.CheckBox(parent=self, id=ID_CHK_HIDE_GUIDE, label='Hide Guide Lines')
        chk3 = wx.CheckBox(parent=self, id=ID_CHK_HIDE_NUM, label='Hide Shape #\'s')
        sf = wx.SizerFlags().Left()
        checks = wx.BoxSizer(wx.VERTICAL)
        checks.AddF(chk1, sf)
        checks.AddF(chk2, sf)
        checks.AddF(chk3, sf)
        rbox1 = wx.RadioBox(parent=self, label='Preview',
                            id=ID_RAD_PREVIEW,
                            choices=['Guide Lines', 'Recursion'],
                            style=wx.RA_SPECIFY_ROWS,
                            majorDimension=2)
        rbox2 = wx.RadioBox(parent=self, label='Aspect Ratio',
                            id=ID_RAD_ASPECT_RATIO,
                            choices=['Fit', 'Stretch'],
                            style=wx.RA_SPECIFY_ROWS,
                            majorDimension=2)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.AddStretchSpacer()
        sf = wx.SizerFlags().Center().DoubleBorder()
        for c in [btn1, btn2, checks, rbox1, rbox2]:
            sizer.AddF(c, sf)
        sizer.AddStretchSpacer()
        self.SetAutoLayout(True)
        self.SetSizer(sizer)

        # Initial state
        chk1.SetValue(g_controls.do_point_snapping)
        chk2.SetValue(g_controls.do_hide_guide_lines)
        chk3.SetValue(g_controls.do_hide_shape_numbers)
        rbox1.SetSelection(1 if g_controls.do_draw_recursion else 0)

        # Events
        btn1.Bind(wx.EVT_BUTTON, self.OnAddLine)
        btn2.Bind(wx.EVT_BUTTON, self.OnDelLine)
        chk1.Bind(wx.EVT_CHECKBOX, self.OnSnap)
        chk2.Bind(wx.EVT_CHECKBOX, self.OnHideGuide)
        chk3.Bind(wx.EVT_CHECKBOX, self.OnHideNum)
        rbox1.Bind(wx.EVT_RADIOBOX, self.OnPreview)
        rbox2.Bind(wx.EVT_RADIOBOX, self.OnAspectRatio)

    #
    # Events
    #

    def OnAddLine(self, evt):
        g_state.add_line_stage = []
        g_state.add_line_stage_info = []
        g_state.del_line_stage = None

    def OnDelLine(self, evt):
        g_state.add_line_stage = None
        g_state.add_line_stage_info = None
        g_state.del_line_stage = []

    def OnSnap(self, evt):
        g_controls.do_point_snapping = evt.Checked()

    def OnHideGuide(self, evt):
        g_controls.do_hide_guide_lines = evt.Checked()
        self.GetParent().force_redraw()

    def OnHideNum(self, evt):
        g_controls.do_hide_shape_numbers = evt.Checked()
        self.GetParent().force_redraw()

    def OnPreview(self, evt):
        g_controls.do_draw_recursion = (evt.GetInt() == 1)
        self.GetParent().force_redraw()

    def OnAspectRatio(self, evt):
        g_controls.aspect_ratio_fit = (evt.GetInt() == 0)
        self.GetParent().force_redraw()


class MainFrame(wx.Frame):
    def __init__(self, parent, title, size):
        wx.Frame.__init__(self, parent=parent, title=title, size=size)

        # File menu
        file_menu = wx.Menu()
        file_menu.Append(wx.ID_NEW, "", "New Project")
        file_menu.Append(wx.ID_OPEN, "", "Open Project")
        file_menu.Append(wx.ID_SAVE, "", "Save Project")
        file_menu.Append(wx.ID_SAVEAS, "", "Save Project As")
        file_menu.Append(ID_EXPORT_FULL, "Export", "Export Full SVG");
        file_menu.Append(ID_EXPORT_INDIVIDUAL, "Export Shapes", "Export Individual SVGs");
        file_menu.Append(wx.ID_EXIT, "", "")
        # Edit menu
        edit_menu = wx.Menu()
        edit_menu.Append(wx.ID_UNDO, "", "")
        edit_menu.Append(wx.ID_REDO, "", "")
        self._edit_menu = edit_menu
        # Menu bar
        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, "&File")
        menu_bar.Append(edit_menu, "&Edit")
        self.SetMenuBar(menu_bar)
        self.CreateStatusBar()

        # Control panel
        self._control_panel = ControlsPanel(parent=self)

        # Draw panel
        self._draw_panel = None
        self.init_draw_panel()

        # Events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        # File
        self.Bind(wx.EVT_MENU, self.OnNew, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveAs, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnExportFull, id=ID_EXPORT_FULL)
        self.Bind(wx.EVT_MENU, self.OnExportIndividual, id=ID_EXPORT_INDIVIDUAL)
        self.Bind(wx.EVT_MENU, self.OnExit, id=wx.ID_EXIT)
        # Edit
        self.Bind(wx.EVT_MENU, self.OnUndo, id=wx.ID_UNDO)
        self.Bind(wx.EVT_MENU, self.OnRedo, id=wx.ID_REDO)

    #
    # Internal
    #

    def set_undo_state(self, undo_stack):
        self._edit_menu.Enable(wx.ID_UNDO, undo_stack.can_undo())
        self._edit_menu.Enable(wx.ID_REDO, undo_stack.can_redo())

    def init_draw_panel(self):
        if self._draw_panel:
            self._draw_panel.Destroy()
        self._draw_panel = GraphicsContextDrawPanel(self)
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddF(self._control_panel, wx.SizerFlags().Expand())
        sizer.AddF(self._draw_panel, wx.SizerFlags().Expand().Proportion(1))
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.Layout()

    def force_redraw(self):
        self._draw_panel._buffer = None
        self.Update()
        self.Refresh()

    def post_paint(self, start_time):
        end_time = time.clock()
        fps = int(1 / (end_time - start_time))
        w,h = self._draw_panel.GetSize()
        x,y = self._draw_panel.ScreenToClient(wx.GetMousePosition())
        #self.SetStatusText('Canvas: %dx%d  Cursor: (%d,%d)  FPS: %d' % (w,h,x,y,fps))
        self.SetStatusText('Canvas: %dx%d  Cursor: (%d,%d)' % (w,h,x,y))

    def save_internal(self, title, default_filename, keep_filename):
        filename = default_filename
        if not filename:
            dlg = wx.FileDialog(self, title, "", "", "JSON Files (*.json)|*.json", wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
            if dlg.ShowModal() == wx.ID_OK:
                filename = dlg.GetPath()
            dlg.Destroy()
        if filename:
            save_project(filename, keep_filename)

    #
    # Events
    #

    def OnNew(self, evt):
        dlg = wx.MessageDialog(self, 'All Unsaved progress will be lost.', 'Create New Project', wx.OK|wx.CANCEL)
        if dlg.ShowModal() == wx.ID_OK:
            new_project()
            self.force_redraw()
        dlg.Destroy()

    def OnOpen(self, evt):
        dlg = wx.FileDialog(self, "Open project file", "", "", "JSON Files (*.json)|*.json", wx.OPEN|wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            load_project(filename)
        dlg.Destroy()
        self.force_redraw()

    def OnSave(self, evt):
        self.save_internal("Save project file", g_controls.json_save_filename, True)

    def OnSaveAs(self, evt):
        self.save_internal("Save project file as", None, False)

    def OnExportFull(self, evt):
        dlg = wx.FileDialog(self, "Export SVG file", "", "", "SVG Files (*.svg)|*.svg", wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            export_full(filename)
        dlg.Destroy()

    def OnExportIndividual(self, evt):
        dlg = wx.DirDialog(parent=self)
        if dlg.ShowModal() == wx.ID_OK:
            directory = dlg.GetPath()
            export_individual(directory)
        dlg.Destroy()

    def OnExit(self, evt):
        self.Close()

    def OnUndo(self, evt):
        if g_undo_stack.can_undo():
            tmp_proj = g_undo_stack.undo()
            state_from_project(tmp_proj, False)

    def OnRedo(self, evt):
        if g_undo_stack.can_redo():
            tmp_proj = g_undo_stack.redo()
            state_from_project(tmp_proj, False)

    def OnOptDrawing(self, evt):
        self.set_draw_type(evt.Id)
        self.force_redraw()

    def OnPaint(self, evt):
        start_time = time.clock()
        wx.CallAfter(self.post_paint, start_time)


class AttrFrame(wx.Frame):
    def __init__(self, parent, title, size):
        wx.Frame.__init__(self, parent=parent, title=title, size=size)

        #
        # Shape attributes
        #
        self._shape_panel = wx.Panel(parent=self)

        txtShapeAttrs = wx.StaticText(parent=self._shape_panel, id=ID_TXT_SHAPE_ATTRS, label='SHAPE ATTRIBUTES')
        txtShapeAttrs.SetFont(txtShapeAttrs.GetFont().Larger().Bold())
        raDir = wx.RadioBox(parent=self._shape_panel, label='Direction',
                            id=ID_RA_SHAPE_DIR,
                            choices=['Clockwise', 'Counter-Clockwise'],
                            style=wx.RA_SPECIFY_ROWS,
                            majorDimension=2)

        txtDepth = wx.StaticText(parent=self._shape_panel, label='Depth')
        txtDepth.SetMinSize((52, -1))
        slDepth = wx.Slider(parent=self._shape_panel, id=ID_SL_SHAPE_DEPTH, minValue=1, maxValue=150, value=1)
        slDepth.SetMinSize((200, slDepth.GetMinSize()[1]))
        spDepth = wx.SpinCtrl(parent=self._shape_panel, id=ID_SP_SHAPE_DEPTH, min=1, max=1000, value='1',
                              style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spDepth.SetMinSize((75, -1))

        txtStep = wx.StaticText(parent=self._shape_panel, label='Step')
        txtStep.SetMinSize(txtDepth.GetMinSize())
        slStep = wx.Slider(parent=self._shape_panel, id=ID_SL_SHAPE_STEP, minValue=1, maxValue=1000)
        slStep.SetMinSize((200, slStep.GetMinSize()[1]))
        spStep = wx.SpinCtrlDouble(parent=self._shape_panel, id=ID_SP_SHAPE_STEP, min=0.001, max=1.0, inc=0.01, initial=0.0,
                                   style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spStep.SetMinSize(spDepth.GetMinSize())
        spStep.SetDigits(3)

        txtInc = wx.StaticText(parent=self._shape_panel, label='Inner')
        txtInc.SetMinSize(txtDepth.GetMinSize())
        slInc = wx.Slider(parent=self._shape_panel, id=ID_SL_SHAPE_INNER, minValue=0, maxValue=1000)
        slInc.SetMinSize((200, slInc.GetMinSize()[1]))
        spInc = wx.SpinCtrlDouble(parent=self._shape_panel, id=ID_SP_SHAPE_INNER, min=0.0, max=0.1, inc=0.0001, initial=0.0,
                                  style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spInc.SetMinSize(spDepth.GetMinSize())
        spInc.SetDigits(4)

        chkReverseColors = wx.CheckBox(parent=self._shape_panel, id=ID_CHK_REVERSE_COLORS, label='Reverse colors')
        chkDisabled = wx.CheckBox(parent=self._shape_panel, id=ID_CHK_DISABLED, label='Disable')

        txtFooter = wx.StaticText(parent=self._shape_panel, label='Footer')
        txtFooter.SetMinSize(txtDepth.GetMinSize())
        slFooter = wx.Slider(parent=self._shape_panel, id=ID_SL_SHAPE_FOOTER,
                             minValue=0, maxValue=500, value=0)
        slFooter.SetMinSize((200, slFooter.GetMinSize()[1]))
        spFooter = wx.SpinCtrlDouble(parent=self._shape_panel, id=ID_SP_SHAPE_FOOTER,
                                     min=0.0, max=1.0, inc=0.002, initial=0.0,
                                     style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spFooter.SetMinSize(spDepth.GetMinSize())
        spFooter.SetDigits(3)

        txtFooterInc = wx.StaticText(parent=self._shape_panel, label='Buffer')
        txtFooterInc.SetMinSize(txtDepth.GetMinSize())
        slFooterInc = wx.Slider(parent=self._shape_panel, id=ID_SL_SHAPE_FOOTER_BUFFER,
                                minValue=0, maxValue=500, value=0)
        slFooterInc.SetMinSize((200, slFooterInc.GetMinSize()[1]))
        spFooterInc = wx.SpinCtrlDouble(parent=self._shape_panel, id=ID_SP_SHAPE_FOOTER_BUFFER,
                                        min=0.0, max=1.0, inc=0.002, initial=0.0,
                                        style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spFooterInc.SetMinSize(spDepth.GetMinSize())
        spFooterInc.SetDigits(3)

        txtFooterOffset = wx.StaticText(parent=self._shape_panel, label='Offset')
        txtFooterOffset.SetMinSize(txtDepth.GetMinSize())
        slFooterOffset = wx.Slider(parent=self._shape_panel, id=ID_SL_SHAPE_FOOTER_OFFSET,
                                   minValue=0, maxValue=150, value=0)
        slFooterOffset.SetMinSize((200, slFooterOffset.GetMinSize()[1]))
        spFooterOffset = wx.SpinCtrl(parent=self._shape_panel, id=ID_SP_SHAPE_FOOTER_OFFSET,
                                     min=0, max=1000, value='0',
                                     style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spFooterOffset.SetMinSize(spDepth.GetMinSize())

        flags = wx.SizerFlags()
        szDepth = wx.BoxSizer(wx.HORIZONTAL)
        szDepth.AddF(txtDepth, flags)
        szDepth.AddF(slDepth, flags)
        szDepth.AddF(spDepth, flags)
        szStep = wx.BoxSizer(wx.HORIZONTAL)
        szStep.AddF(txtStep, flags)
        szStep.AddF(slStep, flags)
        szStep.AddF(spStep, flags)
        szInc = wx.BoxSizer(wx.HORIZONTAL)
        szInc.AddF(txtInc, flags)
        szInc.AddF(slInc, flags)
        szInc.AddF(spInc, flags)
        szFooter = wx.BoxSizer(wx.HORIZONTAL)
        szFooter.AddF(txtFooter, flags)
        szFooter.AddF(slFooter, flags)
        szFooter.AddF(spFooter, flags)
        szFooterInc = wx.BoxSizer(wx.HORIZONTAL)
        szFooterInc.AddF(txtFooterInc, flags)
        szFooterInc.AddF(slFooterInc, flags)
        szFooterInc.AddF(spFooterInc, flags)
        szFooterOffset = wx.BoxSizer(wx.HORIZONTAL)
        szFooterOffset.AddF(txtFooterOffset, flags)
        szFooterOffset.AddF(slFooterOffset, flags)
        szFooterOffset.AddF(spFooterOffset, flags)

        outer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        outer.AddF(sizer, wx.SizerFlags().DoubleBorder())
        sizer.AddF(txtShapeAttrs, flags)
        sizer.AddF(raDir, flags)
        sizer.AddF(szDepth, flags)
        sizer.AddF(szStep, flags)
        sizer.AddF(szInc, flags)
        sizer.AddF(chkReverseColors, flags)
        sizer.AddF(chkDisabled, flags)
        sizer.AddF(szFooter, wx.SizerFlags().DoubleBorder(wx.TOP))
        sizer.AddF(szFooterInc, flags)
        sizer.AddF(szFooterOffset, flags)

        self._shape_panel.SetAutoLayout(True)
        self._shape_panel.SetSizer(outer)

        self._last_shape = None
        self._shape_num_label = txtShapeAttrs
        self._s_ra_dir = raDir
        self._s_sl_depth = slDepth
        self._s_sp_depth = spDepth
        self._s_sl_step = slStep
        self._s_sp_step = spStep
        self._s_sl_inc = slInc
        self._s_sp_inc = spInc
        self._s_chk_reverse_colors = chkReverseColors
        self._s_chk_disabled = chkDisabled
        self._s_sl_footer = slFooter
        self._s_sp_footer = spFooter
        self._s_sl_footer_inc = slFooterInc
        self._s_sp_footer_inc = spFooterInc
        self._s_sl_footer_offset = slFooterOffset
        self._s_sp_footer_offset = spFooterOffset

        self.set_enabled_recursive(self._shape_panel, False)

        self.Bind(wx.EVT_RADIOBOX, self.OnShapeClockwise, id=ID_RA_SHAPE_DIR)
        self.Bind(wx.EVT_SCROLL, self.OnShapeDepthScroll, id=ID_SL_SHAPE_DEPTH)
        self.Bind(wx.EVT_SPINCTRL, self.OnShapeDepthSpin, id=ID_SP_SHAPE_DEPTH)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnShapeDepthText, id=ID_SP_SHAPE_DEPTH)
        self.Bind(wx.EVT_SCROLL, self.OnShapeStepScroll, id=ID_SL_SHAPE_STEP)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnShapeStepSpin, id=ID_SP_SHAPE_STEP)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnShapeStepText, id=ID_SP_SHAPE_STEP)
        self.Bind(wx.EVT_SCROLL, self.OnShapeInnerScroll, id=ID_SL_SHAPE_INNER)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnShapeInnerSpin, id=ID_SP_SHAPE_INNER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnShapeInnerText, id=ID_SP_SHAPE_INNER)
        self.Bind(wx.EVT_CHECKBOX, self.OnShapeReverseColors, id=ID_CHK_REVERSE_COLORS)
        self.Bind(wx.EVT_CHECKBOX, self.OnShapeDisabled, id=ID_CHK_DISABLED)
        self.Bind(wx.EVT_SCROLL, self.OnShapeFooterScroll, id=ID_SL_SHAPE_FOOTER)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnShapeFooterSpin, id=ID_SP_SHAPE_FOOTER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnShapeFooterText, id=ID_SP_SHAPE_FOOTER)
        self.Bind(wx.EVT_SCROLL, self.OnShapeFooterBufferScroll, id=ID_SL_SHAPE_FOOTER_BUFFER)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnShapeFooterBufferSpin, id=ID_SP_SHAPE_FOOTER_BUFFER)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnShapeFooterBufferText, id=ID_SP_SHAPE_FOOTER_BUFFER)
        self.Bind(wx.EVT_SCROLL, self.OnShapeFooterOffsetScroll, id=ID_SL_SHAPE_FOOTER_OFFSET)
        self.Bind(wx.EVT_SPINCTRL, self.OnShapeFooterOffsetSpin, id=ID_SP_SHAPE_FOOTER_OFFSET)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnShapeFooterOffsetText, id=ID_SP_SHAPE_FOOTER_OFFSET)

        #
        # Global attributes
        #
        self._global_panel = wx.Panel(parent=self)

        txtGlobalAttrs = wx.StaticText(parent=self._global_panel, label='GLOBAL ATTRIBUTES')
        txtGlobalAttrs.SetFont(txtShapeAttrs.GetFont().Larger().Bold())

        txtGlobalStep = wx.StaticText(parent=self._global_panel, label='Step')
        txtGlobalStep.SetMinSize(txtDepth.GetMinSize())
        slGlobalStep = wx.Slider(parent=self._global_panel, id=ID_SL_GLOBAL_STEP, minValue=1, maxValue=1000)
        slGlobalStep.SetMinSize((200, slGlobalStep.GetMinSize()[1]))
        spGlobalStep = wx.SpinCtrlDouble(parent=self._global_panel, id=ID_SP_GLOBAL_STEP,
                                         min=0.001, max=1.0, inc=0.01, initial=g_project_defaults.step,
                                         style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spGlobalStep.SetMinSize(spDepth.GetMinSize())
        spGlobalStep.SetDigits(3)

        txtGlobalColors = wx.StaticText(parent=self._global_panel, label='Colors')
        txtGlobalColors.SetMinSize(txtGlobalStep.GetMinSize())
        cpGlobalColor1 = wx.ColourPickerCtrl(parent=self._global_panel, id=ID_CP_GLOBAL_COLOR1)
        cpGlobalColor2 = wx.ColourPickerCtrl(parent=self._global_panel, id=ID_CP_GLOBAL_COLOR2)

        txtGlobalCanvas = wx.StaticText(parent=self._global_panel, label='Canvas')
        txtGlobalCanvas.SetMinSize(txtGlobalStep.GetMinSize())
        txtGlobalCanvasWidth = wx.StaticText(parent=self._global_panel, label='Width')
        txtGlobalCanvasWidth.SetMinSize(txtGlobalStep.GetMinSize())
        spGlobalCanvasWidth = wx.SpinCtrl(parent=self._global_panel, id=ID_SP_GLOBAL_CANVAS_WIDTH,
                                          min=100, max=100000,
                                          value=str(g_project_defaults.canvas[2] - g_project_defaults.canvas[0]),
                                          style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spGlobalCanvasWidth.SetMinSize(spGlobalStep.GetMinSize())
        txtGlobalCanvasHeight = wx.StaticText(parent=self._global_panel, label='Height')
        txtGlobalCanvasHeight.SetMinSize(txtGlobalStep.GetMinSize())
        spGlobalCanvasHeight = wx.SpinCtrl(parent=self._global_panel, id=ID_SP_GLOBAL_CANVAS_HEIGHT,
                                           min=100, max=100000,
                                           value=str(g_project_defaults.canvas[3] - g_project_defaults.canvas[1]),
                                           style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT|wx.TE_PROCESS_ENTER)
        spGlobalCanvasHeight.SetMinSize(spGlobalStep.GetMinSize())

        btnGlobalBgImage = wx.Button(parent=self._global_panel, id=ID_BTN_GLOBAL_BG_IMAGE, label='Load Background Image')


        szGlobalStep = wx.BoxSizer(wx.HORIZONTAL)
        szGlobalStep.AddF(txtGlobalStep, flags)
        szGlobalStep.AddF(slGlobalStep, flags)
        szGlobalStep.AddF(spGlobalStep, flags)
        szGlobalColors = wx.BoxSizer(wx.HORIZONTAL)
        szGlobalColors.AddF(txtGlobalColors, flags)
        szGlobalColors.AddF(cpGlobalColor1, flags)
        szGlobalColors.AddF(cpGlobalColor2, flags)
        szGlobalCanvasWidth = wx.BoxSizer(wx.HORIZONTAL)
        szGlobalCanvasWidth.AddF(txtGlobalCanvasWidth, flags)
        szGlobalCanvasWidth.AddF(spGlobalCanvasWidth, flags)
        szGlobalCanvasHeight = wx.BoxSizer(wx.HORIZONTAL)
        szGlobalCanvasHeight.AddF(txtGlobalCanvasHeight, flags)
        szGlobalCanvasHeight.AddF(spGlobalCanvasHeight, flags)

        outer = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.BoxSizer(wx.VERTICAL)
        outer.AddF(sizer, wx.SizerFlags().DoubleBorder())
        sizer.AddF(txtGlobalAttrs, flags)
        sizer.AddF(szGlobalStep, flags)
        sizer.AddF(szGlobalColors, flags)
        sizer.AddF(txtGlobalCanvas, flags)
        sizer.AddF(szGlobalCanvasWidth, flags)
        sizer.AddF(szGlobalCanvasHeight, flags)
        sizer.AddF(btnGlobalBgImage, flags.Border(wx.TOP, wx.SizerFlags.GetDefaultBorder()*2))

        self._global_panel.SetAutoLayout(True)
        self._global_panel.SetSizer(outer)

        self._g_sl_step = slGlobalStep
        self._g_sp_step = spGlobalStep
        self._g_cp_color1 = cpGlobalColor1
        self._g_cp_color2 = cpGlobalColor2
        self._g_sp_canvas_width = spGlobalCanvasWidth
        self._g_sp_canvas_height = spGlobalCanvasHeight

        self.Bind(wx.EVT_SCROLL, self.OnGlobalStepScroll, id=ID_SL_GLOBAL_STEP)
        self.Bind(wx.EVT_SPINCTRLDOUBLE, self.OnGlobalStepSpin, id=ID_SP_GLOBAL_STEP)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnGlobalStepText, id=ID_SP_GLOBAL_STEP)
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.OnGlobalColor)
        self.Bind(wx.EVT_SPINCTRL, self.OnGlobalCanvasWidthSpin, id=ID_SP_GLOBAL_CANVAS_WIDTH)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnGlobalCanvasWidthText, id=ID_SP_GLOBAL_CANVAS_WIDTH)
        self.Bind(wx.EVT_SPINCTRL, self.OnGlobalCanvasHeightSpin, id=ID_SP_GLOBAL_CANVAS_HEIGHT)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnGlobalCanvasHeightText, id=ID_SP_GLOBAL_CANVAS_HEIGHT)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnGlobalCanvasHeightText, id=ID_SP_GLOBAL_CANVAS_HEIGHT)
        self.Bind(wx.EVT_BUTTON, self.OnGlobalBGImage, id=ID_BTN_GLOBAL_BG_IMAGE)

        # Frame
        outer = wx.BoxSizer(wx.VERTICAL)
        flags = wx.SizerFlags().Expand().Border(wx.ALL, 0)
        outer.AddF(self._shape_panel, flags.Proportion(0))
        outer.AddF(self._global_panel, flags.Proportion(1))
        self.SetSizer(outer)

    #
    # Internal
    #

    def regen_recursion(self):
        # TODO: Only need to re-generate g_state.selected_shape's
        g_state.rec_list = generate_recursion(g_state.project)
        g_app.force_redraw_internal()

    def set_enabled_recursive(self, ctrl, enabled):
        for c in ctrl.GetChildren():
            ctrl.Enable(enabled)
            s = c.GetNextSibling()
            while s:
                s.Enable(enabled)
                s = s.GetNextSibling()
            self.set_enabled_recursive(c, enabled)

    def update_shape(self, force=False):
        s = g_state.selected_shape
        if (s == self._last_shape) and (not force):
            return
        is_new_shape = (s != self._last_shape)
        self._last_shape = s
        s_num = ''
        if s is not None:
            for i,p_s in enumerate(g_state.project.shapes):
                if s == p_s:
                    s_num = str(i + 1)
                    break
            self._s_ra_dir.SetSelection(0 if s.clockwise else 1)
            self._s_sl_depth.SetValue(s.depth)
            self._s_sp_depth.SetValue(s.depth)
            # [0.0,1.0] -> [0,1000]
            self._s_sl_step.SetValue(s.step * 1000.0)
            self._s_sp_step.SetValue(s.step)
            # [0.0,0.1] -> [0,1000]
            self._s_sl_inc.SetValue(s.inc * 10000.0)
            self._s_sp_inc.SetValue(s.inc)
            self._s_chk_reverse_colors.SetValue(s.reverse_colors)
            self._s_chk_disabled.SetValue(s.disabled)
            # [0.0,1.0] -> [0,1000]
            self._s_sl_footer.SetValue(s.footer * 1000.0)
            self._s_sp_footer.SetValue(s.footer)
            # [0.0,1.0] -> [0,1000]
            self._s_sl_footer_inc.SetValue(s.footer_inc * 1000.0)
            self._s_sp_footer_inc.SetValue(s.footer_inc)
            self._s_sl_footer_offset.SetValue(s.footer_offset)
            self._s_sp_footer_offset.SetValue(s.footer_offset)
        if is_new_shape:
            self.set_enabled_recursive(self._shape_panel, s is not None)
            self._shape_num_label.SetLabel('SHAPE %s ATTRIBUTES' % s_num)


    #
    # Events
    #

    def OnShapeClockwise(self, evt):
        s = g_state.selected_shape
        clockwise = (evt.GetInt() == 0)
        if s.clockwise != clockwise:
            s.clockwise = clockwise
            self.regen_recursion()

    def OnShapeDepthScroll(self, evt):
        s = g_state.selected_shape
        d = evt.GetPosition()
        if (s is not None) and (d != s.depth):
            s.depth = d
            self._s_sp_depth.SetValue(d)
            self.regen_recursion()

    def OnShapeDepthSpin(self, evt):
        s = g_state.selected_shape
        d = evt.GetInt()
        if (s is not None) and (d != s.depth):
            s.depth = d
            self._s_sl_depth.SetValue(d)
            self.regen_recursion()

    def OnShapeDepthText(self, evt):
        s = g_state.selected_shape
        if (s is not None):
            # Will validate and clamp value then trigger spin event
            self._s_sl_depth.SetFocus()

    def OnShapeStepScroll(self, evt):
        s = g_state.selected_shape
        # [0,1000] -> [0.0,1.0]
        step = (evt.GetPosition() / 1000.0)
        if (s is not None) and (step != s.step):
            s.step = step
            self._s_sp_step.SetValue(s.step)
            self.regen_recursion()

    def OnShapeStepSpin(self, evt):
        s = g_state.selected_shape
        step = evt.GetValue()
        if (s is not None) and (step != s.step):
            s.step = step
            self._s_sl_step.SetValue(step * 1000)
            self.regen_recursion()

    def OnShapeStepText(self, evt):
        s = g_state.selected_shape
        if (s is not None):
            # Will validate and clamp value then trigger spin event
            self._s_sl_step.SetFocus()

    def OnShapeInnerScroll(self, evt):
        s = g_state.selected_shape
        # [0,1000] -> [0.0,0.1]
        i = (evt.GetPosition() / 10000.0)
        if (s is not None) and (i != s.inc):
            s.inc = i
            self._s_sp_inc.SetValue(i)
            self.regen_recursion()

    def OnShapeInnerSpin(self, evt):
        s = g_state.selected_shape
        inc = evt.GetValue()
        if (s is not None) and (inc != s.inc):
            s.inc = inc
            self._s_sl_inc.SetValue(inc * 10000)
            self.regen_recursion()

    def OnShapeInnerText(self, evt):
        s = g_state.selected_shape
        if (s is not None):
            # Will validate and clamp value then trigger spin event
            self._s_sl_inc.SetFocus()

    def OnShapeReverseColors(self, evt):
        s = g_state.selected_shape
        if s:
            s.reverse_colors = evt.Checked()
            self.regen_recursion()

    def OnShapeDisabled(self, evt):
        s = g_state.selected_shape
        if s:
            s.disabled = evt.Checked()
            self.regen_recursion()

    def OnShapeFooterScroll(self, evt):
        s = g_state.selected_shape
        # [0,1000] -> [0.0,1.0]
        footer = (evt.GetPosition() / 1000.0)
        if (s is not None) and (footer != s.footer):
            s.footer = footer
            self._s_sp_footer.SetValue(footer)
            self.regen_recursion()

    def OnShapeFooterSpin(self, evt):
        s = g_state.selected_shape
        footer = evt.GetValue()
        if (s is not None) and (footer != s.footer):
            s.footer = footer
            self._s_sl_footer.SetValue(footer * 1000)
            self.regen_recursion()

    def OnShapeFooterText(self, evt):
        s = g_state.selected_shape
        if (s is not None):
            # Will validate and clamp value then trigger spin event
            self._s_sl_footer.SetFocus()

    def OnShapeFooterBufferScroll(self, evt):
        s = g_state.selected_shape
        # [0,1000] -> [0.0,1.0]
        inc = (evt.GetPosition() / 1000.0)
        if (s is not None) and (inc != s.footer_inc):
            s.footer_inc = inc
            self._s_sp_footer_inc.SetValue(inc)
            self.regen_recursion()

    def OnShapeFooterBufferSpin(self, evt):
        s = g_state.selected_shape
        inc = evt.GetValue()
        if (s is not None) and (inc != s.footer_inc):
            s.footer_inc = inc
            self._s_sl_footer_inc.SetValue(inc * 1000)
            self.regen_recursion()

    def OnShapeFooterBufferText(self, evt):
        s = g_state.selected_shape
        if (s is not None):
            # Will validate and clamp value then trigger spin event
            self._s_sl_footer_inc.SetFocus()

    def OnShapeFooterOffsetScroll(self, evt):
        s = g_state.selected_shape
        offset = evt.GetPosition()
        if (s is not None) and (offset != s.footer_offset):
            s.footer_offset = offset
            self._s_sp_footer_offset.SetValue(offset)
            self.regen_recursion()

    def OnShapeFooterOffsetSpin(self, evt):
        s = g_state.selected_shape
        offset = evt.GetInt()
        if (s is not None) and (offset != s.footer_offset):
            s.footer_offset = offset
            self._s_sl_footer_offset.SetValue(offset)
            self.regen_recursion()

    def OnShapeFooterOffsetText(self, evt):
        s = g_state.selected_shape
        if (s is not None):
            # Will validate and clamp value then trigger spin event
            self._s_sl_footer_offset.SetFocus()

    def OnGlobalStepScroll(self, evt):
        # [0,1000] -> [0.0,1.0]
        step = (evt.GetPosition() / 1000.0)
        if g_project_defaults.step != step:
            g_project_defaults.step = step
            for s in g_state.project.shapes:
                s.step = step
            self._g_sp_step.SetValue(step)
            self.update_shape(force=True)
            self.regen_recursion()

    def OnGlobalStepSpin(self, evt):
        step = evt.GetValue()
        if g_project_defaults.step != step:
            g_project_defaults.step = step
            for s in g_state.project.shapes:
                s.step = step
            self._g_sl_step.SetValue(step * 1000)
            self.update_shape(force=True)
            self.regen_recursion()

    def OnGlobalStepText(self, evt):
        # Will validate and clamp value then trigger spin event
        self._g_sl_step.SetFocus()

    def OnGlobalColor(self, evt):
        wxc = wx.Colour(*evt.GetColour())
        name = wxc.GetAsString(wx.C2S_HTML_SYNTAX)
        idx = 0 if (evt.GetId() == ID_CP_GLOBAL_COLOR1) else 1
        if g_state.project.colors[idx] != name:
            g_state.project.colors[idx] = name
            self.regen_recursion()

    def OnGlobalCanvasWidthSpin(self, evt):
        w = evt if (type(evt) is int) else evt.GetInt()
        g_project_defaults.canvas[2] = w
        if g_state.project.canvas[2] != w:
            # Scale all points x values
            xs = float(w) / g_state.project.canvas[2]
            for s in g_state.project.shapes:
                for p in s.poly.points:
                    p.x *= xs
            g_state.project.canvas[2] = w
            post_project_modification()
            self.regen_recursion()

    def OnGlobalCanvasWidthText(self, evt):
        self.OnGlobalCanvasWidthSpin(int(evt.GetString()))

    def OnGlobalCanvasHeightSpin(self, evt):
        h = evt if (type(evt) is int) else evt.GetInt()
        g_project_defaults.canvas[3] = h
        if g_state.project.canvas[3] != h:
            # Scale all points y values
            ys = float(h) / g_state.project.canvas[3]
            for s in g_state.project.shapes:
                for p in s.poly.points:
                    p.y *= ys
            g_state.project.canvas[3] = h
            post_project_modification()
            self.regen_recursion()

    def OnGlobalCanvasHeightText(self, evt):
        self.OnGlobalCanvasHeightSpin(int(evt.GetString()))

    def OnGlobalBGImage(self, evt):
        dlg = wx.FileDialog(parent=self, message="Select image file", style=wx.OPEN|wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            print 'Loading bg image file', filename
            img = wx.Image(filename)
            if img.IsOk():
                g_controls.bg_bitmap = wx.BitmapFromImage(img)
        dlg.Destroy()
        g_app.force_redraw_internal()

class App(wx.App):
    def OnInit(self):
        # main
        size = (896, 504)
        self._frame = MainFrame(parent=None, title="Vector Recursion Workbench", size=size)
        self.SetTopWindow(self._frame)
        self._frame.Show(True)
        # attributes
        size = (350, 525)
        self._attr_frame = AttrFrame(parent=self._frame, title='Attribute Editor', size=size)
        pos = self._frame.GetPosition()
        size = self._frame.GetSize()
        self._attr_frame.Move((pos.x + size.x, pos.y))
        self._attr_frame.Show(True)
        # Events
        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_SET_FOCUS, self.OnSetFocus)
        self._frame.SetFocus()
        return True

    def set_global_ui(self):
        self._attr_frame._g_cp_color1.SetColour(colour_from_name(g_state.project.colors[0]))
        self._attr_frame._g_cp_color2.SetColour(colour_from_name(g_state.project.colors[1]))
        self._attr_frame._g_sp_canvas_width.SetValue(g_state.project.canvas[2])
        self._attr_frame._g_sp_canvas_height.SetValue(g_state.project.canvas[3])

    #
    # Internal
    #

    def force_redraw(self):
        self._attr_frame.update_shape()
        self.force_redraw_internal()

    def force_redraw_internal(self):
        self._frame.force_redraw()

    #
    # Events
    #

    def OnSetFocus(self, event):
        # So text input of numbers doesn't disable the control
        # SpinCtrl comes through as is, double comes through as the child TextCtrl
        exclude = (wx.SpinCtrl, wx.SpinCtrlDouble)
        obj = event.GetEventObject()
        g_state.do_num_hotkey = (type(obj) not in exclude) and (type(obj.GetParent()) not in exclude)
        event.Skip()

    def OnKeyDown(self, evt):
        do_update = False
        kc = evt.GetKeyCode()
        if kc == wx.WXK_ESCAPE:
            if (g_state.add_line_stage is not None) or (g_state.del_line_stage is not None):
                g_state.add_line_stage = None
                g_state.add_line_stage_info = None
                g_state.add_line_proposed = None
                g_state.add_line_proposed_info = None
                g_state.del_line_stage = None
                do_update = True
            elif g_state.selected_shape is not None:
                g_state.selected_shape = None
                do_update = True
        elif g_state.do_num_hotkey and (kc >= ord('1')) and (kc <= ord('9')):
            shape_idx = kc - ord('1')
            if shape_idx < len(g_state.project.shapes):
                g_state.selected_shape = g_state.project.shapes[shape_idx]
            else:
                g_state.selected_shape = None
            do_update = True
        elif kc == ord('D'):
            self._frame._control_panel.OnAddLine(None)
            return
        elif kc == ord('X'):
            self._frame._control_panel.OnDelLine(None)
            return
        if do_update:
            g_app.force_redraw()
        else:
            evt.Skip()


if __name__ == '__main__':
    import sys
    g_app = App()
    g_undo_stack.set_callback(lambda x: g_app._frame.set_undo_state(x))
    if len(sys.argv) > 1:
        load_project(sys.argv[1])
    else:
        new_project()
    g_app.MainLoop()

