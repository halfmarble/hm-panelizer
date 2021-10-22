# Copyright 2021 HalfMarble LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

# See the License for the specific language governing permissions and
# limitations under the License.

from os.path import dirname, join

import os
import math
import sys

from kivy import Config
Config.set('graphics', 'width', '1400')
Config.set('graphics', 'height', '900')
Config.set('graphics', 'minimum_width', '1000')
Config.set('graphics', 'minimum_height', '900')

from kivy.core.window import Window
Window.clearcolor = (1, 1, 1, 1)

from kivy import platform
from kivy.app import App

from kivy.clock import Clock

from kivy.lang import Builder

from kivy.uix.screenmanager import Screen

from kivy.uix.scatter import Scatter
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout

from kivy.uix.widget import Widget

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput

from kivy.properties import ListProperty

from kivy.graphics import Fbo, Color, Line, Rectangle, ClearBuffers, ClearColor
from kivy.graphics import Translate, PushMatrix, PopMatrix
from kivy.graphics.transformation import Matrix

import Constants


fs_mask = '''
$HEADER$
void main(void) {
    gl_FragColor = frag_color * texture2D(texture0, tex_coord0).a;
}
'''


def beep():
    #print('\a')
    sys.stdout.write("\a")


def is_desktop():
    if platform in ('linux', 'windows', 'macosx'):
        return True
    return False


class LayerButton(ToggleButton):
    pass


class GridRenderer:

    def __init__(self):
        self._pixels_per_cm = 1.0

    def set_pixels_per_cm(self, pixels_per_cm):
        self._pixels_per_cm = pixels_per_cm

    def paint(self, fbo, size):
        cx = size[0] / 2.0
        cy = size[1] / 2.0
        line_count_x = int(((math.floor(size[0] / self._pixels_per_cm)) / 2.0) + 1.0)
        line_count_y = int(((math.floor(size[1] / self._pixels_per_cm)) / 2.0) + 1.0)

        with fbo:
            c = Constants.GRID_BACKGROUND_COLOR
            ClearColor(c.r, c.g, c.b, c.a)
            ClearBuffers()

            x = 0.0
            sy = 0.0
            ey = size[1]
            c = Constants.GRID_MAJOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            Line(points=[cx, sy, cx, ey])
            x += self._pixels_per_cm
            c = Constants.GRID_MINOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            for i in range(0, line_count_x):
                x_int = int(round(x))
                Line(points=[cx + x_int, sy, cx + x_int, ey])
                Line(points=[cx - x_int, sy, cx - x_int, ey])
                x += self._pixels_per_cm

            y = 0.0
            sx = 0.0
            ex = size[0]
            c = Constants.GRID_MAJOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            Line(points=[sx, cy, ex, cy])
            y += self._pixels_per_cm
            c = Constants.GRID_MINOR_COLOR
            Color(c.r, c.g, c.b, c.a)
            for i in range(0, line_count_y):
                y_int = int(round(y))
                Line(points=[sx, cy + y_int, ex, cy + y_int])
                Line(points=[sx, cy - y_int, ex, cy - y_int])
                y += self._pixels_per_cm


class OffScreenImage(Image):

    def __init__(self, client, shader, **kwargs):
        super(OffScreenImage, self).__init__(**kwargs)

        self._client = client
        self._fbo = Fbo(use_parent_projection=False, mipmap=True)
        if shader is not None:
            self._fbo.shader.fs = shader

    def paint(self, size):
        if size is not None:
            self.size = size

        self._fbo.size = self.size
        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            if self._client is not None:
                self._client.paint(self._fbo, self.size)
        self._fbo.draw()
        self.texture = self._fbo.texture


