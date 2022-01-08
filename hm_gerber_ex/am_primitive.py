#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2022 HalfMarble LLC
# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from hm_gerber_tool.utils import *
from hm_gerber_tool.am_statements import *
from hm_gerber_tool.am_eval import OpCode

from hm_gerber_ex.am_expression import eval_macro, AMConstantExpression, AMOperatorExpression


class AMPrimitiveDef(AMPrimitive):
    def __init__(self, code, exposure=None, rotation=None):
        super(AMPrimitiveDef, self).__init__(code, exposure)
        if not rotation:
            rotation = AMConstantExpression(0)
        self.rotation = rotation

    def rotate(self, angle, center=None):
        self.rotation = AMOperatorExpression(AMOperatorExpression.ADD, 
                                             self.rotation, 
                                             AMConstantExpression(float(angle)))
        self.rotation = self.rotation.optimize()

    def to_inch(self):
        pass
    
    def to_metric(self):
        pass

    def to_gerber(self, settings=None):
        pass

    def to_instructions(self):
        pass


class AMCommentPrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        return cls(code, modifiers[0])
    
    def __init__(self, code, comment):
        super(AMCommentPrimitiveDef, self).__init__(code)
        self.comment = comment
    
    def to_gerber(self, settings=None):
        return '%d %s*' % (self.code, self.comment.to_gerber())
    
    def to_instructions(self):
        return [(OpCode.PUSH, self.comment), (OpCode.PRIM, self.code)]


class AMCirclePrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        exposure = 'on' if modifiers[0].value == 1 else 'off'
        diameter = modifiers[1]
        center_x = modifiers[2]
        center_y = modifiers[3]
        rotation = modifiers[4] if len(modifiers)>4 else AMConstantExpression(float(0))
        return cls(code, exposure, diameter, center_x, center_y, rotation)

    def __init__(self, code, exposure, diameter, center_x, center_y, rotation):
        super(AMCirclePrimitiveDef, self).__init__(code, exposure, rotation)
        self.diameter = diameter
        self.center_x = center_x
        self.center_y = center_y

    def to_inch(self):
        self.diameter = self.diameter.to_inch().optimize()
        self.center_x = self.center_x.to_inch().optimize()
        self.center_y = self.center_y.to_inch().optimize()
    
    def to_metric(self):
        self.diameter = self.diameter.to_metric().optimize()
        self.center_x = self.center_x.to_metric().optimize()
        self.center_y = self.center_y.to_metric().optimize()

    def to_gerber(self, settings=None):
        data = dict(code = self.code,
                    exposure = 1 if self.exposure == 'on' else 0,
                    diameter = self.diameter.to_gerber(settings),
                    x = self.center_x.to_gerber(settings),
                    y = self.center_y.to_gerber(settings),
                    rotation = self.rotation.to_gerber(settings))
        return '{code},{exposure},{diameter},{x},{y},{rotation}*'.format(**data)
        
    def to_instructions(self):
        yield (OpCode.PUSH, 1 if self.exposure == 'on' else 0)
        for modifier in [self.diameter, self.center_x, self.center_y, self.rotation]:
            for i in modifier.to_instructions():
                yield i
        yield (OpCode.PRIM, self.code)


class AMVectorLinePrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        code = code
        exposure = 'on' if modifiers[0].value == 1 else 'off'
        width = modifiers[1]
        start_x = modifiers[2]
        start_y = modifiers[3]
        end_x = modifiers[4]
        end_y = modifiers[5]
        rotation = modifiers[6]
        return cls(code, exposure, width, start_x, start_y, end_x, end_y, rotation)

    def __init__(self, code, exposure, width, start_x, start_y, end_x, end_y, rotation):
        super(AMVectorLinePrimitiveDef, self).__init__(code, exposure, rotation)
        self.width = width
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y

    def to_inch(self):
        self.width = self.width.to_inch().optimize()
        self.start_x = self.start_x.to_inch().optimize()
        self.start_y = self.start_y.to_inch().optimize()
        self.end_x = self.end_x.to_inch().optimize()
        self.end_y = self.end_y.to_inch().optimize()
    
    def to_metric(self):
        self.width = self.width.to_metric().optimize()
        self.start_x = self.start_x.to_metric().optimize()
        self.start_y = self.start_y.to_metric().optimize()
        self.end_x = self.end_x.to_metric().optimize()
        self.end_y = self.end_y.to_metric().optimize()

    def to_gerber(self, settings=None):
        data = dict(code = self.code,
                    exposure = 1 if self.exposure == 'on' else 0,
                    width = self.width.to_gerber(settings),
                    start_x = self.start_x.to_gerber(settings),
                    start_y = self.start_y.to_gerber(settings),
                    end_x = self.end_x.to_gerber(settings),
                    end_y = self.end_y.to_gerber(settings),
                    rotation = self.rotation.to_gerber(settings))
        return '{code},{exposure},{width},{start_x},{start_y},{end_x},{end_y},{rotation}*'.format(**data)
        
    def to_instructions(self):
        yield (OpCode.PUSH, 1 if self.exposure == 'on' else 0)
        modifiers = [self.width, self.start_x, self.start_y, self.end_x, self.end_y, self.rotation]
        for modifier in modifiers:
            for i in modifier.to_instructions():
                yield i
        yield (OpCode.PRIM, self.code)


class AMCenterLinePrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        code = code
        exposure = 'on' if modifiers[0].value == 1 else 'off'
        width = modifiers[1]
        height = modifiers[2]
        x = modifiers[3]
        y = modifiers[4]
        rotation = modifiers[5]
        return cls(code, exposure, width, height, x, y, rotation)

    def __init__(self, code, exposure, width, height, x, y, rotation):
        super(AMCenterLinePrimitiveDef, self).__init__(code, exposure, rotation)
        self.width = width
        self.height = height
        self.x = x
        self.y = y

    def to_inch(self):
        self.width = self.width.to_inch().optimize()
        self.height = self.height.to_inch().optimize()
        self.x = self.x.to_inch().optimize()
        self.y = self.y.to_inch().optimize()
    
    def to_metric(self):
        self.width = self.width.to_metric().optimize()
        self.height = self.height.to_metric().optimize()
        self.x = self.x.to_metric().optimize()
        self.y = self.y.to_metric().optimize()

    def to_gerber(self, settings=None):
        data = dict(code = self.code,
                    exposure = 1 if self.exposure == 'on' else 0,
                    width = self.width.to_gerber(settings),
                    height = self.height.to_gerber(settings),
                    x = self.x.to_gerber(settings),
                    y = self.y.to_gerber(settings),
                    rotation = self.rotation.to_gerber(settings))
        return '{code},{exposure},{width},{height},{x},{y},{rotation}*'.format(**data)
        
    def to_instructions(self):
        yield (OpCode.PUSH, 1 if self.exposure == 'on' else 0)
        modifiers = [self.width, self.height, self.x, self.y, self.rotation]
        for modifier in modifiers:
            for i in modifier.to_instructions():
                yield i
        yield (OpCode.PRIM, self.code)


class AMOutlinePrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        num_points = int(modifiers[1].value + 1)
        code = code
        exposure = 'on' if modifiers[0].value == 1 else 'off'
        addrs = modifiers[2:num_points * 2 + 2]
        rotation = modifiers[2 + num_points * 2]
        return cls(code, exposure, addrs, rotation)

    def __init__(self, code, exposure, addrs, rotation):
        super(AMOutlinePrimitiveDef, self).__init__(code, exposure, rotation)
        self.addrs = addrs

    def to_inch(self):
        self.addrs = [i.to_inch().optimize() for i in self.addrs]
    
    def to_metric(self):
        self.addrs = [i.to_metric().optimize() for i in self.addrs]
 
    def to_gerber(self, settings=None):
        def strs():
            yield '%d,%d,%d' % (self.code, 
                                1 if self.exposure == 'on' else 0,
                                len(self.addrs) / 2 - 1)
            for i in self.addrs:
                yield i.to_gerber(settings)
            yield self.rotation.to_gerber(settings)

        return '%s*' % ','.join(strs())
        
    def to_instructions(self):
        yield (OpCode.PUSH, 1 if self.exposure == 'on' else 0)
        yield (OpCode.PUSH, int(len(self.addrs) / 2 - 1))
        for modifier in self.addrs:
            for i in modifier.to_instructions():
                yield i
        for i in self.rotation.to_instructions():
            yield i
        yield (OpCode.PRIM, self.code)


class AMPolygonPrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        code = code
        exposure = 'on' if modifiers[0].value == 1 else 'off'
        vertices = modifiers[1]
        x = modifiers[2]
        y = modifiers[3]
        diameter = modifiers[4]
        rotation = modifiers[5]
        return cls(code, exposure, vertices, x, y, diameter, rotation)

    def __init__(self, code, exposure, vertices, x, y, diameter, rotation):
        super(AMPolygonPrimitiveDef, self).__init__(code, exposure, rotation)
        self.vertices = vertices
        self.x = x
        self.y = y
        self.diameter = diameter

    def to_inch(self):
        self.x = self.x.to_inch().optimize()
        self.y = self.y.to_inch().optimize()
        self.diameter = self.diameter.to_inch().optimize()
    
    def to_metric(self):
        self.x = self.x.to_metric().optimize()
        self.y = self.y.to_metric().optimize()
        self.diameter = self.diameter.to_metric().optimize()

    def to_gerber(self, settings=None):
        data = dict(code = self.code,
                    exposure = 1 if self.exposure == 'on' else 0,
                    vertices = self.vertices.to_gerber(settings),
                    x = self.x.to_gerber(settings),
                    y = self.y.to_gerber(settings),
                    diameter = self.diameter.to_gerber(settings),
                    rotation = self.rotation.to_gerber(settings))
        return '{code},{exposure},{vertices},{x},{y},{diameter},{rotation}*'.format(**data)
        
    def to_instructions(self):
        yield (OpCode.PUSH, 1 if self.exposure == 'on' else 0)
        modifiers = [self.vertices, self.x, self.y, self.diameter, self.rotation]
        for modifier in modifiers:
            for i in modifier.to_instructions():
                yield i
        yield (OpCode.PRIM, self.code)


class AMMoirePrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        code = code
        exposure = 'on'
        x = modifiers[0]
        y = modifiers[1]
        diameter = modifiers[2]
        ring_thickness = modifiers[3]
        gap = modifiers[4]
        max_rings = modifiers[5]
        crosshair_thickness = modifiers[6]
        crosshair_length = modifiers[7]
        rotation = modifiers[8]
        return cls(code, exposure, x, y, diameter, ring_thickness, gap,
                   max_rings, crosshair_thickness, crosshair_length, rotation)

    def __init__(self, code, exposure, x, y, diameter, ring_thickness, gap, max_rings, crosshair_thickness, crosshair_length, rotation):
        super(AMMoirePrimitiveDef, self).__init__(code, exposure, rotation)
        self.x = x
        self.y = y
        self.diameter = diameter
        self.ring_thickness = ring_thickness
        self.gap = gap
        self.max_rings = max_rings
        self.crosshair_thickness = crosshair_thickness
        self.crosshair_length = crosshair_length

    def to_inch(self):
        self.x = self.x.to_inch().optimize()
        self.y = self.y.to_inch().optimize()
        self.diameter = self.diameter.to_inch().optimize()
        self.ring_thickness = self.ring_thickness.to_inch().optimize()
        self.gap = self.gap.to_inch().optimize()
        self.crosshair_thickness = self.crosshair_thickness.to_inch().optimize()
        self.crosshair_length = self.crosshair_length.to_inch().optimize()
    
    def to_metric(self):
        self.x = self.x.to_metric().optimize()
        self.y = self.y.to_metric().optimize()
        self.diameter = self.diameter.to_metric().optimize()
        self.ring_thickness = self.ring_thickness.to_metric().optimize()
        self.gap = self.gap.to_metric().optimize()
        self.crosshair_thickness = self.crosshair_thickness.to_metric().optimize()
        self.crosshair_length = self.crosshair_length.to_metric().optimize()

    def to_gerber(self, settings=None):
        data = dict(code = self.code,
                    x = self.x.to_gerber(settings),
                    y = self.y.to_gerber(settings),
                    diameter = self.diameter.to_gerber(settings),
                    ring_thickness = self.ring_thickness.to_gerber(settings),
                    gap = self.gap.to_gerber(settings),
                    max_rings = self.max_rings.to_gerber(settings),
                    crosshair_thickness = self.crosshair_thickness.to_gerber(settings),
                    crosshair_length = self.crosshair_length.to_gerber(settings),
                    rotation = self.rotation.to_gerber(settings))
        return '{code},{x},{y},{diameter},{ring_thickness},{gap},{max_rings},'\
               '{crosshair_thickness},{crosshair_length},{rotation}*'.format(**data)
        
    def to_instructions(self):
        modifiers = [self.x, self.y, self.diameter, 
                     self.ring_thickness, self.gap, self.max_rings,
                     self.crosshair_thickness, self.crosshair_length,
                     self.rotation]
        for modifier in modifiers:
            for i in modifier.to_instructions():
                yield i
        yield (OpCode.PRIM, self.code)


