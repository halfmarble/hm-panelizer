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
from kivy.graphics import Rectangle

from Constants import *


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
        PCB_PASTE_COLOR,
        PCB_DRILL_NPH_COLOR,
        PCB_DRILL_COLOR,
    ]

    _layers_always = [0, 1]
    _layers_top = [2, 3, 4, 5]
    _layers_bottom = [6, 7, 8, 9]

    def __init__(self, path, **kwargs):

        self._images = []

        self._images.append(Image(source=join(path, '0_outline_mask.png')))
        self._images.append(Image(source=join(path, '1_outline.png')))

        self._images.append(Image(source=join(path, '2_toppaste.png')))
        self._images.append(Image(source=join(path, '3_topsilk.png')))
        self._images.append(Image(source=join(path, '4_topmask.png')))
        self._images.append(Image(source=join(path, '5_top.png')))

        self._images.append(Image(source=join(path, '6_bottom.png')))
        self._images.append(Image(source=join(path, '7_bottommask.png')))
        self._images.append(Image(source=join(path, '8_bottomsilk.png')))
        self._images.append(Image(source=join(path, '9_bottompaste.png')))

        self._images.append(Image(source=join(path, '10_drill.png')))
        self._images.append(Image(source=join(path, '11_drill.png')))

        self._layers = [0, 1, 3, 4, 5, 10, 11]

        self._name = path.split(os.path.sep)[-1]
        self._size_mm = (58.01868, 95.6146) # TODO: fix hardcoded value (calculate it from outline path)
        self._size_pixels = self._images[0].texture_size
        self._size_rounded_mm = (math.ceil(self._size_mm[0]), math.ceil(self._size_mm[1]))

    def paint_layer(self, layer, fbo):
        yes = False
        if layer in self._layers_always:
            yes = True
        elif layer in self._layers:
            yes = True
        if yes:
            with fbo:
                color = self._colors[layer]
                Color(color.r, color.g, color.b, color.a)
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

    def set_layer(self, ids, layer, state):
        if state is 'down':
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
