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
import os
import sys
import math
import os
import shutil
import zipfile
from os.path import join

import kivy
from kivy.base import EventLoop
from kivy.uix.image import Image


def unzip_file(dst_folder, src_zip):
    with zipfile.ZipFile(src_zip) as zip_file:
        for member in zip_file.namelist():
            filename = os.path.basename(member)
            # skip directories
            if not filename:
                continue

            # copy file (taken from zipfile's extract)
            source = zip_file.open(member)
            target = open(os.path.join(dst_folder, filename), "wb")
            with source, target:
                shutil.copyfileobj(source, target)


def redraw_window():
    kivy.core.window.Window.canvas.ask_update()
    EventLoop.idle()


def update_progressbar(widget, text=None, value=None):
    if value is not None:
        progressbar = widget.ids._progress_bar
        progressbar.value = min(value, 1.0)
    if text is not None:
        label = widget.ids._progress_bar_label
        label.text = text
    redraw_window()


def beep():
    # print('\a')
    sys.stdout.write("\a")


def is_desktop():
    if sys.platform in ('linux', 'windows', 'macosx'):
        return True
    return False


def load_image(path, name):
    print('load_image')
    print(' path: {}'.format(path))
    print(' name: {}'.format(name))
    full_path = os.path.join(path, name)
    print(' full_path: {}'.format(full_path))
    image = None
    if os.path.isfile(full_path):
        try:
            image = Image(source=full_path)
        except:
            image = None
    return image


def load_file(path, name):
    try:
        with open(join(path, name)) as file:
            text = file.read()
    except FileNotFoundError:
        text = None
    return text


def calculate_fit_scale(scale, size_mm, size_pixels):
    target = scale * size_mm[0]
    fit_x = target / size_pixels[0]
    target = scale * size_mm[1]
    fit_y = target / size_pixels[1]
    return min(fit_x, fit_y)


def round_float(value):
    return int(math.ceil(value))


def str_to_float(value):
    return float(value.replace(',', ''))

