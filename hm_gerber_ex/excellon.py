#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 HalfMarble LLC
# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import operator

import hm_gerber_tool.excellon
from hm_gerber_tool.excellon import ExcellonParser, detect_excellon_format, ExcellonFile, DrillHit, DrillSlot
from hm_gerber_tool.excellon_statements import ExcellonStatement, UnitStmt, CoordinateStmt, UnknownStmt, \
                                       SlotStmt, DrillModeStmt, RouteModeStmt, LinearModeStmt, \
                                       ToolSelectionStmt, ZAxisRoutPositionStmt, \
                                       RetractWithClampingStmt, RetractWithoutClampingStmt, \
                                       EndOfProgramStmt
from hm_gerber_tool.cam import FileSettings
from hm_gerber_tool.utils import inch, metric, write_gerber_value, parse_gerber_value
from hm_gerber_ex.utility import rotate


def loads(data, filename=None, settings=None, tools=None, format=None):
    if not settings:
        settings = FileSettings(**detect_excellon_format(data))
        if format:
            settings.format = format
    hm_gerber_tool.excellon.CoordinateStmt = CoordinateStmtEx
    hm_gerber_tool.excellon.UnitStmt = UnitStmtEx
    file = ExcellonParser(settings, tools).parse_raw(data, filename)
    return ExcellonFileEx.from_file(file)


def write_excellon_header(file, settings, tools):
    file.write('M48\nFMAT,2\nICI,OFF\n%s\n' %
               UnitStmtEx(settings.units, settings.zeros, settings.format).to_excellon(settings))
    for tool in tools:
        file.write(tool.to_excellon(settings) + '\n')
    file.write('%%\nG90\n%s\n' % ('M72' if settings.units == 'inch' else 'M71'))


