#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 HalfMarble LLC
# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
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

# .APR	            Aperture File
# .APT	            Aperture File
# .EXTREP	            Extension Report of Gerber Files
# .REP	            Report of Individual Layer Used Aperture List
# .RUL	            DRC Rules
# .GKO	            Keep Out Layer
# .GTO	            Top Overlay
# .GBO	            Bottom Overlay
# .GPT	            Pad Master Top
# .GPB	            Pad Master Bottom
# .GTS	            Top Solder
# .GBS	            Bottom Solder
# .GTL	            Top Layer
# .GBL	            Bottom Layer
# .GTP	            Top Paste
# .GBP	            Bottom Paste
# .G1, .G2, etc.	Mid-layer 1, 2, etc.
# .GP1, .GP2, etc.	Internal Plane Layer 1, 2, etc.
# .P01, .P02, etc.	Gerber Panels
# .GM1, .GM2, etc.	Mechanical Layer 1, 2, etc.
# .GD1, .GD2, etc.	Drill Drawing
# .GG1, .GG2, etc.	Drill Guide
# .DRL	            Drill Data
# .TXT	            Drill Position
# .DRR	            Drill Tool Size
# .LDP	            Layer Pairs Export File for PCB

import os
import re
from collections import namedtuple

from . import common
from .excellon import ExcellonFile
from .ipc356 import IPCNetlist


Hint = namedtuple('Hint', 'layer ext name regex content')

