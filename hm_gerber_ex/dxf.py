#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022 HalfMarble LLC
# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

import io, sys
from math import pi, cos, sin, tan, atan, atan2, acos, asin, sqrt
import dxfgrabber
from hm_gerber_tool.cam import CamFile, FileSettings
from hm_gerber_tool.utils import inch, metric, write_gerber_value, rotate_point
from hm_gerber_tool.gerber_statements import ADParamStmt
from hm_gerber_tool.excellon_statements import ExcellonTool
from hm_gerber_tool.excellon_statements import CoordinateStmt
from hm_gerber_ex.utility import is_equal_point, is_equal_value
from hm_gerber_ex.dxf_path import generate_paths, judge_containment
from hm_gerber_ex.excellon import write_excellon_header
from hm_gerber_ex.rs274x import write_gerber_header

ACCEPTABLE_ERROR = 0.001

def _normalize_angle(start_angle, end_angle):
    angle = end_angle - start_angle
    if angle > 0:
        start = start_angle % 360
    else:
        angle = -angle
        start = end_angle % 360
    angle = min(angle, 360)
    start = start - 360 if  start > 180 else start

    regions = []
    while angle > 0:
        end = start + angle
        if  end <= 180:
            regions.append((start * pi / 180, end * pi / 180))
            angle = 0
        else:
            regions.append((start * pi / 180, pi))
            angle = end - 180
            start = -180
    return regions

def _intersections_of_line_and_circle(start, end, center, radius, error_range):
    x1 = start[0] - center[0]
    y1 = start[1] - center[1]
    x2 = end[0] - center[0]
    y2 = end[1] - center[1]

    dx = x2 - x1
    dy = y2 - y1
    dr = sqrt(dx * dx + dy * dy)
    D = x1 * y2 - x2 * y1

    distance = abs(dy * x1 - dx * y1) / dr

    D2 = D * D
    dr2 = dr * dr
    r2 = radius * radius
    delta = r2 * dr2 - D2
    if distance > radius - error_range and distance < radius + error_range:
        delta = 0
    if delta < 0:
        return None

    sqrt_D = sqrt(delta)
    E_x = -dx * sqrt_D if dy < 0 else dx * sqrt_D
    E_y = abs(dy) * sqrt_D

    p1_x = (D * dy + E_x) / dr2
    p2_x = (D * dy - E_x) / dr2
    p1_y = (-D * dx + E_y) / dr2
    p2_y = (-D * dx - E_y) / dr2

    p1_angle = atan2(p1_y, p1_x)
    p2_angle = atan2(p2_y, p2_x)
    if dx == 0: 
        p1_t = (p1_y - y1) / dy
        p2_t = (p2_y - y1) / dy
    else:
        p1_t = (p1_x - x1) / dx
        p2_t = (p2_x - x1) / dx

    if delta == 0:
        return (
            (p1_x + center[0], p1_y + center[1]),
            None,
            p1_angle, None,
            p1_t, None
        )
    else:
        return (
            (p1_x + center[0], p1_y + center[1]),
            (p2_x + center[0], p2_y + center[1]),
            p1_angle, p2_angle,
            p1_t, p2_t
        )

class DxfStatement(object):
    def __init__(self, entity):
        self.entity = entity
        self.start = None
        self.end = None
        self.is_closed = False

    def to_inch(self):
        pass
    
    def to_metric(self):
        pass

    def is_equal_to(self, target, error_range=0):
        return False

    def reverse(self):
        raise Exception('Not implemented')

    def offset(self, offset_x, offset_y):
        raise Exception('Not supported')
    
    def rotate(self, angle, center=(0, 0)):
        raise Exception('Not supported')


