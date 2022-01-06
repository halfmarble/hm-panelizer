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


from kivy.uix.image import Image
from kivy.graphics import Fbo, ClearBuffers, ClearColor


class OffScreenImage(Image):

    def __init__(self, client, shader, **kwargs):
        super(OffScreenImage, self).__init__(**kwargs)

        self._client = client
        self._fbo = Fbo(use_parent_projection=False, mipmap=True)
        if shader is not None:
            self._fbo.shader.fs = shader

    def paint(self, size):
        if size is not None:
            self.size = size

        self._fbo.size = self.size
        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            if self._client is not None:
                self._client.paint(self._fbo, self.size)
        self._fbo.draw()
        self.texture = self._fbo.texture
