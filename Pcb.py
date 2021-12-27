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

import os
import math
from os.path import join

import kivy
from kivy.base import EventLoop
from kivy.uix.image import Image
from kivy.graphics import Scale, Rectangle, Line

from Constants import *
from Utilities import *
from OffScreenImage import *


FS_MASK: Final = '''
$HEADER$
void main(void) {
    gl_FragColor = vec4(frag_color.r, frag_color.g, frag_color.b, texture2D(texture0, tex_coord0).a);
}
'''

GOOD_COLOR: Final = Color(PCB_BITE_GOOD_COLOR.r, PCB_BITE_GOOD_COLOR.g, PCB_BITE_GOOD_COLOR.b, 1.0)
BAD_COLOR: Final = Color(PCB_BITE_BAD_COLOR.r, PCB_BITE_BAD_COLOR.g, PCB_BITE_BAD_COLOR.b, 1.0)


class PcbPrimitive:

    def __init__(self, primitive, edge, good):
        self._primitive = primitive
        self._edge = edge
        if good:
            self._color = GOOD_COLOR
        else:
            self._color = BAD_COLOR

    @property
    def primitive(self):
        return self._primitive

    @property
    def edge(self):
        return self._edge

    @property
    def r(self):
        return self._color.r

    @property
    def g(self):
        return self._color.g

    @property
    def b(self):
        return self._color.b

    @property
    def a(self):
        return self._color.a


class PcbOutline:

    def __init__(self, path, size):

        self._valid = True

        self._vertical = []
        self._horizontal = []
        self._arcs = []

        self._min_x = 1000000.0
        self._max_x = 0.0
        self._min_y = 1000000.0
        self._max_y = 0.0

        if path is not None:
            segments = path.split("\n")

            for s in segments:
                parts = s.split(" ")
                if parts[0] == 'Line:':
                    x1 = str_to_float(parts[1])
                    self._min_x = min(self._min_x, x1)
                    self._max_x = max(self._max_x, x1)
                    y1 = str_to_float(parts[2])
                    self._min_y = min(self._min_y, y1)
                    self._max_y = max(self._max_y, y1)
                    x2 = str_to_float(parts[3])
                    self._min_x = min(self._min_x, x2)
                    self._max_x = max(self._max_x, x2)
                    y2 = str_to_float(parts[4])
                    self._min_y = min(self._min_y, y2)
                    self._max_y = max(self._max_y, y2)

            for s in segments:
                parts = s.split(" ")
                if parts[0] == 'Line:':
                    x1 = str_to_float(parts[1])
                    y1 = str_to_float(parts[2])
                    x2 = str_to_float(parts[3])
                    y2 = str_to_float(parts[4])
                    line = Line(points=[x1, y1, x2, y2])
                    x_delta = abs(x1 - x2)
                    y_delta = abs(y1 - y2)
                    if x_delta < y_delta:
                        edge = (x1 == self._min_x or x1 == self._max_x) and (x2 == self._min_x or x2 == self._max_x)
                        good = x_delta == 0.0
                        self._vertical.append(PcbPrimitive(line, edge, good))
                    else:
                        edge = (y1 == self._min_y or y1 == self._max_y) and (y2 == self._min_y or y2 == self._max_y)
                        good = y_delta == 0.0
                        self._horizontal.append(PcbPrimitive(line, edge, good))

            self._scale = size / max(self._max_x, self._max_y)
        else:
            self._scale = 1.0
            self._max_x = 1.0
            self._max_y = 1.0

    def paint(self, fbo, size):
        scale = 1.0 / self._scale
        thickness = PCB_OUTLINE_WIDTH * scale
        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            Scale(self._scale, self._scale, 1.0)
            for line in self._horizontal:
                Color(line.r, line.g, line.b, line.a)
                width = thickness
                if line.edge:
                    width *= 2.0
                Line(points=line.primitive.points, width=width, cap='none')
            for line in self._vertical:
                Color(line.r, line.g, line.b, line.a)
                width = thickness
                if line.edge:
                    width *= 2.0
                Line(points=line.primitive.points, width=width, cap='none')

    @property
    def valid(self):
        return self._valid

    @property
    def min_x(self):
        return self._min_x

    @property
    def min_y(self):
        return self._min_y

    @property
    def max_x(self):
        return self._max_x

    @property
    def max_y(self):
        return self._max_y


