#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 HalfMarble LLC
# Copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# See the License for the specific language governing permissions and
# limitations under the License.

try:
    import cairo
except ImportError:
    import cairocffi as cairo

from operator import mul
from re import S
import tempfile
import copy
import os

from hm_gerber_tool import render

from .render import GerberContext, RenderSettings
from .theme import THEMES
from ..primitives import *
from ..utils import rotate_point

from io import BytesIO


MIN_LINE_WIDTH = 0.75


class GerberCairoContext(GerberContext):

    def __init__(self, resolution=800):
        super(GerberCairoContext, self).__init__()

        self.max_size = resolution
        self.scale = None
        self.bounds = None
        self.native_origin = None
        self.native_size = None
        self.pixels_origin = None
        self.pixels_size = None

        self.output_surface_buffer = None
        self.output_surface = None
        self.output_surface_ctx = None

        self.active_surface = None
        self.active_ctx = None
        self.active_matrix = None
        self._active_matrix_base = None

        self.clip_surface = None

        self.has_bg = False

    @property
    def origin_in_pixels(self):
        return self.scale_point(self.native_origin)

    @property
    def size_in_pixels(self):
        return self.scale_point(self.native_size)

    def scale_point(self, point):
        return tuple([coord * scale for coord, scale in zip(point, self.scale)])

    def calculate_scale(self, layer, verbose):
        if self.bounds is None:
            self.bounds = layer.bounds
        if self.scale is None:
            width = self.max_size
            height = self.max_size
            x_range = [10000, -10000]
            y_range = [10000, -10000]
            if self.bounds is not None:
                layer_x, layer_y = self.bounds
                x_range[0] = min(x_range[0], layer_x[0])
                x_range[1] = max(x_range[1], layer_x[1])
                y_range[0] = min(y_range[0], layer_y[0])
                y_range[1] = max(y_range[1], layer_y[1])
                width = x_range[1] - x_range[0]
                height = y_range[1] - y_range[0]

            # protect against weirdly defined pcbs (i.e. manually created/tweaked for debugging)
            width = max(width, 1)
            height = max(height, 1)

            self.native_size = (width, height)
            self.native_origin = (self.bounds[0][0], self.bounds[1][0])

            scale = math.floor(min(float(self.max_size) / width, float(self.max_size) / height))
            self.scale = (scale, scale)

            self.pixels_origin = self.scale_point(self.native_origin)
            self.pixels_size = self.scale_point(self.native_size)

            self._active_matrix_base = cairo.Matrix(xx=1.0, yy=1.0, x0=-self.origin_in_pixels[0],
                                                    y0=-self.origin_in_pixels[1])

        if verbose:
            print('\n[Render]: calculate_scale()')
            print('[Render]:   x_range,y_range: {},{}'.format(x_range, y_range))
            print('[Render]:   width,height: {},{}'.format(width, height))
            print('[Render]:   self.native_size: {}'.format(self.native_size))
            print('[Render]:   self.native_origin: {}'.format(self.native_origin))
            print('[Render]:   self.scale: {}'.format(self.scale))
            print('[Render]:   self.pixels_origin: {}'.format(self.pixels_origin))
            print('[Render]:   self.pixels_size: {}'.format(self.pixels_size))
            print('[Render]:   self._active_matrix_base: {}'.format(self._active_matrix_base))

    def clear(self):
        self.scale = None
        self.native_origin = None
        self.native_size = None
        self.pixels_origin = None
        self.pixels_size = None

        self.output_surface = None
        self.output_surface_ctx = None
        self.output_surface_buffer = None

        self.has_bg = False
        self._active_matrix_base = None

    def setup(self, layer, bounds=None, verbose=False):
        if bounds is not None:
            self.bounds = bounds
        self.calculate_scale(layer, verbose)

        self.output_surface_buffer = tempfile.NamedTemporaryFile()
        self.output_surface = cairo.SVGSurface(self.output_surface_buffer, self.pixels_size[0], self.pixels_size[1])
        self.output_surface_ctx = cairo.Context(self.output_surface)

    def render_layer(self, layer, filename=None, fgsettings=None, bgsettings=None, background=True, verbose=False):
        if verbose:
            print('\n[Render]: render_layer()')
            print('[Render]:   layer: {}'.format(layer))
            print('[Render]:   filename: {}'.format(filename))

        if fgsettings is None:
            fgsettings = THEMES['default'].get(layer.layer_class, RenderSettings())

        if bgsettings is None:
            bgsettings = THEMES['default'].get('background', RenderSettings())

        self.clear()
        self.setup(layer, None, verbose)

        if background and not self.has_bg:
            if verbose:
                print('[Render]:   Rendering Background.')
            self.paint_background(bgsettings)

        if verbose:
            print('[Render]:   Rendering {} Layer.'.format(layer.layer_class))

        self._render_layer(layer, fgsettings)

        if filename is not None:
            self.dump(filename, verbose)

    def _add_arc(self, arc, ctx):
        center = self.scale_point(arc.center)
        radius = self.scale[0] * arc.radius
        two_pi = 2 * math.pi
        angle1 = (arc.start_angle + two_pi) % two_pi
        angle2 = (arc.end_angle + two_pi) % two_pi
        if angle1 == angle2 and arc.quadrant_mode != 'single-quadrant':
            # Make the angles slightly different otherwise Cario will draw nothing
            angle2 -= 0.000000001
        if isinstance(arc.aperture, Circle):
            width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.1
        else:
            width = max(arc.aperture.width, arc.aperture.height, 0.1)
        ctx.set_line_width(width * self.scale[0])
        ctx.set_line_cap(cairo.LINE_CAP_ROUND if isinstance(arc.aperture, Circle) else cairo.LINE_CAP_SQUARE)
        if arc.direction == 'counterclockwise':
            ctx.arc(center[0], center[1], radius, angle1, angle2)
        else:
            ctx.arc_negative(center[0], center[1], radius, angle1, angle2)

    def _add_line(self, line, ctx):
        end = self.scale_point(line.end)
        if isinstance(line.aperture, Circle):
            width = line.aperture.diameter
            ctx.set_line_width(width * self.scale[0])
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.line_to(*end)
        elif hasattr(line, 'vertices') and line.vertices is not None:
            points = [self.scale_point(x) for x in line.vertices]
            ctx.set_line_width(0)
            for point in points:
                ctx.line_to(*point)

    @classmethod
    def _are_equal(cls, p1, p2):
        error = 0.01
        return (abs(p1[0] - p2[0]) <= error) and (abs(p1[1] - p2[1]) <= error)

    def _are_connected_end_start(self, one, two):
        if one is None:
            return False
        elif two is None:
            return False
        else:
            connected = self._are_equal(one.end, two.start)
            return connected

    def _are_backwards_connected(self, one, two):
        if one is None:
            return False
        elif two is None:
            return False
        else:
            connected = self._are_equal(one.end, two.end)
            return connected

    @classmethod
    def _reverse_prim(cls, prim):
        prim_reversed = copy.copy(prim)
        prim_reversed.start = prim.end
        prim_reversed.end = prim.start
        if isinstance(prim_reversed, Arc):
            arc = prim_reversed
            if arc.direction == 'counterclockwise':
                arc.direction = 'clockwise'
            else:
                arc.direction = 'counterclockwise'
        return prim_reversed

    def _find_next_prim(self, remaining, last_prim):
        next_prim = None
        next_prim_reversed = None
        for prim in remaining:
            if self._are_connected_end_start(last_prim, prim):
                next_prim = prim
                break  # found next segment
        if next_prim is None:
            for prim in remaining:
                if self._are_backwards_connected(last_prim, prim):
                    next_prim = prim
                    next_prim_reversed = self._reverse_prim(next_prim)
                    break  # found backwards next segment
        return [next_prim, next_prim_reversed]

    @classmethod
    def _report_outline_disconnected(cls, original, chain, remaining, last_prim):
        print('\nERROR: Could not find next connected segment {} (path unconnected?)'.format(last_prim))
        print(' original segments [{}]:'.format(len(original)))
        for prim in original:
            print('  {}'.format(prim))
        print(' chain so far [{}]:'.format(len(chain)))
        for prim in chain:
            print('  {}'.format(prim))
        print(' remaining[{}]:'.format(len(remaining)))
        for prim in remaining:
            print('  {}'.format(prim))
        print('')

    @classmethod
    def _add_prim(cls, chain, next_prim, next_prim_reversed):
        if next_prim_reversed is not None:
            next_prim = next_prim_reversed
        chain.append(copy.copy(next_prim))
        return next_prim

    def _get_outline_segments(self, segments, verbose):
        _all = []
        _chain = []
        _current_prim = segments[0]
        _chain.append(copy.copy(_current_prim))

        segments.remove(_current_prim)
        _remaining = segments

        while len(_remaining) > 0:
            _found_prim = None
            _found_prim_reversed = None

            _found = self._find_next_prim(_remaining, _current_prim)
            _found_prim = _found[0]
            _found_prim_reversed = _found[1]

            if _found_prim is not None:
                _remaining.remove(_found_prim)
                _current_prim = self._add_prim(_chain, _found_prim, _found_prim_reversed)
            else:
                # did not find next primitive that connects to "remaining" chain
                # check to see if it connect anywhere to our current chain
                # (back to first segment perhaps?)
                _found = self._find_next_prim(_chain, _current_prim)
                _found_prim = _found[0]
                _found_prim_reversed = _found[1]
                if _found_prim is not None:
                    _all.append(copy.copy(_chain))
                    _chain.clear()
                    _current_prim = _remaining[0]
                    _chain.append(copy.copy(_current_prim))
                    _remaining.remove(_current_prim)
                else:
                    self._report_outline_disconnected(segments, _chain, _remaining, _current_prim)
                    break

        if len(_chain) > 0:
            _all.append(_chain)

        _all.sort(key=len, reverse=True)  # sort based on length of chains

        # find the chain with the biggest area (that's the most outside outline path)
        _index = 0
        _max_index = _index
        _max_area = 0
        for _chain in _all:
            _x_min = 1000000
            _y_min = 1000000
            _x_max = -1000000
            _y_max = -1000000
            for prim in _chain:
                _x_min = min(_x_min, prim.start[0])
                _y_min = min(_y_min, prim.start[1])
                _x_max = max(_x_max, prim.end[0])
                _y_max = max(_y_max, prim.end[1])
            _width = abs(_x_max - _x_min)
            _height = abs(_y_max - _y_min)
            _area = _width * _height
            if _area > _max_area:
                _max_area = _area
                _max_index = _index
            _index += 1

        _sorted = [_all[_max_index]]
        _all.remove(_sorted[0])
        for _chain in _all:
            _sorted.append(_chain)
        _all = []

        return _sorted

    def _render_chain(self, chain):
        first = chain[0]
        first_start = self.scale_point(first.start)
        self.active_ctx.move_to(*first_start)
        for prim in chain:
            if isinstance(prim, Line):
                self._add_line(prim, self.active_ctx)
            elif isinstance(prim, Arc):
                self._add_arc(prim, self.active_ctx)
            else:
                print('WARNING: Unhandled primitive while clipping! {}'.format(prim))
        self.active_ctx.close_path()
        self.active_ctx.fill_preserve()
        self.active_ctx.stroke()

    @classmethod
    def mm(cls, is_metric, value):
        if is_metric:
            return value
        else:
            return value / 25.4

    def get_outline_mask(self, layer, filename=None, bounds=None, verbose=False):
        if layer is None:
            print('WARNING: can not get outline from None layer')
            return

        if verbose:
            print('layer {}'.format(layer))
            print('original segments chain count: {}'.format(len(layer.primitives)))
            for prim in layer.primitives:
                print('  {}'.format(prim))

        self.clip_surface = None
        _all = self._get_outline_segments(copy.copy(layer.primitives), verbose)
        if _all is None:
            return None

        if verbose:
            print('sorted segments chain count: {}'.format(len(_all)))
            for chain in _all:
                print('  chain length {}'.format(len(chain)))
                for segment in chain:
                    print('    {}'.format(segment))

        self.clear()
        self.setup(layer, bounds, verbose)

        self.clip_surface = self.new_render_layer(mirror=False, flip=True)
        _passes = 0
        for chain in _all:
            if _passes == 0:
                self.active_ctx.set_operator(cairo.OPERATOR_OVER)
                self.active_ctx.set_source_rgba(0, 0, 0, 1)
            else:
                self.active_ctx.set_operator(cairo.OPERATOR_CLEAR)
                self.active_ctx.set_source_rgba(1, 1, 1, 1)
            self._render_chain(chain)
            _passes = _passes + 1
        self.color = (0, 0, 0)
        self.alpha = 1
        self.flatten_render_layer()

        if filename is not None:
            self.dump(filename+'.png')

        m = layer.metric
        xrange = bounds[0]
        yrange = bounds[1]
        bsx = self.mm(m, xrange[0])
        bsy = self.mm(m, yrange[0])
        bex = self.mm(m, xrange[1])
        bey = self.mm(m, yrange[1])
        w = bex - bsx
        h = bey - bsy
        _string = 'Bounds: {}, {}, {}, {}\n'.format(bsx, bsy, bex, bey)
        _string += 'Size: {}, {}\n'.format(w, h)
        for chain in _all:
            _string += 'Length: {}\n'.format(len(chain))
            for s in chain:
                if isinstance(s, Line):
                    sx = self.mm(m, s.start[0]) - bsx
                    sy = self.mm(m, s.start[1]) - bsy
                    ex = self.mm(m, s.end[0]) - bsx
                    ey = self.mm(m, s.end[1]) - bsy
                    _string += 'Line: {}, {}, {}, {}\n'.format(sx, sy, ex, ey)
                if isinstance(s, Arc):
                    sx = self.mm(m, s.start[0]) - bsx
                    sy = self.mm(m, s.start[1]) - bsy
                    ex = self.mm(m, s.end[0]) - bsx
                    ey = self.mm(m, s.end[1]) - bsy
                    cx = self.mm(m, s.center[0]) - bsx
                    cy = self.mm(m, s.center[1]) - bsy
                    r = self.mm(m, s.radius)
                    sa = self.mm(m, s.start_angle)
                    ea = self.mm(m, s.end_angle)
                    _string += 'Arc: {}, {}, {}, {}, {}, {}, {}, {}, {}\n'.format(sx, sy, ex, ey, cx, cy, r, sa, ea)

        if filename is not None:
            with open(filename + '.txt', "w") as text_file:
                text_file.write(_string)

        return _string

    def render_clipped_layer(self, layer, clip_to_outline, filename=None, theme=THEMES['default'], bounds=None,
                             background=True, verbose=False):
        if verbose:
            print('\n[Render]: render_clipped_layer()')
            print('[Render]:   layer: {}'.format(layer))
            print('[Render]:   filename: {}'.format(filename))
            print('[Render]:   theme: {}'.format(theme))
            print('[Render]:   max_size: {}'.format(self.max_size))
            print('[Render]:   bounds: {}'.format(bounds))

        self.clear()
        self.setup(layer, bounds, verbose)

        bgsettings = theme['background']

        mirror = False
        fgsettings = theme.get(layer.layer_class, RenderSettings())
        self.render_layer(layer, fgsettings=fgsettings, bgsettings=bgsettings, background=background, verbose=verbose)
        mirror = mirror or fgsettings.mirror

        if verbose:
            print('[Render]:   mirror: {}'.format(mirror))

        self.new_render_layer(mirror=False, flip=True)
        self.active_ctx.translate(self.origin_in_pixels[0], self.origin_in_pixels[1])
        self.active_ctx.set_operator(cairo.OPERATOR_OVER)
        self.active_ctx.set_source_surface(self.output_surface)
        self.active_ctx.paint()

        if mirror:
            self.output_surface_ctx.scale(-1.0, 1.0)
            self.output_surface_ctx.translate(-self.size_in_pixels[0], 0.0)
        self.output_surface_ctx.set_operator(cairo.OPERATOR_CLEAR)
        self.output_surface_ctx.set_source_rgba(1, 1, 1, 1)
        self.output_surface_ctx.paint()
        self.output_surface_ctx.set_operator(cairo.OPERATOR_OVER)
        self.output_surface_ctx.set_source_surface(self.active_surface)

        if clip_to_outline:
            if self.clip_surface is None:
                print(
                    "\nWARNING outline clip requested, but not generated yet [did you call ctx.clip_outline() and did it work?]\n")
            else:
                self.output_surface_ctx.mask_surface(self.clip_surface)
        else:
            self.output_surface_ctx.paint()

        if filename is not None:
            self.dump(filename + '.png', verbose)

    def dump(self, filename=None, verbose=False):
        """ Save image as `filename`
        """
        try:
            is_svg = os.path.splitext(filename.lower())[1] == '.svg'
        except:
            is_svg = False
        if verbose:
            print('[Render]: Writing image to {}'.format(filename))
        if is_svg:
            self.output_surface.finish()
            self.output_surface_buffer.flush()
            with open(filename, "wb") as f:
                self.output_surface_buffer.seek(0)
                f.write(self.output_surface_buffer.read())
                f.flush()
        else:
            return self.output_surface.write_to_png(filename)

    def dump_str(self):
        """ Return a byte-string containing the rendered image.
        """
        fobj = BytesIO()
        self.output_surface.write_to_png(fobj)
        return fobj.getvalue()

    def dump_svg_str(self):
        """ Return a string containg the rendered SVG.
        """
        self.output_surface.finish()
        self.output_surface_buffer.flush()
        return self.output_surface_buffer.read()

    def _new_mask(self):
        class Mask:
            def __enter__(msk):
                size_in_pixels = self.size_in_pixels
                msk.surface = cairo.SVGSurface(None, size_in_pixels[0], size_in_pixels[1])
                msk.ctx = cairo.Context(msk.surface)
                return msk

            def __exit__(msk, exc_type, exc_val, traceback):
                if hasattr(msk.surface, 'finish'):
                    msk.surface.finish()

        return Mask()

    def _render_layer(self, layer, settings):
        self.invert = settings.invert
        self.new_render_layer(mirror=settings.mirror)
        for prim in layer.primitives:
            #print('{}'.format(prim))
            self.render(prim)
        self.flatten_render_layer(settings.color, settings.alpha)

    def _render_line(self, line, color):
        start = self.scale_point(line.start)
        end = self.scale_point(line.end)
        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if line.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)

        if isinstance(line.aperture, Circle):
            width = line.aperture.diameter
            width = max(width * self.scale[0], MIN_LINE_WIDTH)
            self.active_ctx.set_line_width(width)
            self.active_ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            self.active_ctx.move_to(*start)
            self.active_ctx.line_to(*end)
            self.active_ctx.stroke()

        elif hasattr(line, 'vertices') and line.vertices is not None:
            points = [self.scale_point(x) for x in line.vertices]
            self.active_ctx.set_line_width(0)
            self.active_ctx.move_to(*points[-1])
            for point in points:
                self.active_ctx.line_to(*point)
            self.active_ctx.fill()

    def _render_arc(self, arc, color):
        center = self.scale_point(arc.center)
        start = self.scale_point(arc.start)
        end = self.scale_point(arc.end)
        radius = self.scale[0] * arc.radius
        two_pi = 2 * math.pi
        angle1 = (arc.start_angle + two_pi) % two_pi
        angle2 = (arc.end_angle + two_pi) % two_pi
        if angle1 == angle2 and arc.quadrant_mode != 'single-quadrant':
            # Make the angles slightly different otherwise Cario will draw nothing
            angle2 -= 0.000000001
        if isinstance(arc.aperture, Circle):
            width = arc.aperture.diameter if arc.aperture.diameter != 0 else 0.1
        else:
            width = max(arc.aperture.width, arc.aperture.height, 0.1)
        width = max(width * self.scale[0], MIN_LINE_WIDTH)

        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if arc.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)
        self.active_ctx.set_line_width(width)
        self.active_ctx.set_line_cap(cairo.LINE_CAP_ROUND if isinstance(arc.aperture, Circle) else cairo.LINE_CAP_SQUARE)
        self.active_ctx.move_to(*start)  # You actually have to do this...
        if arc.direction == 'counterclockwise':
            self.active_ctx.arc(center[0], center[1], radius, angle1, angle2)
        else:
            self.active_ctx.arc_negative(center[0], center[1], radius, angle1, angle2)
        self.active_ctx.move_to(*end)  # ...lame
        self.active_ctx.stroke()

    def _render_region(self, region, color):
        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if region.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)

        self.active_ctx.set_line_width(0)
        self.active_ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.active_ctx.move_to(*self.scale_point(region.primitives[0].start))
        for prim in region.primitives:
            if isinstance(prim, Line):
                self.active_ctx.line_to(*self.scale_point(prim.end))
            else:
                center = self.scale_point(prim.center)
                radius = self.scale[0] * prim.radius
                angle1 = prim.start_angle
                angle2 = prim.end_angle
                if prim.direction == 'counterclockwise':
                    self.active_ctx.arc(center[0], center[1], radius, angle1, angle2)
                else:
                    self.active_ctx.arc_negative(center[0], center[1], radius, angle1, angle2)
        self.active_ctx.fill()

    def _render_circle(self, circle, color):
        center = self.scale_point(circle.position)
        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if circle.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)

        self.active_ctx.set_line_width(0)
        self.active_ctx.arc(center[0], center[1], (circle.radius * self.scale[0]), 0, (2 * math.pi))
        self.active_ctx.fill()

        if hasattr(circle, 'hole_diameter') and circle.hole_diameter is not None and circle.hole_diameter > 0:
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR)
            self.active_ctx.arc(center[0], center[1], circle.hole_radius * self.scale[0], 0, 2 * math.pi)
            self.active_ctx.fill()

        if (hasattr(circle, 'hole_width') and hasattr(circle, 'hole_height')
                and circle.hole_width is not None and circle.hole_height is not None
                and circle.hole_width > 0 and circle.hole_height > 0):
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR
                                         if circle.level_polarity == 'dark' and (not self.invert)
                                         else cairo.OPERATOR_OVER)
            width, height = self.scale_point((circle.hole_width, circle.hole_height))
            lower_left = rotate_point((center[0] - width / 2.0, center[1] - height / 2.0), circle.rotation, center)
            lower_right = rotate_point((center[0] + width / 2.0, center[1] - height / 2.0), circle.rotation, center)
            upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0), circle.rotation, center)
            upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0), circle.rotation, center)
            points = (lower_left, lower_right, upper_right, upper_left)
            self.active_ctx.move_to(*points[-1])
            for point in points:
                self.active_ctx.line_to(*point)
            self.active_ctx.fill()

    def _render_rectangle(self, rectangle, color):
        lower_left = self.scale_point(rectangle.lower_left)
        width, height = tuple([abs(coord) for coord in self.scale_point((rectangle.width, rectangle.height))])
        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if rectangle.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)

        self.active_ctx.set_line_width(0)
        self.active_ctx.rectangle(lower_left[0], lower_left[1], width, height)
        self.active_ctx.fill()

        center = self.scale_point(rectangle.position)
        if rectangle.hole_diameter > 0:
            # Render the center clear
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR
                                         if rectangle.level_polarity == 'dark' and (not self.invert)
                                         else cairo.OPERATOR_OVER)

            self.active_ctx.arc(center[0], center[1], rectangle.hole_radius * self.scale[0], 0, 2 * math.pi)
            self.active_ctx.fill()

        if rectangle.hole_width > 0 and rectangle.hole_height > 0:
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR
                                         if rectangle.level_polarity == 'dark' and (not self.invert)
                                         else cairo.OPERATOR_OVER)
            width, height = self.scale_point((rectangle.hole_width, rectangle.hole_height))
            lower_left = rotate_point((center[0] - width / 2.0, center[1] - height / 2.0), rectangle.rotation, center)
            lower_right = rotate_point((center[0] + width / 2.0, center[1] - height / 2.0), rectangle.rotation, center)
            upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0), rectangle.rotation, center)
            upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0), rectangle.rotation, center)
            points = (lower_left, lower_right, upper_right, upper_left)
            self.active_ctx.move_to(*points[-1])
            for point in points:
                self.active_ctx.line_to(*point)
            self.active_ctx.fill()

    def _render_obround(self, obround, color):
        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if obround.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)

        self.active_ctx.set_line_width(0)

        # Render circles
        for circle in (obround.subshapes['circle1'], obround.subshapes['circle2']):
            center = self.scale_point(circle.position)
            self.active_ctx.arc(center[0], center[1], (circle.radius * self.scale[0]), 0, (2 * math.pi))
            self.active_ctx.fill()

        # Render Rectangle
        rectangle = obround.subshapes['rectangle']
        lower_left = self.scale_point(rectangle.lower_left)
        width, height = tuple([abs(coord) for coord in self.scale_point((rectangle.width, rectangle.height))])
        self.active_ctx.rectangle(lower_left[0], lower_left[1], width, height)
        self.active_ctx.fill()

        center = self.scale_point(obround.position)
        if obround.hole_diameter > 0:
            # Render the center clear
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR)
            self.active_ctx.arc(center[0], center[1], obround.hole_radius * self.scale[0], 0, 2 * math.pi)
            self.active_ctx.fill()

        if obround.hole_width > 0 and obround.hole_height > 0:
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR
                                         if rectangle.level_polarity == 'dark' and (not self.invert)
                                         else cairo.OPERATOR_OVER)
            width, height = self.scale_point((obround.hole_width, obround.hole_height))
            lower_left = rotate_point((center[0] - width / 2.0, center[1] - height / 2.0),
                                      obround.rotation, center)
            lower_right = rotate_point((center[0] + width / 2.0, center[1] - height / 2.0),
                                       obround.rotation, center)
            upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0),
                                      obround.rotation, center)
            upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0),
                                       obround.rotation, center)
            points = (lower_left, lower_right, upper_right, upper_left)
            self.active_ctx.move_to(*points[-1])
            for point in points:
                self.active_ctx.line_to(*point)
            self.active_ctx.fill()

    def _render_polygon(self, polygon, color):
        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if polygon.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)

        vertices = polygon.vertices
        self.active_ctx.set_line_width(0)
        self.active_ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        # Start from before the end so it is easy to iterate and make sure
        # it is closed
        self.active_ctx.move_to(*self.scale_point(vertices[-1]))
        for v in vertices:
            self.active_ctx.line_to(*self.scale_point(v))
        self.active_ctx.fill()

        center = self.scale_point(polygon.position)
        if polygon.hole_radius > 0:
            # Render the center clear
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR
                                         if polygon.level_polarity == 'dark' and (not self.invert)
                                         else cairo.OPERATOR_OVER)
            self.active_ctx.set_line_width(0)
            self.active_ctx.arc(center[0], center[1], polygon.hole_radius * self.scale[0], 0, 2 * math.pi)
            self.active_ctx.fill()

        if polygon.hole_width > 0 and polygon.hole_height > 0:
            self.active_ctx.set_operator(cairo.OPERATOR_CLEAR
                                         if polygon.level_polarity == 'dark' and (not self.invert)
                                         else cairo.OPERATOR_OVER)
            width, height = self.scale_point((polygon.hole_width, polygon.hole_height))
            lower_left = rotate_point((center[0] - width / 2.0, center[1] - height / 2.0),
                                      polygon.rotation, center)
            lower_right = rotate_point((center[0] + width / 2.0, center[1] - height / 2.0),
                                       polygon.rotation, center)
            upper_left = rotate_point((center[0] - width / 2.0, center[1] + height / 2.0),
                                      polygon.rotation, center)
            upper_right = rotate_point((center[0] + width / 2.0, center[1] + height / 2.0),
                                       polygon.rotation, center)
            points = (lower_left, lower_right, upper_right, upper_left)
            self.active_ctx.move_to(*points[-1])
            for point in points:
                self.active_ctx.line_to(*point)
            self.active_ctx.fill()

    def _render_drill(self, circle, color=None):
        color = color if color is not None else self.drill_color
        self._render_circle(circle, color)

    def _render_slot(self, slot, color):
        start = map(mul, slot.start, self.scale)
        end = map(mul, slot.end, self.scale)

        width = slot.diameter

        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if slot.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)

        self.active_ctx.set_line_width(width * self.scale[0])
        self.active_ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.active_ctx.move_to(*start)
        self.active_ctx.line_to(*end)
        self.active_ctx.stroke()

    def _render_amgroup(self, amgroup, color):
        for primitive in amgroup.primitives:
            primitive.level_polarity = amgroup.level_polarity
            self.render(primitive)

    def _render_test_record(self, primitive, color):
        position = [pos + origin for pos, origin in zip(primitive.position, self.native_origin)]
        self.active_ctx.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.active_ctx.set_font_size(13)
        self._render_circle(Circle(position, 0.015), color)
        self.active_ctx.set_operator(cairo.OPERATOR_OVER
                                     if primitive.level_polarity == 'dark' and (not self.invert)
                                     else cairo.OPERATOR_CLEAR)
        self.active_ctx.move_to(*[self.scale[0] * (coord + 0.015) for coord in position])
        self.active_ctx.scale(1, -1)
        self.active_ctx.show_text(primitive.net_name)
        self.active_ctx.scale(1, -1)

    def new_render_layer(self, mirror=False, flip=False):
        matrix = copy.copy(self._active_matrix_base)
        surface = cairo.SVGSurface(None, self.size_in_pixels[0], self.size_in_pixels[1])
        ctx = cairo.Context(surface)

        if self.invert:
            ctx.set_source_rgba(0, 0, 0, 1)
            ctx.set_operator(cairo.OPERATOR_OVER)
            ctx.paint()
        if mirror:
            matrix.xx = -1.0
            matrix.x0 = self.origin_in_pixels[0] + self.size_in_pixels[0]
        if flip:
            matrix.yy = -1.0
            matrix.y0 = self.origin_in_pixels[1] + self.size_in_pixels[1]

        self.active_surface = surface
        self.active_ctx = ctx
        self.active_matrix = matrix
        self.active_ctx.set_matrix(matrix)

        return self.active_surface

    def flatten_render_layer(self, color=None, alpha=None):
        color = color if color is not None else self.color
        alpha = alpha if alpha is not None else self.alpha
        self.output_surface_ctx.set_source_rgba(color[0], color[1], color[2], alpha)
        self.output_surface_ctx.mask_surface(self.active_surface)
        self.active_ctx = None
        self.active_surface = None
        self.active_matrix = None

    def paint_background(self, settings=None):
        color = settings.color if settings is not None else self.background_color
        alpha = settings.alpha if settings is not None else 1.0
        if not self.has_bg:
            self.has_bg = True
            self.output_surface_ctx.set_source_rgba(color[0], color[1], color[2], alpha)
            self.output_surface_ctx.paint()
