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

from kivy.graphics import Rectangle, Color

from AppSettings import *
from Utilities import *
from Constants import *
import tempfile


class PcbMouseBites:

    def __init__(self):

        self._gm1 = None
        self._drl = None

        self._tmp_folder = tempfile.TemporaryDirectory().name
        try:
            os.mkdir(self._tmp_folder)
        except FileExistsError:
            pass

    def render_masks(self):
        if self._tmp_folder is None:
            print('ERROR: PcbMouseBites temp folder is NULL')
            return

        if self._gm1 is None or self._drl is None:
            render_mouse_bite_gm1(self._tmp_folder, 'bites_edge_cuts',
                                  origin=(0, 0), size=(AppSettings.bite, AppSettings.gap),
                                  arc=1, close=True)
            render_mouse_bite_drl(self._tmp_folder, 'bites_holes_npth',
                                  origin=(0, 0), size=(AppSettings.bite, AppSettings.gap),
                                  radius=AppSettings.bite_hole_radius, gap=AppSettings.bite_hole_space)

            self._gm1 = load_image_masked(self._tmp_folder, 'bites_edge_cuts_mask.png', Color(1, 1, 1, 1))
            self._drl = load_image_masked(self._tmp_folder, 'bites_holes_npth.png', Color(1, 1, 1, 1))

    def paint(self, color, pos, size):
        Color(color.r, color.g, color.b, color.a)
        Rectangle(texture=self.gm1_image.texture, size=size, pos=pos)
        color = PCB_DRILL_NPTH_COLOR
        Color(color.r, color.g, color.b, color.a)
        Rectangle(texture=self.drl_image.texture, size=size, pos=pos)

    @property
    def gm1_image(self):
        self.render_masks()
        return self._gm1

    @property
    def drl_image(self):
        self.render_masks()
        return self._drl

    def cleanup(self):
        rmrf(self._tmp_folder)


PcbMouseBites = PcbMouseBites()