class OffScreenScatter(Scatter):

    def __init__(self, client, size, shader=None, **kwargs):

        self.size_hint = (None, None)
        self.do_rotation = False
        self.do_scale = False
        self.do_translation_x = False
        self.do_translation_y = False

        super(OffScreenScatter, self).__init__(**kwargs)

        self.size = size
        self._width_org = self.size[0]
        self._height_org = self.size[1]

        self._scale = 1.0
        self._angle = 0.0

        self._client = client

        self._fbo = Fbo(size=self.size, use_parent_projection=False, mipmap=True)
        if shader is not None:
            self._fbo.shader.fs = shader

        self._image = Image(size=size, texture=self._fbo.texture)
        self.add_widget(self._image)

        self.paint()

    def set_scale(self, scale):
        self._scale = scale / 100.0

    def paint(self):
        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            if self._client is not None:
                self._client.paint(self._fbo)
        self._fbo.draw()
        self._image.texture = self._fbo.texture

    def center(self, available_size, angle=None):
        if angle is not None:
            self._angle = angle
        cx = available_size[0] / 2.0
        cy = available_size[1] / 2.0
        ax = (self.size[0] / 2.0)
        ay = (self.size[1] / 2.0)
        self.transform = Matrix().identity()
        mat = Matrix().translate(cx-ax, cy-ay, 0.0)
        self.apply_transform(mat)
        mat = Matrix().rotate(math.radians(self._angle), 0.0, 0.0, 1.0)
        self.apply_transform(mat, post_multiply=True, anchor=(ax, ay))
        mat = Matrix().scale(self._scale, self._scale, 1.0)
        self.apply_transform(mat, post_multiply=True, anchor=(ax, ay))


class PcbBoard(OffScreenScatter):

    def __init__(self, client, size, shader, **kwargs):
        super(PcbBoard, self).__init__(client, size, shader, **kwargs)

        self._active = False

    def add_to(self, root):
        if not self._active:
            root.add_widget(self)
            self._active = True

    def remove_from(self, root):
        if self._active:
            root.remove_widget(self)
            self._active = False


class PcbPanel(OffScreenScatter):

    def __init__(self, client, size, shader, **kwargs):
        super(PcbPanel, self).__init__(client, size, shader, **kwargs)

        self._active = False
        self._size_mm = (0, 0)
        self._size_pixels = (0, 0)
        self._layouts_x = []
        self._layouts_y = []
        self._columns = 0
        self._rows = 0

    def add_to(self, root):
        if not self._active:
            root.add_widget(self)
            self._active = True

    def remove_from(self, root):
        if self._active:
            root.remove_widget(self)
            self._active = False

    def panelize(self, columns, rows):
        self._columns = columns
        self._rows = rows

        self._layouts_x.clear()
        self._layouts_y.clear()

        width = self._client.size_mm[0]
        self._layouts_x.append(width)
        for c in range(0, columns-1):
            self._layouts_x.append(Constants.PCB_PANEL_GAP_MM)
            self._layouts_x.append(width)

        height = self._client.size_mm[1]
        self._layouts_y.append(Constants.PCB_PANEL_BOTTOM_RAIL_MM)
        self._layouts_y.append(Constants.PCB_PANEL_GAP_MM)
        for r in range(0, rows):
            self._layouts_y.append(height)
            self._layouts_y.append(Constants.PCB_PANEL_GAP_MM)
        self._layouts_y.append(Constants.PCB_PANEL_BOTTOM_RAIL_MM)

        width = 0
        for x in self._layouts_x:
            width += x

        height = 0
        for y in self._layouts_y:
            height += y

        self._size_mm = (width, height)
        self._size_pixels = (int(math.ceil(width*self._client.pixels_per_cm/10.0)),
                             int(math.ceil(height*self._client.pixels_per_cm/10.0)))
        self.size = self._size_pixels
        self._fbo.size = self.size
        self._image.size = self.size
        self._image.texture_size = self.size
        self.paint2()

    # TODO: if we try to overide the paint() method here,
    #  then we can't access self._rows, why is that?!
    #  AttributeError: 'PcbPanel' object has no attribute '_rows'
    def paint2(self):
        width = self.size[0]
        height = self.size[1]
        height_bottom = Constants.PCB_PANEL_BOTTOM_RAIL_MM * self._client.pixels_per_cm/10.0
        height_top = Constants.PCB_PANEL_TOP_RAIL_MM * self._client.pixels_per_cm/10.0
        gap = Constants.PCB_PANEL_GAP_MM * self._client.pixels_per_cm/10.0
        with self._fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            if self._client is not None:
                c = Constants.PCB_MASK_COLOR
                Color(c.r, c.g, c.b, c.a)
                Rectangle(pos=(0, 0), size=(width, height_bottom))
                Rectangle(pos=(0, height-height_top), size=(width, height_top))
                y = height_bottom + gap
                for r in range(0, self._rows):
                    x = 0.0
                    for c in range(0, self._columns):
                        PushMatrix()
                        Translate(x, y, 0)
                        self._client.paint(self._fbo)
                        PopMatrix()
                        x += self._client.size_pixels[0]
                        x += gap
                    y += self._client.size_pixels[1]
                    y += gap
        self._fbo.draw()
        self._image.texture = self._fbo.texture

    def center(self, available_size, angle=None):
        if angle is not None:
            if self._angle != angle:
                self._angle = angle
                self.panelize(self._columns, self._rows)
        cx = available_size[0] / 2.0
        cy = available_size[1] / 2.0
        ax = (self.size[0] / 2.0)
        ay = (self.size[1] / 2.0)
        self.transform = Matrix().identity()
        mat = Matrix().translate(cx-ax, cy-ay, 0.0)
        self.apply_transform(mat)
        mat = Matrix().scale(self._scale, self._scale, 1.0)
        self.apply_transform(mat, post_multiply=True, anchor=(ax, ay))

    @property
    def size_pixels(self):
        return self._size_pixels

    @property
    def size_mm(self):
        return self._size_mm


