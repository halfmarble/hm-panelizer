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


from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup


class LayerButton(ToggleButton):
    pass


class EmptyLabel(Label):
    pass


class PostLabel(Label):
    pass


class TitleLabel(Label):
    pass


class Settings(Popup):
    pass


class Progress(Popup):
    pass


class Error(Popup):
    pass

