# The MIT License (MIT)

# Copyright 2021,2022 HalfMarble LLC

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import math
from kivy.graphics import Line, ClearBuffers, ClearColor
from Constants import *


class GridRenderer:

    def __init__(self):
        self._pixels_per_cm = 1.0

    def set_pixels_per_cm(self, pixels_per_cm):
        self._pixels_per_cm = pixels_per_cm

    def paint(self, fbo, size):
        cx = size[0] / 2.0
        cy = size[1] / 2.0
        line_count_x = int(((math.floor(size[0] / self._pixels_per_cm)) / 2.0) + 1.0)
        line_count_y = int(((math.floor(size[1] / self._pixels_per_cm)) / 2.0) + 1.0)

        with fbo:
            c = GRID_BACKGROUND_COLOR
            ClearColor(c.r, c.g, c.b, c.a)
            ClearBuffers()

            x = 0.0
            sy = 0.0
            ey = size[1]
            c = GRID_MAJOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            Line(points=[cx, sy, cx, ey])
            x += self._pixels_per_cm
            c = GRID_MINOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            for i in range(0, line_count_x):
                x_int = int(round(x))
                Line(points=[cx + x_int, sy, cx + x_int, ey])
                Line(points=[cx - x_int, sy, cx - x_int, ey])
                x += self._pixels_per_cm

            y = 0.0
            sx = 0.0
            ex = size[0]
            c = GRID_MAJOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            Line(points=[sx, cy, ex, cy])
            y += self._pixels_per_cm
            c = GRID_MINOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            for i in range(0, line_count_y):
                y_int = int(round(y))
                Line(points=[sx, cy + y_int, ex, cy + y_int])
                Line(points=[sx, cy - y_int, ex, cy - y_int])
                y += self._pixels_per_cm