class DxfLineStatement(DxfStatement):
    @classmethod
    def from_entity(cls, entity):
        start = (entity.start[0], entity.start[1])
        end = (entity.end[0], entity.end[1])
        return cls(entity, start, end)

    @property
    def bounding_box(self):
        return (min(self.start[0], self.end[0]),
                min(self.start[1], self.end[1]),
                max(self.start[0], self.end[0]),
                max(self.start[1], self.end[1]))

    def __init__(self, entity, start, end):
        super(DxfLineStatement, self).__init__(entity)
        self.start = start
        self.end = end

    def to_inch(self):
        self.start = (
            inch(self.start[0]), inch(self.start[1]))
        self.end = (
            inch(self.end[0]), inch(self.end[1]))

    def to_metric(self):
        self.start = (
            metric(self.start[0]), metric(self.start[1]))
        self.end = (
            metric(self.end[0]), metric(self.end[1]))

    def is_equal_to(self, target, error_range=0):
        if not isinstance(target, DxfLineStatement):
            return False
        return (is_equal_point(self.start, target.start, error_range) and \
                is_equal_point(self.end, target.end, error_range)) or \
               (is_equal_point(self.start, target.end, error_range) and \
                is_equal_point(self.end, target.start, error_range))

    def reverse(self):
        pt = self.start
        self.start = self.end
        self.end = pt

    def dots(self, pitch, width, offset=0):
        x0, y0 = self.start
        x1, y1 = self.end
        y1 = self.end[1]
        xp = x1 - x0
        yp = y1 - y0
        l = sqrt(xp * xp + yp * yp)
        xd = xp * pitch / l
        yd = yp * pitch / l
        x0 += xp * offset / l
        y0 += yp * offset / l

        if offset > l +  width / 2:
            return (None, offset - l)
        else:
            d = offset;
            while d < l + width / 2:
                yield ((x0, y0), d - l)
                x0 += xd
                y0 += yd
                d += pitch

    def offset(self, offset_x, offset_y):
        self.start = (self.start[0] + offset_x, self.start[1] + offset_y)
        self.end = (self.end[0] + offset_x, self.end[1] + offset_y)

    def rotate(self, angle, center=(0, 0)):
        self.start = rotate_point(self.start, angle, center)
        self.end = rotate_point(self.end, angle, center)
    
    def intersections_with_halfline(self, point_from, point_to, error_range):
        denominator = (self.end[0] - self.start[0]) * (point_to[1] - point_from[1]) - \
                      (self.end[1] - self.start[1]) * (point_to[0] - point_from[0])
        de = error_range * error_range
        if denominator >= -de and denominator <= de:
            return []
        from_dx = point_from[0] - self.start[0]
        from_dy = point_from[1] - self.start[1]
        r = ((point_to[1] - point_from[1]) * from_dx - 
             (point_to[0] - point_from[0]) * from_dy) / denominator
        s = ((self.end[1] - self.start[1]) * from_dx -
             (self.end[0] - self.start[0]) * from_dy) / denominator
        dx = (self.end[0] - self.start[0])
        dy = (self.end[1] - self.start[1])
        le = error_range / sqrt(dx * dx + dy * dy)
        if s < 0 or r < -le or r > 1 + le:
            return []
        
        pt = (self.start[0] + (self.end[0] - self.start[0]) * r,
              self.start[1] + (self.end[1] - self.start[1]) * r)
        if is_equal_point(pt, self.start, error_range):
            return []
        else:
            return [pt]

    def intersections_with_arc(self, center, radius, angle_regions, error_range):
        intersection = \
            _intersections_of_line_and_circle(self.start, self.end, center, radius, error_range)
        if intersection is None:
            return []
        else:
            p1, p2, p1_angle, p2_angle, p1_t, p2_t = intersection

        pts = []
        if p1_t >= 0 and p1_t <= 1:
            for region in angle_regions:
                if p1_angle >= region[0] and p1_angle <= region[1]:
                    pts.append(p1)
                    break
        if p2 is not None and p2_t >= 0 and p2_t <= 1:
            for region in angle_regions:
                if p2_angle >= region[0] and p2_angle <= region[1]:
                    pts.append(p2)
                    break

        return pts

class DxfArcStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfArcStatement, self).__init__(entity)
        if entity.dxftype == 'CIRCLE':
            self.radius = self.entity.radius
            self.center = (self.entity.center[0], self.entity.center[1])
            self.start = (self.center[0] + self.radius, self.center[1])
            self.end = self.start
            self.start_angle = 0
            self.end_angle = 360
            self.is_closed = True
        elif entity.dxftype == 'ARC':
            self.start_angle = self.entity.start_angle
            self.end_angle = self.entity.end_angle
            self.radius = self.entity.radius
            self.center = (self.entity.center[0], self.entity.center[1])
            self.start = (
                self.center[0] + self.radius * cos(self.start_angle / 180. * pi),
                self.center[1] + self.radius * sin(self.start_angle / 180. * pi),
            )
            self.end = (
                self.center[0] + self.radius * cos(self.end_angle / 180. * pi),
                self.center[1] + self.radius * sin(self.end_angle / 180. * pi),
            )
            angle = self.end_angle - self.start_angle
            self.is_closed = angle >= 360 or angle <= -360
        else:
            raise Exception('invalid DXF type was specified')
        self.angle_regions = _normalize_angle(self.start_angle, self.end_angle)

    @property
    def bounding_box(self):
        return (self.center[0] - self.radius, self.center[1] - self.radius,
                self.center[0] + self.radius, self.center[1] + self.radius)

    def to_inch(self):
        self.radius = inch(self.radius)
        self.center = (inch(self.center[0]), inch(self.center[1]))
        self.start = (inch(self.start[0]), inch(self.start[1]))
        self.end = (inch(self.end[0]), inch(self.end[1]))

    def to_metric(self):
        self.radius = metric(self.radius)
        self.center = (metric(self.center[0]), metric(self.center[1]))
        self.start = (metric(self.start[0]), metric(self.start[1]))
        self.end = (metric(self.end[0]), metric(self.end[1]))

    def is_equal_to(self, target, error_range=0):
        if not isinstance(target, DxfArcStatement):
            return False
        aerror_range = error_range / pi * self.radius * 180
        return is_equal_point(self.center, target.center, error_range) and \
               is_equal_value(self.radius, target.radius, error_range) and \
               ((is_equal_value(self.start_angle, target.start_angle, aerror_range) and 
                 is_equal_value(self.end_angle, target.end_angle, aerror_range)) or
                (is_equal_value(self.start_angle, target.end_angle, aerror_range) and
                 is_equal_value(self.end_angle, target.end_angle, aerror_range)))

    def reverse(self):
        tmp = self.start_angle
        self.start_angle = self.end_angle
        self.end_angle = tmp
        tmp = self.start
        self.start = self.end
        self.end = tmp

    def dots(self, pitch, width, offset=0):
        angle = self.end_angle - self.start_angle
        afactor = 1 if angle > 0 else -1
        aangle = angle * afactor
        L = 2 * pi * self.radius
        l = L * aangle / 360
        pangle = pitch / L * 360
        wangle = width / L * 360
        oangle = offset / L * 360

        if offset > l + width / 2:
            yield (None, offset - l)
        else:
            da = oangle
            while da < aangle + wangle / 2:
                cangle = self.start_angle + da * afactor
                x = self.radius * cos(cangle / 180 * pi) + self.center[0]
                y = self.radius * sin(cangle / 180 * pi) + self.center[1]
                remain = (da - aangle) / 360 * L
                yield((x, y), remain)
                da += pangle

    def offset(self, offset_x, offset_y):
        self.center = (self.center[0] + offset_x, self.center[1] + offset_y)
        self.start = (self.start[0] + offset_x, self.start[1] + offset_y)
        self.end = (self.end[0] + offset_x, self.end[1] + offset_y)

    def rotate(self, angle, center=(0, 0)):
        self.start_angle += angle
        self.end_angle += angle
        self.center = rotate_point(self.center, angle, center)
        self.start = rotate_point(self.start, angle, center)
        self.end = rotate_point(self.end, angle, center)
        self.angle_regions = _normalize_angle(self.start_angle, self.end_angle)

    def intersections_with_halfline(self, point_from, point_to, error_range):
        intersection = \
            _intersections_of_line_and_circle(
                point_from, point_to, self.center, self.radius, error_range)
        if intersection is None:
            return []
        else:
            p1, p2, p1_angle, p2_angle, p1_t, p2_t = intersection
        
        if is_equal_point(p1, self.start, error_range):
            p1 = None
        elif p2 is not None and is_equal_point(p2, self.start, error_range):
            p2 = None

        def is_contained(angle, region, error):
            if angle >= region[0] - error and angle <= region[1] + error:
                return True
            if angle < 0 and region[1] > 0:
                angle = angle + 2 * pi
            elif angle > 0 and region[0] < 0:
                angle = angle - 2 * pi
            return  angle >= region[0] - error and angle <= region[1] + error
            
        aerror = error_range * self.radius
        pts = []
        if p1 is not None and p1_t >= 0 and not is_equal_point(p1, self.start, error_range):
            for region in self.angle_regions:
                if is_contained(p1_angle, region, aerror):
                    pts.append(p1)
                    break
        if p2 is not None and p2_t >= 0 and not is_equal_point(p2, self.start, error_range):
            for region in self.angle_regions:
                if is_contained(p2_angle, region, aerror):
                    pts.append(p2)
                    break

        return pts

    def intersections_with_arc(self, center, radius, angle_regions, error_range):
        x1 = center[0] - self.center[0]
        y1 = center[1] - self.center[1]
        r1 = self.radius
        r2 = radius
        cd_sq = x1 * x1 + y1 * y1
        cd = sqrt(cd_sq)
        rd = abs(r1 - r2)

        if (cd >= 0 and cd <= rd) or cd >= r1 + r2:
            return []
        
        A = (cd_sq + r1 * r1 - r2 * r2) / 2
        scale = sqrt(cd_sq * r1 * r1 - A * A) / cd_sq
        xl = A * x1 / cd_sq
        xr = y1 * scale
        yl = A * y1 / cd_sq
        yr = x1 * scale

        pt1_x = xl + xr
        pt1_y = yl - yr
        pt2_x = xl - xr
        pt2_y = yl + yr
        pt1_angle1 = atan2(pt1_y, pt1_x)
        pt1_angle2 = atan2(pt1_y - y1, pt1_x - x1)
        pt2_angle1 = atan2(pt2_y, pt2_x)
        pt2_angle2 = atan2(pt2_y - y1, pt2_x - x1)

        aerror = error_range * self.radius
        pts=[]
        for region in self.angle_regions:
            if pt1_angle1 >= region[0] and pt1_angle1 <= region[1]:
                for region in angle_regions:
                    if pt1_angle2 >= region[0] - aerror and pt1_angle2 <= region[1] + aerror:
                        pts.append((pt1_x + self.center[0], pt1_y + self.center[1]))
                        break
                break
        for region in self.angle_regions:
            if pt2_angle1 >= region[0] and pt2_angle1 <= region[1]:
                for region in angle_regions:
                    if pt2_angle2 >= region[0] - aerror and pt2_angle2 <= region[1] + aerror:
                        pts.append((pt2_x + self.center[0], pt2_y + self.center[1]))
                        break
                break
        return pts

