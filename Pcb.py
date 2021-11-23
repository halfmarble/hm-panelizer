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
from kivy.uix.image import Image
from kivy.graphics import Scale, Rectangle, Line

from Constants import *
from Utilities import *
from OffScreenImage import *


GOOD_COLOR: Final = Color(PCB_BITE_GOOD_COLOR.r, PCB_BITE_GOOD_COLOR.g, PCB_BITE_GOOD_COLOR.b, 1.0)
BAD_COLOR: Final  = Color(PCB_BITE_BAD_COLOR.r, PCB_BITE_BAD_COLOR.g, PCB_BITE_BAD_COLOR.b, 1.0)


class PcbPrimitive:

    def __init__(self, primitive, good):
        self._primitive = primitive
        if good:
            self._color = GOOD_COLOR
        else:
            self._color = BAD_COLOR

    @property
    def primitive(self):
        return self._primitive

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
        self._vertical = []
        self._horizontal = []
        self._arcs = []

        self._min_x = 1000000.0
        self._max_x = 0.0
        self._min_y = 1000000.0
        self._max_y = 0.0

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
                line = Line(points=[x1, y1, x2, y2])
                x_delta = abs(x1-x2)
                y_delta = abs(y1-y2)
                if x_delta < y_delta:
                    self._vertical.append(PcbPrimitive(line, x_delta == 0.0))
                else:
                    self._horizontal.append(PcbPrimitive(line, y_delta == 0.0))
            # else:
            #     print("arc")
        self._scale = size / max(self._max_x, self._max_y)
        print("size: {}".format(size))
        print("self._min_x: {}".format(self._min_x))
        print("self._min_y: {}".format(self._min_y))
        print("self._max_x: {}".format(self._max_x))
        print("self._max_y: {}".format(self._max_y))
        print("self._scale: {}".format(self._scale))

    def paint(self, fbo, size):
        scale = 1.0 / self._scale
        thickness = PCB_OUTLINE_WIDTH * scale
        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            Scale(self._scale, self._scale, 1.0)
            for line in self._horizontal:
                Color(line.r, line.g, line.b, line.a)
                Line(points=line.primitive.points, width=thickness)
            for line in self._vertical:
                Color(line.r, line.g, line.b, line.a)
                Line(points=line.primitive.points, width=thickness)

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


FS_MASK: Final = '''
$HEADER$
void main(void) {
    gl_FragColor = frag_color * texture2D(texture0, tex_coord0).a;
}
'''

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
        PCB_DRILL_NPH_COLOR,
        PCB_DRILL_COLOR,
    ]

    _layers_always = [1]
    _layers_top = [2, 3, 4, 5]
    _layers_bottom = [6, 7, 8, 9]

    def colored_mask(self, mask, color):
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

    def __init__(self, path, **kwargs):
        self._name = path.split(os.path.sep)[-1]

        mask = Image(source=join(path, '0_outline_mask.png'))
        self._size_pixels = mask.texture_size

        with open(join(path, '1_outline.txt')) as file:
            outline_path = file.read()
        pcb = PcbOutline(outline_path, max(self._size_pixels[0], self._size_pixels[1]))
        colored_outline = OffScreenImage(pcb, None)
        self._size_mm = (pcb.max_x, pcb.max_y)
        self._size_rounded_mm = (math.ceil(self._size_mm[0]), math.ceil(self._size_mm[1]))

        self._images = []

        self._images.append(self.colored_mask(mask, PCB_MASK_COLOR))

        mask = Image(source=join(path, '1_outline.png'))
        self._images.append(self.colored_mask(mask, PCB_TOP_PASTE_COLOR))

        mask = Image(source=join(path, '2_toppaste.png'))
        self._images.append(self.colored_mask(mask, PCB_TOP_PASTE_COLOR))

        mask = Image(source=join(path, '3_topsilk.png'))
        self._images.append(self.colored_mask(mask, PCB_TOP_SILK_COLOR))

        mask = Image(source=join(path, '4_topmask.png'))
        self._images.append(self.colored_mask(mask, PCB_TOP_MASK_COLOR))

        mask = Image(source=join(path, '5_top.png'))
        self._images.append(self.colored_mask(mask, PCB_TOP_TRACES_COLOR))

        mask = Image(source=join(path, '6_bottom.png'))
        self._images.append(self.colored_mask(mask, PCB_BOTTOM_TRACES_COLOR))

        mask = Image(source=join(path, '7_bottommask.png'))
        self._images.append(self.colored_mask(mask, PCB_BOTTOM_MASK_COLOR))

        mask = Image(source=join(path, '8_bottomsilk.png'))
        self._images.append(self.colored_mask(mask, PCB_BOTTOM_SILK_COLOR))

        mask = Image(source=join(path, '9_bottompaste.png'))
        self._images.append(self.colored_mask(mask, PCB_BOTTOM_PASTE_COLOR))

        mask = Image(source=join(path, '10_drill.png'))
        self._images.append(self.colored_mask(mask, PCB_DRILL_NPH_COLOR))

        mask = Image(source=join(path, '11_drill.png'))
        self._images.append(self.colored_mask(mask, PCB_DRILL_COLOR))

        colored_outline.paint(self._size_pixels)
        self._images.append(colored_outline)

        self._layers = [0, 1, 3, 4, 5, 10, 11]

    def paint_layer(self, layer, fbo):
        yes = False
        if layer in self._layers_always:
            yes = True
        elif layer in self._layers:
            yes = True
        if yes:
            with fbo:
                image = self._images[layer]
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
            self._layers.append(layer)
        else:
            if layer in self._layers:
                self._layers.remove(layer)

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