hints = [
    Hint(layer='top_copper',
         ext=['gtl', 'cmp', 'top', ],
         name=['art01', 'top', 'GTL', 'layer1', 'soldcom', 'comp', 'F.Cu', ],
         regex='',
         content=[]
         ),
    Hint(layer='bottom_copper',
         ext=['gbl', 'sld', 'bot', 'sol', 'bottom', ],
         name=['art02', 'bottom', 'bot', 'GBL', 'layer2', 'soldsold', 'B.Cu', ],
         regex='',
         content=[]
         ),
    Hint(layer='internal',
         ext=['in', 'gt1', 'gt2', 'gt3', 'gt4', 'gt5', 'gt6', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6', ],
         name=['art', 'internal', 'pgp', 'pwr', 'gnd', 'ground', 'gp1', 'gp2', 'gp3', 'gp4', 'gt5', 'gp6',
               'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'group3', 'group4', 'group5', 'group6', 'group7', 'group8', ],
         regex='',
         content=[]
         ),
    Hint(layer='top_silk',
         ext=['gto', 'sst', 'plc', 'ts', 'skt', 'topsilk', ],
         name=['sst01', 'topsilk', 'silk', 'slk', 'sst', 'F.SilkS', 'F.Silkscreen'],
         regex='',
         content=[]
         ),
    Hint(layer='bottom_silk',
         ext=['gbo', 'ssb', 'pls', 'bs', 'skb', 'bottomsilk', ],
         name=['bsilk', 'ssb', 'botsilk', 'bottomsilk', 'B.SilkS', 'B.Silkscreen'],
         regex='',
         content=[]
         ),
    Hint(layer='top_mask',
         ext=['gts', 'stc', 'tmk', 'smt', 'tr', 'topmask', ],
         name=['sm01', 'cmask', 'tmask', 'mask1', 'maskcom', 'topmask', 'mst', 'F.Mask', ],
         regex='',
         content=[]
         ),
    Hint(layer='bottom_mask',
         ext=['gbs', 'sts', 'bmk', 'smb', 'br', 'bottommask', ],
         name=['sm', 'bmask', 'mask2', 'masksold', 'botmask', 'bottommask', 'msb', 'B.Mask', ],
         regex='',
         content=[]
         ),
    Hint(layer='top_paste',
         ext=['gtp', 'tm', 'toppaste', ],
         name=['sp01', 'toppaste', 'pst', 'F.Paste'],
         regex='',
         content=[]
         ),
    Hint(layer='bottom_paste',
         ext=['gbp', 'bm', 'bottompaste', ],
         name=['sp02', 'botpaste', 'bottompaste', 'psb', 'B.Paste', ],
         regex='',
         content=[]
         ),
    Hint(layer='edge_cuts',
         ext=['gm1', 'gm2', 'gm3', 'gml', 'gko', 'outline'],
         name=['BDR', 'GML', 'border', 'out', 'outline', 'Edge.Cuts', ],
         regex='',
         content=[]
         ),
    Hint(layer='ipc_netlist',
         ext=['ipc'],
         name=[],
         regex='',
         content=[]
         ),
    Hint(layer='drawing',
         ext=['fab'],
         name=['assembly drawing', 'assembly', 'fabrication', 'fab drawing', 'fab', ],
         regex='',
         content=[]
         ),
    Hint(layer='top_drawing',
         ext=[''],
         name=['F_Fab', ],
         regex='',
         content=[]
         ),
    Hint(layer='bottom_drawing',
         ext=[''],
         name=['B_Fab', ],
         regex='',
         content=[]
         ),
    Hint(layer='drill',
         ext=['drl', 'txt'],
         name=['PTH', 'NPTH'],
         regex='',
         content=[]
         ),
]


def layer_signatures(layer_class):
    for hint in hints:
        if hint.layer == layer_class:
            return hint.ext + hint.name
    return []


def load_layer(filename):
    return PCBLayer.from_cam(common.read(filename))


def load_layer_data(data, filename=None):
    return PCBLayer.from_cam(common.loads(data, filename))


def guess_layer_class(filename):
    try:
        layer = guess_layer_class_by_content(filename)
        if layer:
            return layer
    except:
        pass

    try:
        directory, filename = os.path.split(filename)
        name, ext = os.path.splitext(filename.lower())
        for hint in hints:
            if hint.regex:
                if re.findall(hint.regex, filename, re.IGNORECASE):
                    return hint.layer

            patterns = [r'^(\w*[.-])*{}([.-]\w*)?$'.format(x) for x in hint.name]
            if ext[1:] in hint.ext or any(re.findall(p, name, re.IGNORECASE) for p in patterns):
                return hint.layer
    except:
        pass
    return 'unknown'


def guess_layer_class_by_content(filename):
    try:
        file = open(filename, 'r')
        for line in file:
            for hint in hints:
                if len(hint.content) > 0:
                    patterns = [r'^(.*){}(.*)$'.format(x) for x in hint.content]
                    if any(re.findall(p, line, re.IGNORECASE) for p in patterns):
                        return hint.layer
    except:
        pass

    return False


def sort_layers(layers, from_top=True):
    #print('<PCBLayer: layers {}>'.format(layers))
    layer_order = ['edge_cuts', 'top_paste', 'top_silk', 'top_mask', 'top_copper',
                   'internal', 'bottom_copper', 'bottom_mask', 'bottom_silk',
                   'bottom_paste', 'top_drawing', 'bottom_drawing', ]
    append_after = ['drill', 'drawing']

    output = []
    drill_layers = [layer for layer in layers if layer.layer_class == 'drill']
    #print('<PCBLayer: drill_layers {}>'.format(output))
    internal_layers = list(sorted([layer for layer in layers if layer.layer_class == 'internal']))
    #print('<PCBLayer: internal_layers {}>'.format(output))

    for layer_class in layer_order:
        if layer_class == 'internal':
            output += internal_layers
        elif layer_class == 'drill':
            output += drill_layers
        else:
            for layer in layers:
                if layer.layer_class == layer_class:
                    output.append(layer)
    if not from_top:
        output = list(reversed(output))

    for layer_class in append_after:
        for layer in layers:
            if layer.layer_class == layer_class:
                output.append(layer)
    #print('<PCBLayer: {}>'.format(output))
    return output


class PCBLayer(object):
    """ Base class for PCB Layers

    Parameters
    ----------
    source : CAMFile
        CAMFile representing the layer


    Attributes
    ----------
    filename : string
        Source Filename

    """
    @classmethod
    def from_cam(cls, camfile):
        filename = camfile.filename
        metric = camfile.is_metric
        layer_class = guess_layer_class(filename)
        if isinstance(camfile, ExcellonFile) or (layer_class == 'drill'):
            return DrillLayer.from_cam(camfile)
        elif layer_class == 'internal':
            return InternalLayer.from_cam(camfile)
        if isinstance(camfile, IPCNetlist):
            layer_class = 'ipc_netlist'
        return cls(filename, layer_class, camfile, metric)

    def __init__(self, filename=None, layer_class=None, cam_source=None, metric=True, **kwargs):
        super(PCBLayer, self).__init__(**kwargs)
        self.filename = filename
        self.layer_class = layer_class
        self.cam_source = cam_source
        self.metric = metric
        self.surface = None
        self.primitives = cam_source.primitives if cam_source is not None else []

    @property
    def bounds(self):
        if self.cam_source is not None:
            return self.cam_source.bounds
        else:
            return None

    @property
    def is_metric(self):
        return self.metric

    def name(self):
        return '{}'.format(self.layer_class)

    def __repr__(self):
        return '<PCBLayer: {}>'.format(self.layer_class)


class DrillLayer(PCBLayer):

    @classmethod
    def from_cam(cls, camfile):
        return cls(camfile.filename, camfile)

    def __init__(self, filename=None, cam_source=None, layers=None, **kwargs):
        super(DrillLayer, self).__init__(filename, 'drill', cam_source, **kwargs)
        self.layers = layers if layers is not None else ['top', 'bottom']
        self.type = "_npth" if "npth" in filename.lower() else "_pth"

    def name(self):
        return '{}{}'.format(self.layer_class, self.type)


class InternalLayer(PCBLayer):

    @classmethod
    def from_cam(cls, camfile):
        filename = camfile.filename
        try:
            order = int(re.search(r'\d+', filename).group())
        except AttributeError:
            order = 0
        return cls(filename, camfile, order)

    def __init__(self, filename=None, cam_source=None, order=0, **kwargs):
        super(InternalLayer, self).__init__(filename, 'internal', cam_source, **kwargs)
        self.order = order

    def __eq__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order == other.order)

    def __ne__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order != other.order)

    def __gt__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order > other.order)

    def __lt__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order < other.order)

    def __ge__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order >= other.order)

    def __le__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order <= other.order)
