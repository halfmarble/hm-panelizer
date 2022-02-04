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


import hm_gerber_ex
from hm_gerber_ex import GerberComposition
from hm_gerber_tool.gerber_statements import CoordStmt, EofStmt

from AppSettings import *
from Utilities import *


class SplitGerberComposition(GerberComposition):

    def __init__(self, settings=None, comments=None, cutout_lines=None):
        super(SplitGerberComposition, self).__init__(settings, comments)
        self.cutout_lines = cutout_lines

    def split_line(self, f, cutouts, start, end, verbose=False):
        if verbose:
            print('#   SPLIT')
            print('#            LINE START  {},{} [{}] '
                  .format(start.x, start.y, start.to_gerber(self.settings)))
        f.write(start.to_gerber(self.settings) + '\n')
        for cutout in cutouts:
            cutout_y = cutout[0]
            if equal_floats(cutout_y, round_down(start.y), AppSettings.merge_error):
                lines = cutout[1]
                for cutout_line in lines:
                    start_cutout_x = cutout_line[0]
                    end_cutout_x = cutout_line[1]
                    if start_cutout_x >= start.x and end_cutout_x <= end.x:
                        new_end = CoordStmt(None, start_cutout_x, cutout_y, None, None, 'D01', self.settings)
                        new_start = CoordStmt(None, end_cutout_x, cutout_y, None, None, 'D02', self.settings)
                        if verbose:
                            print('#   INSERTING LINE END   {},{} [{}] '
                                  .format(new_end.x, new_end.y, new_end.to_gerber(self.settings)))
                            print('#   INSERTING LINE START {},{} [{}] '
                                  .format(new_start.x, new_start.y, new_start.to_gerber(self.settings)))
                        f.write(new_end.to_gerber(self.settings) + '\n')
                        f.write(new_start.to_gerber(self.settings) + '\n')
        if verbose:
            print('#            LINE END    {},{} [{}] '
                  .format(end.x, end.y, end.to_gerber(self.settings)))
        f.write(end.to_gerber(self.settings) + '\n')
        return True

    def process_segment(self, f, i, lines, cutouts, verbose=False):
        split = False
        start = lines[i]
        if isinstance(start, CoordStmt) and start.op == 'D02' and len(lines) > (i+1):
            end = lines[i + 1]
            if isinstance(end, CoordStmt) and end.op == 'D01':
                if equal_floats(end.y, start.y, AppSettings.merge_error):
                    if verbose:
                        print('#')
                        print('# HORIZONTAL LINE')
                        print('# LINE START {},{} [{}] '
                              .format(start.x, start.y, start.to_gerber(self.settings)))
                        print('# LINE END   {},{} [{}] '
                              .format(end.x, end.y, end.to_gerber(self.settings)))
                    for cutout in cutouts:
                        cutout_y = cutout[0]
                        if equal_floats(cutout_y, round_down(end.y), AppSettings.merge_error):
                            if verbose:
                                print('#')
                                print('#  MATCHING Y {}'.format(cutout_y))
                                print('#  LINE START {},{} [{}] '
                                      .format(start.x, start.y, start.to_gerber(self.settings)))
                                print('#  LINE END   {},{} [{}] '
                                      .format(end.x, end.y, end.to_gerber(self.settings)))
                            if end.x > start.x:
                                if verbose:
                                    print('#  DIRECTION ----->')
                            else:
                                if verbose:
                                    print('#  DIRECTION <----- (SWAP NEEDED)')
                                temp_x = end.x
                                end.x = start.x
                                start.x = temp_x
                                if verbose:
                                    print('#   NOW LINE START {},{} [{}] '
                                          .format(start.x, start.y, start.to_gerber(self.settings)))
                                    print('#   NOW LINE END   {},{} [{}] '
                                          .format(end.x, end.y, end.to_gerber(self.settings)))
                            split = self.split_line(f, cutouts, start, end, verbose)
        if split:
            return i+1
        else:
            f.write(lines[i].to_gerber(self.settings) + '\n')
            return i

    # can handle only horizontal lines, and lines going from left to right (i.e. start.x < end.x)
    def process_statements(self, f, statements, cutouts, verbose=False):
        if verbose:
            print('>>>>>>>>>>> process_statements')
            print('>>>>>>>>>>> cutouts: {}'.format(cutouts))
        statements_list = []
        for statement in statements:
            statements_list.append(statement)
        for i in range(len(statements_list)):
            i = self.process_segment(f, i, statements_list, cutouts, verbose)

    def dump(self, path):
        def statements():
            for k in self.aperture_macros:
                yield self.aperture_macros[k]
            for s in self.apertures:
                yield s
            for s in self.drawings:
                yield s
            yield EofStmt()
        self.settings.notation = 'absolute'
        self.settings.zeros = 'trailing'
        with open(path, 'w') as f:
            hm_gerber_ex.rs274x.write_gerber_header(f, self.settings)
            if self.cutout_lines is not None:
                self.process_statements(f, statements(), self.cutout_lines, verbose=False)
            else:
                for statement in statements():
                    f.write(statement.to_gerber(self.settings) + '\n')
