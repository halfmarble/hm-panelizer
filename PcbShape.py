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


from enum import Enum


class PcbKind(Enum):
    top = 1
    main = 2
    bottom = 3


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
