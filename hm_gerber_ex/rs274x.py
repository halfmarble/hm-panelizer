#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022 HalfMarble LLC
# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from hm_gerber_tool.cam import FileSettings
import hm_gerber_tool.rs274x
from hm_gerber_tool.gerber_statements import *
from hm_gerber_ex.gerber_statements import AMParamStmt, AMParamStmtEx, ADParamStmtEx
from hm_gerber_ex.utility import rotate
import re


def loads(data, filename=None):
    cls = hm_gerber_tool.rs274x.GerberParser
    cls.SF = r"(?P<param>SF)(A(?P<a>{decimal}))?(B(?P<b>{decimal}))?".format(decimal=cls.DECIMAL)
    cls.PARAMS = (cls.FS, cls.MO, cls.LP, cls.AD_CIRCLE, 
                  cls.AD_RECT, cls.AD_OBROUND, cls.AD_POLY,
                  cls.AD_MACRO, cls.AM, cls.AS, cls.IF, cls.IN, 
                  cls.IP, cls.IR, cls.MI, cls.OF, cls.SF, cls.LN)
    cls.PARAM_STMT = [re.compile(r"%?{0}\*%?".format(p)) for p in cls.PARAMS]
    return cls().parse_raw(data, filename)


def write_gerber_header(file, settings):
    file.write('%s\n%s\n%%IPPOS*%%\n' % (
               MOParamStmt('MO', settings.units).to_gerber(settings),
               FSParamStmt('FS', settings.zero_suppression, 
                           settings.notation, settings.format).to_gerber(settings)))


class GerberFile(hm_gerber_tool.rs274x.GerberFile):

    @classmethod
    def from_gerber_file(cls, gerber_file):
        if not isinstance(gerber_file, hm_gerber_tool.rs274x.GerberFile):
            raise Exception('only gerber.rs274x.GerberFile object is specified')
        
        return cls(gerber_file.statements, gerber_file.settings, gerber_file.primitives,
                   gerber_file.apertures, gerber_file.filename)

    def __init__(self, statements, settings, primitives, apertures, filename=None):
        super(GerberFile, self).__init__(statements, settings, primitives, apertures, filename)
        self.context = GerberContext.from_settings(self.settings)
        self.aperture_macros = {}
        self.aperture_defs = []
        self.main_statements = []
        for stmt in self.statements:
            type, stmts = self.context.normalize_statement(stmt)
            if type == self.context.TYPE_AM:
                for mdef in stmts:
                    self.aperture_macros[mdef.name] = mdef
            elif type == self.context.TYPE_AD:
                self.aperture_defs.extend(stmts)
            elif type == self.context.TYPE_MAIN:
                self.main_statements.extend(stmts)
        if self.context.angle != 0:
            self.rotate(self.context.angle)
        if self.context.is_negative:
            self.negate_polarity()
        self.context.notation = 'absolute'
        self.context.zeros = 'trailing'

    def write(self, filename=None):
        self.context.notation = 'absolute'
        self.context.zeros = 'trailing'
        self.context.format = self.format
        self.units = self.units
        filename=filename if filename is not None else self.filename
        with open(filename, 'w') as f:
            write_gerber_header(f, self.context)
            for macro in self.aperture_macros:
                f.write(self.aperture_macros[macro].to_gerber(self.context) + '\n')
            for aperture in self.aperture_defs:
                f.write(aperture.to_gerber(self.context) + '\n')
            for statement in self.main_statements:
                f.write(statement.to_gerber(self.context) + '\n')
            f.write('M02*\n')

    def to_inch(self):
        if self.units == 'metric':
            for macro in self.aperture_macros:
                self.aperture_macros[macro].to_inch()
            for aperture in self.aperture_defs:
                aperture.to_inch()
            for statement in self.statements:
                statement.to_inch()
            self.units = 'inch'
            self.context.units = 'inch'

    def to_metric(self):
        if self.units == 'inch':
            for macro in self.aperture_macros:
                self.aperture_macros[macro].to_metric()
            for aperture in self.aperture_defs:
                aperture.to_metric()
            for statement in self.statements:
                statement.to_metric()
            self.units='metric'
            self.context.units='metric'

    def offset(self, x_offset=0, y_offset=0):
        for statement in self.main_statements:
            if isinstance(statement, CoordStmt):
                if statement.x is not None:
                    statement.x += x_offset
                if statement.y is not None:
                    statement.y += y_offset
        for primitive in self.primitives:
            primitive.offset(x_offset, y_offset)

    def rotate(self, angle, center=(0, 0)):
        if angle % 360 == 0:
            return
        self._generalize_aperture()
        last_x = 0
        last_y = 0
        last_rx = 0
        last_ry = 0
        for name in self.aperture_macros:
            self.aperture_macros[name].rotate(angle, center)
        for statement in self.main_statements:
            if isinstance(statement, CoordStmt) and statement.x is not None and statement.y is not None:
                if statement.i is not None and statement.j is not None:
                    cx = last_x + statement.i
                    cy = last_y + statement.j
                    cx, cy = rotate(cx, cy, angle, center)
                    statement.i = cx - last_rx
                    statement.j = cy - last_ry
                last_x = statement.x
                last_y = statement.y
                last_rx, last_ry = rotate(statement.x, statement.y, angle, center)
                statement.x = last_rx
                statement.y = last_ry
    
    def negate_polarity(self):
        for statement in self.main_statements:
            if isinstance(statement, LPParamStmt):
                statement.lp = 'dark' if statement.lp == 'clear' else 'clear'
    
    def _generalize_aperture(self):
        CIRCLE = 0
        RECTANGLE = 1
        LANDSCAPE_OBROUND = 2
        PORTRATE_OBROUND = 3
        POLYGON = 4
        macro_defs = [
            ('MACC', AMParamStmtEx.circle),
            ('MACR', AMParamStmtEx.rectangle),
            ('MACLO', AMParamStmtEx.landscape_obround),
            ('MACPO', AMParamStmtEx.portrate_obround),
            ('MACP', AMParamStmtEx.polygon)
        ]

        need_to_change = False
        for statement in self.aperture_defs:
            if isinstance(statement, ADParamStmt) and statement.shape in ['R', 'O', 'P']:
                need_to_change = True
        
        if need_to_change:
            for idx in range(0, len(macro_defs)):
                macro_def = macro_defs[idx]
                name = macro_def[0]
                num = 1
                while name in self.aperture_macros:
                    name = '%s_%d' % (macro_def[0], num)
                    num += 1
                self.aperture_macros[name] = macro_def[1](name, self.units)
                macro_defs[idx] = (name, macro_def[1])
            for statement in self.aperture_defs:
                if isinstance(statement, ADParamStmt):
                    if statement.shape == 'R':
                        statement.shape = macro_defs[RECTANGLE][0]
                    elif statement.shape == 'O':
                        x = statement.modifiers[0][0] if len(statement.modifiers[0]) > 0 else 0
                        y = statement.modifiers[0][1] if len(statement.modifiers[0]) > 1 else 0
                        if x == y:
                            statement.shape = macro_defs[CIRCLE][0]
                        elif x > y:
                            statement.shape = macro_defs[LANDSCAPE_OBROUND][0]
                        else:
                            statement.shape = macro_defs[PORTRATE_OBROUND][0]
                    elif statement.shape == 'P':
                        statement.shape = macro_defs[POLYGON][0]


