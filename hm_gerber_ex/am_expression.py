#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 HalfMarble LLC
# Copyright 2019 Hiroshi Murayama <opiopan@gmail.com>

from hm_gerber_tool.utils import *
from hm_gerber_tool.am_eval import OpCode
from hm_gerber_tool.am_statements import *


class AMExpression(object):
    COMMENT = 0
    CONSTANT = 1
    VARIABLE = 2
    OPERATOR = 3

    def __init__(self, kind):
        self.kind = kind

    @property
    def value(self):
        return self

    def optimize(self):
        pass
    
    def to_inch(self):
        return AMOperatorExpression(AMOperatorExpression.DIV, self, 
                                    AMConstantExpression(MILLIMETERS_PER_INCH))

    def to_metric(self):
        return AMOperatorExpression(AMOperatorExpression.MUL, self,
                                    AMConstantExpression(MILLIMETERS_PER_INCH))

    def to_gerber(self, settings=None):
        pass

    def to_instructions(self):
        pass


class AMCommentExpression(AMExpression):
    def __init__(self, value):
        super(AMCommentExpression, self).__init__(AMExpression.COMMENT)
        self._value = value

    @property
    def value(self):
        return self._value

    def optimize(self):
        return self

    def to_gerber(self, settings=None):
        print('AMCommentExpression.to_gerber(): [{}]'.format(self._value))
        return '%s' % self._value

    def to_instructions(self):
        return [(OpCode.PRIM, self._value)]


class AMConstantExpression(AMExpression):
    def __init__(self, value):
        super(AMConstantExpression, self).__init__(AMExpression.CONSTANT)
        self._value = value

    @property
    def value(self):
        return self._value

    def optimize(self):
        return self
    
    def to_gerber(self, settings=None):
        if isinstance(self._value, str):
            return self._value
        else:
            gerber = '%.6g' % self._value
            return '%.6f' % self._value if 'e' in gerber else gerber

    def to_instructions(self):
        return [(OpCode.PUSH, self._value)]


class AMVariableExpression(AMExpression):
    def __init__(self, number):
        super(AMVariableExpression, self).__init__(AMExpression.VARIABLE)
        self.number = number

    def optimize(self):
        return self
    
    def to_gerber(self, settings=None):
        return '$%d' % self.number
    
    def to_instructions(self):
        return (OpCode.LOAD, self.number)


class AMOperatorExpression(AMExpression):
    ADD = '+'
    SUB = '-'
    MUL = 'X'
    DIV = '/'

    def __init__(self, op, lvalue, rvalue):
        super(AMOperatorExpression, self).__init__(AMExpression.OPERATOR)
        self.op = op
        self.lvalue = lvalue
        self.rvalue = rvalue
    
    def optimize(self):
        self.lvalue = self.lvalue.optimize()
        self.rvalue = self.rvalue.optimize()

        if isinstance(self.lvalue, AMConstantExpression) and isinstance(self.rvalue, AMConstantExpression):
            lvalue = float(self.lvalue.value)
            rvalue = float(self.rvalue.value)
            value = lvalue + rvalue if self.op == self.ADD else \
                lvalue - rvalue if self.op == self.SUB else \
                lvalue * rvalue if self.op == self.MUL else \
                lvalue / rvalue if self.op == self.DIV else None
            return AMConstantExpression(value)
        elif self.op == self.ADD:
            if self.rvalue.value == 0:
                return self.lvalue
            elif self.lvalue.value == 0:
                return self.rvalue
        elif self.op == self.SUB:
            if self.rvalue.value == 0:
                return self.lvalue
            elif self.lvalue.value == 0 and isinstance(self.rvalue, AMConstantExpression):
                return AMConstantExpression(-self.rvalue.value)
        elif self.op == self.MUL:
            if self.rvalue.value == 1:
                return self.lvalue
            elif self.lvalue.value == 1:
                return self.rvalue
            elif self.lvalue == 0 or self.rvalue == 0:
                return AMConstantExpression(0)
        elif self.op == self.DIV:
            if self.rvalue.value == 1:
                return self.lvalue
            elif self.lvalue.value == 0:
                return AMConstantExpression(0)
        
        return self
        
    def to_gerber(self, settings=None):
        return '(%s)%s(%s)' % (self.lvalue.to_gerber(settings), self.op, self.rvalue.to_gerber(settings))

    def to_instructions(self):
        for i in self.lvalue.to_instructions():
            yield i
        for i in self.rvalue.to_instructions():
            yield i
        op = OpCode.ADD if self.op == self.ADD else\
             OpCode.SUB if self.op == self.SUB else\
             OpCode.MUL if self.op == self.MUL else\
             OpCode.DIV
        yield (op, None)


def eval_macro(instructions):
    stack = []

    def pop():
        return stack.pop()

    def push(op):
        stack.append(op)

    def top():
        return stack[-1]

    def empty():
        return len(stack) == 0

    for opcode, argument in instructions:
        if opcode == OpCode.PUSH:
            push(AMConstantExpression(argument))
        elif opcode == OpCode.LOAD:
            push(AMVariableExpression(argument))
        elif opcode == OpCode.STORE:
            yield (-argument, [pop()])
        elif opcode == OpCode.ADD:
            op1 = pop()
            op2 = pop()
            push(AMOperatorExpression(AMOperatorExpression.ADD, op2, op1))
        elif opcode == OpCode.SUB:
            op1 = pop()
            op2 = pop()
            push(AMOperatorExpression(AMOperatorExpression.SUB, op2, op1))
        elif opcode == OpCode.MUL:
            op1 = pop()
            op2 = pop()
            push(AMOperatorExpression(AMOperatorExpression.MUL, op2, op1))
        elif opcode == OpCode.DIV:
            op1 = pop()
            op2 = pop()
            push(AMOperatorExpression(AMOperatorExpression.DIV, op2, op1))
        elif opcode == OpCode.PRIM:
            yield (argument, stack)
            stack = []
