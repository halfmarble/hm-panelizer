#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022 HalfMarble LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

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

if False:
    #test case 1
    pcb_height = 0.5
    row1_height = pcb_height
    row2_height = pcb_height + pcb_height + mouse_bite_height
    rail_origins = [(0, 0), (0, row2_height + mouse_bite_height)]
    pcb_origins = [(0, row1_height + mouse_bite_height)]
    mouse_bite_origins = [[(3.0, row1_height)], [(3.0, row2_height)]]
    pcb_path = os.path.join('.', 'example', 'pcb_rails')
    pcb_height_mm = 10.0 * pcb_height
elif True:
    # test case 2
    rail_origins = [(0.0, 0.0), (0.0, 2.9667866927592965)]
    pcb_origins = [(-12.190000000000001, 7.404000000000001)]
    mouse_bite_origins = [[(0.2501441617742988, 0.5)], [(0.2501441617742988, 2.7140000000000004)]]
    pcb_path = '/Users/gerard/PCBs/rectangle'
    pcb_height_mm = 19.640000000000008

print('rail_origins {}'.format(rail_origins))
print('pcb_origins {}'.format(pcb_origins))
print('mouse_bite_origins: {}'.format(mouse_bite_origins))

progress = None
panel_path = os.path.abspath(os.path.join('.', 'example', 'panelized'))
rail_path = os.path.join('.', 'example', 'pcb_rails')
mouse_bite_path = os.path.join('.', 'example', 'pcb_mouse_bites')
mouse_bite_width_mm = 10.0*mouse_bite_width
mouse_bite_height_mm = 10.0*mouse_bite_height
angle = 0.0

error_msg = export_pcb_panel(progress, panel_path,
                             pcb_path, pcb_origins, pcb_height_mm,
                             rail_path, rail_origins,
                             mouse_bite_path, mouse_bite_origins, mouse_bite_width_mm, mouse_bite_height_mm,
                             angle)
