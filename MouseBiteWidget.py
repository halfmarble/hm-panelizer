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


from Constants import *
from OffScreenScatter import *
from PcbMouseBites import *


class MouseBitesRenderer:

    def __init__(self, owner):
        self._owner = owner

    def paint(self, fbo):
        with fbo:
            PcbMouseBites.paint(self._owner.color, pos=(0, 0), size=self._owner.size)


class MouseBiteWidget(OffScreenScatter):

    def __init__(self, gap, root, horizontal, slide):
        self._gap = gap
        self._root = root
        self._horizontal = horizontal
        self._slide = slide

        self._connected = False
        self._base_color = PCB_MASK_COLOR
        self._moving_color = PCB_BITE_GOOD_COLOR
        self._disconnected_color = PCB_BITE_BAD_COLOR
        self._moving = False

        super(MouseBiteWidget, self).__init__(MouseBitesRenderer(self))

        if horizontal:
            self.do_translation_x = True
            self.do_translation_y = False
        else:
            self.do_translation_x = False
            self.do_translation_y = True

        self._group = None
        self._start = (0, 0)

    def set(self, pos, size):
        self.pos = pos
        self.size = size
        self.paint()

    def repaint(self):
        self.paint()
        # TODO: is there a better way to repaint?
        if self.parent is not None:
            self.deactivate()
            self.activate()

    def validate_pos(self):
        # TODO" assumes horizontal layout
        self._gap.validate_pos(self, self.pos[0])

    def start_move(self):
        self._moving = True
        self._start = self.pos
        self.validate_pos()
        self.repaint()

    def end_move(self):
        self._moving = False
        self._slide = self._gap.validate_move(self, self.pos[0])
        self._gap.layout()  # constrain the bite location to lie within the gap
        self.repaint()

    def move_by(self, dx, dy):
        if self._moving:
            position = (self._start[0] + dx, self._start[1] + dy)
            self.pos = position
            self._slide = self._gap.validate_move(self, self.pos[0])

    def on_touch_down(self, touch):
        handled = super(MouseBiteWidget, self).on_touch_down(touch)
        if handled:
            self.start_move()
            for b in self._group:
                if b is not self:
                    b.start_move()
        return handled

    def on_touch_move(self, touch):
        handled = super(MouseBiteWidget, self).on_touch_move(touch)
        if self._moving:
            self._gap.validate_pos(self, self.pos[0])
            dx = self.pos[0] - self._start[0]
            dy = self.pos[1] - self._start[1]
            for b in self._group:
                if b is not self:
                    b.move_by(dx, dy)
        return handled

    def on_touch_up(self, touch):
        handled = super(MouseBiteWidget, self).on_touch_up(touch)
        if self._moving:
            self.end_move()
            for b in self._group:
                if b is not self:
                    b.end_move()
        return handled

    def assign_group(self, group):
        self._group = group

    def activate(self):
        self._root.add_widget(self)

    def deactivate(self):
        self._root.remove_widget(self)

    def mark_connected(self, value):
        update = (self._connected != value)
        self._connected = value
        if update:
            self.repaint()

    @property
    def position(self):
        return self.pos

    @property
    def slide(self):
        return self._slide

    @property
    def connected(self):
        return self._connected

    @property
    def color(self):
        if self._moving:
            if not self._connected:
                return self._disconnected_color
            else:
                return self._moving_color
        else:
            if not self._connected:
                return self._disconnected_color
            else:
                return self._base_color


