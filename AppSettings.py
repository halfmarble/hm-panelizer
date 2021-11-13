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
from kivy.graphics import Line, ClearBuffers, ClearColor
from Constants import *


class AppSettings:

    def __init__(self):
        self._gap = 0
        self._top = 0
        self._bottom = 0
        self._bite = 0
        self._bites_x = 0
        self._bites_x = 0
        self._bites_y = 0

        self.reset()

    def reset(self):
        self._top = PCB_PANEL_TOP_RAIL_MM
        self._bottom = PCB_PANEL_BOTTOM_RAIL_MM
        self._gap = PCB_PANEL_GAP_MM
        self._bite = PCB_PANEL_BITES_SIZE_MM
        self._bites_x = PCB_PANEL_BITES_X
        self._bites_y = PCB_PANEL_BITES_Y

    @property
    def top(self):
        return self._top

    @property
    def bottom(self):
        return self._bottom

    @property
    def gap(self):
        return self._gap

    @property
    def bite(self):
        return self._bite

    @property
    def bites_x(self):
        return self._bites_x

    @property
    def bites_y(self):
        return self._bites_y


AppSettings = AppSettings()
