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


class LayerButton(ToggleButton):
    pass


    # on_state:
    #     self.background_color = self.state == 'down' and [0.65, 0.48, 0.46, 1.0] or [0.2, 0.2, 0.2, 1]
    # canvas.before:
    #     Color:
    #         rgba: self.background_color
    #     Rectangle:
    #         pos: self.pos
    #         size: self.size
