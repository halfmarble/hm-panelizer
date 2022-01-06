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


from kivy.graphics import Fbo, Rectangle, Translate, Rotate, Color


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
