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

from hm_gerber_tool.utils import listdir

from Utilities import *


# Test
# Workaround needed for PCB Way online gerber preview
# to work correctly, if using routing in drill files
def fix_drl(path):
    if not os.path.isdir(path):
        print('ERROR: path {} does not exist'.format(path))
        return

    for filename in listdir(path, True, True):
        filename_ext = os.path.splitext(filename)[1].lower()
        if filename_ext == '.drl':
            header = True
            routing = False
            tool = None
            lines_main = []
            lines_route = []
            file = load_file(path, filename)
            segments = file.split("\n")
            for s in segments:
                if s == '%':
                    header = False
                    lines_main.append(s+'\n')
                elif s == 'M30':
                    pass
                else:
                    if header is True:
                        lines_main.append(s+'\n')
                    else:
                        if s.startswith('T'):
                            tool = s
                            routing = False
                        if not routing:
                            if s.startswith('G0'):
                                lines_main.pop()
                                lines_route.append(tool+'\n')
                                routing = True
                        if not routing:
                            lines_main.append(s+'\n')
                        else:
                            lines_route.append(s+'\n')

            f = open(os.path.join(path, "fixed_"+filename), "w")
            f.writelines(lines_main)
            f.writelines(lines_route)
            f.write('M30\n')
            f.close()


fix_drl('/Users/gerard/Desktop/pcb')