class DxfPolylineStatement(DxfStatement):
    def __init__(self, entity):
        super(DxfPolylineStatement, self).__init__(entity)
        self.start = (self.entity.points[0][0], self.entity.points[0][1])
        self.is_closed = self.entity.is_closed
        if self.is_closed:
            self.end = self.start
        else:
            self.end = (self.entity.points[-1][0], self.entity.points[-1][1])

    def disassemble(self):
        class Item:
            pass

        def ptseq():
            for i in range(1, len(self.entity.points)):
                yield i
            if self.entity.is_closed:
                yield 0

        x0 = self.entity.points[0][0]
        y0 = self.entity.points[0][1]
        b = self.entity.bulge[0]
        for idx in ptseq():
            pt = self.entity.points[idx]
            x1 = pt[0]
            y1 = pt[1]
            if b == 0:
                item = Item()
                item.dxftype = 'LINE'
                item.start = (x0, y0)
                item.end = (x1, y1)
                item.is_closed = False
                yield DxfLineStatement.from_entity(item)
            else:
                ang = 4 * atan(b)
                xm = x0 + x1
                ym = y0 + y1
                t = 1 / tan(ang / 2)
                xc = (xm - t * (y1 - y0)) / 2
                yc = (ym + t * (x1 - x0)) / 2
                r = sqrt((x0 - xc)*(x0 - xc) + (y0 - yc)*(y0 - yc))
                rx0 = x0 - xc
                ry0 = y0 - yc
                rc = max(min(rx0 / r, 1.0), -1.0)
                start_angle = acos(rc) if ry0 > 0 else 2 * pi - acos(rc)
                start_angle *= 180 / pi
                end_angle = start_angle + ang * 180 / pi

                item = Item()
                item.dxftype = 'ARC'
                item.start = (x0, y0)
                item.end = (x1, y1)
                item.start_angle = start_angle
                item.end_angle = end_angle
                item.radius = r
                item.center = (xc, yc)
                item.is_closed = end_angle - start_angle >= 360
                yield DxfArcStatement(item)

            x0 = x1
            y0 = y1
            b = self.entity.bulge[idx]

    def to_inch(self):
        self.start = (inch(self.start[0]), inch(self.start[1]))
        self.end = (inch(self.end[0]), inch(self.end[1]))
        for idx in range(0, len(self.entity.points)):
            self.entity.points[idx] = (
                inch(self.entity.points[idx][0]), inch(self.entity.points[idx][1]))

    def to_metric(self):
        self.start = (metric(self.start[0]), metric(self.start[1]))
        self.end = (metric(self.end[0]), metric(self.end[1]))
        for idx in range(0, len(self.entity.points)):
            self.entity.points[idx] = (
                metric(self.entity.points[idx][0]), metric(self.entity.points[idx][1]))
    
    def offset(self, offset_x, offset_y):
        for idx in range(len(self.entity.points)):
            self.entity.points[idx] = (
                self.entity.points[idx][0] + offset_x, self.entity.points[idx][1] + offset_y)

    def rotate(self, angle, center=(0, 0)):
        for idx in range(len(self.entity.points)):
            self.entity.points[idx] = rotate_point(self.entity.points[idx], angle, center)

