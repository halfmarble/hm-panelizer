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


from AppSettings import *
from MouseBiteWidget import *
from PcbShape import *


class PcbGap:

    # shape1 is either the bottom or left
    # shape2 is either top or right
    def __init__(self, panel, root, horizontal, bites_count, shape1, shape2):
        self._panel = panel
        self._root = root
        self._horizontal = horizontal
        self._bites_count = bites_count
        self._shape1 = shape1
        self._shape2 = shape2
        self._main_shape = None
        self._bottom_shape = None
        self._bottom_shape = None

        self._bites = []
        self._gap_start = 0
        self._gap_end = 0
        self._gap_width = 0
        self._bite_width = 0

        self._main_shape = self._shape1
        if not self._main_shape.is_of_kind(PcbKind.main):
            self._main_shape = self._shape2
        self._bottom_shape = self._shape1

        for i in range(self._bites_count):
            slide = (float(i + 1) / float(self._bites_count + 1))
            self._bites.append(MouseBiteWidget(self, root, self._horizontal, slide))

    def layout(self):
        scale = self._panel.scale
        scale_mm = self._panel.pixels_per_cm * scale / 10.0

        gap = (AppSettings.gap * scale_mm)
        width = (AppSettings.bite * scale_mm)

        panel_ox = self._panel.origin[0]
        panel_oy = self._panel.origin[1]
        shape_ox = (self._main_shape.x * scale)
        shape_oy = ((self._shape1.y + self._shape1.height) * scale) - 2.0
        shape_w = (self._main_shape.width * scale)
        origin_x = panel_ox + shape_ox
        origin_y = panel_oy + shape_oy

        self._gap_start = origin_x
        self._gap_end = origin_x + shape_w
        self._gap_width = (self._gap_end - self._gap_start)
        self._bite_width = width

        for i in range(self._bites_count):
            bite = self._bites[i]
            slide = (bite.slide * shape_w)
            x = (origin_x + slide)
            pos = (x, origin_y)
            size = (width, gap + 3.0)
            bite.set(pos, size)

        valid = True
        for i in range(self._bites_count):
            bite = self._bites[i]
            bite.validate_pos()
            valid = valid and bite.connected
        return valid

    def connects(self, pos, length):
        if not self._shape1.connects(self._horizontal, False, pos, length):
            return False
        else:
            return self._shape2.connects(self._horizontal, True, pos, length)

    def __str__(self):
        rep = 'PcbGap'
        return rep + ' {}, {} with {} bites'.format(self._shape1, self._shape2, self._bites_count)

    def activate(self):
        for b in self._bites:
            b.activate()

    def deactivate(self):
        for b in self._bites:
            b.deactivate()

    def validate_pos(self, bite, pos):
        inside = True
        connected = True
        if self._gap_width > 0:
            if self._horizontal:
                if pos < self._gap_start:
                    inside = False
                    pos = self._gap_start
                elif pos >= self._gap_end - self._bite_width:
                    inside = False
                    pos = self._gap_end - self._bite_width
                rel_x = (pos - self._gap_start) / self._gap_width
            else:
                rel_x = 0  # TODO
            if inside:
                rel_w = self._bite_width / self._gap_width
                connected = self.connects(rel_x, rel_w)
        bite.mark_connected(inside and connected)
        self._panel.update_status()
        return pos

    def validate_layout(self):
        for b in self._bites:
            b.validate_pos()

    def validate_move(self, bite, x):
        x = self.validate_pos(bite, x)
        return (x - self._gap_start) / self._gap_width

    def bite(self, index):
        return self._bites[index]

    @property
    def bites_count(self):
        return self._bites_count

    @property
    def bite_center_offset(self):
        return self._bite_offset

    @property
    def main_shape(self):
        return self._main_shape

    @property
    def bottom_shape(self):
        return self._bottom_shape
