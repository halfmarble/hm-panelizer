# Copyright 2021 HalfMarble LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# See the License for the specific language governing permissions and
# limitations under the License.

from kivy.graphics import Color, Rectangle
from kivy.graphics import Translate, Rotate, PushMatrix, PopMatrix

from Constants import *
from OffScreenScatter import *


class PcbPanel(OffScreenScatter):

    def __init__(self, client, size, shader, **kwargs):
        super(PcbPanel, self).__init__(client, size, shader, **kwargs)

        self._active = False
        self._size_mm = (0, 0)
        self._size_pixels = (0, 0)
        self._layouts_x = []
        self._layouts_y = []
        self._columns = 0
        self._rows = 0

    def add_to(self, root):
        if not self._active:
            root.add_widget(self)
            self._active = True

    def remove_from(self, root):
        if self._active:
            root.remove_widget(self)
            self._active = False

    def panelize(self, columns, rows, angle):
        self._columns = columns
        self._rows = rows
        #self._angle = 0.0
        self._angle = angle

        self._layouts_x.clear()
        self._layouts_y.clear()

        pcb_width = self._client.size_mm[0]
        pcb_height = self._client.size_mm[1]
        if self._angle != 0.0:
            pcb_width = self._client.size_mm[1]
            pcb_height = self._client.size_mm[0]

        self._layouts_x.append(pcb_width)
        for c in range(0, columns-1):
            self._layouts_x.append(PCB_PANEL_GAP_MM)
            self._layouts_x.append(pcb_width)

        self._layouts_y.append(PCB_PANEL_BOTTOM_RAIL_MM)
        self._layouts_y.append(PCB_PANEL_GAP_MM)
        for r in range(0, rows):
            self._layouts_y.append(pcb_height)
            self._layouts_y.append(PCB_PANEL_GAP_MM)
        self._layouts_y.append(PCB_PANEL_BOTTOM_RAIL_MM)

        width = 0
        for x in self._layouts_x:
            width += x
        height = 0
        for y in self._layouts_y:
            height += y
        scale = self._client.pixels_per_cm / 10.0

        self._size_mm = (width, height)
        self._size_pixels = (int(math.ceil(width*scale)), int(math.ceil(height*scale)))
        self.size = self._size_pixels
        self._fbo.size = self.size
        self._image.size = self.size
        self._image.texture_size = self.size
        self.paint2()

    # TODO: if we try to overide the paint() method here,
    #  then we can't access self._rows:
    #    AttributeError: 'PcbPanel' object has no attribute '_rows'
    #  why is that?!
    def paint2(self):
        width = self.size[0]
        height = self.size[1]

        pcb_width = self._client.size_pixels[0]
        pcb_height = self._client.size_pixels[1]
        pcb_width_adjusted = pcb_width
        pcb_height_adjusted = pcb_height
        if self._angle != 0.0:
            pcb_width_adjusted = pcb_height
            pcb_height_adjusted = pcb_width

        scale = self._client.pixels_per_cm / 10.0
        height_bottom = PCB_PANEL_BOTTOM_RAIL_MM * scale
        height_top = PCB_PANEL_TOP_RAIL_MM * scale
        gap = PCB_PANEL_GAP_MM * scale

        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            if self._client is not None:
                c = PCB_MASK_COLOR
                Color(c.r, c.g, c.b, c.a)
                Rectangle(pos=(0, 0), size=(width, height_bottom))
                Rectangle(pos=(0, height-height_top), size=(width, height_top))
                y = height_bottom + gap
                for r in range(0, self._rows):
                    x = 0.0
                    for c in range(0, self._columns):
                        #Color(0.0, 0.5, 0.0, 0.5)
                        #Rectangle(pos=(x, y), size=(pcb_width_adjusted, pcb_height_adjusted))

                        PushMatrix()
                        Translate(x+pcb_width_adjusted/2.0, y+pcb_height_adjusted/2.0, 0.0)
                        Rotate(self._angle, 0.0, 0.0, 1.0)
                        Translate(-pcb_width/2.0, -pcb_height/2.0, 0.0)
                        self._client.paint(self._fbo)
                        PopMatrix()

                        x += pcb_width_adjusted
                        x += gap
                    y += pcb_height_adjusted
                    y += gap
        self._fbo.draw()
        self._image.texture = self._fbo.texture

    def center(self, available_size, angle):
        if angle is not None:
            if self._angle != angle:
                self._angle = angle
                self.panelize(self._columns, self._rows, self._angle)

        cx = available_size[0] / 2.0
        cy = available_size[1] / 2.0
        ax = (self.size[0] / 2.0)
        ay = (self.size[1] / 2.0)

        self.transform = Matrix().identity()
        mat = Matrix().translate(cx-ax, cy-ay, 0.0)
        self.apply_transform(mat)
        mat = Matrix().scale(self._scale, self._scale, 1.0)
        self.apply_transform(mat, post_multiply=True, anchor=(ax, ay))

    @property
    def size_pixels(self):
        return self._size_pixels

    @property
    def size_mm(self):
        return self._size_mm
