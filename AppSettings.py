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
        self._top = 0
        self._bottom = 0
        self._bite = 0
        self._bite_hole_radius = 0
        self._bite_hole_space = 0
        self._bites_count_x = 0
        self._bites_count_y = 0
        self._bites_gm1 = None
        self._bites_drl = None
        self._rail_gm1 = None
        self._rail_gtl = None
        self._rail_gts = None
        self._rail_gto = None

        self._tmp_folder = tempfile.TemporaryDirectory().name
        try:
            os.mkdir(self._tmp_folder)
        except FileExistsError:
            pass

        self.reset()

    def reset(self):
        self._top = PCB_PANEL_RAIL_HEIGHT_MM
        self._bottom = PCB_PANEL_RAIL_HEIGHT_MM
        self._gap = PCB_PANEL_GAP_MM
        self._bite_hole_radius = PCB_BITES_HOLE_RADIUS_MM
        self._bite_hole_space = PCB_BITES_HOLE_SPACE_MM
        self._bite = PCB_PANEL_BITES_SIZE_MM
        self._bites_count_x = PCB_PANEL_BITES_COUNT_X
        self._bites_count_y = PCB_PANEL_BITES_COUNT_Y
        self._bites_gm1 = None
        self._bites_drl = None
        self._rail_gm1 = None
        self._rail_gtl = None
        self._rail_gts = None
        self._rail_gto = None

    def render_bites(self):
        if (self._bites_gm1 is None or self._bites_drl is None) \
                and self._tmp_folder is not None:

            render_mouse_bite_gm1(self._tmp_folder, 'bites_edge_cuts',
                                  origin=(0, 0), size=(self._bite, self._gap),
                                  arc=1, close=True)
            render_mouse_bite_drl(self._tmp_folder, 'bites_holes_npth',
                                  origin=(0, 0), size=(self._bite, self._gap),
                                  radius=self._bite_hole_radius, gap=self._bite_hole_space)

            self._bites_gm1 = load_image_masked(self._tmp_folder, 'bites_edge_cuts_mask.png', Color(1, 1, 1, 1))
            self._bites_drl = load_image_masked(self._tmp_folder, 'bites_holes_npth.png', Color(1, 1, 1, 1))

    def render_rail(self):
        if (self._rail_gm1 is None or self._rail_gtl is None or self._rail_gts is None or self._rail_gto is None) \
                and self._tmp_folder is not None:

            panels = 2
            vcut = True
            origin = (0, 0)
            size = (205, 5)

            bounds = render_rail_gm1(self._tmp_folder, 'rail_edge_cuts',
                                     origin=origin, size=size, panels=panels, vcut=vcut)
            render_rail_gtl(bounds, self._tmp_folder, 'rail_top_copper',
                            origin=origin, size=size)
            render_rail_gts(bounds, self._tmp_folder, 'rail_top_mask',
                            origin=origin, size=size)
            render_rail_gto(bounds, self._tmp_folder, 'rail_top_silk',
                            origin=origin, size=size, panels=panels, vcut=vcut)

            self._rail_gm1 = load_image_masked(self._tmp_folder, 'rail_edge_cuts_mask.png', Color(1, 1, 1, 1))
            self._rail_gtl = load_image_masked(self._tmp_folder, 'rail_top_copper.png', Color(1, 1, 1, 1))
            self._rail_gts = load_image_masked(self._tmp_folder, 'rail_top_mask.png', Color(1, 1, 1, 1))
            self._rail_gto = load_image_masked(self._tmp_folder, 'rail_top_silk.png', Color(1, 1, 1, 1))

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
    def bites_count_x(self):
        return self._bites_count_x

    @property
    def bites_count_y(self):
        return self._bites_count_y

    @property
    def bite_hole_radius(self):
        return self._bite_hole_radius

    @property
    def bite_hole_space(self):
        return self._bite_hole_space

    @property
    def bites_gm1_image(self):
        self.render_bites()
        return self._bites_gm1

    @property
    def bites_drl_image(self):
        self.render_bites()
        return self._bites_drl

    @property
    def rail_gm1_image(self):
        self.render_rail()
        return self._rail_gm1

    @property
    def rail_gtl_image(self):
        self.render_rail()
        return self._rail_gtl

    @property
    def rail_gts_image(self):
        self.render_rail()
        return self._rail_gts

    @property
    def rail_gto_image(self):
        self.render_rail()
        return self._rail_gto

    def cleanup(self):
        rmrf(self._tmp_folder)


AppSettings = AppSettings()
