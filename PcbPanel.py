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

from kivy.graphics import Rectangle, Translate, Rotate, PushMatrix, PopMatrix

from enum import Enum

from AppSettings import *
from Array2D import *
from Utilities import *
from Constants import *
from OffScreenScatter import *
from PcbMouseBites import *
from PcbRail import *


class PcbKind(Enum):
    top = 1
    main = 2
    bottom = 3


class PcbMask:

    def __init__(self, mask, angle):

        self._pixels = mask.texture.pixels
        self._pixels_w = int(mask.texture_size[0])
        self._pixels_h = int(mask.texture_size[1])

        if angle == 0.0:
            self._pixels_w = int(mask.texture_size[0])
            self._pixels_h = int(mask.texture_size[1])
            fbo = Fbo(size=(self._pixels_w, self._pixels_h))
            mask.texture.flip_vertical()
            fbo.clear()
            with fbo:
                Color(1, 1, 1, 1)
                Rectangle(size=(self._pixels_w, self._pixels_h), texture=mask.texture)
            fbo.draw()
            mask.texture.flip_vertical()
            self._pixels = fbo.pixels
        else:
            self._pixels_w = int(mask.texture_size[0])
            self._pixels_h = int(mask.texture_size[1])
            fbo = Fbo(size=(self._pixels_w, self._pixels_h))
            mask.texture.flip_horizontal()
            fbo.clear()
            with fbo:
                Color(1, 1, 1, 1)
                Translate(self._pixels_w, self._pixels_h)
                Rotate(angle, 0.0, 0.0, 1.0)
                Translate(-self._pixels_h, 0)
                Rectangle(size=(self._pixels_h, self._pixels_w), texture=mask.texture)
            fbo.draw()
            mask.texture.flip_horizontal()
            self._pixels = fbo.pixels

        # for y in range(0, self._pixels_h, 4):
        #     for x in range(0, self._pixels_w, 2):
        #         i = int((y*self._pixels_w*4) + (x*4) + 3)
        #         p = self._pixels[i] > 0
        #         v = '.'
        #         if p > 0:
        #             v = 'X'
        #         print('{}'.format(v), end='')
        #     print('')

    def get_mask_index(self, x, y):
        if x < 0:
            x = 0
        elif x >= self._pixels_w:
            x = self._pixels_w - 1
        if y < 0:
            y = 0
        elif y >= self._pixels_h:
            y = self._pixels_h - 1
        y = self._pixels_h - y
        x = int(x)
        y = int(y)
        return int((y*self._pixels_w*4) + (x*4) + 3)  # we want alpha channel only (GL_RGBA, GL_UNSIGNED_BYTE)

    def get_mask_alpha(self, x, y, length):
        length = int(length*self._pixels_w)
        alpha = self._pixels[self.get_mask_index(int(x+length), y)] > 0
        for pos in range(int(x), int(x+length-1), 2):
            alpha = alpha and self._pixels[self.get_mask_index(pos, y)] > 0
            if not alpha:
                break
        return alpha

    def get_mask_bottom(self, x, length):
        x *= self._pixels_w
        y = 1
        return self.get_mask_alpha(x, y, length)

    def get_mask_top(self, x, length):
        x *= self._pixels_w
        y = self._pixels_h - 1
        return self.get_mask_alpha(x, y, length)

    def get_mask_left(self, y, length):
        x = 1
        y *= self._pixels_h
        return self.get_mask_alpha(x, y, length)

    def get_mask_right(self, y, length):
        x = self._pixels_w - 1
        y *= self._pixels_h
        return self.get_mask_alpha(x, y, length)


class MouseBitesRenderer:

    def __init__(self, owner):
        self._owner = owner

    def paint(self, fbo):
        with fbo:
            PcbMouseBites.paint(self._owner.color, pos=(0, 0), size=self._owner.size)


