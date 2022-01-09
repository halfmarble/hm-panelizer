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
from Constants import *
from PcbFile import *
from Utilities import *
import Constants


class PcbMouseBites:

    def __init__(self):

        self._gm1 = None
        self._drl = None

        self._bite = 0
        self._gap = 0
        self._bite_hole_radius = 0
        self._bite_hole_space = 0

        self._tmp_folder = tempfile.TemporaryDirectory().name
        try:
            os.mkdir(self._tmp_folder)
        except FileExistsError:
            pass

    def generate_pcb_files(self):
        if self._tmp_folder is None:
            print('ERROR: PcbMouseBites temp folder is NULL')
            return

        origin = (0, 0)
        size = (self._bite, self._gap)
        save_mouse_bite_gm1(self._tmp_folder, origin, size, arc=Constants.PCB_BITES_ARC_MM, close=False)
        save_mouse_bite_drl(self._tmp_folder, origin, size, self._bite_hole_radius, self._bite_hole_space)

        return self._tmp_folder

    def render_masks(self, bite, gap, bite_hole_radius, bite_hole_space):
        if self._tmp_folder is None:
            print('ERROR: PcbMouseBites temp folder is NULL')
            return

        if self._gm1 is None or self._bite != bite or self._gap != gap or \
                self._bite_hole_radius != bite_hole_radius or self._bite_hole_space != bite_hole_space:

            render_mouse_bite_gm1(self._tmp_folder, 'bites_edge_cuts',
                                  origin=(0, 0), size=(bite, gap), arc=Constants.PCB_BITES_ARC_MM, close=True)
            render_mouse_bite_drl(self._tmp_folder, 'bites_holes_npth',
                                  origin=(0, 0), size=(bite, gap), radius=bite_hole_radius, gap=bite_hole_space)

            self._gm1 = load_image_masked(self._tmp_folder, 'bites_edge_cuts_mask.png', Color(1, 1, 1, 1))
            self._drl = load_image_masked(self._tmp_folder, 'bites_holes_npth.png', Color(1, 1, 1, 1))

            # TODO: is there anything else that's more efficient that we can do here?
            # without this the rail images do not refresh correctly
            Cache.remove('kv.image')
            Cache.remove('kv.texture')

            self._bite = bite
            self._gap = gap
            self._bite_hole_radius = bite_hole_radius
            self._bite_hole_space = bite_hole_space

    def paint(self, color, pos, size):
        if self.gm1_image is not None:
            Color(color.r, color.g, color.b, color.a)
            Rectangle(texture=self.gm1_image.texture, size=size, pos=pos)
            color = PCB_DRILL_NPTH_COLOR
            Color(color.r, color.g, color.b, color.a)
            Rectangle(texture=self.drl_image.texture, size=size, pos=pos)

    @property
    def gm1_image(self):
        return self._gm1

    @property
    def drl_image(self):
        return self._drl

    def invalidate(self):
        self._gm1 = None
        self._drl = None

    def cleanup(self):
        rmrf(self._tmp_folder)


PcbMouseBites = PcbMouseBites()
