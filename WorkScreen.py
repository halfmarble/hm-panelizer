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

from kivy.uix.screenmanager import Screen
from kivy.graphics import Color, Rectangle


class WorkScreen(Screen):

    def __init__(self, app, **kwargs):
        super(WorkScreen, self).__init__(**kwargs)

        self._app = app

        with self.canvas:
            Color(1.0, 0.0, 0.0, 0.5)
            self.background_rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(size=self.update_rect)

    def update_rect(self, *args):
        self.background_rect.size = (self.size[0], self.size[1])
        self._app.resize(self.background_rect.size)