class Pcb:
    _colors = [
        PCB_MASK_COLOR,
        PCB_OUTLINE_COLOR,
        PCB_TOP_PASTE_COLOR,
        PCB_TOP_SILK_COLOR,
        PCB_TOP_MASK_COLOR,
        PCB_TOP_TRACES_COLOR,
        PCB_BOTTOM_TRACES_COLOR,
        PCB_BOTTOM_MASK_COLOR,
        PCB_BOTTOM_SILK_COLOR,
        PCB_BOTTOM_PASTE_COLOR,
        PCB_DRILL_NPTH_COLOR,
        PCB_DRILL_PTH_COLOR,
    ]

    _layers_always = [1]
    _layers_top = [2, 3, 4, 5]
    _layers_bottom = [6, 7, 8, 9]
    _layers_verify = [0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    def colored_mask(self, mask, color):
        image = None
        if mask is not None:
            image = Image()
            image.size = self._size_pixels
            fbo = Fbo()
            fbo.shader.fs = FS_MASK
            fbo.size = image.size
            with fbo:
                ClearColor(0, 0, 0, 0)
                ClearBuffers()
                Color(color.r, color.g, color.b, color.a)
                Rectangle(texture=mask.texture, size=mask.texture_size, pos=(0, 0))
            fbo.draw()
            image.texture = fbo.texture
        return image

    def __init__(self, ids, path, name, **kwargs):
        # print('PCB()')
        # print(' path: {}'.format(path))
        # print(' name: {}'.format(name))

        self.invalid_reason = None

        if name is not None:
            self._name = name
        else:
            self._name = os.path.basename(path)

        image = load_image(path, 'edge_cuts_mask.png')
        if image is not None:
            self._size_pixels = image.texture_size
        else:
            self.invalid_reason = 'Missing \"edge_cuts_mask.png\"'
            self._size_pixels = (1, 1)
            fallbacks = ['edge_cuts.png', 'top_copper.png', 'bottom_copper.png', 'top_mask.png', 'bottom_mask.png']
            for f in fallbacks:
                image = load_image(path, f)
                if image is not None:
                    image._fbo = Fbo(use_parent_projection=False, mipmap=True)
                    image._fbo.size = image.texture_size
                    with image._fbo:
                        Color(0, 0, 0, 1)
                        Rectangle(size=image.texture_size, pos=(0, 0))
                    image._fbo.draw()
                    image.texture = image._fbo.texture
                    self._size_pixels = image.texture_size
                    break

        outline_path = load_file(path, 'edge_cuts_mask.txt')
        if outline_path is not None:
            pcb = PcbOutline(outline_path, max(self._size_pixels[0], self._size_pixels[1]))
            colored_outline = OffScreenImage(pcb, None)
            self._valid = pcb.valid
            if not self._valid:
                self.invalid_reason = 'Invalid PCB'
        else:
            pcb = PcbOutline(None, max(self._size_pixels[0], self._size_pixels[1]))
            colored_outline = None
            self._valid = False
            self.invalid_reason = 'No outline (no \"edge_cuts.grbl\" or \"outline.gm1\" found)'

        self._size_mm = (pcb.max_x, pcb.max_y)
        self._size_rounded_mm = (math.ceil(self._size_mm[0]), math.ceil(self._size_mm[1]))

        self._images = []

        self._images.append(self.colored_mask(image, PCB_MASK_COLOR))

        image = load_image(path, 'edge_cuts.png')
        self._images.append(self.colored_mask(image, PCB_TOP_PASTE_COLOR))

        image = load_image(path, 'top_paste.png')
        self._images.append(self.colored_mask(image, PCB_TOP_PASTE_COLOR))

        image = load_image(path, 'top_silk.png')
        self._images.append(self.colored_mask(image, PCB_TOP_SILK_COLOR))

        image = load_image(path, 'top_mask.png')
        self._images.append(self.colored_mask(image, PCB_TOP_MASK_COLOR))

        image = load_image(path, 'top_copper.png')
        self._images.append(self.colored_mask(image, PCB_TOP_TRACES_COLOR))

        image = load_image(path, 'bottom_copper.png')
        self._images.append(self.colored_mask(image, PCB_BOTTOM_TRACES_COLOR))

        image = load_image(path, 'bottom_mask.png')
        self._images.append(self.colored_mask(image, PCB_BOTTOM_MASK_COLOR))

        image = load_image(path, 'bottom_silk.png')
        self._images.append(self.colored_mask(image, PCB_BOTTOM_SILK_COLOR))

        image = load_image(path, 'bottom_paste.png')
        self._images.append(self.colored_mask(image, PCB_BOTTOM_PASTE_COLOR))

        image = load_image(path, 'drill_npth.png')
        self._images.append(self.colored_mask(image, PCB_DRILL_NPTH_COLOR))

        image = load_image(path, 'drill_pth.png')
        self._images.append(self.colored_mask(image, PCB_DRILL_PTH_COLOR))

        if colored_outline is not None:
            colored_outline.paint(self._size_pixels)
        self._images.append(colored_outline)

        self._layers = [0, 1, 3, 4, 5, 10, 11]

        ids._zoom_button.text = '100%'
        ids._pcb.state = 'down'
        ids._outline_verified.state = 'normal'
        ids._top1.state = 'down'
        ids._top2.state = 'normal'
        ids._top3.state = 'down'
        ids._top4.state = 'down'
        ids._bottom1.state = 'normal'
        ids._bottom2.state = 'normal'
        ids._bottom3.state = 'normal'
        ids._bottom4.state = 'normal'
        ids._drillnpth.state = 'down'
        ids._drillpth.state = 'down'

    def paint_layer(self, layer, fbo):
        yes = False
        if layer in self._layers_always:
            yes = True
        elif layer in self._layers:
            yes = True
        if yes:
            with fbo:
                image = self._images[layer]
                if image is not None:
                    Rectangle(texture=image.texture, size=image.texture_size, pos=(0, 0))

    def paint(self, fbo):
        with fbo:
            self.paint_layer(0, fbo)
            self.paint_layer(1, fbo)

            self.paint_layer(5, fbo)
            self.paint_layer(3, fbo)
            self.paint_layer(4, fbo)
            self.paint_layer(2, fbo)

            self.paint_layer(6, fbo)
            self.paint_layer(8, fbo)
            self.paint_layer(7, fbo)
            self.paint_layer(9, fbo)

            self.paint_layer(10, fbo)
            self.paint_layer(11, fbo)

            self.paint_layer(12, fbo)

    def set_layer(self, ids, layer, state):
        if state == 'down':
            if layer in self._layers_top:
                ids._bottom1.state = 'normal'
                ids._bottom2.state = 'normal'
                ids._bottom3.state = 'normal'
                ids._bottom4.state = 'normal'
                for bottom in self._layers_bottom:
                    if bottom in self._layers:
                        self._layers.remove(bottom)
            elif layer in self._layers_bottom:
                ids._top1.state = 'normal'
                ids._top2.state = 'normal'
                ids._top3.state = 'normal'
                ids._top4.state = 'normal'
                for top in self._layers_top:
                    if top in self._layers:
                        self._layers.remove(top)
            elif layer == 12:
                ids._pcb.state = 'normal'
                ids._top1.state = 'normal'
                ids._top2.state = 'normal'
                ids._top3.state = 'normal'
                ids._top4.state = 'normal'
                ids._bottom1.state = 'normal'
                ids._bottom2.state = 'normal'
                ids._bottom3.state = 'normal'
                ids._bottom4.state = 'normal'
                ids._drillnpth.state = 'normal'
                ids._drillpth.state = 'normal'
                for l in self._layers_verify:
                    if l in self._layers:
                        self._layers.remove(l)
            self._layers.append(layer)
        else:
            if layer in self._layers:
                self._layers.remove(layer)

    @property
    def valid(self):
        return self._valid

    @property
    def mask(self):
        return self._images[0]

    @property
    def size_pixels(self):
        return self._size_pixels

    @property
    def size_mm(self):
        return self._size_mm

    @property
    def size_rounded_mm(self):
        return self._size_rounded_mm

    @property
    def pixels_per_cm(self):
        return 10.0 * self.size_pixels[1] / self.size_mm[1]

    @property
    def board_name(self):
        return self._name
