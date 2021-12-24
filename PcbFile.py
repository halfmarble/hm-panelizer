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

import os
import math
from os.path import join
from kivy.uix.image import Image
from kivy.graphics import Scale, Rectangle, Line

from Constants import *
from Utilities import *
from OffScreenImage import *

from hm_gerber_tool import PCB
from hm_gerber_tool.render import theme
from hm_gerber_tool.render.cairo_backend import GerberCairoContext


def log_text(progressbar, text=None, value=None):
    if progressbar is not None:
        update_progressbar(progressbar, text, value)
    elif text is not None:
        print(text)


def generate_pcb_data_layers(cwd, pcb_rel_path, data_rel_path, size=1024, progressbar=None):
    pcb_path = os.path.abspath(os.path.join(cwd, pcb_rel_path))
    data_path = os.path.abspath(os.path.join(cwd, data_rel_path))

    progressbar_value = 0.1

    try:
        os.mkdir(data_path)
    except FileExistsError:
        pass

    print('\n')
    text = 'Reading PCB \"{}\"...'.format(pcb_path)
    log_text(progressbar, text, progressbar_value)
    pcb = PCB.from_directory(pcb_path, verbose=True)
    print('\n')

    progressbar_value = 0.25
    for layer in pcb.layers:
        text = 'Found layer \"{}\"'.format(layer.name())
        log_text(progressbar, text, progressbar_value)
    print('\n')

    ctx = GerberCairoContext(size)

    bounds = pcb.board_bounds
    get_outline = True
    clip_to_outline = False
    print_outline = False

    if get_outline:
        file_path = os.path.join(data_path, 'edge_cuts_mask')
        layer = pcb.edge_cuts_layer
        if layer is not None:
            text = 'Rendering mask for layer \"{}\"'.format(layer.name())
            progressbar_value = 0.5
            log_text(progressbar, text, progressbar_value)
            outline_str = ctx.get_outline_mask(layer, file_path, bounds=bounds, verbose=False)
            if print_outline and outline_str is not None:
                print('\n{}'.format(outline_str))

    layers = pcb.layers
    progressbar_advance = 0.5 / len(layers)
    for layer in pcb.layers:
        file_path = os.path.join(data_path, '{}'.format(layer.name()))
        text = 'Rendering layer \"{}\"'.format(layer.name())
        log_text(progressbar, text, progressbar_value)
        progressbar_value += progressbar_advance
        ctx.render_clipped_layer(layer, clip_to_outline, file_path, theme.THEMES['Mask'], bounds=bounds,
                                 background=False, verbose=False)

    log_text(progressbar, 'Done', 1.0)

    print('\n')