class BiteWidget(OffScreenScatter):

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

        super(BiteWidget, self).__init__(MouseBitesRenderer(self))

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
        handled = super(BiteWidget, self).on_touch_down(touch)
        if handled:
            self.start_move()
            for b in self._group:
                if b is not self:
                    b.start_move()
        return handled

    def on_touch_move(self, touch):
        handled = super(BiteWidget, self).on_touch_move(touch)
        if self._moving:
            self._gap.validate_pos(self, self.pos[0])
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

        self._bites = []
        self._gap_start = 0
        self._gap_end = 0
        self._gap_width = 0
        self._bite_width = 0

        for i in range(self._bites_count):
            slide = (float(i + 1) / float(self._bites_count + 1))
            self._bites.append(BiteWidget(self, root, self._horizontal, slide))

    def layout(self):
        self._main_shape = self._shape1
        if not self._main_shape.is_of_kind(PcbKind.main):
            self._main_shape = self._shape2

        self._bottom_shape = self._shape1

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
    def main_shape(self):
        return self._main_shape

    @property
    def bottom_shape(self):
        return self._bottom_shape


class PcbBites:

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
        for c in range(self._horizontal.width):
            for r in range(self._horizontal.height):
                gap = self._horizontal.get(c, r)
                main = gap.main_shape
                main_origin = main.get_origin_mm(scale)
                main_size = main.get_size_mm(scale)
                bottom = gap.bottom_shape
                bottom_origin = bottom.get_origin_mm(scale)
                bottom_size = bottom.get_size_mm(scale)
                for b in range(gap.bites_count):
                    bite = gap.bite(b)
                    origin_x = main_origin[0] + bite.slide*main_size[0]
                    origin_y = bottom_origin[1] + bottom_size[1]
                    origins.append((origin_x, origin_y))
        return origins

    def validate_layout(self):
        valid = True
        for b in self._bites:
            valid = valid and b.connected
        return valid


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

    def mask_connects_horizontal(self, bottom, x, length):
        if bottom:
            return self._mask.get_mask_bottom(x, length)
        else:
            return self._mask.get_mask_top(x, length)

    def connects(self, horizontal, side, pos, length):
        if horizontal:
            if self._kind is PcbKind.bottom:
                return True  # always connects
            elif self._kind is PcbKind.top:
                return True  # always connects
            elif self._kind is PcbKind.main:
                return self.mask_connects_horizontal(side, pos, length)

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
    def pos(self):
        return self._pos

    def get_origin_mm(self, scale):
        return (self._pos[0]/scale, self._pos[1]/scale)

    @property
    def size(self):
        return self._size

    def get_size_mm(self, scale):
        return (self._size[0]/scale, self._size[1]/scale)


