# The MIT License (MIT)

# Copyright 2021,2022 HalfMarble LLC

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


import math

from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.graphics import Fbo, ClearBuffers, ClearColor
from kivy.graphics.transformation import Matrix


class OffScreenScatter(Scatter):

    def __init__(self, client, pos=(0, 0), size=(100, 100), **kwargs):
        self.pos = pos
        self.size = size
        self.size_hint = (None, None)
        self.do_rotation = False
        self.do_scale = False
        self.do_translation_x = False
        self.do_translation_y = False

        super(OffScreenScatter, self).__init__(**kwargs)

        self._width_org = self.size[0]
        self._height_org = self.size[1]

        self._scale = 1.0
        self._angle = 0.0

        self._client = client

        self._fbo = Fbo(size=self.size, use_parent_projection=False, mipmap=True)

        self._image = Image(size=size, texture=self._fbo.texture)
        self.add_widget(self._image)

        self.paint()

    def set_scale(self, scale):
        self._scale = scale / 100.0

    def paint(self):
        self._fbo.size = self.size
        self._image.size = self.size
        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            if self._client is not None:
                self._client.paint(self._fbo)
        self._fbo.draw()
        self._image.texture = self._fbo.texture

    def center(self, available_size, angle=None):
        if angle is not None:
            self._angle = angle
        cx = available_size[0] / 2.0
        cy = available_size[1] / 2.0
        ax = (self.size[0] / 2.0)
        ay = (self.size[1] / 2.0)
        self.transform = Matrix().identity()
        mat = Matrix().translate(cx-ax, cy-ay, 0.0)
        self.apply_transform(mat)
        mat = Matrix().rotate(math.radians(self._angle), 0.0, 0.0, 1.0)
        self.apply_transform(mat, post_multiply=True, anchor=(ax, ay))
        mat = Matrix().scale(self._scale, self._scale, 1.0)
        self.apply_transform(mat, post_multiply=True, anchor=(ax, ay))
