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