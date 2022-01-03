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


def generate_pcb_data_layers(cwd, pcb_rel_path, data_rel_path, progressbar=None, board_name=None):
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

    bounds = pcb.board_bounds
    get_outline = True
    clip_to_outline = False
    print_outline = False

    size = bounds_to_size(bounds)
    resolution = size_to_resolution(size, PIXELS_PER_MM, PIXELS_SIZE_MIN, PIXELS_SIZE_MAX)
    ctx = GerberCairoContext(resolution)

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


# converts from:
# X14410952Y3047620D02*
# to code like:
#    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.4110), generate_float46(oy+3.0476))
# suitable for generate_*_text_data functions
def convert_grbl_to_code(path, file_name, offset_x, offset_y):
    file = load_file(path, file_name)
    segments = file.split("\n")
    for s in segments:
        s = s.replace('X', ' ').replace('Y', ' ').replace('D', ' ')
        parts = s.split(" ")

        x = parts[1]
        x = insert_str(x, '.', len(x) - 6)
        x = str_to_float(x) - offset_x
        x = '{:+0.4f}'.format(x)

        y = parts[2]
        y = insert_str(y, '.', len(y) - 6)
        y = str_to_float(y) - offset_y
        y = '{:+0.4f}'.format(y)

        d = parts[3]

        print('    data += \'X{{}}Y{{}}D{}\\n\'.format(generate_float46(ox{}), generate_float46(oy{}))'.format(d, x, y))


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

    data += 'M02*\n'
    return data


def generate_rail_gm1_data(origin, size, panels, vcut):
    min_x = origin[0]
    min_y = origin[1]
    max_x = min_x+size[0]
    max_y = min_y+size[1]
    width = size[0]

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
    data += 'X{}Y{}D01*\n'.format(generate_float46(max_x), generate_float46(min_y))
    data += 'X{}Y{}D02*\n'.format(generate_float46(max_x), generate_float46(min_y))
    data += 'X{}Y{}D01*\n'.format(generate_float46(max_x), generate_float46(max_y))
    data += 'X{}Y{}D02*\n'.format(generate_float46(min_x), generate_float46(max_y))
    data += 'X{}Y{}D01*\n'.format(generate_float46(max_x), generate_float46(max_y))
    data += 'X{}Y{}D02*\n'.format(generate_float46(min_x), generate_float46(max_y))
    data += 'X{}Y{}D01*\n\n'.format(generate_float46(min_x), generate_float46(min_y))

    if vcut and panels > 1:
        section = width / float(panels)
        x = min_x
        for i in range(0, panels-1):
            x += section
            data += 'X{}Y{}D02*\n'.format(generate_float46(x), generate_float46(max_y))
            data += 'X{}Y{}D01*\n'.format(generate_float46(x), generate_float46(min_y))
            data += '\n\n'

    data += 'M02*\n'
    return data


def generate_jlcjlcjlcjlc_text_data(origin, aperture):
    ox = origin[0]
    oy = origin[1]

    data = ''
    data += 'D{}*\n'.format(aperture)
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.4110), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4110), generate_float46(oy-0.1667))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.3633), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.2681), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1252), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0300), generate_float46(oy-0.4524))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+1.3633), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8871), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8871), generate_float46(oy+0.5476))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+2.2681), generate_float46(oy-0.3571))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.2205), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.0776), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.9824), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.8395), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.7443), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.6967), generate_float46(oy-0.2143))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.6490), generate_float46(oy-0.0238))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.6490), generate_float46(oy+0.1190))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.6967), generate_float46(oy+0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.7443), generate_float46(oy+0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.8395), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+1.9824), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.0776), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.2205), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.2681), generate_float46(oy+0.4524))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+2.9824), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.9824), generate_float46(oy-0.1667))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.9348), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.8395), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.6967), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+2.6014), generate_float46(oy-0.4524))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+3.9348), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+3.4586), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+3.4586), generate_float46(oy+0.5476))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+4.8395), generate_float46(oy-0.3571))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.7919), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.6490), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.5538), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.4110), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.3157), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.2681), generate_float46(oy-0.2143))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.2205), generate_float46(oy-0.0238))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.2205), generate_float46(oy+0.1190))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.2681), generate_float46(oy+0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.3157), generate_float46(oy+0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.4110), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.5538), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.6490), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.7919), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+4.8395), generate_float46(oy+0.4524))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+5.5538), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+5.5538), generate_float46(oy-0.1667))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+5.5062), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+5.4110), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+5.2681), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+5.1729), generate_float46(oy-0.4524))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+6.5062), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.0300), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.0300), generate_float46(oy+0.5476))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+7.4110), generate_float46(oy-0.3571))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.3633), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.2205), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.1252), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.9824), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.8871), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.8395), generate_float46(oy-0.2143))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.7919), generate_float46(oy-0.0238))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.7919), generate_float46(oy+0.1190))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.8395), generate_float46(oy+0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.8871), generate_float46(oy+0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+6.9824), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.1252), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.2205), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.3633), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.4110), generate_float46(oy+0.4524))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+8.1252), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+8.1252), generate_float46(oy-0.1667))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+8.0776), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.9824), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.8395), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+7.7443), generate_float46(oy-0.4524))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+9.0776), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+8.6014), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+8.6014), generate_float46(oy+0.5476))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+9.9824), generate_float46(oy-0.3571))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.9348), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.7919), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.6967), generate_float46(oy-0.4524))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.5538), generate_float46(oy-0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.4586), generate_float46(oy-0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.4110), generate_float46(oy-0.2143))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.3633), generate_float46(oy-0.0238))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.3633), generate_float46(oy+0.1190))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.4110), generate_float46(oy+0.3095))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.4586), generate_float46(oy+0.4048))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.5538), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.6967), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.7919), generate_float46(oy+0.5476))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.9348), generate_float46(oy+0.5000))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+9.9824), generate_float46(oy+0.4524))

    data += '\n'
    return data


