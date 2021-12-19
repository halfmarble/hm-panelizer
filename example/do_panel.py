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

import hm_gerber_ex
from hm_gerber_ex import GerberComposition, DrillComposition
from hm_gerber_tool.utils import listdir

extensions = ['.gtl']
#extensions = ['.gm1', '.gbl', '.gbo', '.gbp', '.gbs', '.gtl', '.gto', '.gtp', '.gts', '.drl']
# '.gm1'

boards = [
    ('pcb/',  0, 0, 0),
#    ('pcb/', 65, 0, 0),
]

output = 'panelized'
pcb = 'panel'

os.chdir(os.path.dirname(__file__))
try:
    os.mkdir(output)
except FileExistsError:
    pass

for ext in extensions:
    print('PROCESS: {}'.format(ext))

    if ext == '.drl':
        ctx = DrillComposition()
    else:
        ctx = GerberComposition()

    for directory, x_offset, y_offset, angle in boards:
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            raise TypeError('{} is not a directory.'.format(directory))

        for filename in listdir(directory, True, True):
            filename_ext = os.path.splitext(filename)[1].lower()
            if ext == filename_ext:
                file = hm_gerber_ex.read(os.path.join(os.path.dirname(__file__), directory, filename))
                file.to_metric()
                if angle != 0.0:
                    file.rotate(angle)
                file.offset(x_offset, y_offset)
                ctx.merge(file)
                print('.')
                break

    # if ext != '.drl':
    #     file = hm_gerber_ex.read(outline)
    #     ctx.merge(file)
    # else:
    #     file = hm_gerber_ex.read(mousebites)
    #     file.draw_mode = DxfFile.DM_MOUSE_BITES
    #     file.to_metric()
    #     file.width = 0.5
    #     file.format = (3, 3)
    #     ctx.merge(file)

    ctx.dump(os.path.join(os.path.dirname(__file__), output, pcb + ext))
    print('DONE\n')

# output_text('generating GML: ')
# file = hm_gerber_ex.read(outline)
# file.write(outputs + '.GML')
# output_text('.')
# ctx = GerberComposition()
# base = hm_gerber_ex.rectangle(width=100, height=100, left=0, bottom=0, units='metric')
# base.draw_mode = DxfFile.DM_LINE
# ctx.merge(base)
# output_text('. end\n')
