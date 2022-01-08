#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022 HalfMarble LLC
# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from hm_gerber_tool.utils import inch, metric, write_gerber_value
from hm_gerber_tool.cam import FileSettings
from hm_gerber_ex.utility import is_equal_point, is_equal_value, normalize_vec2d, dot_vec2d
from hm_gerber_ex.excellon import CoordinateStmtEx

class DxfPath(object):
    def __init__(self, statements, error_range=0):
        self.statements = statements
        self.error_range = error_range
        self.bounding_box = statements[0].bounding_box
        self.containers = []
        for statement in statements[1:]:
            self._merge_bounding_box(statement.bounding_box)
    
    @property
    def start(self):
        return self.statements[0].start
    
    @property
    def end(self):
        return self.statements[-1].end

    @property
    def is_closed(self):
        if len(self.statements) == 1:
            return self.statements[0].is_closed
        else:
            return is_equal_point(self.start, self.end, self.error_range)
    
    def is_equal_to(self, target, error_range=0):
        if not isinstance(target, DxfPath):
            return False
        if len(self.statements) != len(target.statements):
            return False
        if is_equal_point(self.start, target.start, error_range) and \
           is_equal_point(self.end, target.end, error_range):
            for i in range(0, len(self.statements)):
               if not self.statements[i].is_equal_to(target.statements[i], error_range):
                   return False
            return True
        elif is_equal_point(self.start, target.end, error_range) and \
             is_equal_point(self.end, target.start, error_range):
            for i in range(0, len(self.statements)):
               if not self.statements[i].is_equal_to(target.statements[-1 - i], error_range):
                   return False
            return True
        return False
    
    def contain(self, target, error_range=0):
        for statement in self.statements:
            if statement.is_equal_to(target, error_range):
                return True
        else:
            return False

    def to_inch(self):
        self.error_range = inch(self.error_range)
        for statement in self.statements:
            statement.to_inch()

    def to_metric(self):
        self.error_range = metric(self.error_range)
        for statement in self.statements:
            statement.to_metric()

    def offset(self, offset_x, offset_y):
        for statement in self.statements:
            statement.offset(offset_x, offset_y)

    def rotate(self, angle, center=(0, 0)):
        for statement in self.statements:
            statement.rotate(angle, center)

    def reverse(self):
        rlist = []
        for statement in reversed(self.statements):
            statement.reverse()
            rlist.append(statement)
        self.statements = rlist
    
    def merge(self, element, error_range=0):
        if self.is_closed or element.is_closed:
            return False
        if not error_range:
            error_range = self.error_range
        if is_equal_point(self.end, element.start, error_range):
            return self._append_at_end(element, error_range)
        elif is_equal_point(self.end, element.end, error_range):
            element.reverse()
            return self._append_at_end(element, error_range)
        elif is_equal_point(self.start, element.end, error_range):
            return self._insert_on_top(element, error_range)
        elif is_equal_point(self.start, element.start, error_range):
            element.reverse()
            return self._insert_on_top(element, error_range)
        else:
            return False
    
    def _append_at_end(self, element, error_range=0):
        if isinstance(element, DxfPath):
            if self.is_equal_to(element, error_range):
                return False
            for i in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[-1 - i].is_equal_to(element.statements[i]):
                    break
            for j in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[j].is_equal_to(element.statements[-1 - j]):
                    break
            if i + j >= len(element.statements):
                return False
            mergee = list(element.statements)
            if i > 0:
                del mergee[0:i]
                del self.statements[-i]
            if j > 0:
                del mergee[-j]
                del self.statements[0:j]
            for statement in mergee:
                self._merge_bounding_box(statement.bounding_box)
            self.statements.extend(mergee)
            return True
        else:
            if self.statements[-1].is_equal_to(element, error_range) or \
               self.statements[0].is_equal_to(element, error_range):
                return False
            self._merge_bounding_box(element.bounding_box)
            self.statements.appen(element)
            return True

    def _insert_on_top(self, element, error_range=0):
        if isinstance(element, DxfPath):
            if self.is_equal_to(element, error_range):
                return False
            for i in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[-1 - i].is_equal_to(element.statements[i]):
                    break
            for j in range(0, min(len(self.statements), len(element.statements))):
                if not self.statements[j].is_equal_to(element.statements[-1 - j]):
                    break
            if i + j >= len(element.statements):
                return False
            mergee = list(element.statements)
            if i > 0:
                del mergee[0:i]
                del self.statements[-i]
            if j > 0:
                del mergee[-j]
                del self.statements[0:j]
            self.statements[0:0] = mergee
            return True
        else:
            if self.statements[-1].is_equal_to(element, error_range) or \
               self.statements[0].is_equal_to(element, error_range):
                return False
            self.statements.insert(0, element)
            return True

    def _merge_bounding_box(self, box):
        self.bounding_box = (min(self.bounding_box[0], box[0]),
                             min(self.bounding_box[1], box[1]),
                             max(self.bounding_box[2], box[2]),
                             max(self.bounding_box[3], box[3]))

    def may_be_in_collision(self, path):
        if self.bounding_box[0] >= path.bounding_box[2] or \
           self.bounding_box[1] >= path.bounding_box[3] or \
           self.bounding_box[2] <= path.bounding_box[0] or \
           self.bounding_box[3] <= path.bounding_box[1]:
            return False
        else:
            return True

    def to_gerber(self, settings=FileSettings(), pitch=0, width=0):
        from hm_gerber_ex.dxf import DxfArcStatement
        if pitch == 0:
            x0, y0 = self.statements[0].start
            gerber = 'G01*\nX{0}Y{1}D02*\nG75*'.format(
                write_gerber_value(x0, settings.format,
                                   settings.zero_suppression),
                write_gerber_value(y0, settings.format,
                                   settings.zero_suppression),
            )

            for statement in self.statements:
                x0, y0 = statement.start
                x1, y1 = statement.end
                if isinstance(statement, DxfArcStatement):
                    xc, yc = statement.center
                    gerber += '\nG{0}*\nX{1}Y{2}I{3}J{4}D01*'.format(
                        '03' if statement.end_angle > statement.start_angle else '02',
                        write_gerber_value(x1, settings.format,
                                           settings.zero_suppression),
                        write_gerber_value(y1, settings.format,
                                           settings.zero_suppression),
                        write_gerber_value(xc - x0, settings.format,
                                           settings.zero_suppression),
                        write_gerber_value(yc - y0, settings.format,
                                           settings.zero_suppression)
                    )
                else:
                    gerber += '\nG01*\nX{0}Y{1}D01*'.format(
                        write_gerber_value(x1, settings.format,
                                           settings.zero_suppression),
                        write_gerber_value(y1, settings.format,
                                           settings.zero_suppression),
                    )
        else:
            def ploter(x, y):
                return 'X{0}Y{1}D03*\n'.format(
                    write_gerber_value(x, settings.format,
                                       settings.zero_suppression),
                    write_gerber_value(y, settings.format,
                                          settings.zero_suppression),
                )
            gerber = self._plot_dots(pitch, width, ploter)

        return gerber

    def to_excellon(self, settings=FileSettings(), pitch=0, width=0):
        from hm_gerber_ex.dxf import DxfArcStatement
        if pitch == 0:
            x0, y0 = self.statements[0].start
            excellon = 'G00{0}\nM15\n'.format(
                CoordinateStmtEx(x=x0, y=y0).to_excellon(settings))

            for statement in self.statements:
                x0, y0 = statement.start
                x1, y1 = statement.end
                if isinstance(statement, DxfArcStatement):
                    i = statement.center[0] - x0
                    j = statement.center[1] - y0
                    excellon += '{0}{1}\n'.format(
                        'G03' if statement.end_angle > statement.start_angle else 'G02',
                        CoordinateStmtEx(x=x1, y=y1, i=i, j=j).to_excellon(settings))
                else:
                    excellon += 'G01{0}\n'.format(
                        CoordinateStmtEx(x=x1, y=y1).to_excellon(settings))
            
            excellon += 'M16\nG05\n'
        else:
            def ploter(x, y):
                return CoordinateStmtEx(x=x, y=y).to_excellon(settings) + '\n'
            excellon = self._plot_dots(pitch, width, ploter)

        return excellon

    def _plot_dots(self, pitch, width, ploter):
        out = ''
        offset = 0
        for idx in range(0, len(self.statements)):
            statement = self.statements[idx]
            if offset < 0:
                offset += pitch
            for dot, offset in statement.dots(pitch, width, offset):
                if dot is None:
                    break
                if offset > 0 and (statement.is_closed or idx != len(self.statements) - 1):
                    break
                #if idx == len(self.statements) - 1 and statement.is_closed and offset > -pitch:
                #    break
                out += ploter(dot[0], dot[1])
        return out

    def intersections_with_halfline(self, point_from, point_to, error_range=0):
        def calculator(statement):
            return statement.intersections_with_halfline(point_from, point_to, error_range)
        def validator(pt, statement, idx):
            if is_equal_point(pt, statement.end, error_range) and \
                not self._judge_cross(point_from, point_to, idx, error_range):
                    return False
            return True
        return self._collect_intersections(calculator, validator, error_range)

    def intersections_with_arc(self, center, radius, angle_regions, error_range=0):
        def calculator(statement):
            return statement.intersections_with_arc(center, radius, angle_regions, error_range)
        return self._collect_intersections(calculator, None, error_range)

    def _collect_intersections(self, calculator, validator, error_range):
        allpts = []
        last = allpts
        for i in range(0, len(self.statements)):
            statement = self.statements[i]
            cur = calculator(statement)
            if cur:
                for pt in cur:
                    for dest in allpts:
                        if is_equal_point(pt, dest, error_range):
                            break
                    else:
                        if validator is not None and not validator(pt, statement, i):
                            continue
                        allpts.append(pt)
            last = cur
        return allpts
    
    def _judge_cross(self, from_pt, to_pt, index, error_range):
        standard = normalize_vec2d((to_pt[0] - from_pt[0], to_pt[1] - from_pt[1]))
        normal = (standard[1], -standard[0])
        def statements():
            for i in range(index, len(self.statements)):
                yield self.statements[i]
            for i in range(0, index):
                yield self.statements[i]
        dot_standard = None
        for statement in statements():
            tstart = statement.start
            tend = statement.end
            target = normalize_vec2d((tend[0] - tstart[0], tend[1] - tstart[1]))
            dot= dot_vec2d(normal, target)
            if dot_standard is None:
                dot_standard = dot
                continue
            if is_equal_point(standard, target, error_range):
                continue
            return (dot_standard > 0 and dot > 0) or (dot_standard < 0 and dot < 0)
        raise Exception('inconsistensy is detected while cross judgement between paths')
            