class GerberContext(FileSettings):
    TYPE_NONE = 'none'
    TYPE_AM = 'am'
    TYPE_AD = 'ad'
    TYPE_MAIN = 'main'
    IP_LINEAR = 'linear'
    IP_ARC = 'arc'
    DIR_CLOCKWISE = 'cw'
    DIR_COUNTERCLOCKWISE = 'ccw'

    ignored_stmt = ('FSParamStmt', 'MOParamStmt', 'ASParamStmt',
                    'INParamStmt', 'IPParamStmt', 'IRParamStmt',
                    'MIParamStmt', 'OFParamStmt', 'SFParamStmt',
                    'LNParamStmt', 'CommentStmt', 'EofStmt',)

    @classmethod
    def from_settings(cls, settings):
        return cls(settings.notation, settings.units, settings.zero_suppression,
                   settings.format, settings.zeros, settings.angle_units)

    def __init__(self, notation='absolute', units='inch',
                 zero_suppression=None, format=(2, 5), zeros=None,
                 angle_units='degrees',
                 name=None,
                 mirror=(False, False), offset=(0., 0.), scale=(1., 1.),
                 angle=0., axis='xy'):
        super(GerberContext, self).__init__(notation, units, zero_suppression, format, zeros, angle_units)
        self.name = name
        self.mirror = mirror
        self.offset = offset
        self.scale = scale
        self.angle = angle
        self.axis = axis

        self.matrix = (1, 0, 
                       1, 0,
                       1, 1)

        self.is_negative = False
        self.is_first_coordinate = True
        self.no_polarity = True
        self.in_single_quadrant_mode = False
        self.op = None
        self.interpolation = self.IP_LINEAR
        self.direction = self.DIR_CLOCKWISE
        self.x = 0.
        self.y = 0.

    def normalize_statement(self, stmt):
        additional_stmts = None
        if isinstance(stmt, INParamStmt):
            self.name = stmt.name
        elif isinstance(stmt, MIParamStmt):
            self.mirror = (stmt.a, stmt.b)
            self._update_matrix()
        elif isinstance(stmt, OFParamStmt):
            self.offset = (stmt.a, stmt.b)
            self._update_matrix()
        elif isinstance(stmt, SFParamStmt):
            self.scale = (stmt.a, stmt.b)
            self._update_matrix()
        elif isinstance(stmt, ASParamStmt):
            self.axis = 'yx' if stmt.mode == 'AYBX' else 'xy'
            self._update_matrix()
        elif isinstance(stmt, IRParamStmt):
            self.angle = stmt.angle
        elif isinstance(stmt, AMParamStmt) and not isinstance(stmt, AMParamStmtEx):
            stmt = AMParamStmtEx.from_stmt(stmt)
            return (self.TYPE_AM, [stmt])
        elif isinstance(stmt, ADParamStmt) and not isinstance(stmt, AMParamStmtEx):
            stmt = ADParamStmtEx.from_stmt(stmt)
            return (self.TYPE_AD, [stmt])
        elif isinstance(stmt, QuadrantModeStmt):
            self.in_single_quadrant_mode = stmt.mode == 'single-quadrant'
            stmt.mode = 'multi-quadrant'
        elif isinstance(stmt, IPParamStmt):
            self.is_negative = stmt.ip == 'negative'
        elif isinstance(stmt, LPParamStmt):
            self.no_polarity = False
        elif isinstance(stmt, CoordStmt):
            self._normalize_coordinate(stmt)
            if self.is_first_coordinate:
                self.is_first_coordinate = False
                if self.no_polarity:
                    additional_stmts = [LPParamStmt('LP', 'dark'), stmt]

        if type(stmt).__name__ in self.ignored_stmt:
            return (self.TYPE_NONE, None)
        elif additional_stmts is not None:
            return (self.TYPE_MAIN, additional_stmts)
        else:
            return (self.TYPE_MAIN, [stmt])

    def _update_matrix(self):
        if self.axis == 'xy':
            mx = -1 if self.mirror[0] else 1
            my = -1 if self.mirror[1] else 1
            self.matrix = (
                self.scale[0] * mx, self.offset[0],
                self.scale[1] * my, self.offset[1],
                self.scale[0] * mx, self.scale[1] * my)
        else:
            mx = -1 if self.mirror[1] else 1
            my = -1 if self.mirror[0] else 1
            self.matrix = (
                self.scale[1] * mx, self.offset[1],
                self.scale[0] * my, self.offset[0],
                self.scale[1] * mx, self.scale[0] * my)

    def _normalize_coordinate(self, stmt):
        if stmt.function == 'G01' or stmt.function == 'G1':
            self.interpolation = self.IP_LINEAR
        elif stmt.function == 'G02' or stmt.function == 'G2':
            self.interpolation = self.IP_ARC
            self.direction = self.DIR_CLOCKWISE
            if self.mirror[0] != self.mirror[1]:
                stmt.function = 'G03'
        elif stmt.function == 'G03' or stmt.function == 'G3':
            self.interpolation = self.IP_ARC
            self.direction = self.DIR_COUNTERCLOCKWISE
            if self.mirror[0] != self.mirror[1]:
                stmt.function = 'G02'
        if stmt.only_function:
            return

        last_x = self.x
        last_y = self.y
        if self.notation == 'absolute':
            x = stmt.x if stmt.x is not None else self.x
            y = stmt.y if stmt.y is not None else self.y
        else:
            x = self.x + stmt.x if stmt.x is not None else 0
            y = self.y + stmt.y if stmt.y is not None else 0
        self.x, self.y = x, y
        self.op = stmt.op if stmt.op is not None else self.op

        stmt.op = self.op
        stmt.x = self.matrix[0] * x + self.matrix[1]
        stmt.y = self.matrix[2] * y + self.matrix[3]
        if stmt.op == 'D01' and self.interpolation == self.IP_ARC:
            qx, qy = 1, 1
            if self.in_single_quadrant_mode:
                if self.direction == self.DIR_CLOCKWISE:
                    qx = 1 if y > last_y else -1
                    qy = 1 if x < last_x else -1
                else:
                    qx = 1 if y < last_y else -1
                    qy = 1 if x > last_x else -1
                if last_x == x and last_y == y:
                    qx, qy = 0, 0
            stmt.i = qx * self.matrix[4] * stmt.i if stmt.i is not None else 0
            stmt.j = qy * self.matrix[5] * stmt.j if stmt.j is not None else 0
