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


from kivy.uix.label import Label
from kivy.uix.stencilview import StencilView
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle


class WorkScreen(StencilView):

    def __init__(self, **kwargs):
        super(WorkScreen, self).__init__(**kwargs)

        self._app = None

        with self.canvas:
            Color(1.0, 0.0, 0.0, 0.5)
            self.background_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_rect)

    def update_rect(self, *args):
        self.pos = (0, 2.0*self.pos[1])  # TODO: why do we need this here to center the screen vertically?
        self.background_rect.size = (self.pos[0]+self.size[0], self.pos[1]+self.size[1])
        self._app.resize(self.background_rect.size)


class LayerButton(ToggleButton):
    pass


class DemoLabel(Label):
    pass


class EmptyLabel(Label):
    pass


class PostLabel(Label):
    pass


class TitleLabel(Label):
    pass


class MenuLabel(Label):
    pass


class Settings(Popup):
    pass


class About(Popup):
    pass


class Progress(Popup):
    pass


class Error(Popup):
    pass

