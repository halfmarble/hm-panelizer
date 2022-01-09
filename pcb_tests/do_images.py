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
