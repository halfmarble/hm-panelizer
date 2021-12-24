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

from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup


class LayerButton(ToggleButton):
    pass


class Settings(Popup):
    pass

    # class FloatInput(TextInput):
    #
    #     pat = re.compile('[^0-9]')
    #
    #     def insert_text(self, substring, from_undo=False):
    #         pat = self.pat
    #         if '.' in self.text:
    #             s = re.sub(pat, '', substring)
    #         else:
    #             s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
    #         return super(FloatInput, self).insert_text(s, from_undo=from_undo)

    # on_state:
    #     self.background_color = self.state == 'down' and [0.65, 0.48, 0.46, 1.0] or [0.2, 0.2, 0.2, 1]
    # canvas.before:
    #     Color:
    #         rgba: self.background_color
    #     Rectangle:
    #         pos: self.pos
    #         size: self.size


class Progress(Popup):
    pass