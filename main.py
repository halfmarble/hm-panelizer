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
Config.set('graphics', 'width', '1200')
Config.set('graphics', 'height', '900')
Config.set('graphics', 'minimum_width', '1024')
Config.set('graphics', 'minimum_height', '800')

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


class PCB:
    colors = [
        Color(0.15, 0.35, 0.15, 1.00),  # 0 pcb mask
        Color(0.00, 0.00, 0.00, 1.00),  # 1 pcb outline
        Color(0.55, 0.55, 0.55, 1.00),  # 2 top paste
        Color(0.95, 0.95, 0.95, 1.00),  # 3 top silk
        Color(0.75, 0.65, 0.00, 1.00),  # 4 top mask
        Color(0.00, 0.50, 0.00, 0.50),  # 5 top traces
        Color(0.00, 0.50, 0.00, 0.50),  # 6 bottom traces
        Color(0.75, 0.65, 0.00, 1.00),  # 7 bottom mask
        Color(0.95, 0.95, 0.95, 1.00),  # 8 bottom silk
        Color(0.55, 0.55, 0.55, 1.00),  # 9 bottom paste
        Color(0.10, 0.10, 0.10, 0.80),  # 10 drill 1
        Color(0.10, 0.10, 0.10, 0.90),  # 11 drill 2
    ]

    layers_always = [0, 1]
    layers_top = [2, 3, 4, 5]
    layers_bottom = [6, 7, 8, 9]

    def __init__(self, path):

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
    def size(self):
        return self.board_size_pixels

    @property
    def board_size_pixels(self):
        return self.images[0].texture_size

    @property
    def board_size_mm(self):
        return self.board_size_metric

    @property
    def board_size(self):
        return self.board_size_rounded


class PcbImage(Image):

    def __init__(self, pcb):
        super(PcbImage, self).__init__()

        self.pcb = pcb
        self.size = self.pcb.size
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
            self.pcb.render(self.fbo)
        self.fbo.draw()


class ScalableScatter(Scatter):

    def __init__(self, **kwargs):
        super(ScalableScatter, self).__init__(**kwargs)
        self.width_org = self.size[0]
        self.height_org = self.size[1]
        self.image = None

    def add_widget(self, *args, **kwargs):
        self.image = args[0]
        self.width_org = self.image.size[0]
        self.height_org = self.image.size[1]
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


class PanelizerApp(App):

    zoom_values_index = 0
    zoom_values = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    zoom_str = '{}%'.format(zoom_values[zoom_values_index])
    zoom_values_properties = ListProperty([])

    panelization_values_index = 0
    panelization_values = ['1x1', '2x2', '3x3', '4x4', '5x5', '10x10', '20x20']
    panelization_str = '{}'.format(panelization_values[panelization_values_index])
    panelization_values_properties = ListProperty([])

    def __init__(self, **kwargs):
        super(PanelizerApp, self).__init__(**kwargs)

        self.pcb = None
        self.pcb_image = None
        self.pcb_scatter = None
        self.background_fbo = None
        self.background_image = None
        self.screen = None
        self.surface = None
        self.scatters = []
        self.images = []
        self.scale = 70.0
        self.angle = 0.0
        self.pixels_per_cm = 10.0
        self.pixels_per_cm_scaled = 10.0
        self.size = (0, 0)

    def build(self):
        self.title = 'hmPanelizer'

        self.zoom_values_index = self.zoom_values.index(self.scale)
        for value in self.zoom_values:
            self.zoom_values_properties.append('{}%'.format(value))

        self.panelization_values_index = self.panelization_values.index('1x1')
        for value in self.panelization_values:
            self.panelization_values_properties.append('{}'.format(value))

        self.screen = PanelizerScreen(self)
        self.surface = Widget()
        self.screen.add_widget(self.surface, False)
        self.update_zoom_title()
        self.root.ids._screen_manager.switch_to(self.screen)

        self.background_fbo = Fbo(size=self.screen.size, use_parent_projection=False, mipmap=True)
        self.background_image = Image(texture=self.background_fbo.texture, texture_size=self.screen.size, pos=(0, 0))
        self.surface.add_widget(self.background_image)

        self.load_pcb(join(dirname(__file__), 'data', 'example_pcb', 'NEAToBoard'))

    def load_pcb(self, path):
        self.pcb = PCB(path)
        self.add_pcb_image()

    def add_pcb_image(self, draggabex=False, draggabey=False):
        self.pcb_image = PcbImage(self.pcb)
        #self.images.append(self.pcb_image)
        self.pcb_scatter = ScalableScatter(size_hint=(None, None), size=self.pcb_image.size,
                                           do_rotation=False, do_scale=False, do_translation_x=draggabex, do_translation_y=draggabey)
        #self.pcb_scatter.rotation = 90.0
        self.pcb_scatter.add_widget(self.pcb_image)
        #self.scatters.append(self.pcb_scatter)
        self.surface.add_widget(self.pcb_scatter)
        self.pcb_scatter.resize(self.scale)
        self.update_zoom_title()

    def panelize(self):
        if self.root.ids._panelization_button.state == 'down':
            print('TODO: panelize')

    def update_status(self):
        status = self.root.ids._status_label
        if self.pcb is not None:
            status.text = ''
            status.text += '  PCB: {},'.format(self.pcb.board_name)
            status.text += '  size: {}mm x {}mm,'.format(round(self.pcb.board_size_mm[0], 2), round(self.pcb.board_size_mm[1], 2))
        else:
            status.text = 'PCB board not loaded'

    def select_panelization_index(self, index):
        self.root.ids._panelization_button.state = 'down'
        self.panelize()

    def update_zoom_title(self):
        self.zoom_str = self.zoom_values_properties[self.zoom_values_index]
        self.root.ids._zoom_button.text = self.zoom_str
        self.scale = self.zoom_values[self.zoom_values_index]
        if self.pcb_scatter is not None:
            self.pcb_scatter.resize(self.scale)
        if self.pcb_image is not None:
            self.pcb_image.resize(self.scale)
        for scatter in self.scatters:
            scatter.resize(self.scale)
        for image in self.images:
            image.resize(self.scale)
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
        self.pcb.set_layer(self.root.ids, layer, state)
        if self.pcb_image is not None:
            self.pcb_image.render()
        for image in self.images:
            image.render()
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

    def center(self):
        if self.pcb_image is None:
            return
        if self.size[0] > self.size[1]:
            self.pixels_per_cm = 10.0 * self.pcb.board_size_pixels[0] / self.pcb.board_size_mm[0]
        else:
            self.pixels_per_cm = 10.0 * self.pcb.board_size_pixels[1] / self.pcb.board_size_mm[1]
        self.pixels_per_cm_scaled = (self.pixels_per_cm * self.scale) / 100.0

        cx = self.size[0] / 2.0
        cy = self.size[1] / 2.0
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

        anchor_x = (self.pcb_image.size[0]/2.0)
        anchor_y = (self.pcb_image.size[1]/2.0)
        self.pcb_scatter.transform = Matrix().identity()
        mat = Matrix().translate(cx-anchor_x, cy-anchor_y, 0.0)
        self.pcb_scatter.apply_transform(mat)
        mat = Matrix().rotate(math.radians(self.angle), 0.0, 0.0, 1.0)
        self.pcb_scatter.apply_transform(mat, post_multiply=True, anchor=(anchor_x, anchor_y))

        self.update_status()


if __name__ == '__main__':
    PanelizerApp().run()