class DxfStatements(object):
    def __init__(self, statements, units, dcode=10, draw_mode=None, fill_mode=None):
        if draw_mode is None:
            draw_mode = DxfFile.DM_LINE
        if fill_mode is None:
            fill_mode = DxfFile.FM_TURN_OVER
        self._units = units
        self.dcode = dcode
        self.draw_mode = draw_mode
        self.fill_mode = fill_mode
        self.pitch = inch(1) if self._units == 'inch' else 1
        self.width = 0
        self.error_range = inch(ACCEPTABLE_ERROR) if self._units == 'inch' else ACCEPTABLE_ERROR
        self.statements = list(filter(
            lambda i: not (isinstance(i, DxfLineStatement) and \
                          is_equal_point(i.start, i.end, self.error_range)),
            statements
        ))
        self.close_paths, self.open_paths = generate_paths(self.statements, self.error_range)
        self.sorted_close_paths = []
        self.polarity = True # True means dark, False means clear

    @property
    def units(self):
        return _units

    def _polarity_command(self, polarity=None):
        if polarity is None:
            polarity = self.polarity
        return '%LPD*%' if polarity else '%LPC*%'

    def _prepare_sorted_close_paths(self):
        if self.sorted_close_paths:
            return
        for i in range(0, len(self.close_paths)):
            for j in range(i + 1, len(self.close_paths)):
                containee, container = judge_containment(
                    self.close_paths[i], self.close_paths[j], self.error_range)
                if containee is not None:
                    containee.containers.append(container)
        self.sorted_close_paths = sorted(self.close_paths, key=lambda path: len(path.containers))

    def to_gerber(self, settings=FileSettings()):
        def gerbers():
            yield 'G75*'
            yield self._polarity_command()
            yield 'D{0}*'.format(self.dcode)
            if self.draw_mode == DxfFile.DM_FILL:
                yield 'G36*'
                if self.fill_mode == DxfFile.FM_TURN_OVER:
                    self._prepare_sorted_close_paths()
                    polarity = self.polarity
                    level = 0
                    for path in self.sorted_close_paths:
                        if len(path.containers) > level:
                            level = len(path.containers)
                            polarity = not polarity
                            yield 'G37*'
                            yield self._polarity_command(polarity)
                            yield 'G36*'
                        yield path.to_gerber(settings)
                else:
                    for path in self.close_paths:
                        yield path.to_gerber(settings)
                yield 'G37*'
            else:
                pitch = self.pitch if self.draw_mode == DxfFile.DM_MOUSE_BITES else 0
                for path in self.open_paths:
                    yield path.to_gerber(settings, pitch=pitch, width=self.width)
                for path in self.close_paths:
                    yield path.to_gerber(settings, pitch=pitch, width=self.width)

        return '\n'.join(gerbers())

    def to_excellon(self, settings=FileSettings()):
        if self.draw_mode == DxfFile.DM_FILL:
            return
        def drills():
            pitch = self.pitch if self.draw_mode == DxfFile.DM_MOUSE_BITES else 0
            for path in self.open_paths:
                yield path.to_excellon(settings, pitch=pitch, width=self.width)
            for path in self.close_paths:
                yield path.to_excellon(settings, pitch=pitch, width=self.width)
        return '\n'.join(drills())

    def to_inch(self):
        if self._units == 'metric':
            self._units = 'inch'
            self.pitch = inch(self.pitch)
            self.width = inch(self.width)
            self.error_range = inch(self.error_range)
            for path in self.open_paths:
                path.to_inch()
            for path in self.close_paths:
                path.to_inch()

    def to_metric(self):
        if self._units == 'inch':
            self._units = 'metric'
            self.pitch = metric(self.pitch)
            self.width = metric(self.width)
            self.error_range = metric(self.error_range)
            for path in self.open_paths:
                path.to_metric()
            for path in self.close_paths:
                path.to_metric()
    
    def offset(self, offset_x, offset_y):
        for path in self.open_paths:
            path.offset(offset_x, offset_y)
        for path in self.close_paths:
            path.offset(offset_x, offset_y)

    def rotate(self, angle, center=(0, 0)):
        for path in self.open_paths:
            path.rotate(angle, center)
        for path in self.close_paths:
            path.rotate(angle, center)

