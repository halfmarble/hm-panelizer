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

from kivy.cache import Cache
from kivy.graphics import Rectangle, Color

from AppSettings import *
from Utilities import *
from Constants import *
import tempfile


class PcbRail:

    def __init__(self):
        self._gm1 = None
        self._gtl = None
        self._gts = None
        self._gto = None

        self._panels = 0
        self._origin = (0, 0)
        self._size = (0, 0)
        self._vcut = False
        self._jlc = False

        self._tmp_folder = tempfile.TemporaryDirectory().name
        try:
            os.mkdir(self._tmp_folder)
        except FileExistsError:
            pass

    def generate_pcb_files(self):
        if self._tmp_folder is None:
            print('ERROR: PcbMouseBites temp folder is NULL')
            return

        save_rail_gm1(self._tmp_folder, self._origin, self._size, self._panels, self._vcut)
        save_rail_gtl(self._tmp_folder, self._origin, self._size)
        save_rail_gts(self._tmp_folder, self._origin, self._size)
        save_rail_gto(self._tmp_folder, self._origin, self._size, self._panels, self._vcut, self._jlc)

        return self._tmp_folder

    def render_masks(self, panels, origin, size, vcut, jlc):
        if self._tmp_folder is None:
            print('ERROR: PcbRail temp folder is NULL')
            return

        if self._gm1 is None or self._panels != panels or self._origin != origin or self._size != size or \
                self._vcut != vcut or self._jlc != jlc:
            # TODO: is there anything else that's more efficient that we can do here?
            # without this the rail images do not refresh correctly
            Cache.remove('kv.image')
            Cache.remove('kv.texture')

            bounds = render_rail_gm1(self._tmp_folder, 'rail_edge_cuts', origin, size, panels, vcut)
            render_rail_gtl(bounds, self._tmp_folder, 'rail_top_copper', origin, size)
            render_rail_gts(bounds, self._tmp_folder, 'rail_top_mask', origin, size)
            render_rail_gto(bounds, self._tmp_folder, 'rail_top_silk', origin, size, panels, vcut, jlc)

            self._gm1 = load_image_masked(self._tmp_folder, 'rail_edge_cuts_mask.png', Color(1, 1, 1, 1))
            self._gtl = load_image_masked(self._tmp_folder, 'rail_top_copper.png', Color(1, 1, 1, 1))
            self._gts = load_image_masked(self._tmp_folder, 'rail_top_mask.png', Color(1, 1, 1, 1))
            self._gto = load_image_masked(self._tmp_folder, 'rail_top_silk.png', Color(1, 1, 1, 1))

            self._panels = panels
            self._origin = origin
            self._size = size
            self._vcut = vcut
            self._jlc = jlc

    def paint(self, bottom, top):
        c = PCB_MASK_COLOR
        Color(c.r, c.g, c.b, c.a)
        Rectangle(texture=self._gm1.texture, pos=bottom.pos, size=bottom.size)
        Rectangle(texture=self._gm1.texture, pos=top.pos, size=top.size)

        c = PCB_TOP_MASK_COLOR
        Color(c.r, c.g, c.b, c.a)
        Rectangle(texture=self._gts.texture, pos=bottom.pos, size=bottom.size)
        Rectangle(texture=self._gts.texture, pos=top.pos, size=top.size)

        c = PCB_TOP_TRACES_COLOR
        Color(c.r, c.g, c.b, c.a)
        Rectangle(texture=self._gtl.texture, pos=bottom.pos, size=bottom.size)
        Rectangle(texture=self._gtl.texture, pos=top.pos, size=top.size)

        c = PCB_TOP_SILK_COLOR
        Color(c.r, c.g, c.b, c.a)
        Rectangle(texture=self._gto.texture, pos=bottom.pos, size=bottom.size)
        Rectangle(texture=self._gto.texture, pos=top.pos, size=top.size)

    def invalidate(self):
        self._gm1 = None
        self._gtl = None
        self._gts = None
        self._gto = None

    def cleanup(self):
        rmrf(self._tmp_folder)


PcbRail = PcbRail()
