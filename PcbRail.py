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


import tempfile

from kivy.cache import Cache
from kivy.graphics import Rectangle, Color

from AppSettings import *
from PcbFile import *
from Utilities import *
from Constants import *


class PcbRail:

    def __init__(self):
        self._gm1 = None
        self._gtl = None
        self._gts = None
        self._gto = None

        self._panels = 0
        self._gap = 0
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
            print('ERROR: PcbRail temp folder is NULL')
            return

        save_rail_gm1(self._tmp_folder, self._origin, self._size, self._panels, self._gap, self._vcut)
        save_rail_gtl(self._tmp_folder, self._origin, self._size)
        save_rail_gts(self._tmp_folder, self._origin, self._size)
        save_rail_gto(self._tmp_folder, self._origin, self._size, self._panels, self._gap, self._vcut, self._jlc)
        save_rail_gbo(self._tmp_folder, self._origin, self._size)

        return self._tmp_folder

    def render_masks(self, panels, gap, origin, size, vcut, jlc):
        if self._tmp_folder is None:
            print('ERROR: PcbRail temp folder is NULL')
            return

        if self._gm1 is None or self._panels != panels or self._origin != origin or self._size != size or \
                self._vcut != vcut or self._jlc != jlc:

            bounds = render_rail_gm1(self._tmp_folder, 'rail_edge_cuts', origin, size, panels, gap, vcut)
            render_rail_gtl(bounds, self._tmp_folder, 'rail_top_copper', origin, size)
            render_rail_gts(bounds, self._tmp_folder, 'rail_top_mask', origin, size)
            render_rail_gto(bounds, self._tmp_folder, 'rail_top_silk', origin, size, panels, gap, vcut, jlc)

            self._gm1 = load_image_masked(self._tmp_folder, 'rail_edge_cuts_mask.png', Color(1, 1, 1, 1))
            self._gtl = load_image_masked(self._tmp_folder, 'rail_top_copper.png', Color(1, 1, 1, 1))
            self._gts = load_image_masked(self._tmp_folder, 'rail_top_mask.png', Color(1, 1, 1, 1))
            self._gto = load_image_masked(self._tmp_folder, 'rail_top_silk.png', Color(1, 1, 1, 1))

            # TODO: is there anything else that's more efficient that we can do here?
            # without this the rail images do not refresh correctly
            Cache.remove('kv.image')
            Cache.remove('kv.texture')

            self._panels = panels
            self._gap = gap
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