class PcbPanel(OffScreenScatter):

    def __init__(self, parent, root, pcb, **kwargs):
        self._parent = parent
        self._root = root
        self._pcb = pcb
        self._active = False
        self._size_mm = (0, 0)
        self._size_pixels = (0, 0)
        self._origin = (0, 0)

        self._width = 0
        self._height = 0
        self._angle = 0
        self._columns = 0
        self._rows = 0

        self._mask = None
        self._shapes = None

        self._bites_count = 0  # per single pcb
        self._bites = None

        self._valid_layout = False

        super(PcbPanel, self).__init__(pcb, (0, 0), pcb.size_pixels, **kwargs)

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

    def panelize(self, columns, rows, angle, bites_x):
        width = self.size[0]
        height = self.size[1]

        changed = self._columns != columns or self._rows != rows or self._angle != angle or \
                  self._bites_count != bites_x or self._width != width or self._height != height

        self._columns = columns
        self._rows = rows
        self._angle = angle
        self._bites_count = bites_x
        self._width = width
        self._height = height

        if changed:
            self._shapes = None
            self._bites = None

            self._mask = PcbMask(self._client.mask, self._angle)

            scale = self._client.pixels_per_cm / 10.0

            self.allocate_parts()
            self.calculate_sizes(scale, self._columns, self._rows)
            self.layout_parts(scale, self._width, self._height)

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
            panel_width += AppSettings.gap
            panel_width += pcb_width

        panel_height = 0
        panel_height += AppSettings.rail
        panel_height += AppSettings.gap
        for r in range(0, rows):
            panel_height += pcb_height
            panel_height += AppSettings.gap
        panel_height += AppSettings.rail

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
                self._shapes.put(c, r + 1, PcbShape(PcbKind.main, self._mask))

        self._bites = PcbBites(self, self._root, self._shapes, self._bites_count)

    def layout_parts(self, scale, panel_width, panel_height):
        pcb_client_width = self._client.size_pixels[0]
        pcb_client_height = self._client.size_pixels[1]
        pcb_width = pcb_client_width
        pcb_height = pcb_client_height
        if self._angle != 0.0:
            pcb_width = pcb_client_height
            pcb_height = pcb_client_width

        height_bottom = AppSettings.rail * scale
        height_top = AppSettings.rail * scale
        gap = AppSettings.gap * scale

        # we only have 1 top and 1 bottom pcb, but pretend we have as many as columns to
        # map 1:1 to the main pieces for easy calculations later
        for c in range(0, self._columns):
            bottom = self._shapes.get(c, 0)
            pos = (0, 0)
            size = (round_float(panel_width), round_float(height_bottom))
            bottom.set(pos, size)
        for c in range(0, self._columns):
            top = self._shapes.get(c, self._rows + 1)
            pos = (0, round_float(panel_height - height_top))
            size = (round_float(panel_width), round_float(height_top))
            top.set(pos, size)

        y = height_bottom + gap
        for r in range(0, self._rows):
            x = 0.0
            for c in range(0, self._columns):
                shape = self._shapes.get(c, r + 1)
                pos = (round_float(x), round_float(y))
                size = (round_float(pcb_width), round_float(pcb_height))
                shape.set(pos, size)
                x += pcb_width + gap
            y += pcb_height + gap

        self._valid_layout = self._bites.layout()
        self.update_status()

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

        panels = self._columns
        origin = (0, 0)
        size = (self._size_mm[0], AppSettings.rail)
        vcut = AppSettings.use_vcut
        jlc = AppSettings.use_jlc
        PcbRail.render_masks(panels, origin, size, vcut, jlc)

        bite = AppSettings.bite
        gap = AppSettings.gap
        bite_hole_radius = AppSettings.bite_hole_radius
        bite_hole_space = AppSettings.bite_hole_space
        PcbMouseBites.render_masks(bite, gap, bite_hole_radius, bite_hole_space)

        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()

            bottom = self._shapes.get(0, 0)
            top = self._shapes.get(0, self._rows + 1)
            PcbRail.paint(bottom, top)

            Color(1, 1, 1, 1)
            for r in range(0, self._rows):
                for c in range(0, self._columns):
                    main = self._shapes.get(c, r + 1)

                    # pos_main = (round_float(main.x), round_float(main.y))
                    # size_main = (round_float(pcb_width), round_float(pcb_height))
                    # Color(0.5, 0.5, 0.5, 0.25)
                    # Rectangle(pos=pos_main, size=size_main)

                    PushMatrix()
                    Translate(main.x + pcb_width / 2.0, main.y + pcb_height / 2.0, 0.0)
                    Rotate(self._angle, 0.0, 0.0, 1.0)
                    Translate(-pcb_client_width / 2.0, -pcb_client_height / 2.0, 0.0)
                    self._client.paint(self._fbo)
                    PopMatrix()

        self._fbo.draw()
        self._image.texture = self._fbo.texture

    def center(self, available_size, angle):
        if angle is not None:
            if self._angle != angle:
                self.panelize(self._columns, self._rows, angle, self._bites_count)

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

    def update_status(self):
        self._valid_layout = self._bites.validate_layout()
        self._parent.update_status()

    def print_layout(self):
        print('print_layout')
        scale = float(self.pixels_per_cm)
        top = self._shapes.get(0, 0)
        print('  bottom: {} cm'.format(top.get_origin_mm(scale)))
        bottom = self._shapes.get(0, self._rows + 1)
        print('  top: {} cm'.format(bottom.get_origin_mm(scale)))
        for r in range(0, self._rows):
            for c in range(0, self._columns):
                main = self._shapes.get(c, r + 1)
                print('  main: {} cm'.format(main.get_origin_mm(scale)))
        bites_origins = self._bites.get_origins_mm(scale)
        print('  {} bites:'.format(len(bites_origins)))
        for o in bites_origins:
            print('   bite: {} cm'.format(o))

    @property
    def valid_layout(self):
        return self._valid_layout

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
