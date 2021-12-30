# Copyright 2021,2022 HalfMarble LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Final
from kivy.graphics import Color
from posixpath import join


VERSION_STR: Final              = '1.0.0 (alpha)'
APP_STR: Final                  = 'hm-panelizer {}'.format(VERSION_STR)

ALLOW_DIR_DELETIONS: Final      = True

DEMO_PCB_PATH_STR: Final        = join('data', 'example_pcb', 'NEAToBOARD')

# careful: the higher the number the better the resolution, but needs more VRAM
PIXELS_PER_MM: Final            = 16

PIXELS_SIZE_MIN: Final          = 128
# super careful (do not go above 4096, unless you have a good GPU and lots of VRAM)
PIXELS_SIZE_MAX: Final          = 2048

PCB_OUTLINE_WIDTH: Final        = 1.5

INITIAL_ROWS: Final             = 2
INITIAL_COLUMNS: Final          = 2
MAX_ROWS: Final                 = 99
MAX_COLUMNS: Final              = 99

# the ratio of the pcb board to the available window size at 100% zoom
FIT_SCALE: Final                = 0.9

PCB_PANEL_USE_VCUT: Final       = True
PCB_PANEL_USE_JLC: Final        = True

PCB_PANEL_GAP_MM: Final         = 5

# no less than 5mm
PCB_PANEL_RAIL_HEIGHT_MM: Final = 5

PCB_PANEL_BITES_SIZE_MM: Final  = 5
PCB_PANEL_BITES_COUNT_X: Final  = 2

# leave at 0, unimplemented yet
PCB_PANEL_BITES_COUNT_Y: Final  = 0

PCB_BITES_HOLE_RADIUS_MM: Final = 0.15
PCB_BITES_HOLE_SPACE_MM: Final  = 0.6

GRID_BACKGROUND_COLOR: Final    = Color(0.95, 0.95, 0.95, 1.0)
GRID_MAJOR_COLOR: Final         = Color(0.50, 0.50, 0.50, 1.0)
GRID_MINOR_COLOR: Final         = Color(0.80, 0.80, 0.80, 1.0)

PCB_MASK_COLOR: Final           = Color(0.15, 0.35, 0.15, 1.00)
PCB_OUTLINE_COLOR: Final        = Color(0.00, 0.00, 0.00, 1.00)
PCB_TOP_PASTE_COLOR: Final      = Color(0.55, 0.55, 0.55, 1.00)
PCB_TOP_SILK_COLOR: Final       = Color(0.95, 0.95, 0.95, 1.00)
PCB_TOP_MASK_COLOR: Final       = Color(0.75, 0.65, 0.00, 1.00)
PCB_TOP_TRACES_COLOR: Final     = Color(0.00, 0.50, 0.00, 0.50)
PCB_BOTTOM_TRACES_COLOR: Final  = Color(0.00, 0.50, 0.00, 0.50)
PCB_BOTTOM_MASK_COLOR: Final    = Color(0.75, 0.65, 0.00, 1.00)
PCB_BOTTOM_SILK_COLOR: Final    = Color(0.95, 0.95, 0.95, 1.00)
PCB_BOTTOM_PASTE_COLOR: Final   = Color(0.55, 0.55, 0.55, 1.00)
PCB_DRILL_NPTH_COLOR: Final     = Color(0.10, 0.10, 0.10, 0.80)
PCB_DRILL_PTH_COLOR: Final      = Color(0.65, 0.55, 0.00, 0.50)

PCB_BITE_GOOD_COLOR: Final      = Color(0.25, 0.85, 0.25, 0.75)
PCB_BITE_BAD_COLOR: Final       = Color(0.85, 0.25, 0.25, 0.75)
