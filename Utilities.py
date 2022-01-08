# Copyright 2021,2022 HalfMarble LLC

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
from typing import Final

import kivy
from kivy.base import EventLoop
from kivy.graphics import Fbo, ClearColor, ClearBuffers, Color, Rectangle
from kivy.uix.image import Image

from math import floor, ceil


def round_down(n, d=2):
    d = int('1' + ('0' * d))
    return floor(n * d) / d


def round_up(n, d=2):
    d = int('1' + ('0' * d))
    return ceil(n * d) / d


def clamp(left, value, right):
    return max(left, min(value, right))


def insert_str(string, str_to_insert, index):
    return string[:index] + str_to_insert + string[index:]


def truncate_str_middle(s, n):
    if len(s) <= n:
        # string is already short-enough
        return s
    # half of the size, minus the 3 .'s
    n_2 = int(n / 2 - 3)
    #  whatever is left
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
    if widget is not None:
        if value is not None:
            progressbar = widget.ids._progress_bar
            progressbar.value = min(value, 1.0)
        if text is not None:
            label = widget.ids._progress_bar_label
            label.text = text
        redraw_window()
    else:
        if text is not None:
            print('LOG: {} [{:.2f}%]'.format(text, round_down(value)))


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
            image = Image(size=(2, 2))
    return image


def load_image_masked(path, name, color):
    image = load_image(path, name)
    if image is not None:
        image = colored_mask(image, color)
    return image


def load_file(path, name):
    try:
        with open(join(path, name)) as file:
            text = file.read()
    except FileNotFoundError:
        text = None
    return text


def rmrf(directory):
    if directory is not None:
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


def generate_decfloat3(value):
    return '{:0.3f}'.format(value)


FS_MASK: Final = '''
$HEADER$
void main(void) {
    gl_FragColor = vec4(frag_color.r, frag_color.g, frag_color.b, texture2D(texture0, tex_coord0).a);
}
'''


def colored_mask(mask, color):
    image = None
    if mask is not None:
        image = Image()
        image.size = mask.texture_size
        fbo = Fbo()
        fbo.shader.fs = FS_MASK
        fbo.size = image.size
        with fbo:
            ClearColor(0, 0, 0, 0)
            ClearBuffers()
            Color(color.r, color.g, color.b, color.a)
            Rectangle(texture=mask.texture, size=mask.texture_size, pos=(0, 0))
        fbo.draw()
        image.texture = fbo.texture
    return image


def bounds_to_size(bounds, verbose=False):
    x_bounds = bounds[0]
    y_bounds = bounds[1]
    width = abs(x_bounds[1]-x_bounds[0])
    height = abs(y_bounds[1]-y_bounds[0])

    if verbose:
        print('bounds_to_size:')
        print(' bounds: {}'.format(bounds))
        print(' x_bounds: {}'.format(x_bounds))
        print(' y_bounds: {}'.format(y_bounds))
        print(' width: {}'.format(width))
        print(' height: {}'.format(height))

    return (width, height)


def next_power_of_2(x):
    return 1 if x == 0 else 2**(x - 1).bit_length()


def size_to_resolution(size, pixels_per_unit, pixels_min, pixels_max):
    resolution = pixels_per_unit*int(max(size[0], size[1]))
    resolution = next_power_of_2(resolution)
    resolution = max(resolution, pixels_min)
    resolution = min(resolution, pixels_max)
    return resolution

