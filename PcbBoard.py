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

from OffScreenScatter import *


class PcbBoard(OffScreenScatter):

    def __init__(self, client, size, shader, **kwargs):
        super(PcbBoard, self).__init__(client, size, shader, **kwargs)

        self._active = False

    def add_to(self, root):
        if not self._active:
            root.add_widget(self)
            self._active = True

    def remove_from(self, root):
        if self._active:
            root.remove_widget(self)
            self._active = False
