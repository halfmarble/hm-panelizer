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
]

# experimental (should hm-panelier use it?)
#
# optimizes gerber file by grouping instructions belonging to the same 'D0x*'
# section together, ex:
#
# D13*
# X164134517Y-35560000D03*
# D12*
# X174144517Y-28845000D03*
# D13*
# X107860000Y-31200000D03*
#
# becomes:
#
# D12*
# X174144517Y-28845000D03*
# D13*
# X164134517Y-35560000D03*
# X107860000Y-31200000D03*


def optimize_gbr(path):
    if not os.path.isdir(path):
        print('ERROR: path {} does not exist'.format(path))
        return

    for filename in listdir(path, True, True):
        filename_ext = os.path.splitext(filename)[1].lower()
        if filename_ext in extensions:
            current_chunk = None
            chunks_all = [(None, [])]
            file = load_file(path, filename)
            segments = file.split("\n")
            for s in segments:
                if s == 'M02*':
                    pass
                elif s.startswith('D') and s.endswith('*'):
                    current_chunk = s
                    new_chunk = True
                    for chunk in chunks_all:
                        if chunk[0] == s:
                            new_chunk = False
                            break
                    if new_chunk:
                        chunks_all.append((current_chunk, [current_chunk+'\n']))
                elif current_chunk is None:
                    chunk = chunks_all[0]
                    chunk[1].append(s+'\n')
                else:
                    for chunk in chunks_all:
                        if chunk[0] == current_chunk:
                            chunk[1].append(s+'\n')
                            break
            f = open(os.path.join(path, filename), "w")
            for chunk in chunks_all:
                f.writelines(chunk[1])
            f.write('M02*')
            f.close()


optimize_gbr('/Users/gerard/Desktop/neatoboardG_unoptimized')