class ExcellonFileEx(ExcellonFile):

    @classmethod
    def from_file(cls, file):
        def correct_statements():
            for stmt in file.statements:
                if isinstance(stmt, UnknownStmt):
                    line = stmt.stmt.strip()
                    if line[:3] == 'G02':
                        yield CircularCWModeStmt()
                        if len(line) > 3:
                            yield CoordinateStmtEx.from_excellon(line[3:], file.settings)
                    elif line[:3] == 'G03':
                        yield CircularCCWModeStmt()
                        if len(line) > 3:
                            yield CoordinateStmtEx.from_excellon(line[3:], file.settings)
                    elif line[0] == 'X' or line[0] == 'Y' or line[0] == 'A' or line[0] == 'I':
                        yield CoordinateStmtEx.from_excellon(line, file.settings)
                    else:
                        yield stmt
                else:
                    yield stmt

        def generate_hits(statements):
            class CoordinateCtx:
                def __init__(self, notation):
                    self.notation = notation
                    self.x = 0.
                    self.y = 0.
                    self.radius = None
                    self.center_offset = None
                
                def update(self, x=None, y=None, radius=None, center_offset=None):
                    if self.notation == 'absolute':
                        if x is not None:
                            self.x = x
                        if y is not None:
                            self.y = y
                    else:
                        if x is not None:
                            self.x += x
                        if y is not None:
                            self.y += y
                    if radius is not None:
                        self.radius = radius
                    if center_offset is not None:
                        self.center_offset = center_offset
                
                def node(self, mode, center_offset):
                    radius, offset = None, None
                    if mode == DrillRout.MODE_CIRCULER_CW or mode == DrillRout.MODE_CIRCULER_CCW:
                        if center_offset is None:
                            radius = self.radius
                            offset = self.center_offset
                        else:
                            radius = None
                            offset = center_offset
                    return DrillRout.Node(mode, self.x, self.y, radius, offset)

            STAT_DRILL = 0
            STAT_ROUT_UP = 1
            STAT_ROUT_DOWN = 2

            status = STAT_DRILL
            current_tool = None
            rout_mode = None
            coordinate_ctx = CoordinateCtx(file.notation)
            rout_nodes = []

            last_position = (0., 0.)
            last_radius = None
            last_center_offset = None

            def make_rout(status, nodes):
                if status != STAT_ROUT_DOWN or len(nodes) == 0 or current_tool is None:
                    return None
                return DrillRout(current_tool, nodes)

            rout_statements = []
            for stmt in statements:
                if isinstance(stmt, ToolSelectionStmt):
                    if file.tools.get(stmt.tool, None) is not None:
                        current_tool = file.tools[stmt.tool]
                    else:
                        print('!!! WARNING skipping tool {} (used without previous definition)'.format(stmt.tool))
                elif isinstance(stmt, DrillModeStmt):
                    rout = make_rout(status, rout_statements)
                    rout_statements = []
                    if rout is not None:
                        yield rout
                    status = STAT_DRILL
                    rout_mode = None
                elif isinstance(stmt, RouteModeStmt):
                    if status == STAT_DRILL:
                        status = STAT_ROUT_UP
                        rout_mode = DrillRout.MODE_ROUT
                    else:
                        rout_mode = DrillRout.MODE_LINEAR

                elif isinstance(stmt, LinearModeStmt):
                    rout_mode = DrillRout.MODE_LINEAR
                elif isinstance(stmt, CircularCWModeStmt):
                    rout_mode = DrillRout.MODE_CIRCULER_CW
                elif isinstance(stmt, CircularCCWModeStmt):
                    rout_mode = DrillRout.MODE_CIRCULER_CCW
                elif isinstance(stmt, ZAxisRoutPositionStmt) and status == STAT_ROUT_UP:
                    status = STAT_ROUT_DOWN
                elif isinstance(stmt, RetractWithClampingStmt) or isinstance(stmt, RetractWithoutClampingStmt):
                    rout = make_rout(status, rout_nodes)
                    rout_statements = []
                    if rout is not None:
                        yield rout
                    status = STAT_ROUT_UP
                elif isinstance(stmt, SlotStmt):
                    coordinate_ctx.update(stmt.x_start, stmt.y_start)
                    x_start = coordinate_ctx.x
                    y_start = coordinate_ctx.y
                    coordinate_ctx.update(stmt.x_end, stmt.y_end)
                    x_end = coordinate_ctx.x
                    y_end = coordinate_ctx.y
                    yield DrillSlotEx(current_tool, (x_start, y_start), (x_end, y_end), DrillSlotEx.TYPE_G85)
                elif isinstance(stmt, CoordinateStmtEx):
                    center_offset = (stmt.i, stmt.j) \
                                    if stmt.i is not None and stmt.j is not None else None
                    coordinate_ctx.update(stmt.x, stmt.y, stmt.radius, center_offset)
                    if stmt.x is not None or stmt.y is not None:
                        if status == STAT_DRILL:
                            yield DrillHitEx(current_tool, (coordinate_ctx.x, coordinate_ctx.y))
                        elif status == STAT_ROUT_UP:
                            rout_nodes = [coordinate_ctx.node(DrillRout.MODE_ROUT, None)]
                        elif status == STAT_ROUT_DOWN:
                            rout_nodes.append(coordinate_ctx.node(rout_mode, center_offset))

        statements = [s for s in correct_statements()]
        hits = [h for h in generate_hits(statements)]
        return cls(statements, file.tools, hits, file.settings, file.filename)
    
    @property
    def primitives(self):
        return []

    def __init__(self, statements, tools, hits, settings, filename=None):
        super(ExcellonFileEx, self).__init__(statements, tools, hits, settings, filename)

    def rotate(self, angle, center=(0,0)):
        if angle % 360 == 0:
            return
        for hit in self.hits:
            hit.rotate(angle, center)
    
    def to_inch(self):
        if self.units == 'metric':
            for stmt in self.statements:
                stmt.to_inch()
            for tool in self.tools:
                self.tools[tool].to_inch()
            for hit in self.hits:
                hit.to_inch()
            self.units = 'inch'

    def to_metric(self):
        if self.units == 'inch':
            for stmt in self.statements:
                stmt.to_metric()
            for tool in self.tools:
                self.tools[tool].to_metric()
            for hit in self.hits:
                hit.to_metric()
            self.units = 'metric'
    
    def write(self, filename=None):
        self.notation = 'absolute'
        self.zeros = 'trailing'
        filename = filename if filename is not None else self.filename
        with open(filename, 'w') as f:
            write_excellon_header(f, self.settings, [self.tools[t] for t in self.tools])
            for tool in iter(self.tools.values()):
                f.write(ToolSelectionStmt(
                    tool.number).to_excellon(self.settings) + '\n')
                for hit in self.hits:
                    if hit.tool.number == tool.number:
                        f.write(hit.to_excellon(self.settings) + '\n')
            f.write(EndOfProgramStmt().to_excellon() + '\n')


