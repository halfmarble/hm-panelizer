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
from kivy.graphics import ClearColor, PushMatrix, PopMatrix

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

    def size(self):
        return self.images[0].texture_size


class PcbImage(Image):

    def __init__(self, pcb):
        super(PcbImage, self).__init__()

        self.pcb = pcb
        self.size = self.pcb.size()
        self.width_org = self.size[0]
        self.height_org = self.size[1]
        self.fbo = Fbo(size=self.size, use_parent_projection=False, mipmap=True)
        self.fbo.shader.fs = fs_mask
        self.render()
        self.texture = self.fbo.texture
        self.texture_size = self.size

    def resize(self, scale):
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
        self.image.resize(scale)


class PanelizerScreen(Screen):

    def __init__(self, **kwargs):
        super(PanelizerScreen, self).__init__(**kwargs)

        with self.canvas:
            Color(0.95, 0.95, 0.95, 1.0)
            self.background_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_rect)

    def update_rect(self, *args):
        self.background_rect.size = (self.size[0], self.size[1])


class PanelizerApp(App):

    zoom_values_index = 0
    zoom_values = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    zoom_str = '{}%'.format(zoom_values[zoom_values_index])
    zoom_values_properties = ListProperty([])

    def __init__(self, **kwargs):
        super(PanelizerApp, self).__init__(**kwargs)

        self.pcb = None
        self.scatters = []
        self.images = []
        self.scale = 70

    def build(self):
        self.title = 'hmPanelizer'

        self.zoom_values_index = self.zoom_values.index(self.scale)
        for value in self.zoom_values:
            self.zoom_values_properties.append('{}%'.format(value))

        self.screen = PanelizerScreen()
        self.surface = Widget()
        self.screen.add_widget(self.surface, False)
        self.update_zoom_title()
        self.root.ids._screen_manager.switch_to(self.screen)

        self.load_pcb(join(dirname(__file__), 'data'))
        self.add_pcb_image()

    def load_pcb(self, path):
        self.pcb = PCB(path)

    def add_pcb_image(self):
        pcb_image = PcbImage(self.pcb)
        self.images.append(pcb_image)
        scatter = ScalableScatter(size_hint=(None, None), size=pcb_image.size)
        scatter.add_widget(pcb_image)
        self.scatters.append(scatter)
        self.surface.add_widget(scatter)
        scatter.resize(self.scale)

    def update_zoom_title(self):
        self.zoom_str = self.zoom_values_properties[self.zoom_values_index]
        self.root.ids._zoom_button.text = self.zoom_str
        self.scale = self.zoom_values[self.zoom_values_index]
        for scatter in self.scatters:
            scatter.resize(self.scale)

    def select_zoom_index(self, index):
        self.zoom_values_index = index
        self.update_zoom_title()

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

    def layer_toggle(self, layer, state):
        self.pcb.set_layer(self.root.ids, layer, state)
        for image in self.images:
            image.render()


if __name__ == '__main__':
    PanelizerApp().run()
