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
from hm_gerber_tool.cam import FileSettings


def is_pth(name):
    if '-npth' in name.lower():
        return False
    else:
        return True


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

settings = FileSettings(format=(3, 3), zeros='decimal')
ctx_npth_drl = DrillComposition(settings)
ctx_pth_drl = DrillComposition(settings)
ctx = None

board_count = len(boards)


# ext
for ext in extensions:
    print('\nPROCESS: {}'.format(ext))

    if ext != '.drl':
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
                    if is_pth(filename):
                        ctx = ctx_pth_drl
                    else:
                        ctx = ctx_npth_drl

                print('MERGING: {}'.format(filename))
                file = hm_gerber_ex.read(os.path.join(os.path.dirname(__file__), directory, filename))
                file.to_metric()
                if angle != 0.0:
                    file.rotate(angle)
                file.offset(x_offset, y_offset)
                ctx.merge(file)

    if file is not None and ext != '.drl':
        new_name = extensions_to_names.get(ext, 'unknown')
        full_path = os.path.join(os.path.dirname(__file__), output, new_name + ext)
        print('\nWRITING: {}'.format(full_path))
        ctx.dump(full_path)
        print('DONE\n')

full_path = os.path.join(os.path.dirname(__file__), output, 'drill-NPTH.drl')
print('\nWRITING: {}'.format(full_path))
ctx_npth_drl.dump(full_path)
print('DONE\n')

full_path = os.path.join(os.path.dirname(__file__), output, 'drill-PTH.drl')
print('\nWRITING: {}'.format(full_path))
ctx_pth_drl.dump(full_path)
print('DONE\n')