class DxfFile(CamFile):
    DM_LINE = 0
    DM_FILL = 1
    DM_MOUSE_BITES = 2

    FM_SIMPLE = 0
    FM_TURN_OVER = 1

    FT_RX274X = 0
    FT_EXCELLON = 1

    @classmethod
    def from_dxf(cls, dxf, settings=None, draw_mode=None, filename=None):
        fsettings = settings if settings else \
            FileSettings(zero_suppression='leading')

        if dxf.header['$INSUNITS'] == 1:
            fsettings.units = 'inch'
            if not settings:
                fsettings.format = (2, 5)
        else:
            fsettings.units = 'metric'
            if not settings:
                fsettings.format = (3, 4)

        statements = []
        for entity in dxf.entities:
            if entity.dxftype == 'LWPOLYLINE':
                statements.append(DxfPolylineStatement(entity))
            elif entity.dxftype == 'LINE':
                statements.append(DxfLineStatement.from_entity(entity))
            elif entity.dxftype == 'CIRCLE':
                statements.append(DxfArcStatement(entity))
            elif entity.dxftype == 'ARC':
                statements.append(DxfArcStatement(entity))
        
        return cls(statements, fsettings, draw_mode, filename)
    
    @classmethod
    def rectangle(cls, width, height, left=0, bottom=0, units='metric', draw_mode=None, filename=None):
        if units == 'metric':
            settings = FileSettings(units=units, zero_suppression='leading', format=(3,4))
        else:
            settings = FileSettings(units=units, zero_suppression='leading', format=(2,5))
        statements = [
            DxfLineStatement(None, (left, bottom), (left + width, bottom)),
            DxfLineStatement(None, (left + width, bottom), (left + width, bottom + height)),
            DxfLineStatement(None, (left + width, bottom + height), (left, bottom + height)),
            DxfLineStatement(None, (left, bottom + height), (left, bottom)),
        ]
        return cls(statements, settings, draw_mode, filename)

    def __init__(self, statements, settings=None, draw_mode=None, filename=None):
        if not settings:
            settings = FileSettings(units='metric', format=(3,4), zero_suppression='leading')
        if draw_mode == None:
            draw_mode = self.DM_LINE

        super(DxfFile, self).__init__(settings=settings, filename=filename)
        self._draw_mode = draw_mode
        self._fill_mode = self.FM_TURN_OVER
        
        self.aperture = ADParamStmt.circle(dcode=10, diameter=0.0)
        if settings.units == 'inch':
            self.aperture.to_inch()
        else:
            self.aperture.to_metric()
        self.statements = DxfStatements(
            statements, self.units, dcode=self.aperture.d, draw_mode=self.draw_mode, fill_mode=self.filename)

    @property
    def dcode(self):
        return self.aperture.dcode

    @dcode.setter
    def dcode(self, value):
        self.aperture.d = value
        self.statements.dcode = value

    @property
    def width(self):
        return self.aperture.modifiers[0][0]

    @width.setter
    def width(self, value):
        self.aperture.modifiers = ([float(value),],)
        self.statements.width = value

    @property
    def draw_mode(self):
        return self._draw_mode
    
    @draw_mode.setter
    def draw_mode(self, value):
        self._draw_mode = value
        self.statements.draw_mode = value

    @property
    def fill_mode(self):
        return self._fill_mode
    
    @fill_mode.setter
    def fill_mode(self, value):
        self._fill_mode = value
        self.statements.fill_mode = value

    @property
    def pitch(self):
        return self.statements.pitch
    
    @pitch.setter
    def pitch(self, value):
        self.statements.pitch = value
    
    def write(self, filename=None, filetype=FT_RX274X):
        self.settings.notation = 'absolute'
        self.settings.zeros = 'trailing'
        filename = filename if filename is not None else self.filename
        with open(filename, 'w') as f:
            if filetype == self.FT_RX274X:
                write_gerber_header(f, self.settings)
                f.write(self.aperture.to_gerber(self.settings) + '\n')
                f.write(self.statements.to_gerber(self.settings) + '\n')
                f.write('M02*\n')
            else:
                tools = [ExcellonTool(self.settings, number=1, diameter=self.width)]
                write_excellon_header(f, self.settings, tools)
                f.write('T01\n')
                f.write(self.statements.to_excellon(self.settings) + '\n')
                f.write('M30\n')


    def to_inch(self):
        if self.units == 'metric':
            self.aperture.to_inch()
            self.statements.to_inch()
            self.pitch = inch(self.pitch)
            self.units = 'inch'

    def to_metric(self):
        if self.units == 'inch':
            self.aperture.to_metric()
            self.statements.to_metric()
            self.pitch = metric(self.pitch)
            self.units = 'metric'

    def offset(self, offset_x, offset_y):
        self.statements.offset(offset_x, offset_y)
    
    def rotate(self, angle, center=(0, 0)):
        self.statements.rotate(angle, center)

    def negate_polarity(self):
        self.statements.polarity = not self.statements.polarity

def loads(data, filename=None):
    if sys.version_info.major == 2:
        data = unicode(data)
    stream = io.StringIO(data)
    dxf = dxfgrabber.read(stream)
    return DxfFile.from_dxf(dxf)
