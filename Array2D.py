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


class Array2D:

    def __init__(self, width, height):
        self._width = width
        self._height = height
        self._matrix = [[0 for x in range(width)] for y in range(height)]

    def put(self, x, y, value):
        self._matrix[y][x] = value

    def get(self, x, y):
        return self._matrix[y][x]

    # 0,0 is left,bottom
    def print(self, str=''):
        for y in reversed(range(self._height)):
            for x in (range(self._width)):
                print('{}[{}] '.format(str, self.get(x, y)), end='')
            print('')

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height