def generate_vscore_text_data(origin, aperture):
    ox = origin[0]
    oy = origin[1]

    data = ''
    data += 'D{}*\n'.format(aperture)

    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+0.5500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+0.7833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+1.0167))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.8036), generate_float46(oy+1.2167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+1.3167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+1.4833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8036), generate_float46(oy+1.5500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.7679), generate_float46(oy+1.5833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.6964), generate_float46(oy+1.6167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.6250), generate_float46(oy+1.6167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.5536), generate_float46(oy+1.5833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.5179), generate_float46(oy+1.5500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4821), generate_float46(oy+1.4833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4464), generate_float46(oy+1.3500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4107), generate_float46(oy+1.2833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.3750), generate_float46(oy+1.2500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.3036), generate_float46(oy+1.2167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.2321), generate_float46(oy+1.2167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1607), generate_float46(oy+1.2500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1250), generate_float46(oy+1.2833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+1.3500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+1.5167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1250), generate_float46(oy+1.6167))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.7679), generate_float46(oy+2.3167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8036), generate_float46(oy+2.2833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+2.1833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+2.1167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8036), generate_float46(oy+2.0167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.7321), generate_float46(oy+1.9500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.6607), generate_float46(oy+1.9167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.5179), generate_float46(oy+1.8833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4107), generate_float46(oy+1.8833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.2679), generate_float46(oy+1.9167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1964), generate_float46(oy+1.9500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1250), generate_float46(oy+2.0167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+2.1167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+2.1833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1250), generate_float46(oy+2.2833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1607), generate_float46(oy+2.3167))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+2.7500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+2.8833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1250), generate_float46(oy+2.9500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1964), generate_float46(oy+3.0167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.3393), generate_float46(oy+3.0500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.5893), generate_float46(oy+3.0500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.7321), generate_float46(oy+3.0167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8036), generate_float46(oy+2.9500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+2.8833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+2.7500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8036), generate_float46(oy+2.6833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.7321), generate_float46(oy+2.6167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.5893), generate_float46(oy+2.5833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.3393), generate_float46(oy+2.5833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1964), generate_float46(oy+2.6167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1250), generate_float46(oy+2.6833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+2.7500))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+3.7500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4821), generate_float46(oy+3.5167))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+3.3500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+3.3500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+3.6167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1250), generate_float46(oy+3.6833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.1607), generate_float46(oy+3.7167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.2321), generate_float46(oy+3.7500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.3393), generate_float46(oy+3.7500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4107), generate_float46(oy+3.7167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4464), generate_float46(oy+3.6833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4821), generate_float46(oy+3.6167))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4821), generate_float46(oy+3.3500))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.4464), generate_float46(oy+4.0500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.4464), generate_float46(oy+4.2833))
    data += 'X{}Y{}D02*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+4.3833))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.8393), generate_float46(oy+4.0500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+4.0500))
    data += 'X{}Y{}D01*\n'.format(generate_float46(ox+0.0893), generate_float46(oy+4.3833))

    data += '\n'
    return data


