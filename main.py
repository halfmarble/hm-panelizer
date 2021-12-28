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
import os.path
import tempfile
from os import listdir
from os.path import dirname

from kivy import Config
from kivy.uix.filechooser import FileChooserIconView

Config.set('kivy', 'keyboard_mode', 'system')

Config.set('graphics', 'width', '1550')
Config.set('graphics', 'height', '800')
Config.set('graphics', 'minimum_width', '800')
Config.set('graphics', 'minimum_height', '800')


from kivy.app import App
from kivy.factory import Factory
from kivy.utils import platform
from kivy.uix.widget import Widget
from kivy.properties import ListProperty, ObservableList
from typing import Final
from kivy.clock import Clock
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty

from os.path import sep, expanduser, isdir, dirname

from AppSettings import *
from Utilities import *
from GridRenderer import *
from OffScreenImage import *
from OffScreenScatter import *
from Pcb import *
from PcbBoard import *
from PcbPanel import *
from WorkScreen import *
from UI import *
from PcbFile import *


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    cancel = ObjectProperty(None)


Factory.register('LoadDialog', cls=LoadDialog)


class PanelizerApp(App):
    _zoom_values = [500, 300, 200, 175, 150, 125, 100, 90, 80, 70, 60, 50, 40, 30, 20, 10]
    _zoom_values_index = _zoom_values.index(100)
    _zoom_str = '{}%'.format(_zoom_values[_zoom_values_index])
    _zoom_values_properties = ListProperty([])

    def timer_callback(self, dt):
        self._angle += 5.0
        self.panelize()

    def __init__(self, **kwargs):
        super(PanelizerApp, self).__init__(**kwargs)

        self._tmp_folders_to_delete = []
        self._current_pcb_folder = None

        self._finish_load_selected = None
        self._finish_save_selected = None

        if platform == 'win':
            self._root_path = dirname(expanduser('~'))
        else:
            self._root_path = expanduser('~')
        self._load_file_path = self._root_path
        self._save_folder_path = self._root_path

        self._load_popup = None
        self._save_popup = None
        self._progress = None
        self._error_popup = None
        self._settings_popup = None

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
        self._panels_x = INITIAL_COLUMNS
        self._panels_y = INITIAL_ROWS
        self._panelization_str = '{}x{}'.format(self._panels_x, self._panels_y)

        self._bites_x = AppSettings.bites_count_x
        self._bites_y = AppSettings.bites_count_y

    def build(self):
        self.title = 'hmPanelizer'

        self._zoom_values_index = self._zoom_values.index(self._scale)
        for value in self._zoom_values:
            self._zoom_values_properties.append('{}%'.format(value))

        self._screen = WorkScreen(self)
        self._surface = Widget()
        self._screen.add_widget(self._surface, False)
        self.root.ids._screen_manager.switch_to(self._screen)

        self._progress = Progress(title='Progress processing PCB')
        self._error_popup = Error(title='Error')
        self._settings_popup = Settings(title='Panelizing settings')

        self._grid = OffScreenImage(client=self._grid_renderer, shader=None)
        self._surface.add_widget(self._grid)

        self.load_pcb(join(dirname(__file__), DEMO_PCB_PATH_STR), None)
        Clock.schedule_once(self.load_real_pcb_board, 2.0)

    def load_real_pcb_board(self, time):
        demo_real_pcb = '/Users/gerard/PCBs/neatoboardB'
        if os.path.isdir(demo_real_pcb):
            self._current_pcb_folder = demo_real_pcb
            #self.load(demo_real_pcb, [])

    def load_pcb(self, path, name):
        self.root.ids._panelization_button.state = 'normal'
        self.rotate(True)

        if self._pcb_board is not None:
            self._pcb_board.deactivate()
            self._pcb_board = None
        if self._pcb_panel is not None:
            self._pcb_panel.deactivate()
            self._pcb_panel = None

        self._pcb = Pcb(self.root.ids, path, name)
        if self._pcb.valid:
            self._pixels_per_cm = self._pcb.pixels_per_cm
            self._pcb_board = PcbBoard(root=self._surface, pcb=self._pcb)
            self._pcb_board.activate()
            self._pcb_panel = PcbPanel(parent=self, root=self._surface, pcb=self._pcb)
            self._panels_x = INITIAL_COLUMNS
            self._panels_y = INITIAL_ROWS
            self._pcb_panel.panelize(self._panels_x, self._panels_y, self._angle, self._bites_x, self._bites_y)
        else:
            self._pixels_per_cm = self._pcb.pixels_per_cm
            self._pcb_board = PcbBoard(root=self._surface, pcb=self._pcb)
            self._pcb_board.activate()

        self.update_status()
        self.panelize()
        # Clock.schedule_interval(self.timer_callback, 0.1)

        return self._pcb.invalid_reason

    def panelize(self):
        if self._pcb is not None:
            self._show_panel = self.root.ids._panelization_button.state == 'down'
            if self._show_panel:
                self._pcb_board.deactivate()
                if self._pcb_panel is not None:
                    self._pcb_panel.deactivate()
                self.update_scale()
                self.calculate_pcb_fit_scale()
                if self._pcb_panel is not None:
                    self._pcb_panel.panelize(self._panels_x, self._panels_y, self._angle, self._bites_x, self._bites_y)
                self.center()
                if self._pcb_panel is not None:
                    self._pcb_panel.activate()
            else:
                if self._pcb_panel is not None:
                    self._pcb_panel.deactivate()
                self.update_scale()
                self.center()
                self._pcb_board.activate()
            self.update_status()
            self.calculate_pcb_fit_scale()

    def panelize_column(self, add):
        if self._pcb is not None:
            if add:
                self._panels_x += 1
                if self._panels_x > MAX_COLUMNS:
                    self._panels_x = MAX_COLUMNS
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
        if self._pcb is not None:
            if add:
                self._panels_y += 1
                if self._panels_y > MAX_ROWS:
                    self._panels_y = MAX_ROWS
                    beep()
                    print('WARNING: clamping self.panels_y: {}'.format(self._panels_y))
            else:
                self._panels_y -= 1
                if self._panels_y < 1:
                    self._panels_y = 1
                    beep()
            self.root.ids._panelization_button.state = 'down'
            self.panelize()

    def calculate_pcb_fit_scale(self):
        if self._pcb is not None:
            self._board_scale_fit = calculate_fit_scale(FIT_SCALE, self._size, self._pcb.size_pixels)
            if self._pcb_panel is not None:
                self._panel_scale_fit = calculate_fit_scale(FIT_SCALE, self._size, self._pcb_panel.size_pixels)
            self.update_scale()

    def update_scale(self):
        if self._pcb is not None:
            self._scale = self._zoom_values[self._zoom_values_index]

            if self._pcb_board is not None:
                self._pcb_board.set_scale(self._board_scale_fit * self._scale)
            if self._pcb_panel is not None:
                self._pcb_panel.set_scale(self._panel_scale_fit * self._scale)

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
        units = ''
        if self._pcb.valid:
            units = 'mm'
        if self._pcb is not None:
            #self.root.ids._save_button.disabled = False
            status.text += '  PCB: {},'.format(self._pcb.board_name)
            if self._angle == 0.0:
                status.text += '  size: {}{} x {}{},'.format(round(self._pcb.size_mm[0], 2), units,
                                                             round(self._pcb.size_mm[1], 2), units)
            else:
                status.text += '  size: {}{} x {}{},'.format(round(self._pcb.size_mm[1], 2), units,
                                                             round(self._pcb.size_mm[0], 2), units)
            status.text += '  {}valid pcb, '.format('in' if not self._pcb.valid else '')
            if self._pcb_panel is not None:
                # self.root.ids._save_button.disabled = True
                status.text += '  panel pcb count: {},'.format(self._panels_x * self._panels_y)
                status.text += '  panel size: {}{} x {}{},'.format(round(self._pcb_panel.size_mm[0], 2), units,
                                                                   round(self._pcb_panel.size_mm[1], 2), units)
                status.text += '  {}valid layout.'.format('in' if not self._pcb_panel.valid_layout else '')
            else:
                status.text += '  invalid layout.'
        else:
            status.text = '  Invalid PCB.'

    def update_zoom_title(self):
        if self._pcb is not None:
            self._zoom_str = self._zoom_values_properties[self._zoom_values_index]
            self.root.ids._zoom_button.text = self._zoom_str
            self.update_scale()
            self.update_status()

    def select_zoom_index(self, index):
        if self._pcb is not None:
            self._zoom_values_index = index
            self.update_zoom_title()

    def select_zoom(self, in_out):
        if self._pcb is not None:
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
        if self._pcb is not None:
            self._pcb.set_layer(self.root.ids, layer, state)
            if self._pcb_board is not None:
                self._pcb_board.paint()
            if self._pcb_panel is not None:
                self._pcb_panel.paint()
            self.update_status()
            # self.panelize()

    def resize(self, size):
        if self._pcb is not None:
            self._size = size
            self.calculate_pcb_fit_scale()

    def rotate(self, vertical):
        if self._pcb is not None:
            if vertical:
                self._angle = 0.0
                self.root.ids._vertical_button.state = 'down'
                self.root.ids._horizontal_button.state = 'normal'
            else:
                self._angle = 90.0
                self.root.ids._vertical_button.state = 'normal'
                self.root.ids._horizontal_button.state = 'down'
            self.panelize()

    def center(self):
        self._grid.paint(self._size)
        if self._pcb is not None:
            if self._pcb_board is not None:
                self._pcb_board.center(self._size, self._angle)
            if self._pcb_panel is not None:
                self._pcb_panel.center(self._size, self._angle)
            self.update_status()

    def dismiss_load_popup(self):
        if self._load_popup is not None:
            self._load_popup.dismiss()

    def load_finish(self, time):
        path = self._finish_load_selected

        temp_zip_dir = None
        filename_only = os.path.basename(os.path.splitext(path)[0])
        filename_ext = os.path.splitext(path)[1].lower()
        if filename_ext == '.zip':
            temp_zip_dir = tempfile.TemporaryDirectory().name
            #print('creating temporary zip directory', temp_zip_dir)
            try:
                os.mkdir(temp_zip_dir)
            except FileExistsError:
                pass
            unzip_file(temp_zip_dir, path)
            path = temp_zip_dir
        else:
            if not os.path.isdir(path):
                path = self._load_file_path

        if os.path.isdir(path):
            temp_dir = tempfile.TemporaryDirectory().name
            #print('creating temporary directory', temp_dir)
            try:
                os.mkdir(temp_dir)
            except FileExistsError:
                pass
            self._current_pcb_folder = path
            generate_pcb_data_layers(path, '.', temp_dir, 1024, self._progress, filename_only)
            error_msg = self.load_pcb(temp_dir, filename_only)
            #print('marking temporary directory for deletion {}', temp_dir)
            self._tmp_folders_to_delete.append(temp_dir)

        if temp_zip_dir is not None:
            #print('marking temporary zip directory for deletion {}', temp_zip_dir)
            self._tmp_folders_to_delete.append(temp_zip_dir)

        self._progress.dismiss()

        if error_msg is not None:
            self.error_open(error_msg)

    def load(self, path, selection):
        # print('load')
        # print(' path {}'.format(path))
        # print(' selection {}'.format(selection))
        # print(' self._root_path {}'.format(self._root_path))

        if self._root_path in path:
            self._load_file_path = path
            self._finish_load_selected = path
            if len(selection) > 0:
                self._load_file_path = os.path.dirname(os.path.abspath(selection[0]))
        self._finish_load_selected = self._load_file_path

        if len(selection) > 0:
            if self._root_path in selection[0]:
                self._finish_load_selected = os.path.abspath(selection[0])
        if os.path.isfile(self._finish_load_selected):
            selection_ext = os.path.splitext(self._finish_load_selected)[1].lower()
            if selection_ext != '.zip':
                self._finish_load_selected = os.path.dirname(self._finish_load_selected)

        self.dismiss_load_popup()
        Clock.schedule_once(self.load_finish, 1.0)

        self._progress.open()
        update_progressbar(self._progress, 'Loading PCB ...', 0.0)

    def load_pcb_from_disk(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_load_popup)
        file_chooser = content.ids._load_file_chooser
        file_chooser.rootpath = self._root_path
        file_chooser.path = self._load_file_path
        file_chooser.dirselect = True

        self._load_popup = Popup(title="Select folder with PCB gerber files or .zip archive file to load",
                                 content=content, size_hint=(0.9, 0.9))
        self._load_popup.open()

    def save_finish(self, time):
        path = self._finish_save_selected
        print('save_finish')
        print(' path {}'.format(path))

        Clock.schedule_once(self._progress.dismiss, 5)
        #self._progress.dismiss()

    def dismiss_save_popup(self):
        self._save_popup.dismiss()

    def save(self, path, selection, foldername):
        # print('save')
        # print(' path {}'.format(path))
        # print(' selection {}'.format(selection))
        # print(' foldername {}'.format(foldername))
        # print(' self._root_path {}'.format(self._root_path))

        if len(selection) > 0:
            if self._root_path in selection[0]:
                self._save_folder_path = selection[0]
                if not os.path.isdir(self._save_folder_path) and os.path.isfile(self._save_folder_path):
                    self._save_folder_path = os.path.dirname(selection[0])
        if foldername is not None and len(foldername) > 0:
            self._finish_save_selected = os.path.join(self._save_folder_path, foldername)
        else:
            self._finish_save_selected = os.path.join(self._save_folder_path, self._pcb.board_name+"_panelized")

        self.dismiss_save_popup()

        if os.path.isdir(self._finish_save_selected):
            string = truncate_str_middle(self._finish_save_selected, 60)
            self.error_open("Folder {} already exists!".format(string))
        else:
            Clock.schedule_once(self.save_finish, 1.0)
            self._progress.open()
            update_progressbar(self._progress, 'Saving PCB ...', 0.0)

    def save_pcb_to_disk(self):
        if self._current_pcb_folder is None:
            self.error_open("Can not save demo PCB board (no src gerber files available)")
            return

        if self._pcb_panel is not None:
            if self._pcb_panel.valid_layout:
                content = SaveDialog(save=self.save, cancel=self.dismiss_save_popup)
                file_chooser = content.ids._save_file_chooser
                file_chooser.rootpath = self._root_path
                file_chooser.path = self._save_folder_path
                file_chooser.dirselect = True
                content.ids._save_file_name.text = self._pcb.board_name+'_panelized'

                self._save_popup = Popup(title="Select folder where to save the PCB panel",
                                         content=content, size_hint=(0.9, 0.9))
                self._save_popup.open()
            else:
                self.error_open("Invalid PCB panel layout")
        else:
            self.error_open("Invalid PCB board")

    def error_open(self, text):
        label = self._error_popup.ids._error_label
        label.text = text
        self._error_popup.open()

    def error_close(self):
        self._error_popup.dismiss()

    def settings_open(self):
        self._settings_popup.open()

    def settings_close(self):
        self._settings_popup.dismiss()

    def settings_bites(self):
        print('settings_bites')

    def cleanup(self):
        if ALLOW_DIR_DELETIONS and len(self._tmp_folders_to_delete) > 0:
            for folder in self._tmp_folders_to_delete:
                rmrf(folder)


if __name__ == '__main__':
    app = PanelizerApp()
    app.run()
    app.cleanup()

