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
from hm_gerber_tool.layers import PCBLayer
from hm_gerber_tool.render import GerberCairoContext, theme
from hm_gerber_tool.common import rs274x
from hm_gerber_tool.common import excellon


def log_text(progressbar, text=None, value=None):
    if progressbar is not None:
        update_progressbar(progressbar, text, value)
    elif text is not None:
        print(text)


def generate_pcb_data_layers(cwd, pcb_rel_path, data_rel_path, size=1024, progressbar=None, board_name=None):
    pcb_path = os.path.abspath(os.path.join(cwd, pcb_rel_path))
    data_path = os.path.abspath(os.path.join(cwd, data_rel_path))

    progressbar_value = 0.1

    try:
        os.mkdir(data_path)
    except FileExistsError:
        pass

    print('\n')
    if board_name is None:
        board_name = pcb_path
    text = 'Reading PCB \"{}\"'.format(board_name)
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


def generate_float46(value):
    data = ''
    float_full_str = '{:0.6f}'.format(value)
    segments = float_full_str.split('.')
    for s in segments:
        data += '{}'.format(s)
    return data


def generate_mouse_bite_gm1_data(origin, size, arc, close):
    min_x = origin[0]
    min_y = origin[1]
    max_x = min_x+size[0]
    max_y = min_y+size[1]

    data = ''
    data += '%TF.GenerationSoftware,{}*%\n'.format(APP_STR)
    data += '%TF.SameCoordinates,Original*%\n'
    data += '%TF.FileFunction,Profile,NP*%\n'
    data += '%FSLAX46Y46*%\n'
    data += 'G04 Gerber Fmt 4.6, Leading zero omitted, Abs format (unit mm)*\n'
    data += 'G04 Created by {}*\n\n'.format(APP_STR)

    data += '%MOMM*%\n'
    data += '%LPD*%\n\n'

    data += 'G04 APERTURE LIST*\n'
    data += '%TA.AperFunction,Profile*%\n'
    data += '%ADD10C,0.100000*%\n'
    data += '%TD*%\n'
    data += 'G04 APERTURE END LIST*\n'
    data += 'D10*\n\n'

    data += 'G01*\n'
    data += 'X{}Y{}D02*\n'.format(generate_float46(min_x), generate_float46(min_y))
    data += 'G75*\n'
    data += 'G03*\n'
    data += 'X{}Y{}I{}J{}D01*\n\n'.format(generate_float46(min_x+arc), generate_float46(min_y+arc),
                                          generate_float46(0), generate_float46(arc))

    data += 'G01*\n'
    data += 'X{}Y{}D02*\n'.format(generate_float46(min_x+arc), generate_float46(min_y+arc))
    data += 'X{}Y{}D01*\n\n'.format(generate_float46(min_x+arc), generate_float46(max_y-arc))

    data += 'G01*\n'
    data += 'X{}Y{}D02*\n'.format(generate_float46(min_x+arc), generate_float46(max_y-arc))
    data += 'G75*\n'
    data += 'G03*\n'
    data += 'X{}Y{}I{}J{}D01*\n\n'.format(generate_float46(min_x), generate_float46(max_y),
                                          generate_float46(-arc), generate_float46(0))

    data += 'G01*\n'
    data += 'X{}Y{}D02*\n'.format(generate_float46(max_x), generate_float46(min_y))
    data += 'G75*\n'
    data += 'G02*\n'
    data += 'X{}Y{}I{}J{}D01*\n\n'.format(generate_float46(max_x-arc), generate_float46(min_y+arc),
                                          generate_float46(0), generate_float46(arc))

    data += 'G01*\n'
    data += 'X{}Y{}D02*\n'.format(generate_float46(max_x-arc), generate_float46(min_y+arc))
    data += 'X{}Y{}D01*\n\n'.format(generate_float46(max_x-arc), generate_float46(max_y-arc))

    data += 'G01*\n'
    data += 'X{}Y{}D02*\n'.format(generate_float46(max_x-arc), generate_float46(max_y-arc))
    data += 'G75*\n'
    data += 'G02*\n'
    data += 'X{}Y{}I{}J{}D01*\n\n'.format(generate_float46(max_x), generate_float46(max_y),
                                          generate_float46(arc), generate_float46(0))

    if close:
        data += 'G01*\n'
        data += 'X{}Y{}D02*\n'.format(generate_float46(min_x), generate_float46(min_y))
        data += 'X{}Y{}D01*\n\n'.format(generate_float46(max_x), generate_float46(min_y))
        data += 'X{}Y{}D02*\n'.format(generate_float46(min_x), generate_float46(max_y))
        data += 'X{}Y{}D01*\n\n'.format(generate_float46(max_x), generate_float46(max_y))

    data += 'M02*\n\n'

    return data


def generate_mouse_bite_drl_data(origin, size, radius, gap):
    min_x = origin[0]
    min_y = origin[1]
    max_x = min_x+size[0]
    max_y = min_y+size[1]
    w = size[0]
    h = size[1]
    diameter = 2.0*radius

    data = ''
    data += 'M48'
    data += '; DRILL file {{{}}}\n'.format(APP_STR)
    data += '; FORMAT={{-:-/ absolute / metric / decimal}}\n'
    data += '; #@! TF.GenerationSoftware,{}\n'.format(APP_STR)
    data += '; #@! TF.FileFunction,NonPlated,1,2,NPTH\n'
    data += 'FMAT,2\n'
    data += 'METRIC\n\n'

    data += '; #@! TA.AperFunction,NonPlated,NPTH,ComponentDrill\n'
    data += 'T1C{:0.3f}\n'.format(diameter)
    data += '%\n'
    data += 'G90\n'
    data += 'G05\n'
    data += 'T1\n'

    unit = (radius + radius + gap)
    count = int(w / unit) - 1
    cx = min_x + (w / 2.0)
    data += 'X{:0.2f}Y{:0.2f}\n'.format(cx, min_y)
    data += 'X{:0.2f}Y{:0.2f}\n'.format(cx, max_y)
    x = 0
    for i in range(0, count):
        x += gap
        data += 'X{:0.2f}Y{:0.2f}\n'.format((cx+x), min_y)
        data += 'X{:0.2f}Y{:0.2f}\n'.format((cx-x), min_y)
        data += 'X{:0.2f}Y{:0.2f}\n'.format((cx+x), max_y)
        data += 'X{:0.2f}Y{:0.2f}\n'.format((cx-x), max_y)

    data += 'M30\n\n'

    return data


def generate_mouse_bite_gm1_files(path, filename, origin, size, arc, close, pixel_size=128):
    gm1 = generate_mouse_bite_gm1_data(origin, size, arc, close)
    data = rs274x.loads(gm1, 'dummy.gm1')
    layer = PCBLayer.from_cam(data)

    ctx = GerberCairoContext(pixel_size)
    ctx.get_outline_mask(layer, os.path.join(path, filename+'_mask'),
                         bounds=layer.bounds, verbose=False)

    ctx.render_clipped_layer(layer, False, os.path.join(path, filename),
                             theme.THEMES['Mask'], bounds=layer.bounds, verbose=False)


def generate_mouse_bite_drl_files(path, filename, origin, size, radius, gap, pixel_size=128):
    drl = generate_mouse_bite_drl_data(origin, size, radius, gap)
    data = excellon.loads(drl, 'dummy.drl')
    layer = PCBLayer.from_cam(data)

    ctx = GerberCairoContext(pixel_size)
    ctx.render_clipped_layer(layer, False, os.path.join(path, filename),
                             theme.THEMES['Mask'], bounds=layer.bounds, verbose=False)
