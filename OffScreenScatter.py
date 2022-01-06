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
