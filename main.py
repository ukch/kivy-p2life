import logging as log # TODO proper logger config

import numpy as np

import kivy
kivy.require('1.8.0')

from kivy.core.window import Window
from kivy.app import App
#from kivy.config import Config
#from kivy.uix.widget import Widget
#from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

from kivy.properties import (
    #NumericProperty,
    ObjectProperty,
    #ListProperty,
    #ReferenceListProperty,
    #BooleanProperty,
)


from kivy_grid_cells import DrawableGrid


class CustomLayout(BoxLayout):
    grid = ObjectProperty(None)


class GameOfLifeApp(App):

    def on_start(self):
        # TODO can we calculate this in the kv file?
        def refresh_grid_position(*args):
            self.root.grid.center = self.root.grid.parent.center[:]

        Window.bind(on_resize=refresh_grid_position)
        refresh_grid_position()


if __name__ == '__main__':
    GameOfLifeApp().run()