def generate_rail_gto_data(origin, size, panels, vcut, jlc):
    min_x = origin[0]
    min_y = origin[1]
    max_x = min_x+size[0]
    max_y = min_y+size[1]
    width = size[0]
    height = size[1]

    data = ''
    data += '%TF.GenerationSoftware,{}*%\n'.format(APP_STR)
    data += '%TF.SameCoordinates,Original*%\n'
    data += '%TF.FileFunction,Legend,Top*%\n'
    data += '%TF.FilePolarity,Positive*%\n'
    data += '%FSLAX46Y46*%\n'
    data += 'G04 Gerber Fmt 4.6, Leading zero omitted, Abs format (unit mm)*\n'
    data += 'G04 Created by {}*\n\n'.format(APP_STR)

    data += '%MOMM*%\n'
    data += '%LPD*%\n\n'

    data += 'G04 APERTURE LIST*\n'
    data += '%TA.AperFunction,Profile*%\n'
    data += '%ADD10C,0.150000*%\n'
    data += '%ADD11C,0.125000*%\n'
    data += 'G04 APERTURE END LIST*\n\n'

    if jlc:
        data += generate_jlcjlcjlcjlc_text_data(origin=(10, height/2.0), aperture=10)

    if vcut and panels > 0:
        section = width / float(panels)
        x = min_x
        for i in range(0, panels - 1):
            x += section
            data += 'D10*\n'
            data += 'X{}Y{}D02*\n'.format(generate_float46(x), generate_float46(max_y))
            data += 'X{}Y{}D01*\n\n'.format(generate_float46(x), generate_float46(min_y))
            data += generate_vscore_text_data(origin=(x+0.5, 0.0), aperture=11)

    data += 'M02*\n'
    return data


def generate_rail_gtl_data(origin, size):
    min_x = origin[0]
    min_y = origin[1]
    max_x = min_x+size[0]
    max_y = min_y+size[1]
    height = size[1]

    offset = 5
    y = min_x + (height / 2.0)

    data = ''
    data += '%TF.GenerationSoftware,{}*%\n'.format(APP_STR)
    data += '%TF.SameCoordinates,Original*%\n'
    data += '%TF.FileFunction,Copper,L1,Top*%\n'
    data += '%TF.FilePolarity,Positive*%\n'
    data += '%FSLAX46Y46*%\n'
    data += 'G04 Gerber Fmt 4.6, Leading zero omitted, Abs format (unit mm)*\n'
    data += 'G04 Created by {}*\n\n'.format(APP_STR)

    data += '%MOMM*%\n'
    data += '%LPD*%\n\n'

    data += 'G04 APERTURE LIST*\n'
    data += '%TA.AperFunction,SMDPad,CuDef*%\n'
    data += '%ADD10C,1.000000*%\n'
    data += '%TD*%\n'
    data += 'G04 APERTURE END LIST*\n'
    data += 'D10*\n\n'

    data += 'G01*\n'
    data += 'X{}Y{}D03*\n'.format(generate_float46(min_x+offset), generate_float46(y))

    x = min_x
    while x < max_x:
        x += 10
    x -= 10
    data += 'X{}Y{}D03*\n'.format(generate_float46(x), generate_float46(y))

    data += 'M02*\n'
    return data


def generate_rail_gts_data(origin, size):
    min_x = origin[0]
    min_y = origin[1]
    max_x = min_x+size[0]
    max_y = min_y+size[1]
    height = size[1]

    offset = 5
    y = min_x + (height / 2.0)

    data = ''
    data += '%TF.GenerationSoftware,{}*%\n'.format(APP_STR)
    data += '%TF.SameCoordinates,Original*%\n'
    data += '%TF.FileFunction,Soldermask,Top*%\n'
    data += '%TF.FilePolarity,Negative*%\n'
    data += '%FSLAX46Y46*%\n'
    data += 'G04 Gerber Fmt 4.6, Leading zero omitted, Abs format (unit mm)*\n'
    data += 'G04 Created by {}*\n\n'.format(APP_STR)

    data += '%MOMM*%\n'
    data += '%LPD*%\n\n'

    data += 'G04 APERTURE LIST*\n'
    data += '%TA.AperFunction,SMDPad,CuDef*%\n'
    data += '%ADD10C,2.000000*%\n'
    data += 'G04 APERTURE END LIST*\n'
    data += 'D10*\n\n'

    data += 'G01*\n'
    data += 'X{}Y{}D03*\n'.format(generate_float46(min_x+offset), generate_float46(y))

    x = min_x
    while x < max_x:
        x += 10
    x -= 10
    data += 'X{}Y{}D03*\n'.format(generate_float46(x), generate_float46(y))

    data += 'M02*\n'
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
    data += 'X{}Y{}\n'.format(generate_decfloat3(cx), generate_decfloat3(min_y))
    data += 'X{}Y{}\n'.format(generate_decfloat3(cx), generate_decfloat3(max_y))
    x = 0
    for i in range(0, count):
        x += gap
        data += 'X{}Y{}\n'.format(generate_decfloat3(cx+x), generate_decfloat3(min_y))
        data += 'X{}Y{}\n'.format(generate_decfloat3(cx-x), generate_decfloat3(min_y))
        data += 'X{}Y{}\n'.format(generate_decfloat3(cx+x), generate_decfloat3(max_y))
        data += 'X{}Y{}\n'.format(generate_decfloat3(cx-x), generate_decfloat3(max_y))

    data += 'M30\n'
    return data


