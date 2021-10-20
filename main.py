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

import copy
import os
import math

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

from kivy.uix.actionbar import ActionBar
from kivy.uix.actionbar import ActionView
from kivy.uix.actionbar import ActionPrevious
from kivy.uix.actionbar import ActionOverflow
from kivy.uix.actionbar import ActionButton
from kivy.uix.actionbar import ActionSeparator

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput

from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty

from kivy.graphics.stencil_instructions import StencilPush, StencilPop, StencilUse, StencilUnUse
from kivy.graphics import RenderContext, Canvas, Fbo, Scale, Color, Line, Rectangle, BindTexture, ClearBuffers
from kivy.graphics import ClearColor, PushMatrix, PopMatrix, Translate
from kivy.graphics.transformation import Matrix

from random import random as r

import constants


fs_mask = '''
$HEADER$
void main(void) {
    gl_FragColor = frag_color * texture2D(texture0, tex_coord0).a;
}
'''


def is_desktop():
    if platform in ('linux', 'windows', 'macosx'):
        return True
    return False


class LayerButton(ToggleButton):
    pass


class PcbBoard:
    colors = [
        constants.PCB_MASK_COLOR,
        constants.PCB_OUTLINE_COLOR,
        constants.PCB_TOP_PASTE_COLOR,
        constants.PCB_TOP_SILK_COLOR,
        constants.PCB_TOP_MASK_COLOR,
        constants.PCB_TOP_TRACES_COLOR,
        constants.PCB_BOTTOM_TRACES_COLOR,
        constants.PCB_BOTTOM_MASK_COLOR,
        constants.PCB_BOTTOM_SILK_COLOR,
        constants.PCB_PASTE_COLOR,
        constants.PCB_DRILL_NPH_COLOR,
        constants.PCB_DRILL_COLOR,
    ]

    layers_always = [0, 1]
    layers_top = [2, 3, 4, 5]
    layers_bottom = [6, 7, 8, 9]

    def __init__(self, path, **kwargs):

        self.images = []

        self.images.append(Image(source=join(path, '0_outline_mask.png')))
        self.images.append(Image(source=join(path, '1_outline.png')))

        self.images.append(Image(source=join(path, '2_toppaste.png')))
        self.images.append(Image(source=join(path, '3_topsilk.png')))
        self.images.append(Image(source=join(path, '4_topmask.png')))
        self.images.append(Image(source=join(path, '5_top.png')))

        self.images.append(Image(source=join(path, '6_bottom.png')))
        self.images.append(Image(source=join(path, '7_bottommask.png')))
        self.images.append(Image(source=join(path, '8_bottomsilk.png')))
        self.images.append(Image(source=join(path, '9_bottompaste.png')))

        self.images.append(Image(source=join(path, '10_drill.png')))
        self.images.append(Image(source=join(path, '11_drill.png')))

        self.layers = [0, 1, 3, 4, 5, 10, 11]

        self.board_name = path.split(os.path.sep)[-1]
        self.board_size = self.images[0].texture_size
        self.board_size_metric = (58.01868, 95.6146)
        self.board_size_rounded = (math.ceil(self.board_size_metric[0]), math.ceil(self.board_size_metric[1]))

    def render_layer(self, layer, fbo):
        yes = False
        if layer in self.layers_always:
            yes = True
        elif layer in self.layers:
            yes = True
        if yes:
            with fbo:
                color = self.colors[layer]
                Color(color.r, color.g, color.b, color.a)
                image = self.images[layer]
                Rectangle(texture=image.texture, size=image.texture_size, pos=(0, 0))

    def render(self, fbo):

        with fbo:
            self.render_layer(0, fbo)
            self.render_layer(1, fbo)

            self.render_layer(5, fbo)
            self.render_layer(3, fbo)
            self.render_layer(4, fbo)
            self.render_layer(2, fbo)

            self.render_layer(6, fbo)
            self.render_layer(8, fbo)
            self.render_layer(7, fbo)
            self.render_layer(9, fbo)

            self.render_layer(10, fbo)
            self.render_layer(11, fbo)

    def set_layer(self, ids, layer, state):
        if state is 'down':
            if layer in self.layers_top:
                ids._bottom1.state = 'normal'
                ids._bottom2.state = 'normal'
                ids._bottom3.state = 'normal'
                ids._bottom4.state = 'normal'
                for bottom in self.layers_bottom:
                    if bottom in self.layers:
                        self.layers.remove(bottom)
            elif layer in self.layers_bottom:
                ids._top1.state = 'normal'
                ids._top2.state = 'normal'
                ids._top3.state = 'normal'
                ids._top4.state = 'normal'
                for top in self.layers_top:
                    if top in self.layers:
                        self.layers.remove(top)
            self.layers.append(layer)
        else:
            if layer in self.layers:
                self.layers.remove(layer)

    @property
    def board_size_pixels(self):
        return self.board_size

    @property
    def board_size_mm(self):
        return self.board_size_metric

    @property
    def board_size_rounded_mm(self):
        return self.board_size_rounded


