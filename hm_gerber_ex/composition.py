#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 HalfMarble LLC
# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import os
from functools import reduce
from hm_gerber_tool.cam import FileSettings
from hm_gerber_tool.gerber_statements import EofStmt, CoordStmt, CommentStmt
from hm_gerber_tool.excellon_statements import *
from hm_gerber_tool.excellon import DrillSlot, DrillHit
import hm_gerber_tool.rs274x
import hm_gerber_tool.excellon
import hm_gerber_ex.dxf


class Composition(object):
    def __init__(self, settings=None, comments=None):
        self.settings = settings
        self.comments = comments if comments != None else []


class GerberComposition(Composition):
    APERTURE_ID_BIAS = 10

    def __init__(self, settings=None, comments=None, cutout_lines=None):
        super(GerberComposition, self).__init__(settings, comments)
        self.aperture_macros = {}
        self.apertures = []
        self.drawings = []
        self.cutout_lines = cutout_lines

    def merge(self, file):
        if isinstance(file, hm_gerber_ex.rs274x.GerberFile):
            self._merge_gerber(file)
        elif isinstance(file, hm_gerber_ex.dxf.DxfFile):
            self._merge_dxf(file)
        else:
            raise Exception('unsupported file type')

    def split_line(self, f, start, end, verbose=False):
        if verbose:
            print('# SPLIT')
            print('#            LINE START  {:3.2f},{:3.2f} [{}] '
                  .format(start.x, start.y, start.to_gerber(self.settings)))
        f.write(start.to_gerber(self.settings) + '\n')
        for cutout in self.cutout_lines:
            cutout_y = cutout[0]
            if cutout_y == start.y:
                lines = cutout[1]
                for cutout_line in lines:
                    start_cutout_x = cutout_line[0]
                    end_cutout_x = cutout_line[1]
                    if start_cutout_x >= start.x and end_cutout_x <= end.x:
                        new_end = CoordStmt(None, start_cutout_x, cutout_y, None, None, 'D01', self.settings)
                        new_start = CoordStmt(None, end_cutout_x, cutout_y, None, None, 'D02', self.settings)
                        if verbose:
                            print('#   INSERTING LINE END   {:3.2f},{:3.2f} [{}] '
                                  .format(new_end.x, new_end.y, new_end.to_gerber(self.settings)))
                            print('#   INSERTING LINE START {:3.2f},{:3.2f} [{}] '
                                  .format(new_start.x, new_start.y, new_start.to_gerber(self.settings)))
                        f.write(new_end.to_gerber(self.settings) + '\n')
                        f.write(new_start.to_gerber(self.settings) + '\n')
        if verbose:
            print('#            LINE END    {:3.2f},{:3.2f} [{}] '
                  .format(end.x, end.y, end.to_gerber(self.settings)))
        f.write(end.to_gerber(self.settings) + '\n')
        return True

    def process_segment(self, f, i, lines, verbose=True):
        split = False
        start = lines[i]
        if isinstance(start, CoordStmt) and start.op == 'D02' and len(lines) > (i+1):
            end = lines[i + 1]
            if isinstance(end, CoordStmt) and end.op == 'D01':
                if end.y == start.y:
                    for cutout in self.cutout_lines:
                        cutout_y = cutout[0]
                        if cutout_y == end.y:
                            if verbose:
                                print('#')
                                print('# LINE START {:3.2f},{:3.2f} [{}] '
                                      .format(start.x, start.y, start.to_gerber(self.settings)))
                                print('# LINE END   {:3.2f},{:3.2f} [{}] '
                                      .format(end.x, end.y, end.to_gerber(self.settings)))
                            if end.x > start.x:
                                if verbose:
                                    print('# DIRECTION ----->')
                            else:
                                if verbose:
                                    print('# DIRECTION <----- (SWAP NEEDED)')
                                temp_x = end.x
                                end.x = start.x
                                start.x = temp_x
                                if verbose:
                                    print('# NOW LINE START {:3.2f},{:3.2f} [{}] '
                                          .format(start.x, start.y, start.to_gerber(self.settings)))
                                    print('# NOW LINE END   {:3.2f},{:3.2f} [{}] '
                                          .format(end.x, end.y, end.to_gerber(self.settings)))
                            split = self.split_line(f, start, end, verbose)
        if split:
            return i+1
        else:
            f.write(lines[i].to_gerber(self.settings) + '\n')
            return i

    # can handle only horizontal lines, and lines going from left to right (i.e. start.x < end.x)
    def process_statements(self, f, statements):
        statements_list = []
        for statement in statements():
            statements_list.append(statement)
        for i in range(len(statements_list)):
            i = self.process_segment(f, i, statements_list)

    def split_line_NOT(self, f, statement_start, statement_end):
        print('# LINE START {}'.format(statement_start.to_gerber(self.settings)))
        print('# LINE END   {}'.format(statement_end.to_gerber(self.settings)))
        f.write(statement_start.to_gerber(self.settings) + '\n')
        new_statement = statement_end
        if statement_end.y == statement_start.y:
            x_start = statement_start.x
            x_end = statement_end.x
            y = statement_end.y
            for c in self.cutout_lines:
                if c[0] == y:
                    f.write('G04 ------- start replacement*\n')
                    f.write('G04 ------- {}\n'.format(statement_start))
                    f.write('G04 ------- {}\n'.format(statement_start.to_gerber(self.settings)))
                    f.write('G04 ------- {}\n'.format(statement_end))
                    f.write('G04 ------- {}\n'.format(statement_end.to_gerber(self.settings)))
                    print()
                    print('# REPLACING {}'.format(new_statement.to_gerber(self.settings)))
                    print('# WITH')
                    lines = c[1]
                    for cutout_line in lines:
                        cutout_line_start = cutout_line[0]
                        cutout_line_end = cutout_line[1]
                        if cutout_line_start >= x_start and cutout_line_end <= x_end:
                            new_statement.x = cutout_line_start
                            print('#           {}'.format(new_statement.to_gerber(self.settings)))
                            f.write(new_statement.to_gerber(self.settings) + '\n')
                            new_statement = CoordStmt(None, cutout_line_end, y, None, None, 'D02', self.settings)
                            print('#           {}'.format(new_statement.to_gerber(self.settings)))
                            f.write(new_statement.to_gerber(self.settings) + '\n')

                            new_statement = CoordStmt(None, cutout_line_end, y, None, None, 'D01', self.settings)

                            x_start = cutout_line_end
                    new_statement.x = x_end
                    f.write('G04 ------- end replacement*\n')
                    print('#           {}'.format(new_statement.to_gerber(self.settings)))
                    print()
        return new_statement

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
                self.process_statements(f, statements)
            else:
                for statement in statements():
                    f.write(statement.to_gerber(self.settings) + '\n')

    def _merge_gerber(self, file):
        aperture_macro_map = {}
        aperture_map = {}

        if self.settings is not None:
            if self.settings.units == 'metric':
                file.to_metric()
            else:
                file.to_inch()

        for macro in file.aperture_macros:
            statement = file.aperture_macros[macro]
            name = statement.name
            newname = self._register_aperture_macro(statement)
            aperture_macro_map[name] = newname

        for statement in file.aperture_defs:
            if statement.param == 'AD':
                if statement.shape in aperture_macro_map:
                    statement.shape = aperture_macro_map[statement.shape]
                dnum = statement.d
                newdnum = self._register_aperture(statement)
                aperture_map[dnum] = newdnum

        for statement in file.main_statements:
            if statement.type == 'APERTURE':
                statement.d = aperture_map[statement.d]
            self.drawings.append(statement)
        
        if self.settings is None:
            self.settings = file.context

    def _merge_dxf(self, file):
        if self.settings is not None:
            if self.settings.units == 'metric':
                file.to_metric()
            else:
                file.to_inch()

        file.dcode = self._register_aperture(file.aperture)
        self.drawings.append(file.statements)

        if self.settings is None:
            self.settings = file.settings

    def _register_aperture_macro(self, statement):
        name = statement.name
        newname = name
        offset = 0
        while newname in self.aperture_macros:
            offset += 1
            newname = '%s_%d' % (name, offset)
        statement.name = newname
        self.aperture_macros[newname] = statement
        return newname

    def _register_aperture(self, statement):
        statement.d = len(self.apertures) + self.APERTURE_ID_BIAS
        self.apertures.append(statement)
        return statement.d


