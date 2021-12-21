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


def is_pth(name):
    if '-npth' in name.lower():
        return False
    else:
        return True


def add_mousebite_drill(ctx):
    # file = hm_gerber_ex.read('mousebites.drl')
    # file.draw_mode = DxfFile.DM_MOUSE_BITES
    # file.to_metric()
    # file.width = 0.5
    # file.format = (3, 3)
    # ctx.merge(file)
    pass


def add_rails_and_mousebite_cutouts(ctx):
    # base = hm_gerber_ex.rectangle(width=100, height=100, left=0, bottom=0, units='metric')
    # base.draw_mode = DxfFile.DM_LINE
    # ctx.merge(base)
    pass


# we process drl files twice - once for 'pth' and the other for 'npth'
extensions = [
    '.gm1',
    '.gbl',
    '.gbo',
    '.gbp',
    '.gbs',
    '.gtl',
    '.gto',
    '.gtp',
    '.gts',
    '.drl',
    '.drl',
]

extensions_to_names = {
    '.gm1': 'edge_cuts',
    '.gbl': 'bottom_copper',
    '.gbo': 'bottom_silk',
    '.gbp': 'bottom_paste',
    '.gbs': 'bottom_mask',
    '.gtl': 'top_copper',
    '.gto': 'top_silk',
    '.gtp': 'top_paste',
    '.gts': 'top_mask',
    '.drl': 'drill',
}

boards = [
    ('pcb/',  0, 0, 90),
    ('pcb/', 10, 0, 0),
]

output = 'panelized'
pcb = 'panel'

os.chdir(os.path.dirname(__file__))
try:
    os.mkdir(output)
except FileExistsError:
    pass

board_count = len(boards)
pth_count = 0
npth_count = 0

# ext
for ext in extensions:
    print('PROCESS: {}'.format(ext))

    if ext == '.drl':
        ctx = DrillComposition()
    else:
        ctx = GerberComposition()

    file = None

    # board
    for directory, x_offset, y_offset, angle in boards:
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            raise TypeError('{} is not a directory.'.format(directory))

        # ext in board
        for filename in listdir(directory, True, True):
            filename_ext = os.path.splitext(filename)[1].lower()
            if ext == filename_ext:

                if ext == '.drl':
                    # first process all 'pth' drill files, then all 'npth' drill files
                    if pth_count < board_count:
                        if not is_pth(filename):
                            continue
                        else:
                            pth_count += 1
                    elif pth_count == board_count:
                        if is_pth(filename):
                            continue
                        else:
                            npth_count += 1

                print('MERGING: {}'.format(filename))
                file = hm_gerber_ex.read(os.path.join(os.path.dirname(__file__), directory, filename))
                file.to_metric()
                if angle != 0.0:
                    file.rotate(angle)
                file.offset(x_offset, y_offset)
                ctx.merge(file)
                if ext != '.drl':
                    break

    if file is not None:
        new_name = extensions_to_names.get(ext, 'unknown')
        if ext == '.drl':
            if is_pth(file.filename):
                new_name += '_pth'
            else:
                new_name += '_npth'
                add_mousebite_drill(ctx)
        elif ext == '.gm1':
            add_rails_and_mousebite_cutouts(ctx)
        ctx.dump(os.path.join(os.path.dirname(__file__), output, new_name + ext))
        print('DONE\n')
    else:
        print('SKIPPED (do not know how to handle)\n')
