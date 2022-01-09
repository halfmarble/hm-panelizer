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


from kivy.graphics import Rectangle, Translate, Rotate, PushMatrix, PopMatrix

from Array2D import *
from PcbGap import *
from PcbPanel import *


class PcbMouseBitesGroup:

    def assign_groups(self, count, columns, rows, gaps):
        for i in range(count):
            group = []
            for r in range(0, rows):
                for c in range(0, columns):
                    gap = gaps.get(c, r)
                    bite = gap.bite(i)
                    group.append(bite)
                    self._bites.append(bite)
            for r in range(0, rows):
                for c in range(0, columns):
                    gap = gaps.get(c, r)
                    bite = gap.bite(i)
                    bite.assign_group(group)

    def __init__(self, panel, root, shapes, bites_count):
        self._bites = []
        self._shapes = shapes
        #self._shapes.print('  ')

        if bites_count > 0:
            columns = self._shapes.width
            rows = (self._shapes.height - 1)
            self._horizontal = Array2D(columns, rows)
            for r in range(0, rows):
                for c in range(0, columns):
                    bottom = self._shapes.get(c, r)
                    top = self._shapes.get(c, r + 1)
                    gap = PcbGap(panel, root, True, bites_count, bottom, top)
                    self._horizontal.put(c, r, gap)
            #print(' horizontal gaps:')
            #self._horizontal.print('  ')
            self.assign_groups(bites_count, columns, rows, self._horizontal)
        else:
            self._horizontal = Array2D(0, 0)

    def activate(self):
        # TODO: implement Array2D iterator and use it here
        for c in range(self._horizontal.width):
            for r in range(self._horizontal.height):
                gap = self._horizontal.get(c, r)
                gap.activate()

    def deactivate(self):
        # TODO: implement Array2D iterator and use it here
        for c in range(self._horizontal.width):
            for r in range(self._horizontal.height):
                gap = self._horizontal.get(c, r)
                gap.deactivate()

    def layout(self):
        valid = True
        # TODO: implement Array2D iterator and use it here
        for c in range(self._horizontal.width):
            for r in range(self._horizontal.height):
                gap = self._horizontal.get(c, r)
                # workaround for "value and function()" optimizing out function() if value == False
                # valid = valid and gap.layout()
                v = gap.layout()
                valid = valid and v
        return valid

    def get_row_xs_mm(self, scale):
        xs_mm = []
        gap = self._horizontal.get(0, 0)
        main = gap.main_shape
        main_origin = main.get_origin_mm(scale)
        main_size = main.get_size_mm(scale)
        for b in range(gap.bites_count):
            bite = gap.bite(b)
            origin_x = main_origin[0] + (bite.slide * main_size[0])
            xs_mm.append(origin_x)
        return xs_mm

    def get_origins_mm(self, scale):
        origins = []
        # TODO: implement Array2D iterator and use it here
        for r in range(self._horizontal.height):
            origins_row = []
            for c in range(self._horizontal.width):
                gap = self._horizontal.get(c, r)
                main = gap.main_shape
                main_origin = main.get_origin_mm(scale)
                main_size = main.get_size_mm(scale)
                bottom = gap.bottom_shape
                bottom_origin = bottom.get_origin_mm(scale)
                bottom_size = bottom.get_size_mm(scale)
                for b in range(gap.bites_count):
                    bite = gap.bite(b)
                    origin_x = main_origin[0] + (bite.slide * main_size[0])
                    origin_y = bottom_origin[1] + bottom_size[1]
                    origins_row.append((origin_x, origin_y))
            origins.append(origins_row)
        return origins

    def validate_layout(self):
        valid = True
        for b in self._bites:
            valid = valid and b.connected
        return valid
