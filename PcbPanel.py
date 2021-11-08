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

    def __init__(self, edge, root, horizontal):
        self._edge = edge
        self._root = root
        self._horizontal = horizontal

        self._base_color = Color(PCB_MASK_COLOR.r, PCB_MASK_COLOR.g, PCB_MASK_COLOR.b, PCB_MASK_COLOR.a)
        self._moving_color = Color(0, 0, 1, 1)
        self._moving = False

        super(BiteWidget, self).__init__(BiteRenderer(self))

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

    # TODO: is there a better way to repaint?
    def repaint(self):
        self.paint()
        self.deactivate()
        self.activate()

    def start_move(self):
        self._moving = True
        self._start = self.pos
        self.repaint()

    def end_move(self):
        self._moving = False
        self.repaint()

    def move_by(self, dx, dy):
        if self._moving:
            position = (self._start[0]+dx, self._start[1]+dy)
            # if self._edge.connects(position[0], position[1]):
            #     self._moving_color = Color(0, 1, 0, 1)
            # else:
            #     self._moving_color = Color(1, 0, 0, 1)
            self.pos = position

    def on_touch_down(self, touch):
        handled = super(BiteWidget, self).on_touch_down(touch)
        if handled:
            self.start_move()
            for b in self._group:
                b.start_move()
        return handled

    def on_touch_move(self, touch):
        handled = super(BiteWidget, self).on_touch_move(touch)
        if self._moving:
            dx = self.pos[0] - self._start[0]
            dy = self.pos[1] - self._start[1]
            for b in self._group:
                if b is not self:
                    b.move_by(dx, dy)
        return handled

    def on_touch_up(self, touch):
        handled = super(BiteWidget, self).on_touch_up(touch)
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

    @property
    def color(self):
        if self._moving:
            return self._moving_color
        else:
            return self._base_color


class PcbEdge:

    def layout(self):
        main = self._shape1
        if not main.is_of_kind(PcbKind.main):
            main = self._shape2

        scale = self._panel.scale
        scale_mm = self._panel.pixels_per_cm * scale / 10.0

        gap = (PCB_PANEL_GAP_MM * scale_mm)
        width = (PCB_PANEL_BITES_SIZE_MM * scale_mm)

        panel_ox = self._panel.origin[0]
        panel_oy = self._panel.origin[1]
        shape_ox = (main.x * scale)
        shape_oy = ((self._shape1.y+self._shape1.height) * scale) - 2.0
        shape_w = (main.width * scale)

        for i in range(self._bites_count):
            slide = ((float(i+1) / float(self._bites_count+1)) * shape_w) - (width / 2.0)
            pos = (panel_ox+shape_ox+slide, panel_oy+shape_oy)
            size = (width, gap+3.0)
            bite = self._bites[i]
            bite.set(pos, size)

    def __init__(self, panel, root, horizontal, bites_count, shape1, shape2):
        self._panel = panel
        self._root = root
        self._horizontal = horizontal
        self._bites_count = bites_count
        self._shape1 = shape1
        self._shape2 = shape2

        self._bites = []
        for i in range(self._bites_count):
            self._bites.append(BiteWidget(self, root, self._horizontal))

    def connects(self, x, y):
        pass
        # if self._horizontal:
        #     if self._kind is PcbKind.top:
        #         return True  # always connects
        #     elif self._kind is PcbKind.bottom:
        #         return True  # always connects
        #     elif self._kind is PcbKind.main:
        #         # TODO: implement
        #         return True

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

    def assign_groups(self, count, columns, rows, edges):
        for i in range(count):
            group = []
            for r in range(0, rows):
                for c in range(0, columns):
                    edge = edges.get(c, r)
                    bite = edge.bite(i)
                    group.append(bite)
            for r in range(0, rows):
                for c in range(0, columns):
                    edge = edges.get(c, r)
                    bite = edge.bite(i)
                    bite.assign_group(group)

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
                    edge = PcbEdge(panel, root, True, bites_x, bottom, top)
                    self._horizontal.put(c, r, edge)
            print(' horizontal edges:')
            self._horizontal.print('  ')
            self.assign_groups(bites_x, columns, rows, self._horizontal)
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
                    edge = PcbEdge(panel, root, False, bites_x, left, right)
                    self._vertical.put(c, r, edge)
            print(' vertical edges:')
            self._vertical.print('  ')
            self.assign_groups(bites_y, columns, rows, self._vertical)
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

    def layout(self):
        # TODO: implement Array2D iterator and use it here
        for c in range(self._horizontal.width):
            for r in range(self._horizontal.height):
                edge = self._horizontal.get(c, r)
                edge.layout()
        for c in range(self._vertical.width):
            for r in range(self._vertical.height):
                edge = self._vertical.get(c, r)
                edge.layout()


