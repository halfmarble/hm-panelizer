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

from enum import Enum
from random import uniform

from Array2D import *
from Utilities import *
from Constants import *
from OffScreenScatter import *


class PcbKind(Enum):
    top = 1
    main = 2
    bottom = 3


class BiteRenderer:

    def __init__(self, owner):
        self._owner = owner

    def paint(self, fbo):
        with fbo:
            c = self._owner.color
            ClearColor(c.r, c.g, c.b, c.a)
            ClearBuffers()


class BiteWidget(OffScreenScatter):

    def __init__(self, root, horizontal, position, size):
        self._base_color = Color(PCB_MASK_COLOR.r, PCB_MASK_COLOR.g, PCB_MASK_COLOR.b, PCB_MASK_COLOR.a)

        super(BiteWidget, self).__init__(BiteRenderer(self), size, None, pos=position)

        if horizontal:
            self.do_translation_x = True
            self.do_translation_y = False
        else:
            self.do_translation_x = False
            self.do_translation_y = True

        self._root = root
        self._group = None

    def assign_group(self, group):
        self._group = group

    def activate(self):
        self._root.add_widget(self)

    def deactivate(self):
        self._root.remove_widget(self)

    @property
    def color(self):
        return self._base_color


class PcbEdge:

    def __init__(self, panel, root, horizontal, bites_count, shape1, shape2):
        self._horizontal = horizontal
        self._bites_count = bites_count
        self._shape1 = shape1
        self._shape2 = shape2

        main = shape1
        if not main.is_of_kind(PcbKind.main):
            main = shape2

        scale = panel.scale
        scale_mm = panel.pixels_per_cm * scale / 10.0

        gap = (PCB_PANEL_GAP_MM * scale_mm)
        bite = (PCB_PANEL_BITES_SIZE_MM * scale_mm)

        panel_ox = panel.origin[0]
        panel_oy = panel.origin[1]
        shape_ox = (main.x * scale)
        shape_oy = ((shape1.y+shape1.height) * scale)
        shape_w = (main.width * scale)

        self._bites = []
        for i in range(bites_count):
            slide = ((float(i+1) / float(bites_count+1)) * shape_w) - (bite / 2.0)
            pos = (panel_ox+shape_ox+slide, panel_oy+shape_oy)
            size = (bite, gap)
            self._bites.append(BiteWidget(root, self._horizontal, pos, size))

    def __str__(self):
        rep = 'PcbEdge'
        return rep + ' {}, {} with {} bites'.format(self._shape1, self._shape2, self._bites_count)

    def activate(self):
        for b in self._bites:
            b.activate()

    def deactivate(self):
        for b in self._bites:
            b.deactivate()

    def bite(self, index):
        return self._bites[index]

    @property
    def bites_count(self):
        return self._bites_count


class PcbBites:

    def __init__(self, panel, root, shapes, bites_x, bites_y):
        print('\nPcbBites:')

        self._shapes = shapes
        print(' pcb shapes:')
        self._shapes.print('  ')

        if bites_x > 0:
            columns = self._shapes.width
            rows = (self._shapes.height - 1)
            self._horizontal = Array2D(columns, rows)
            for r in range(0, rows):
                for c in range(0, columns):
                    bottom = self._shapes.get(c, r)
                    top = self._shapes.get(c, r + 1)
                    self._horizontal.put(c, r, PcbEdge(panel, root, True, bites_x, bottom, top))
            print(' horizontal edges:')
            self._horizontal.print('  ')
        else:
            self._horizontal = Array2D(0, 0)

        if bites_y > 0:
            columns = (self._shapes.width - 1)
            rows = (self._shapes.height - 2)
            self._vertical = Array2D(columns, rows)
            for r in range(0, rows):
                for c in range(0, columns):
                    left = self._shapes.get(c, r)
                    right = self._shapes.get(c+1, r)
                    self._vertical.put(c, r, PcbEdge(panel, root, False, bites_x, left, right))
            print(' vertical edges:')
            self._vertical.print('  ')
        else:
            self._vertical = Array2D(0, 0)

    def activate(self):
        # TODO: implement Array2D iterator and use it here
        for c in range(self._horizontal.width):
            for r in range(self._horizontal.height):
                edge = self._horizontal.get(c, r)
                edge.activate()
        for c in range(self._vertical.width):
            for r in range(self._vertical.height):
                edge = self._vertical.get(c, r)
                edge.activate()

    def deactivate(self):
        # TODO: implement Array2D iterator and use it here
        for c in range(self._horizontal.width):
            for r in range(self._horizontal.height):
                edge = self._horizontal.get(c, r)
                edge.deactivate()
        for c in range(self._vertical.width):
            for r in range(self._vertical.height):
                edge = self._vertical.get(c, r)
                edge.deactivate()


