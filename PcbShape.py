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