class PcbShape:

    def __init__(self, kind, mask):
        self._kind = kind
        self._mask = mask
        self._pos = (0, 0)
        self._size = (0, 0)

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

    def is_of_kind(self, kind):
        return kind == self._kind

    def set(self, pos, size):
        self._pos = pos
        self._size = size

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

    @property
    def pos(self):
        return self._pos

    @property
    def size(self):
        return self._size


class PcbPanel(OffScreenScatter):

    def __init__(self, root, pcb, shader, **kwargs):
        self._root = root
        self._active = False
        self._size_mm = (0, 0)
        self._size_pixels = (0, 0)
        self._origin = (0, 0)
        self._columns = 0
        self._rows = 0
        self._shapes = None
        self._bites_x = 0  # per single pcb
        self._bites_y = 0  # per single pcb

        self._bites = None

        super(PcbPanel, self).__init__(pcb, (0, 0), pcb.size_pixels, shader, **kwargs)

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

    def paint(self):
        if self._shapes is None:
            return

        pcb_client_width = self._client.size_pixels[0]
        pcb_client_height = self._client.size_pixels[1]
        pcb_width = pcb_client_width
        pcb_height = pcb_client_height
        if self._angle != 0.0:
            pcb_width = pcb_client_height
            pcb_height = pcb_client_width

        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()

            c = PCB_MASK_COLOR
            Color(c.r, c.g, c.b, c.a)

            bottom = self._shapes.get(0, 0)
            Rectangle(pos=bottom.pos, size=bottom.size)

            top = self._shapes.get(0, self._rows+1)
            Rectangle(pos=top.pos, size=top.size)

            for r in range(0, self._rows):
                for c in range(0, self._columns):
                    # pos_main = (round_float(x), round_float(y))
                    # size_main = (round_float(pcb_width), round_float(pcb_height))
                    # Color(0.5, 0.5, 0.5, 0.25)
                    # Rectangle(pos=pos_main, size=size_main)

                    main = self._shapes.get(c, r+1)
                    PushMatrix()
                    Translate(main.x + pcb_width / 2.0, main.y + pcb_height / 2.0, 0.0)
                    Rotate(self._angle, 0.0, 0.0, 1.0)
                    Translate(-pcb_client_width / 2.0, -pcb_client_height / 2.0, 0.0)
                    self._client.paint(self._fbo)
                    PopMatrix()

        self._fbo.draw()
        self._image.texture = self._fbo.texture

    def panelize(self, columns, rows, angle, bites_x, bites_y):
        self._columns = columns
        self._rows = rows
        self._angle = angle
        self._bites_x = bites_x
        self._bites_y = bites_y
        self._shapes = None
        self._bites = None

        scale = self._client.pixels_per_cm / 10.0

        self.allocate_parts()
        self.calculate_sizes(scale, self._columns, self._rows)
        self.layout_parts(scale, self.size[0], self.size[1])
        self.paint()

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

    def allocate_parts(self):
        self._shapes = Array2D(self._columns, self._rows + 2)

        # we only have 1 top and 1 bottom pcb, but pretend we have as many as columns to
        # map 1:1 to the main pieces for easy calculations later
        for c in range(0, self._columns):
            self._shapes.put(c, 0, PcbShape(PcbKind.bottom, None))
        for c in range(0, self._columns):
            self._shapes.put(c, self._rows + 1, PcbShape(PcbKind.top, None))

        for r in range(0, self._rows):
            for c in range(0, self._columns):
                self._shapes.put(c, r + 1, PcbShape(PcbKind.main, None))

        self._bites = PcbBites(self, self._root, self._shapes, self._bites_x, self._bites_y)

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

        # we only have 1 top and 1 bottom pcb, but pretend we have as many as columns to
        # map 1:1 to the main pieces for easy calculations later
        for c in range(0, self._columns):
            bottom = self._shapes.get(c, 0)
            pos = (0, 0)
            size = (round_float(panel_width), round_float(height_bottom))
            bottom.set(pos, size)
        for c in range(0, self._columns):
            bottom = self._shapes.get(c, self._rows+1)
            pos = (0, round_float(panel_height - height_top))
            size = (round_float(panel_width), round_float(height_top))
            bottom.set(pos, size)

        y = height_bottom + gap
        for r in range(0, self._rows):
            x = 0.0
            for c in range(0, self._columns):
                main = self._shapes.get(c, r+1)
                pos = (round_float(x), round_float(y))
                size = (round_float(pcb_width), round_float(pcb_height))
                main.set(pos, size)
                x += pcb_width + gap
            y += pcb_height + gap

        self._bites.layout()

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

        scale = self._client.pixels_per_cm / 10.0
        self.calculate_sizes(scale, self._columns, self._rows)
        self.layout_parts(scale, self.size[0], self.size[1])

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
