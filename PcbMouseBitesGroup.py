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
