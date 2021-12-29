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


def truncate_str_middle(s, n):
    if len(s) <= n:
        # string is already short-enough
        return s
    # half of the size, minus the 3 .'s
    n_2 = int(n / 2 - 3)
    # whatever's left
    n_1 = int(n - n_2 - 3)
    return '{0}...{1}'.format(s[:n_1], s[-n_2:])


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
    full_path = os.path.join(path, name)
    image = None
    if os.path.isfile(full_path):
        try:
            image = Image(source=full_path)
        except:
            image = Image(size=(32,32))
    return image


def load_file(path, name):
    try:
        with open(join(path, name)) as file:
            text = file.read()
    except FileNotFoundError:
        text = None
    return text


def rmrf(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    shutil.rmtree(directory, ignore_errors=True)


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


def generate_float46(value):
    data = ''
    float_full_str = '{:0.6f}'.format(value)
    segments = float_full_str.split('.')
    for s in segments:
        data += '{}'.format(s)
    return data

