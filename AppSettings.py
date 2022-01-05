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
import os

from kivy.graphics import Line, ClearBuffers, ClearColor
from Constants import *
from PcbFile import *
from Utilities import *
import tempfile


class AppSettings:

    def __init__(self):
        self._gap = 0
        self._rail = 0
        self._bite = 0
        self._bite_hole_radius = 0
        self._bite_hole_space = 0
        self._bites_count = 0
        self._use_vcut = False
        self._use_jlc = False

        self.default()

    def default(self):
        self._rail = PCB_PANEL_RAIL_HEIGHT_MM
        self._gap = PCB_PANEL_GAP_MM
        self._bite_hole_radius = PCB_BITES_HOLE_RADIUS_MM
        self._bite_hole_space = PCB_BITES_HOLE_SPACE_MM
        self._bite = PCB_PANEL_BITES_SIZE_MM
        self._bites_count = PCB_PANEL_BITES_COUNT_X
        self._use_vcut = PCB_PANEL_USE_VCUT
        self._use_jlc = PCB_PANEL_USE_JLC

    def set(self, gap, rail, bites_count, bite, bite_hole_radius, bite_hole_space, use_vcut, use_jlc):
        self._gap = clamp(2.5, gap, 10.0)
        self._rail = clamp(5, rail, 20.0)
        self._bites_count = int(clamp(1, bites_count, 10))
        self._bite = clamp(5.0, bite, 15.0)
        self._bite_hole_radius = clamp(0.1, bite_hole_radius, 1.0)
        self._bite_hole_space = clamp(0.5, bite_hole_space, 20.0)
        self._use_vcut = use_vcut
        self._use_jlc = use_jlc

    @property
    def rail(self):
        return self._rail

    @property
    def gap(self):
        return self._gap

    @property
    def bite(self):
        return self._bite

    @property
    def bites_count(self):
        return self._bites_count

    @property
    def bite_hole_radius(self):
        return self._bite_hole_radius

    @property
    def bite_hole_space(self):
        return self._bite_hole_space

    @property
    def use_vcut(self):
        return self._use_vcut

    @property
    def use_jlc(self):
        return self._use_jlc


AppSettings = AppSettings()