class PcbPanel:

    def __init__(self, pcb_board, panels_x, panels_y, **kwargs):
        self.pcb = pcb_board
        self.panels_x = panels_x
        self.panels_y = panels_y

        width = (self.pcb.board_size_mm[0] * self.panels_x) + (constants.PCB_PANEL_GAP_MM * (self.panels_x - 1))
        height = (self.pcb.board_size_mm[1] * self.panels_y) + (constants.PCB_PANEL_GAP_MM * (self.panels_y - 1))
        height += constants.PCB_PANEL_TOP_RAIL_MM + constants.PCB_PANEL_GAP_MM
        height += constants.PCB_PANEL_GAP_MM + constants.PCB_PANEL_BOTTOM_RAIL_MM
        self.board_size_metric = (width, height)

    @property
    def panel_size_mm(self):
        return self.board_size_metric


class PcbImage(Image):

    def __init__(self, pcb_board, **kwargs):
        super(PcbImage, self).__init__()

        self.pcb_board = pcb_board
        self.size = self.pcb_board.board_size_pixels
        self.width_org = self.size[0]
        self.height_org = self.size[1]
        self.fbo = Fbo(size=self.size, use_parent_projection=False, mipmap=True)
        self.fbo.shader.fs = fs_mask
        self.render()
        self.texture = self.fbo.texture
        self.texture_size = self.size

    def resize(self, scale):
        scale = scale/100.0
        self.size = (scale*self.width_org, scale*self.height_org)

    def render(self):
        with self.fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            self.pcb_board.render(self.fbo)
        self.fbo.draw()


class ScalableScatter(Scatter):

    def __init__(self, **kwargs):
        super(ScalableScatter, self).__init__(**kwargs)
        self.width_org = self.size[0]
        self.height_org = self.size[1]

    def add_widget(self, *args, **kwargs):
        image = args[0]
        self.width_org = image.size[0]
        self.height_org = image.size[1]
        return super(ScalableScatter, self).add_widget(*args, **kwargs)

    def resize(self, scale):
        scale = scale/100.0
        self.size = (scale*self.width_org, scale*self.height_org)


class PanelizerScreen(Screen):

    def __init__(self, app, **kwargs):
        super(PanelizerScreen, self).__init__(**kwargs)

        self.app = app

        with self.canvas:
            Color(0.95, 0.95, 0.95, 1.0)
            self.background_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_rect)

    def update_rect(self, *args):
        self.background_rect.size = (self.size[0], self.size[1])
        self.app.resize(self.background_rect.size)
        self.app.calculate_fit_scale()