def render_pcb_layer(bounds, layer, path, filename, outline=False, verbose=False):
    if bounds is None:
        bounds = layer.bounds
    size = bounds_to_size(bounds)
    resolution = size_to_resolution(size, PIXELS_PER_MM, PIXELS_SIZE_MIN, PIXELS_SIZE_MAX)
    ctx = GerberCairoContext(resolution)
    if outline:
        ctx.get_outline_mask(layer, os.path.join(path, filename+'_mask'),
                             bounds=bounds, verbose=verbose)
    ctx.render_clipped_layer(layer, False, os.path.join(path, filename),
                             theme.THEMES['Mask'], bounds=bounds, verbose=verbose)


def save_mouse_bite_gm1(path, origin, size, arc, close):
    gm1 = generate_mouse_bite_gm1_data(origin, size, arc, close)
    with open(os.path.join(path, 'Mouse_Bites-Edge_Cuts.gm1'), "w") as text_file:
        text_file.write(gm1)


def render_mouse_bite_gm1(path, filename, origin, size, arc, close):
    gm1 = generate_mouse_bite_gm1_data(origin, size, arc, close)
    data = rs274x.loads(gm1, 'dummy.gm1')
    layer = PCBLayer.from_cam(data)
    render_pcb_layer(layer.bounds, layer, path, filename, outline=True)


def save_mouse_bite_drl(path, origin, size, radius, gap):
    drl = generate_mouse_bite_drl_data(origin, size, radius, gap)
    with open(os.path.join(path, 'Mouse_Bites-NPTH.drl'), "w") as text_file:
        text_file.write(drl)


def render_mouse_bite_drl(path, filename, origin, size, radius, gap):
    drl = generate_mouse_bite_drl_data(origin, size, radius, gap)
    data = excellon.loads(drl, 'dummy.drl')
    layer = PCBLayer.from_cam(data)
    render_pcb_layer(layer.bounds, layer, path, filename)


def save_rail_gm1(path, origin, size, panels, vcut):
    gm1 = generate_rail_gm1_data(origin, size, panels, vcut)
    with open(os.path.join(path, 'Rails-Edge_Cuts.gm1'), "w") as text_file:
        text_file.write(gm1)


def render_rail_gm1(path, filename, origin, size, panels, vcut):
    gm1 = generate_rail_gm1_data(origin, size, panels, vcut)
    data = rs274x.loads(gm1, 'dummy.gm1')
    layer = PCBLayer.from_cam(data)
    render_pcb_layer(layer.bounds, layer, path, filename, outline=True)
    return layer.bounds


def save_rail_gtl(path, origin, size):
    gtl = generate_rail_gtl_data(origin, size)
    with open(os.path.join(path, 'Rails-F_Cu.gtl'), "w") as text_file:
        text_file.write(gtl)


def render_rail_gtl(bounds, path, filename, origin, size):
    gtl = generate_rail_gtl_data(origin, size)
    data = rs274x.loads(gtl, 'dummy.gtl')
    layer = PCBLayer.from_cam(data)
    render_pcb_layer(bounds, layer, path, filename)


def save_rail_gts(path, origin, size):
    gts = generate_rail_gts_data(origin, size)
    with open(os.path.join(path, 'Rails-F_Mask.gts'), "w") as text_file:
        text_file.write(gts)


def render_rail_gts(bounds, path, filename, origin, size):
    gts = generate_rail_gts_data(origin, size)
    data = rs274x.loads(gts, 'dummy.gts')
    layer = PCBLayer.from_cam(data)
    render_pcb_layer(bounds, layer, path, filename)


def save_rail_gto(path, origin, size, panels, vcut, jlc):
    gto = generate_rail_gto_data(origin, size, panels, vcut, jlc)
    with open(os.path.join(path, 'Rails-F_Silkscreen.gto'), "w") as text_file:
        text_file.write(gto)


def render_rail_gto(bounds, path, filename, origin, size, panels, vcut, jlc):
    gto = generate_rail_gto_data(origin, size, panels, vcut, jlc)
    data = rs274x.loads(gto, 'dummy.gto')
    layer = PCBLayer.from_cam(data)
    render_pcb_layer(bounds, layer, path, filename)


