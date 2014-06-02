import kivy
kivy.require('1.8.0')

from kivy.core.window import Window
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from kivy.properties import (
    ObjectProperty,
)


class CustomLayout(BoxLayout):
    grid = ObjectProperty(None)


class GameOfLifeApp(App):

    def on_start(self):
        # TODO can we calculate this in the kv file?
        def refresh_grid_position(*args):
            return  # FIXME fix grid positioning
            self.root.grid.center = self.root.grid.parent.center[:]

        Window.bind(on_resize=refresh_grid_position)
        self.root.grid.init_cells()
        refresh_grid_position()


if __name__ == '__main__':
    GameOfLifeApp().run()