class Pcb:
    _colors = [
        Constants.PCB_MASK_COLOR,
        Constants.PCB_OUTLINE_COLOR,
        Constants.PCB_TOP_PASTE_COLOR,
        Constants.PCB_TOP_SILK_COLOR,
        Constants.PCB_TOP_MASK_COLOR,
        Constants.PCB_TOP_TRACES_COLOR,
        Constants.PCB_BOTTOM_TRACES_COLOR,
        Constants.PCB_BOTTOM_MASK_COLOR,
        Constants.PCB_BOTTOM_SILK_COLOR,
        Constants.PCB_PASTE_COLOR,
        Constants.PCB_DRILL_NPH_COLOR,
        Constants.PCB_DRILL_COLOR,
    ]

    _layers_always = [0, 1]
    _layers_top = [2, 3, 4, 5]
    _layers_bottom = [6, 7, 8, 9]

    def __init__(self, path, **kwargs):

        self._images = []

        self._images.append(Image(source=join(path, '0_outline_mask.png')))
        self._images.append(Image(source=join(path, '1_outline.png')))

        self._images.append(Image(source=join(path, '2_toppaste.png')))
        self._images.append(Image(source=join(path, '3_topsilk.png')))
        self._images.append(Image(source=join(path, '4_topmask.png')))
        self._images.append(Image(source=join(path, '5_top.png')))

        self._images.append(Image(source=join(path, '6_bottom.png')))
        self._images.append(Image(source=join(path, '7_bottommask.png')))
        self._images.append(Image(source=join(path, '8_bottomsilk.png')))
        self._images.append(Image(source=join(path, '9_bottompaste.png')))

        self._images.append(Image(source=join(path, '10_drill.png')))
        self._images.append(Image(source=join(path, '11_drill.png')))

        self._layers = [0, 1, 3, 4, 5, 10, 11]

        self._name = path.split(os.path.sep)[-1]
        self._size_mm = (58.01868, 95.6146) # TODO: fix hardcoded value (calculate it from outline path)
        self._size_pixels = self._images[0].texture_size
        self._size_rounded_mm = (math.ceil(self._size_mm[0]), math.ceil(self._size_mm[1]))

    def paint_layer(self, layer, fbo):
        yes = False
        if layer in self._layers_always:
            yes = True
        elif layer in self._layers:
            yes = True
        if yes:
            with fbo:
                color = self._colors[layer]
                Color(color.r, color.g, color.b, color.a)
                image = self._images[layer]
                Rectangle(texture=image.texture, size=image.texture_size, pos=(0, 0))

    def paint(self, fbo):
        with fbo:
            self.paint_layer(0, fbo)
            self.paint_layer(1, fbo)

            self.paint_layer(5, fbo)
            self.paint_layer(3, fbo)
            self.paint_layer(4, fbo)
            self.paint_layer(2, fbo)

            self.paint_layer(6, fbo)
            self.paint_layer(8, fbo)
            self.paint_layer(7, fbo)
            self.paint_layer(9, fbo)

            self.paint_layer(10, fbo)
            self.paint_layer(11, fbo)

    def set_layer(self, ids, layer, state):
        if state is 'down':
            if layer in self._layers_top:
                ids._bottom1.state = 'normal'
                ids._bottom2.state = 'normal'
                ids._bottom3.state = 'normal'
                ids._bottom4.state = 'normal'
                for bottom in self._layers_bottom:
                    if bottom in self._layers:
                        self._layers.remove(bottom)
            elif layer in self._layers_bottom:
                ids._top1.state = 'normal'
                ids._top2.state = 'normal'
                ids._top3.state = 'normal'
                ids._top4.state = 'normal'
                for top in self._layers_top:
                    if top in self._layers:
                        self._layers.remove(top)
            self._layers.append(layer)
        else:
            if layer in self._layers:
                self._layers.remove(layer)

    @property
    def size_pixels(self):
        return self._size_pixels

    @property
    def size_mm(self):
        return self._size_mm

    @property
    def size_rounded_mm(self):
        return self._size_rounded_mm

    @property
    def pixels_per_cm(self):
        return 10.0 * self.size_pixels[1] / self.size_mm[1]

    @property
    def board_name(self):
        return self._name


