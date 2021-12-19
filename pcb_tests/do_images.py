#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 HalfMarble LLC

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

from hm_gerber_tool import PCB
from hm_gerber_tool.render import theme
from hm_gerber_tool.render.cairo_backend import GerberCairoContext

os.chdir(os.path.dirname(__file__))
pcb = PCB.from_directory(os.path.join(os.path.dirname('.')), verbose=True)

max_size = 800
ctx = GerberCairoContext(max_size)

bounds = pcb.board_bounds
get_outline = False
clip_to_outline = False
print_outline = False

if get_outline:
    outline_str = ctx.get_outline_mask(pcb.outline_layer, os.path.join(os.path.dirname('.'), output, 'outlinemask.png'),
                                       bounds=bounds, verbose=False)
    if print_outline and outline_str is not None:
        print('\n{}'.format(outline_str))

for layer in pcb.layers:
    ctx.render_clipped_layer(layer, clip_to_outline,
                             os.path.join(os.path.dirname('.'), '{}.png'.format(layer.name())),
                             theme.THEMES['Mask'], bounds=bounds, background=False, verbose=False)

# layer = pcb.layers[0]
# ctx.render_clipped_layer(layer, clip_to_outline,
#                          os.path.join(os.path.dirname(__file__), '{}.png'.format(layer.name())),
#                          theme.THEMES['Mask'], bounds=bounds, background=False, verbose=True)