class PcbShape:

    def __init__(self, kind, mask, pos, size):
        self._kind = kind
        self._mask = mask
        self._pos = pos
        self._size = size

    def __str__(self):
        rep = 'PcbShape'
        if self._kind is PcbKind.top:
            rep += ' TOP '
        elif self._kind is PcbKind.bottom:
            rep += ' BOTT'
        elif self._kind is PcbKind.main:
            rep += ' MAIN'
        else:
            rep += ' ????'
        return rep + ' {}, {}'.format(self._pos, self._size)

    def connects(self, x, y):
        if self._kind is PcbKind.top:
            return True  # always connects
        elif self._kind is PcbKind.bottom:
            return True  # always connects
        elif self._kind is PcbKind.main:
            # TODO: implement
            return True

    def is_of_kind(self, kind):
        return kind == self._kind

    @property
    def x(self):
        return self._pos[0]

    @property
    def y(self):
        return self._pos[1]

    @property
    def width(self):
        return self._size[0]

    @property
    def height(self):
        return self._size[1]

    @property
    def cx(self):
        return self.x + (self.width/2)

    @property
    def cy(self):
        return self.y + (self.height/2)


class PcbPanel(OffScreenScatter):

    def __init__(self, root, pcb, shader, **kwargs):
        super(PcbPanel, self).__init__(pcb, pcb.size_pixels, shader, **kwargs)

        self._root = root
        self._active = False
        self._size_mm = (0, 0)
        self._size_pixels = (0, 0)
        self._origin = (0, 0)
        self._columns = 0
        self._rows = 0
        self._bites_x = 0  # per single pcb
        self._bites_y = 0  # per single pcb

        self._bites = None

    def activate(self):
        if not self._active:
            self._root.add_widget(self)
            self._bites.activate()
            self._active = True

    def deactivate(self):
        if self._active:
            self._bites.deactivate()
            self._root.remove_widget(self)
            self._active = False

    def panelize(self, columns, rows, angle, bites_x, bites_y):
        self._columns = columns
        self._rows = rows
        self._angle = angle
        self._bites_x = bites_x
        self._bites_y = bites_y

        scale = self._client.pixels_per_cm / 10.0

        self.calculate_sizes(scale, columns, rows)
        self.layout_parts(scale, self.size[0], self.size[1])

        self.deactivate()

    def calculate_sizes(self, scale, columns, rows):
        pcb_width = self._client.size_mm[0]
        pcb_height = self._client.size_mm[1]
        if self._angle != 0.0:
            pcb_width = self._client.size_mm[1]
            pcb_height = self._client.size_mm[0]

        panel_width = 0
        panel_width += pcb_width
        for c in range(0, columns - 1):
            panel_width += PCB_PANEL_GAP_MM
            panel_width += pcb_width

        panel_height = 0
        panel_height += PCB_PANEL_BOTTOM_RAIL_MM
        panel_height += PCB_PANEL_GAP_MM
        for r in range(0, rows):
            panel_height += pcb_height
            panel_height += PCB_PANEL_GAP_MM
        panel_height += PCB_PANEL_BOTTOM_RAIL_MM

        self._size_mm = (panel_width, panel_height)
        self._size_pixels = (round_float(panel_width * scale), round_float(panel_height * scale))
        self.size = self._size_pixels
        self._fbo.size = self.size
        self._image.size = self.size
        self._image.texture_size = self.size

    def layout_parts(self, scale, panel_width, panel_height):
        pcb_client_width = self._client.size_pixels[0]
        pcb_client_height = self._client.size_pixels[1]
        pcb_width = pcb_client_width
        pcb_height = pcb_client_height
        if self._angle != 0.0:
            pcb_width = pcb_client_height
            pcb_height = pcb_client_width

        height_bottom = PCB_PANEL_BOTTOM_RAIL_MM * scale
        height_top = PCB_PANEL_TOP_RAIL_MM * scale
        gap = PCB_PANEL_GAP_MM * scale

        pos_bottom = (0, 0)
        size_bottom = (round_float(panel_width), round_float(height_bottom))

        pos_top = (0, round_float(panel_height - height_top))
        size_top = (round_float(panel_width), round_float(height_top))

        shapes = Array2D(self._columns, self._rows + 2)

        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            if self._client is not None:
                c = PCB_MASK_COLOR
                Color(c.r, c.g, c.b, c.a)
                Rectangle(pos=pos_bottom, size=size_bottom)
                Rectangle(pos=pos_top, size=size_top)

                # we only have 1 top and 1 bottom pcb, but pretend we have as many as columns to
                # map 1:1 to the main pieces for easy calculations later
                for c in range(0, self._columns):
                    shapes.put(c, 0, PcbShape(PcbKind.bottom, None, pos_bottom, size_bottom))
                for c in range(0, self._columns):
                    shapes.put(c, self._rows + 1, PcbShape(PcbKind.top, None, pos_top, size_top))

                y = height_bottom + gap
                for r in range(0, self._rows):
                    x = 0.0
                    for c in range(0, self._columns):
                        pos_main = (round_float(x), round_float(y))
                        size_main = (round_float(pcb_width), round_float(pcb_height))
                        #Color(0.5, 0.5, 0.5, 0.25)
                        #Rectangle(pos=pos_main, size=size_main)
                        shapes.put(c, r + 1, PcbShape(PcbKind.main, None, pos_main, size_main))

                        PushMatrix()
                        Translate(x + pcb_width / 2.0, y + pcb_height / 2.0, 0.0)
                        Rotate(self._angle, 0.0, 0.0, 1.0)
                        Translate(-pcb_client_width / 2.0, -pcb_client_height / 2.0, 0.0)
                        self._client.paint(self._fbo)
                        PopMatrix()

                        x += pcb_width
                        x += gap
                    y += pcb_height
                    y += gap
        self._fbo.draw()
        self._image.texture = self._fbo.texture

        self._bites = PcbBites(self, self._root, shapes, self._bites_x, self._bites_y)

    def center(self, available_size, angle):
        if angle is not None:
            if self._angle != angle:
                self.panelize(self._columns, self._rows, angle, self._bites_x, self._bites_y)

        ox = round_float((available_size[0] - (self._scale * self.size[0])) / 2.0)
        oy = round_float((available_size[1] - (self._scale * self.size[1])) / 2.0)
        self._origin = (ox, oy)

        cx = available_size[0] / 2.0
        cy = available_size[1] / 2.0
        ax = (self.size[0] / 2.0)
        ay = (self.size[1] / 2.0)

        self.transform = Matrix().identity()
        mat = Matrix().translate(cx - ax, cy - ay, 0.0)
        self.apply_transform(mat)
        mat = Matrix().scale(self._scale, self._scale, 1.0)
        self.apply_transform(mat, post_multiply=True, anchor=(ax, ay))

    @property
    def size_pixels(self):
        return self._size_pixels

    @property
    def size_mm(self):
        return self._size_mm

    @property
    def origin(self):
        return self._origin

    @property
    def scale(self):
        return self._scale

    @property
    def pixels_per_cm(self):
        return self._client.pixels_per_cm