class PanelizerScreen(Screen):

    def __init__(self, app, **kwargs):
        super(PanelizerScreen, self).__init__(**kwargs)

        self._app = app

        with self.canvas:
            Color(1.0, 0.0, 0.0, 0.5)
            self.background_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_rect)

    def update_rect(self, *args):
        self.background_rect.size = (self.size[0], self.size[1])
        self._app.resize(self.background_rect.size)
        self._app.calculate_pcb_fit_scale()


class PanelizerApp(App):

    _zoom_values_index = 2
    _zoom_values = [200, 150, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    _zoom_str = '{}%'.format(_zoom_values[_zoom_values_index])
    _zoom_values_properties = ListProperty([])

    def __init__(self, **kwargs):
        super(PanelizerApp, self).__init__(**kwargs)

        self._screen = None
        self._surface = None

        self._grid = None
        self._grid_renderer = GridRenderer()

        self._pcb = None
        self._pcb_board = None
        self._pcb_panel = None

        self._board_scale_fit = 1.0
        self._panel_scale_fit = 1.0
        self._scale = 100.0
        self._angle = 0.0

        self._pixels_per_cm = 1.0
        self._size = (100, 100)

        self._show_panel = False
        self._panels_x = 3
        self._panels_y = 2
        self._panelization_str = '{}x{}'.format(self._panels_x, self._panels_y)

    def build(self):
        self.title = 'hmPanelizer'

        self._zoom_values_index = self._zoom_values.index(self._scale)
        for value in self._zoom_values:
            self._zoom_values_properties.append('{}%'.format(value))

        self._screen = PanelizerScreen(self)
        self._surface = Widget()
        self._screen.add_widget(self._surface, False)
        self.root.ids._screen_manager.switch_to(self._screen)

        self._grid = OffScreenImage(client=self._grid_renderer, shader=None)
        self._surface.add_widget(self._grid)

        self.load_pcb(join(dirname(__file__), 'data', 'example_pcb', 'NEAToBOARD'))

    def load_pcb(self, path):
        self._pcb = Pcb(path)
        self._pixels_per_cm = self._pcb.pixels_per_cm

        self._pcb_board = PcbBoard(client=self._pcb, size=self._pcb.size_pixels, shader=fs_mask)
        self._pcb_board.add_to(self._surface)
        self._pcb_panel = PcbPanel(client=self._pcb, size=self._pcb.size_pixels, shader=fs_mask)
        self._pcb_panel.panelize(self._panels_x, self._panels_y)
        self.update_status()

    def panelize(self):
        self._show_panel = self.root.ids._panelization_button.state == 'down'
        if self._show_panel:
            self._pcb_board.remove_from(self._surface)
            self._pcb_panel.add_to(self._surface)
            self._pcb_panel.panelize(self._panels_x, self._panels_y)
            self.calculate_panel_fit_scale()
            self._pcb_panel.set_scale(self._panel_scale_fit * self._scale)
            self.center()
        else:
            self._pcb_board.add_to(self._surface)
            self._pcb_panel.remove_from(self._surface)
            self.update_scale()
        self.update_status()

    def panelize_column(self, add):
        if add:
            self._panels_x += 1
            if self._panels_x > 99:
                self._panels_x = 99
                beep()
                print('WARNING: clamping self.panels_x: {}'.format(self._panels_x))
        else:
            self._panels_x -= 1
            if self._panels_x < 1:
                self._panels_x = 1
                beep()
        self.root.ids._panelization_button.state = 'down'
        self.panelize()

    def panelize_row(self, add):
        if add:
            self._panels_y += 1
            if self._panels_y > 99:
                self._panels_y = 99
                beep()
                print('WARNING: clamping self.panels_y: {}'.format(self._panels_y))
        else:
            self._panels_y -= 1
            if self._panels_y < 1:
                self._panels_y = 1
                beep()
        self.root.ids._panelization_button.state = 'down'
        self.panelize()

    def calculate_fit_scale(self, size_mm, size_pixels):
        target = Constants.FIT_SCALE * size_mm[0]
        fit_x = target / size_pixels[0]
        target = Constants.FIT_SCALE * size_mm[1]
        fit_y = target / size_pixels[1]
        return min(fit_x, fit_y)

    def calculate_pcb_fit_scale(self):
        if self._board_scale_fit == 1.0:
            self._board_scale_fit = self.calculate_fit_scale(self._size, self._pcb.size_pixels)
            self.update_scale()

    def calculate_panel_fit_scale(self):
        self._panel_scale_fit = self.calculate_fit_scale(self._size, self._pcb_panel.size_pixels)
        self.update_scale()

    def update_scale(self):
        self._scale = self._zoom_values[self._zoom_values_index]

        self._pcb_board.set_scale(self._board_scale_fit * self._scale)
        self._pcb_panel.set_scale(self._panel_scale_fit * self._scale)

        pixels_per_cm_scaled = 0.0
        if self._show_panel:
            pixels_per_cm_scaled = (self._pixels_per_cm * self._panel_scale_fit * self._scale) / 100.0
        else:
            pixels_per_cm_scaled = (self._pixels_per_cm * self._board_scale_fit * self._scale) / 100.0
        self._grid_renderer.set_pixels_per_cm(pixels_per_cm_scaled)

        self.center()

    def update_status(self):
        self._panelization_str = '{}x{}'.format(self._panels_x, self._panels_y)
        self.root.ids._panelization_label.text = self._panelization_str
        status = self.root.ids._status_label
        status.text = ''
        status.text += '  PCB: {},'.format(self._pcb.board_name)
        status.text += '  size: {}mm x {}mm,'.format(round(self._pcb.size_mm[0], 2), round(self._pcb.size_mm[1], 2))
        status.text += '  panel size: {}mm x {}mm,'.format(round(self._pcb_panel.size_mm[0], 2), round(self._pcb_panel.size_mm[1], 2))

    def update_zoom_title(self):
        self._zoom_str = self._zoom_values_properties[self._zoom_values_index]
        self.root.ids._zoom_button.text = self._zoom_str
        self.update_scale()
        self.update_status()

    def select_zoom_index(self, index):
        self._zoom_values_index = index
        self.update_zoom_title()

    def select_zoom(self, in_out):
        if in_out:
            self._zoom_values_index += 1
            if self._zoom_values_index >= len(self._zoom_values):
                self._zoom_values_index = (len(self._zoom_values) - 1)
                beep()
        else:
            self._zoom_values_index -= 1
            if self._zoom_values_index < 0:
                self._zoom_values_index = 0
                beep()
        self.update_zoom_title()

    def layer_toggle(self, layer, state):
        self._pcb.set_layer(self.root.ids, layer, state)
        self._pcb_board.paint()
        self._pcb_panel.paint()
        self.update_status()

    def resize(self, size):
        self._size = size
        self.center()

    def rotate(self, right):
        if right:
            self._angle = self._angle - 90.0
        else:
            self._angle = self._angle + 90.0
        self._angle = (self._angle % 360.0)
        self.center()

    def center(self):
        self._grid.paint(self._size)
        self._pcb_board.center(self._size, self._angle)
        self._pcb_panel.center(self._size, self._angle)
        self.update_status()


if __name__ == '__main__':
    PanelizerApp().run()