class DrillHitEx(DrillHit):
    def to_inch(self):
        self.position = tuple(map(inch, self.position))

    def to_metric(self):
        self.position = tuple(map(metric, self.position))

    def rotate(self, angle, center=(0, 0)):
        self.position = rotate(*self.position, angle, center)

    def to_excellon(self, settings):
        return CoordinateStmtEx(*self.position).to_excellon(settings)


class DrillSlotEx(DrillSlot):
    def to_inch(self):
        self.start = tuple(map(inch, self.start))
        self.end = tuple(map(inch, self.end))

    def to_metric(self):
        self.start = tuple(map(metric, self.start))
        self.end = tuple(map(metric, self.end))

    def rotate(self, angle, center=(0,0)):
        self.start = rotate(*self.start, angle, center)
        self.end = rotate(*self.end, angle, center)

    def to_excellon(self, settings):
        return SlotStmt(*self.start, *self.end).to_excellon(settings)


class DrillRout(object):
    MODE_ROUT = 'G00'
    MODE_LINEAR = 'G01'
    MODE_CIRCULER_CW = 'G02'
    MODE_CIRCULER_CCW = 'G03'

    class Node(object):
        def __init__(self, mode, x, y, radius=None, center_offset=None):
            self.mode = mode
            self.position = (x, y)
            self.radius = radius
            self.center_offset = center_offset

        def to_excellon(self, settings):
            center_offset = self.center_offset if self.center_offset is not None else (None, None)
            return self.mode + CoordinateStmtEx(
                *self.position, self.radius, *center_offset).to_excellon(settings)

    def __init__(self, tool, nodes):
        self.tool = tool
        self.nodes = nodes
        self.nodes[0].mode = self.MODE_ROUT

    def to_excellon(self, settings):
        excellon = self.nodes[0].to_excellon(settings) + '\nM15\n'
        for node in self.nodes[1:]:
            excellon += node.to_excellon(settings) + '\n'
        excellon += 'M16\nG05'
        return excellon

    def to_inch(self):
        for node in self.nodes:
            node.position = tuple(map(inch, node.position))
            node.radius = inch(
                node.radius) if node.radius is not None else None
            if node.center_offset is not None:
                node.center_offset = tuple(map(inch, node.center_offset))

    def to_metric(self):
        for node in self.nodes:
            node.position = tuple(map(metric, node.position))
            node.radius = metric(
                node.radius) if node.radius is not None else None
            if node.center_offset is not None:
                node.center_offset = tuple(map(metric, node.center_offset))

    def offset(self, x_offset=0, y_offset=0):
        for node in self.nodes:
            node.position = tuple(map(operator.add, node.position, (x_offset, y_offset)))

    def rotate(self, angle, center=(0, 0)):
        for node in self.nodes:
            node.position = rotate(*node.position, angle, center)
            if node.center_offset is not None:
                node.center_offset = rotate(*node.center_offset, angle, (0., 0.))


