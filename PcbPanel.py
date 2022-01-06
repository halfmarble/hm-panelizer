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

from AppSettings import *
from Array2D import *
from Constants import *
from OffScreenScatter import *
from PcbMask import *
from PcbMouseBitesGroup import *
from PcbShape import *
from PcbMouseBites import *
from PcbRail import *
from Utilities import *


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

        self._bite_count = 0  # per single pcb
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

    def panelize(self, columns, rows, angle, bite_count):
        width = self.size[0]
        height = self.size[1]

        changed = self._columns != columns or self._rows != rows or self._angle != angle or \
                  self._bite_count != bite_count or self._width != width or self._height != height

        self._columns = columns
        self._rows = rows
        self._angle = angle
        self._bite_count = bite_count
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

        self._bites = PcbMouseBitesGroup(self, self._root, self._shapes, self._bite_count)

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
            size = (panel_width, height_bottom)
            bottom.set(pos, size)
        for c in range(0, self._columns):
            top = self._shapes.get(c, self._rows + 1)
            pos = (0, (panel_height - height_top))
            size = (panel_width, height_top)
            top.set(pos, size)

        y = height_bottom + gap
        for r in range(0, self._rows):
            x = 0.0
            for c in range(0, self._columns):
                shape = self._shapes.get(c, r + 1)
                pos = (x, y)
                size = (pcb_width, pcb_height)
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
                self.panelize(self._columns, self._rows, angle, self._bite_count)

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
        self.paint()

    def update_status(self):
        self._valid_layout = self._bites.validate_layout()
        self._parent.update_status()

    def get_bites_origins(self):
        origins = []
        scale = float(self.pixels_per_cm)
        bites_origins = self._bites.get_origins_mm(scale)
        for o in bites_origins:
            origins.append(o)
        return origins

    def get_rails_origins(self):
        origins = []
        scale = float(self.pixels_per_cm)
        top = self._shapes.get(0, 0)
        origins.append(top.get_origin_mm(scale))
        bottom = self._shapes.get(0, self._rows + 1)
        origins.append(bottom.get_origin_mm(scale))
        return origins

    def get_pcbs_origins(self):
        origins = []
        scale = float(self.pixels_per_cm)
        for r in range(0, self._rows):
            for c in range(0, self._columns):
                main = self._shapes.get(c, r + 1)
                origins.append(main.get_origin_mm(scale))
        return origins

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
