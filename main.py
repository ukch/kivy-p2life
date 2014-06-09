import kivy
kivy.require('1.8.0')

from kivy.core.window import Window
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from kivy.properties import (
    ObjectProperty,
)

from kivy_grid_cells.constants import Colours
from kivy_p2life.constants import Colours as Players
from kivy_p2life.utils import Player


class CustomLayout(BoxLayout):
    grid = ObjectProperty(None)
    end_turn_button = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(CustomLayout, self).__init__(*args, **kwargs)
        self._player = None

    def set_turn(self, player):
        other_colour = Player(player).next()  # TODO something more clever?
        self.end_turn_button.color = Colours[other_colour]
        self.end_turn_button.background_color = Colours[player]
        self.player = player
        self.grid.selected_state = player

    def end_turn(self, *args):
        self.set_turn(self.player.next())

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, value):
        self._player = Player(value)


class GameOfLifeApp(App):

    def on_start(self):
        # TODO can we calculate this in the kv file?
        def refresh_grid_position(*args):
            return  # FIXME fix grid positioning
            self.root.grid.center = self.root.grid.parent.center[:]

        Window.bind(on_resize=refresh_grid_position)
        self.root.grid.init_cells()
        refresh_grid_position()

        self.root.set_turn(Players.WHITE)
        self.root.end_turn_button.bind(on_press=self.root.end_turn)


if __name__ == '__main__':
    GameOfLifeApp().run()
