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


from typing import Final
from kivy.graphics import Color
from posixpath import join


VERSION_STR: Final              = '1.0.0 (beta)'
APP_NAME: Final                 = 'hm-panelizer'
APP_STR: Final                  = '{} {}'.format(APP_NAME, VERSION_STR)
VENDOR_NAME: Final              = 'halfmarble'

ALLOW_DIR_DELETIONS: Final      = True

DEMO_PCB_PATH_STR: Final        = join('data', 'demo_pcb', 'NEAToBOARD')

# careful: the higher the number the better the resolution, but needs more VRAM
PIXELS_PER_MM: Final            = 8

PIXELS_SIZE_MIN: Final          = 256
# super careful (do not go above 4096, unless you have a good GPU and lots of VRAM)
PIXELS_SIZE_MAX: Final          = 1024

PCB_OUTLINE_WIDTH: Final        = 1.5

INITIAL_ROWS: Final             = 1
INITIAL_COLUMNS: Final          = 1
MAX_ROWS: Final                 = 99
MAX_COLUMNS: Final              = 99

# the ratio of the pcb board to the available window size at 100% zoom
FIT_SCALE: Final                = 0.9

PCB_PANEL_USE_VCUT: Final       = True
PCB_PANEL_USE_JLC: Final        = False

PCB_PANEL_GAP_MM: Final         = 3.0

# no less than 5mm
PCB_PANEL_RAIL_HEIGHT_MM: Final = 6.0

PCB_PANEL_BITES_SIZE_MM: Final  = 4.8
PCB_PANEL_BITES_COUNT_X: Final  = 1
# leave at 0, unimplemented yet
PCB_PANEL_BITES_COUNT_Y: Final  = 0

PCB_BITES_HOLE_RADIUS_MM: Final = 0.2
PCB_BITES_HOLE_SPACE_MM: Final  = 0.6

# OSH Park recommends minimum of 0.8636
PCB_BITES_ARC_MM: Final         = 1.0

# https://docs.oshpark.com/troubleshooting/panelized-designs/
OSHPARK_PCB_PANEL_RAIL_HEIGHT_MM: Final = 5.08
OSHPARK_PCB_PANEL_GAP_MM: Final         = 2.54
OSHPARK_PCB_BITES_HOLE_RADIUS_MM: Final = 0.254
OSHPARK_PCB_BITES_HOLE_SPACE_MM: Final  = 0.508
OSHPARK_PCB_PANEL_BITES_SIZE_MM: Final  = (PCB_BITES_ARC_MM+2.54+PCB_BITES_ARC_MM)
OSHPARK_PCB_PANEL_VCUT: Final           = False

# JLC PCB (TODO need verified values)
JLC_PCB_PANEL_RAIL_HEIGHT_MM: Final = PCB_PANEL_RAIL_HEIGHT_MM
JLC_PCB_PANEL_GAP_MM: Final         = PCB_PANEL_GAP_MM
JLC_PCB_BITES_HOLE_RADIUS_MM: Final = PCB_BITES_HOLE_RADIUS_MM
JLC_PCB_BITES_HOLE_SPACE_MM: Final  = PCB_BITES_HOLE_SPACE_MM
JLC_PCB_PANEL_BITES_SIZE_MM: Final  = (PCB_BITES_ARC_MM+3.0+PCB_BITES_ARC_MM)
JLC_PCB_PANEL_VCUT: Final           = True

# PCB Way (TODO need verified values)
PCBWAY_PCB_PANEL_RAIL_HEIGHT_MM: Final = PCB_PANEL_RAIL_HEIGHT_MM
PCBWAY_PCB_PANEL_GAP_MM: Final         = PCB_PANEL_GAP_MM
PCBWAY_PCB_BITES_HOLE_RADIUS_MM: Final = PCB_BITES_HOLE_RADIUS_MM
PCBWAY_PCB_BITES_HOLE_SPACE_MM: Final  = PCB_BITES_HOLE_SPACE_MM
PCBWAY_PCB_PANEL_BITES_SIZE_MM: Final  = (PCB_BITES_ARC_MM+3.0+PCB_BITES_ARC_MM)
PCBWAY_PCB_PANEL_VCUT: Final           = True

# in mm
PCB_PANEL_MERGE_ERROR: Final    = 0.15


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
PCB_DRILL_NPTH_COLOR: Final     = Color(0.12, 0.12, 0.12, 0.80)
PCB_DRILL_PTH_COLOR: Final      = Color(0.30, 0.15, 0.00, 0.50)

PCB_BITE_GOOD_COLOR: Final      = Color(0.25, 0.85, 0.25, 0.75)
PCB_BITE_BAD_COLOR: Final       = Color(0.85, 0.25, 0.25, 0.75)
