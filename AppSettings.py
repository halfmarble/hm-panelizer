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


from Constants import *
from Utilities import *


class AppSettings:

    def __init__(self):
        self._gap = 0.0
        self._rail = 0.0
        self._bite = 0.0
        self._bite_hole_radius = 0.0
        self._bite_hole_space = 0.0
        self._bites_count = 0
        self._use_vcut = False
        self._use_jlc = False
        self._merge_error = 0.0

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
        self._merge_error = PCB_PANEL_MERGE_ERROR

    def set(self, gap, rail, bites_count, bite, bite_hole_radius, bite_hole_space, use_vcut, use_jlc, merge_error):
        self._gap = clamp(1.0, gap, 10.0)
        self._rail = clamp(5, rail, 20.0)
        self._bites_count = int(clamp(1, bites_count, 10))
        self._bite = clamp((2.0*PCB_BITES_ARC_MM)+0.5, bite, 15.0)
        self._bite_hole_radius = clamp(0.1, bite_hole_radius, 0.5)
        self._bite_hole_space = clamp(0.5, bite_hole_space, 5.0)
        self._use_vcut = use_vcut
        self._use_jlc = use_jlc
        self._merge_error = clamp(0.0, merge_error, 1.0)

    @property
    def rail(self):
        return float(self._rail)

    @property
    def gap(self):
        return float(self._gap)

    @property
    def bite(self):
        return float(self._bite)

    @property
    def bites_count(self):
        return int(self._bites_count)

    @property
    def bite_hole_radius(self):
        return float(self._bite_hole_radius)

    @property
    def bite_hole_space(self):
        return float(self._bite_hole_space)

    @property
    def use_vcut(self):
        return self._use_vcut

    @property
    def use_jlc(self):
        return self._use_jlc

    @property
    def merge_error(self):
        return float(self._merge_error)


AppSettings = AppSettings()
