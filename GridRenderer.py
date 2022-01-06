# Copyright 2021,2022 HalfMarble LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# See the License for the specific language governing permissions and
# limitations under the License.


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