class AMThermalPrimitiveDef(AMPrimitiveDef):

    @classmethod
    def from_modifiers(cls, code, modifiers):
        code = code
        exposure = 'on'
        x = modifiers[0]
        y = modifiers[1]
        outer_diameter = modifiers[2]
        inner_diameter = modifiers[3]
        gap = modifiers[4]
        rotation = modifiers[5]
        return cls(code, exposure, x, y, outer_diameter, inner_diameter, gap, rotation)

    def __init__(self, code, exposure, x, y, outer_diameter, inner_diameter, gap, rotation):
        super(AMThermalPrimitiveDef, self).__init__(code, exposure, rotation)
        self.x = x
        self.y = y
        self.outer_diameter = outer_diameter
        self.inner_diameter = inner_diameter
        self.gap = gap

    def to_inch(self):
        self.x = self.x.to_inch().optimize()
        self.y = self.y.to_inch().optimize()
        self.outer_diameter = self.outer_diameter.to_inch().optimize()
        self.inner_diameter = self.inner_diameter.to_inch().optimize()
        self.gap = self.gap.to_inch().optimize()
    
    def to_metric(self):
        self.x = self.x.to_metric().optimize()
        self.y = self.y.to_metric().optimize()
        self.outer_diameter = self.outer_diameter.to_metric().optimize()
        self.inner_diameter = self.inner_diameter.to_metric().optimize()
        self.gap = self.gap.to_metric().optimize()

    def to_gerber(self, settings=None):
        data = dict(code = self.code,
                    x = self.x.to_gerber(settings),
                    y = self.y.to_gerber(settings),
                    outer_diameter = self.outer_diameter.to_gerber(settings),
                    inner_diameter = self.inner_diameter.to_gerber(settings),
                    gap = self.gap.to_gerber(settings),
                    rotation = self.rotation.to_gerber(settings))
        return '{code},{x},{y},{outer_diameter},{inner_diameter},'\
               '{gap},{rotation}*'.format(**data)
        
    def to_instructions(self):
        modifiers = [self.x, self.y, self.outer_diameter,
                     self.inner_diameter, self.gap, self.rotation]
        for modifier in modifiers:
            for i in modifier.to_instructions():
                yield i
        yield (OpCode.PRIM, self.code)


class AMVariableDef(object):

    def __init__(self, number, value):
        self.number = number
        self.value = value

    def to_inch(self):
        return self
    
    def to_metric(self):
        return self

    def to_gerber(self, settings=None):
        return '$%d=%s*' % (self.number, self.value.to_gerber(settings))

    def to_instructions(self):
        for i in self.value.to_instructions():
            yield i
        yield (OpCode.STORE, self.number)

    def rotate(self, angle, center=None):
        pass


def to_primitive_defs(instructions):
    classes = {
        0: AMCommentPrimitiveDef,
        1: AMCirclePrimitiveDef,
        2: AMVectorLinePrimitiveDef,
        20: AMVectorLinePrimitiveDef,
        21: AMCenterLinePrimitiveDef,
        4: AMOutlinePrimitiveDef,
        5: AMPolygonPrimitiveDef,
        6: AMMoirePrimitiveDef,
        7: AMThermalPrimitiveDef,
    }
    for code, modifiers in eval_macro(instructions):
        if code < 0:
            yield AMVariableDef(-code, modifiers[0])
        else:
            primitive = classes[code]
            yield primitive.from_modifiers(code, modifiers)