def generate_paths(statements, error_range=0):
    from hm_gerber_ex.dxf import DxfPolylineStatement

    paths = []
    for statement in filter(lambda s: isinstance(s, DxfPolylineStatement), statements):
        units = [unit for unit in statement.disassemble()]
        paths.append(DxfPath(units, error_range))

    unique_statements = []
    redundant = 0
    for statement in filter(lambda s: not isinstance(s, DxfPolylineStatement), statements):
        for path in paths:
            if path.contain(statement):
                redundant += 1
                break
        else:
            for target in unique_statements:
                if statement.is_equal_to(target, error_range):
                    redundant += 1
                    break
            else:
                unique_statements.append(statement)

    paths.extend([DxfPath([s], error_range) for s in unique_statements])

    prev_paths_num = 0
    while prev_paths_num != len(paths):
        working = []
        for i in range(len(paths)):
            mergee = paths[i]
            for j in range(i + 1, len(paths)):
                target = paths[j]
                if target.merge(mergee, error_range):
                    break
            else:
                working.append(mergee)
        prev_paths_num = len(paths)
        paths = working
    
    closed_path = list(filter(lambda p: p.is_closed, paths))
    open_path = list(filter(lambda p: not p.is_closed, paths))
    return (closed_path, open_path)

def judge_containment(path1, path2, error_range=0):
    from hm_gerber_ex.dxf import DxfArcStatement, DxfLineStatement

    nocontainment = (None, None)
    if not path1.may_be_in_collision(path2):
        return nocontainment
    
    def is_in_line_segment(point_from, point_to, point):
        dx = point_to[0] - point_from[0]
        ratio = (point[0] - point_from[0]) / dx if dx != 0 else \
                (point[1] - point_from[1]) / (point_to[1] - point_from[1])
        return ratio >= 0 and ratio <= 1

    def contain_in_path(statement, path):
        if isinstance(statement, DxfLineStatement):
            segment = (statement.start, statement.end)
        elif isinstance(statement, DxfArcStatement):
            if statement.start == statement.end:
                segment = (statement.start, statement.center)
            else:
                segment = (statement.start, statement.end)
        else:
            raise Exception('invalid dxf statement type')
        pts = path.intersections_with_halfline(segment[0], segment[1], error_range)
        if len(pts) % 2 == 0:
            return False
        for pt in pts:
            if is_in_line_segment(segment[0], segment[1], pt):
                return False
        if isinstance(statement, DxfArcStatement):
            pts = path.intersections_with_arc(
                statement.center, statement.radius, statement.angle_regions, error_range)
            if len(pts) > 0:
                return False
        return True
    
    if contain_in_path(path1.statements[0], path2):
        containment = [path1, path2]
    elif contain_in_path(path2.statements[0], path1):
        containment = [path2, path1]
    else:
        return nocontainment
    for i in range(1, len(containment[0].statements)):
        if not contain_in_path(containment[0].statements[i], containment[1]):
            return nocontainment
    return containment
