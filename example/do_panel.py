#! /usr/bin/env python
# -*- coding: utf-8 -*-

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

import os
import sys

sys.path.append('.')

import hm_gerber_ex

from hm_gerber_ex import GerberComposition, DrillComposition
from hm_gerber_tool.utils import listdir
from hm_gerber_tool.cam import FileSettings

from PcbExport import *

mouse_bite_width = 0.5
mouse_bite_height = 0.25
rail_origins = [(0.0, 0.0), (0.0, 2.0)]
pcb_origins = [(0.0, 0.75)]
mouse_bite_origins = [[(0.71, 0.5)], [(0.71, 1.75)]]
pcb_path = '/Users/gerard/PCBs/rectangle'
pcb_origin_mm = (121.9, -66.54)
pcb_size_mm = (10.0, 19.640000000000008)

# print('rail_origins {}'.format(rail_origins))
# print('pcb_origins {}'.format(pcb_origins))
# print('mouse_bite_origins: {}'.format(mouse_bite_origins))

progress = None
panel_path = os.path.abspath(os.path.join('.', 'example', 'panelized'))
rail_path = os.path.join('.', 'example', 'pcb_rails')
mouse_bite_path = os.path.join('.', 'example', 'pcb_mouse_bites')
pcb_rect_mm = (pcb_origin_mm, pcb_size_mm)
mouse_bite_width_mm = 10.0*mouse_bite_width
mouse_bite_height_mm = 10.0*mouse_bite_height
angle = 90.0

error_msg = export_pcb_panel(progress, panel_path,
                             pcb_path, pcb_origins, pcb_rect_mm,
                             rail_path, rail_origins,
                             mouse_bite_path, mouse_bite_origins, mouse_bite_width_mm, mouse_bite_height_mm,
                             angle)
