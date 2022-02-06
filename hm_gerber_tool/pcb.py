#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 HalfMarble LLC
# copyright 2015 Hamilton Kibbe <ham@hamiltonkib.be>
#
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

from hm_gerber_tool.cam import CamFile
from .exceptions import ParseError
from .layers import PCBLayer, sort_layers, layer_signatures
from .common import read as gerber_read
from .utils import listdir


skip_extensions = ['.kicad_sch', '.kicad_prl', '.gbrjob', '.zip', '.png', '.jpg']


class PCB(object):

    @classmethod
    def from_directory(cls, directory, board_name=None, verbose=False):
        layers = []
        names = set()

        # Validate
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            raise TypeError('{} is not a directory.'.format(directory))

        # Load gerber files
        for filename in listdir(directory, True, True):
            ext = os.path.splitext(filename)[1].lower()
            if verbose:
                print('[PCB]')
                print('[PCB]: ext [{}]'.format(ext))
            # common extensions that we should skip, which might be in the same path as the gerber files
            if ext is None or len(ext) == 0 or ext in skip_extensions:
                print('[PCB]:  Skipping file {} [unsupported file extension]'.format(filename))
                continue
            try:
                if verbose:
                    print('[PCB]: reading {}'.format(filename))
                camfile = gerber_read(os.path.join(directory, filename))
                if camfile is not None:
                    layer = PCBLayer.from_cam(camfile)
                    if verbose:
                        print(
                            '[PCB]:  layer {}, bounds {}, [metric units: {}]'.format(layer, layer.bounds, layer.metric))
                    layers.append(layer)
                    name = os.path.splitext(filename)[0]
                    if len(os.path.splitext(filename)) > 1:
                        _name, ext = os.path.splitext(name)
                        if ext[1:] in layer_signatures(layer.layer_class):
                            name = _name
                        if layer.layer_class == 'drill' and 'drill' in ext:
                            name = _name
                    names.add(name)
            except ParseError:
                if verbose:
                    print('[PCB]:  Skipping file {} [ParseError]'.format(filename))
            except IOError:
                if verbose:
                    print('[PCB]:  Skipping file {} [IOError]'.format(filename))

        # Try to guess board name
        if board_name is None:
            if len(names) == 1:
                board_name = names.pop()
            else:
                board_name = os.path.basename(directory)

        print('[PCB]')
        print('[PCB]: board_name {}'.format(board_name))

        # Return PCB
        if len(layers) > 0:
            board = cls(layers, board_name)
            print('[PCB]: board_bounds {}'.format(board.board_bounds))
            if board.board_bounds is None:
                return None
            else:
                return board
        else:
            return None

    def __init__(self, layers, name=None):
        self.layers = sort_layers(layers)
        self.name = name

    def __len__(self):
        return len(self.layers)

    @property
    def top_layers(self):
        board_layers = [l for l in reversed(self.layers) if l.layer_class in
        ('top_silk', 'top_mask', 'top_copper')]
        drill_layers = [l for l in self.drill_layers if 'top' in l.layers]
        # Drill layer goes under soldermask for proper rendering of tented vias
        return [board_layers[0]] + drill_layers + board_layers[1:]

    @property
    def bottom_layers(self):
        board_layers = [l for l in self.layers if l.layer_class in
                        ('bottom_silk', 'bottom_mask', 'bottom_copper')]
        drill_layers = [l for l in self.drill_layers if 'bottom' in l.layers]
        # Drill layer goes under soldermask for proper rendering of tented vias
        return [board_layers[0]] + drill_layers + board_layers[1:]

    @property
    def drill_layers(self):
        return [l for l in self.layers if l.layer_class in
                ('drill')]

    @property
    def copper_layers(self):
        return list(reversed([layer for layer in self.layers if layer.layer_class in
                              ('top_copper', 'bottom_copper', 'internal')]))

    @property
    def edge_cuts_layer(self):
        for layer in self.layers:
            if layer.layer_class == 'edge_cuts':
                return layer

    @property
    def layer_count(self):
        """ Number of *COPPER* layers
        """
        return len([l for l in self.layers if l.layer_class in
                    ('top_copper', 'bottom_copper', 'internal')])

    @property
    def metric(self):
        return True

    @property
    def board_bounds(self):
        bounds = None
        if bounds is None:
            for layer in self.layers:
                if layer.layer_class == 'edge_cuts':
                    bounds = layer.bounds
        if bounds is None:
            for layer in self.layers:
                if layer.layer_class == 'top_copper':
                    bounds = layer.bounds
        return bounds

