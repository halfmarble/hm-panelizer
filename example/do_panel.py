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

row1_height = 0.5
row2_height = 1.25

rail_origins = \
[
    (0, 0),
    (0, 1.5),
]
pcb_origins = \
[
    (0, row1_height+mouse_bite_height),
]
mouse_bite_origins = \
[
    [(3.0, row1_height)],
    [(3.0, row2_height)],
]
print('rail_origins {}'.format(rail_origins))
print('pcb_origins {}'.format(pcb_origins))
print('mouse_bite_origins: {}'.format(mouse_bite_origins))

progress = None
panel_path = os.path.abspath(os.path.join('.', 'example', 'panelized'))
pcb_path = os.path.join('.', 'example', 'pcb_rails')
pcb_height_mm = 5.0
rail_path = os.path.join('.', 'example', 'pcb_rails')
mouse_bite_path = os.path.join('.', 'example', 'pcb_mouse_bites')
mouse_bite_width_mm = 5.0
mouse_bite_height_mm = 2.5
angle = 0.0

error_msg = export_pcb_panel(progress, panel_path,
                             pcb_path, pcb_origins, pcb_height_mm,
                             rail_path, rail_origins,
                             mouse_bite_path, mouse_bite_origins, mouse_bite_width_mm, mouse_bite_height_mm,
                             angle)