class DrillComposition(Composition):
    def __init__(self, settings=None, comments=None):
        super(DrillComposition, self).__init__(settings, comments)
        self.tools = []
        self.hits = []
        self.dxf_statements = []
    
    def merge(self, file):

        if isinstance(file, hm_gerber_ex.excellon.ExcellonFileEx):
            self._merge_excellon(file)
        elif isinstance(file, hm_gerber_ex.DxfFile):
            self._merge_dxf(file)
        else:
            raise Exception('unsupported file type')

    def dump(self, path):
        if len(self.tools) == 0:
            return
        def statements():
            for t in self.tools:
                stmt = ToolSelectionStmt(t.number)
                yield ToolSelectionStmt(t.number).to_excellon(self.settings)
                for h in self.hits:
                    if h.tool.number == t.number:
                        yield h.to_excellon(self.settings)
                for num, statement in self.dxf_statements:
                    if num == t.number:
                        yield statement.to_excellon(self.settings)
            yield EndOfProgramStmt().to_excellon()

        with open(path, 'w') as f:
            hm_gerber_ex.excellon.write_excellon_header(f, self.settings, self.tools)
            for statement in statements():
                f.write(statement + '\n')

    def _merge_excellon(self, file):
        tool_map = {}

        if self.settings is None:
            self.settings = file.settings
        if self.settings.units == 'metric':
            file.to_metric()
        else:
            file.to_inch()

        for tool in iter(file.tools.values()):
            num = tool.number
            tool_map[num] = self._register_tool(tool)
        
        for hit in file.hits:
            hit.tool = tool_map[hit.tool.number]
            self.hits.append(hit)
    
    def _merge_dxf(self, file):
        if self.settings is None:
            self.settings = file.settings
        if self.settings.units == 'metric':
            file.to_metric()
        else:
            file.to_inch()

        tool = self._register_tool(ExcellonTool(self.settings, number=1, diameter=file.width))
        self.dxf_statements.append((tool.number, file.statements))

    def _register_tool(self, tool):
        for existing in self.tools:
            if existing.equivalent(tool):
                return existing
        new_tool = ExcellonTool.from_tool(tool)
        new_tool.settings = self.settings
        def toolnums():
            for tool in self.tools:
                yield tool.number
        max_num = reduce(lambda x, y: x if x > y else y, toolnums(), 0)
        new_tool.number = max_num + 1
        self.tools.append(new_tool)
        return new_tool