class PanelizerApp(App):

    zoom_values_index = 0
    zoom_values = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    zoom_str = '{}%'.format(zoom_values[zoom_values_index])
    zoom_values_properties = ListProperty([])

    def __init__(self, **kwargs):
        super(PanelizerApp, self).__init__(**kwargs)

        self.screen = None
        self.surface = None

        self.pcb_board = None
        self.pcb_board_image = None
        self.pcb_board_scatter = None

        self.pcb_panel = None
        self.pb_panel_image = None
        self.pcb_panel_scatter = None

        self.background_fbo = None
        self.background_image = None

        self.fit_scale = 100.0
        self.scale = 100.0
        self.angle = 0.0

        self.pixels_per_cm = 10.0
        self.pixels_per_cm_scaled = 10.0
        self.size = (100, 100)

        self.panels_x = 1
        self.panels_y = 1
        self.panelization_str = '{}x{}'.format(self.panels_x, self.panels_y)

    def build(self):
        self.title = 'hmPanelizer'

        self.zoom_values_index = self.zoom_values.index(self.scale)
        for value in self.zoom_values:
            self.zoom_values_properties.append('{}%'.format(value))

        self.screen = PanelizerScreen(self)
        self.surface = Widget()
        self.screen.add_widget(self.surface, False)
        self.update_zoom_title()
        self.root.ids._screen_manager.switch_to(self.screen)

        self.background_fbo = Fbo(size=self.screen.size, use_parent_projection=False, mipmap=True)
        self.background_image = Image(texture=self.background_fbo.texture, texture_size=self.screen.size, pos=(0, 0))
        self.surface.add_widget(self.background_image)

        self.load_pcb(join(dirname(__file__), 'data', 'example_pcb', 'NEAToBOARD'))

    def load_pcb(self, path):
        self.pcb_board = PcbBoard(path)
        self.pcb_board_image = PcbImage(self.pcb_board)
        self.pcb_board_scatter = ScalableScatter(size_hint=(None, None), size=self.pcb_board_image.size,
                                                 do_rotation=False, do_scale=False,
                                                 do_translation_x=False, do_translation_y=False)
        self.pcb_board_scatter.add_widget(self.pcb_board_image)
        self.surface.add_widget(self.pcb_board_scatter)

        self.pixels_per_cm = 10.0 * self.pcb_board.board_size_pixels[1] / self.pcb_board.board_size_mm[1]
        self.update_zoom_title()
        self.update_scale()

    def panelize(self):
        if self.root.ids._panelization_button.state == 'down':
            self.pcb_panel = PcbPanel(self.pcb_board, self.panels_x, self.panels_y)
        self.panelization_str = '{}x{}'.format(self.panels_x, self.panels_y)
        self.root.ids._panelization_label.text = self.panelization_str
        self.update_status()

    def panelize_column(self, add):
        if add:
            self.panels_x += 1
            if self.panels_x > 99:
                self.panels_x = 99
                print('WARNING: clamping self.panels_x: {}'.format(self.panels_x))
        else:
            self.panels_x -= 1
            if self.panels_x < 1:
                self.panels_x = 1
        self.root.ids._panelization_button.state = 'down'
        self.panelize()

    def panelize_row(self, add):
        if add:
            self.panels_y += 1
            if self.panels_y > 99:
                self.panels_y = 99
                print('WARNING: clamping self.panels_y: {}'.format(self.panels_y))
        else:
            self.panels_y -= 1
            if self.panels_y < 1:
                self.panels_y = 1
        self.root.ids._panelization_button.state = 'down'
        self.panelize()

    def calculate_fit_scale(self):
        if self.fit_scale == 100.0:
            target = constants.FIT_SCALE * self.size[1]
            self.fit_scale = target / self.pcb_board.board_size_pixels[1]
            if self.fit_scale > 1.0:
                # TODO: why is zoom > 1 not working?
                self.fit_scale = 1.0
            self.update_scale()

    def update_scale(self):
        self.scale = self.zoom_values[self.zoom_values_index]
        self.pixels_per_cm_scaled = (self.pixels_per_cm * self.fit_scale * self.scale) / 100.0
        if self.pcb_board_scatter is not None:
            self.pcb_board_scatter.resize(self.fit_scale * self.scale)
        if self.pcb_board_image is not None:
            self.pcb_board_image.resize(self.fit_scale * self.scale)
            self.center()

    def update_status(self):
        status = self.root.ids._status_label
        if self.pcb_board is not None:
            status.text = ''
            status.text += '  PCB: {},'.format(self.pcb_board.board_name)
            status.text += '  size: {}mm x {}mm,'.format(round(self.pcb_board.board_size_mm[0], 2), round(self.pcb_board.board_size_mm[1], 2))
            status.text += '  panel size: {}mm x {}mm,'.format(round(0.0, 2), round(0.0, 2))
        else:
            status.text = 'PCB board not loaded'

    def update_zoom_title(self):
        self.zoom_str = self.zoom_values_properties[self.zoom_values_index]
        self.root.ids._zoom_button.text = self.zoom_str
        self.update_scale()
        self.update_status()

    def select_zoom_index(self, index):
        self.zoom_values_index = index
        self.update_zoom_title()
        self.center()

    def select_zoom(self, in_out):
        if in_out:
            self.zoom_values_index += 1
            if self.zoom_values_index >= len(self.zoom_values):
                self.zoom_values_index = (len(self.zoom_values) - 1)
        else:
            self.zoom_values_index -= 1
            if self.zoom_values_index < 0:
                self.zoom_values_index = 0
        self.update_zoom_title()
        self.center()

    def layer_toggle(self, layer, state):
        self.pcb_board.set_layer(self.root.ids, layer, state)
        if self.pcb_board_image is not None:
            self.pcb_board_image.render()
        self.update_status()

    def resize(self, size):
        self.size = size
        self.center()

    def rotate(self, right):
        if right:
            self.angle = self.angle - 90.0
        else:
            self.angle = self.angle + 90.0
        self.angle = (self.angle % 360.0)
        self.center()

    def render_background(self, cx, cy):
        line_count_x = int(((math.floor(self.size[0] / self.pixels_per_cm_scaled)) / 2.0) + 1.0)
        line_count_y = int(((math.floor(self.size[1] / self.pixels_per_cm_scaled)) / 2.0) + 1.0)
        self.background_fbo.size = self.size
        with self.background_fbo:
            ClearColor(0.95, 0.95, 0.95, 1.0)
            ClearBuffers()

            x = 0.0
            sy = 0.0
            ey = self.size[1]
            Color(0.50, 0.50, 0.50, 1.0)
            Line(points=[cx, sy, cx, ey])
            x += self.pixels_per_cm_scaled
            Color(0.80, 0.80, 0.80, 1.0)
            for i in range(0, line_count_x):
                x_int = int(round(x))
                Line(points=[cx+x_int, sy, cx+x_int, ey])
                Line(points=[cx-x_int, sy, cx-x_int, ey])
                x += self.pixels_per_cm_scaled

            y = 0.0
            sx = 0.0
            ex = self.size[0]
            Color(0.50, 0.50, 0.50, 1.0)
            Line(points=[sx, cy, ex, cy])
            y += self.pixels_per_cm_scaled
            Color(0.80, 0.80, 0.80, 1.0)
            for i in range(0, line_count_y):
                y_int = int(round(y))
                Line(points=[sx, cy+y_int, ex, cy+y_int])
                Line(points=[sx, cy-y_int, ex, cy-y_int])
                y += self.pixels_per_cm_scaled

        self.background_fbo.draw()
        self.background_image.texture = self.background_fbo.texture
        self.background_image.texture_size = self.size
        self.background_image.size = self.size

    def center(self):
        if self.pcb_board_image is None:
            return

        cx = self.size[0] / 2.0
        cy = self.size[1] / 2.0
        self.render_background(cx, cy)

        anchor_x = (self.pcb_board_image.size[0] / 2.0)
        anchor_y = (self.pcb_board_image.size[1] / 2.0)
        self.pcb_board_scatter.transform = Matrix().identity()
        mat = Matrix().translate(cx-anchor_x, cy-anchor_y, 0.0)
        self.pcb_board_scatter.apply_transform(mat)
        mat = Matrix().rotate(math.radians(self.angle), 0.0, 0.0, 1.0)
        self.pcb_board_scatter.apply_transform(mat, post_multiply=True, anchor=(anchor_x, anchor_y))

        self.update_status()


if __name__ == '__main__':
    PanelizerApp().run()
