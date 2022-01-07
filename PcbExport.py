# Copyright 2021,2022 HalfMarble LLC

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

import hm_gerber_ex
from Utilities import update_progressbar

from hm_gerber_ex import GerberComposition, DrillComposition
from hm_gerber_tool.cam import FileSettings
from hm_gerber_tool.utils import listdir


def is_pth(name):
    if '-npth' in name.lower():
        return False
    else:
        return True


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


def export_pcb_panel(progress, path_export, path_pcb, pcb_count, pcb_height,
                     path_rails, path_mouse_bites, mouse_bites_count, origins, mouse_bites_cutouts, angle):
    print('\nexport_pcb_panel')
    print(' path_export: {}'.format(path_export))
    print(' path_pcb: {}'.format(path_pcb))
    print(' pcb_count: {}'.format(pcb_count))
    print(' pcb_height: {}'.format(pcb_height))
    print(' path_rails: {}'.format(path_rails))
    print(' path_mouse_bites: {}'.format(path_mouse_bites))
    print(' mouse_bites_count: {}'.format(mouse_bites_count))
    print(' origins: {}'.format(origins))
    print(' mouse_bites_cutouts: {}'.format(mouse_bites_cutouts))
    print(' angle: {}'.format(angle))

    paths = [path_rails, path_rails]
    for i in range(pcb_count):
        paths.append(path_pcb)
    for i in range(mouse_bites_count):
        paths.append(path_mouse_bites)
    #print(' paths: {}'.format(paths))

    angles = [0.0, 0.0]
    for i in range(pcb_count):
        angles.append(angle)
    for i in range(mouse_bites_count):
        angles.append(0.0)
    #print(' angles: {}'.format(angles))

    board_count = len(paths)
    boards = []
    for i in range(board_count):
        path = paths[i]
        origin = origins[i]
        rotate = angles[i]
        offset_x = 0.0
        if rotate != 0:
            offset_x = pcb_height
        boards.append((path, offset_x+10.0*origin[0], 10.0*origin[1], rotate))
    #print(' boards: {}'.format(boards))

    for directory, x_offset, y_offset, angle in boards:
        directory = os.path.abspath(directory)
        print('\nfiles in {}:'.format(directory))
        for filename in listdir(directory, True, True):
            print(' {}'.format(filename))
    print('\n\n')

    settings = FileSettings(format=(3, 3), zeros='decimal')
    ctx_npth_drl = DrillComposition(settings)
    ctx_pth_drl = DrillComposition(settings)
    ctx = None

    progress_steps = 12.0
    progress_value = 0.2
    progress_chunk = (1.0 - progress_value) / progress_steps

    # ext
    for ext in extensions:
        print('\nPROCESS: {}'.format(ext))

        progress_value += progress_chunk
        update_progressbar(progress, 'exporting panel{} ...'.format(ext), progress_value)

        if ext != '.drl':
            cutout_lines = None
            if ext == '.gm1':
                cutout_lines = mouse_bites_cutouts
            ctx = GerberComposition(cutout_lines=cutout_lines)
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

                    full_path = os.path.join(directory, filename)
                    print(' FILE: {}'.format(filename))
                    file = hm_gerber_ex.read(full_path)
                    file.to_metric()
                    if angle != 0.0:
                        print(' ROTATING')
                        file.rotate(angle)
                    print(' OFFSETTING')
                    file.offset(x_offset, y_offset)
                    print(' MERGING')
                    ctx.merge(file)

        if file is not None and ext != '.drl':
            new_name = extensions_to_names.get(ext, 'unknown')
            full_path = os.path.join(path_export, new_name + ext)
            print('\nWRITING: {}'.format(full_path))
            ctx.dump(full_path)
            print('DONE\n')

    full_path = os.path.join(path_export, 'drill-NPTH.drl')
    print('\nWRITING: {}'.format(full_path))
    ctx_npth_drl.dump(full_path)
    print('DONE\n')

    full_path = os.path.join(path_export, 'drill-PTH.drl')
    print('\nWRITING: {}'.format(full_path))
    ctx_pth_drl.dump(full_path)
    print('DONE\n')

    update_progressbar(progress, 'Done', 1.0)

    return None

