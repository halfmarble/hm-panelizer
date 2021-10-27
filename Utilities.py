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

import sys


def beep():
    #print('\a')
    sys.stdout.write("\a")


def is_desktop():
    if platform in ('linux', 'windows', 'macosx'):
        return True
    return False

def calculate_fit_scale(scale, size_mm, size_pixels):
    target = scale * size_mm[0]
    fit_x = target / size_pixels[0]
    target = scale * size_mm[1]
    fit_y = target / size_pixels[1]
    return min(fit_x, fit_y)