class UnitStmtEx(UnitStmt):
    @classmethod
    def from_statement(cls, stmt):
        return cls(units=stmt.units, zeros=stmt.zeros, format=stmt.format, id=stmt.id)

    def __init__(self, units='inch', zeros='leading', format=None, **kwargs):
        super(UnitStmtEx, self).__init__(units, zeros, format, **kwargs)
    
    def to_excellon(self, settings=None):
        format = settings.format if settings else self.format
        stmt = None
        if self.units == 'inch' and format == (2, 4):
            stmt = 'INCH,%s' % ('LZ' if self.zeros == 'leading' else 'TZ')
        else:
            stmt = '%s,%s,%s.%s' % ('INCH' if self.units == 'inch' else 'METRIC',
                              'LZ' if self.zeros == 'leading' else 'TZ',
                              '0' * format[0], '0' * format[1])
        return stmt


class CircularCWModeStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(CircularCWModeStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G02'


class CircularCCWModeStmt(ExcellonStatement):

    def __init__(self, **kwargs):
        super(CircularCCWModeStmt, self).__init__(**kwargs)

    def to_excellon(self, settings=None):
        return 'G02'


class CoordinateStmtEx(CoordinateStmt):
    @classmethod
    def from_statement(cls, stmt):
        newStmt = cls(x=stmt.x, y=stmt.y)
        newStmt.radius = stmt.radius if isinstance(stmt, CoordinateStmtEx) else None
        return newStmt

    @classmethod
    def from_excellon(cls, line, settings, **kwargs):
        stmt = None
        if 'A' in line:
            parts = line.split('A')
            stmt = cls.from_statement(CoordinateStmt.from_excellon(parts[0], settings)) \
                   if parts[0] != '' else cls()
            stmt.radius = parse_gerber_value(
                parts[1], settings.format, settings.zero_suppression)
        elif 'I' in line:
            jparts = line.split('J')
            iparts = jparts[0].split('I')
            stmt = cls.from_statement(CoordinateStmt.from_excellon(iparts[0], settings)) \
                   if iparts[0] != '' else cls()
            stmt.i = parse_gerber_value(
                iparts[1], settings.format, settings.zero_suppression)
            stmt.j = parse_gerber_value(
                jparts[1], settings.format, settings.zero_suppression)
        else:
            stmt = cls.from_statement(CoordinateStmt.from_excellon(line, settings))
            
        return stmt

    def __init__(self, x=None, y=None, radius=None, i=None, j=None, **kwargs):
        super(CoordinateStmtEx, self).__init__(x, y, **kwargs)
        self.radius = radius
        self.i = i
        self.j = j
    
    def to_excellon(self, settings):
        #print('to_excellon')
        #print(' settings: {}'.format(settings))
        stmt = ''
        if self.x is not None:
            #print(' self.x: {}'.format(self.x))
            string = 'X%s' % write_gerber_value(self.x, settings.format, settings.zero_suppression, settings.zeros)
            #print(' string: {}'.format(string))
            stmt += string
        if self.y is not None:
            #print(' self.y: {}'.format(self.y))
            string = 'Y%s' % write_gerber_value(self.y, settings.format, settings.zero_suppression, settings.zeros)
            #print(' string: {}'.format(string))
            stmt += string
        if self.radius is not None:
            stmt += 'A%s' % write_gerber_value(self.radius, settings.format, settings.zero_suppression)
        elif self.i is not None and self.j is not None:
            stmt += 'I%sJ%s' % (write_gerber_value(self.i, settings.format, settings.zero_suppression),
                                write_gerber_value(self.j, settings.format, settings.zero_suppression))
        return stmt

    def __str__(self):
        coord_str = ''
        if self.x is not None:
            coord_str += 'X: %g ' % self.x
        if self.y is not None:
            coord_str += 'Y: %g ' % self.y
        if self.radius is not None:
            coord_str += 'A: %g ' % self.radius
        if self.i is not None:
            coord_str += 'I: %g ' % self.i
        if self.j is not None:
            coord_str += 'J: %g ' % self.j

        return '<Coordinate Statement: %s>' % (coord_str)
