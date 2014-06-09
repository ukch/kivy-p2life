from __future__ import division

from functools import partial

import kivy
kivy.require('1.8.0')

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout

from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
)

from kivy_grid_cells.constants import Colours
from kivy_p2life.constants import Colours as Players
from kivy_p2life.gol import life_animation
from kivy_p2life.utils import Player


class CustomLayout(BoxLayout):
    app = ObjectProperty(None)
    grid = ObjectProperty(None)
    end_turn_button = ObjectProperty(None)
    interactions_enabled = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        super(CustomLayout, self).__init__(*args, **kwargs)
        self._player = None

    def disable_interaction(self):
        self.interactions_enabled = False
        self.end_turn_button.text = "Waiting..."

    def enable_interaction(self):
        self.interactions_enabled = True
        self.end_turn_button.text = "End turn"

    def set_turn(self, player):
        other_colour = Player(player).next()  # TODO something more clever?
        self.end_turn_button.color = Colours[other_colour]
        self.end_turn_button.background_color = Colours[player]
        self.player = player
        self.grid.selected_state = player

    def evolve(self, iterations, speed, callback=None):
        anim = life_animation(self.grid.cells)

        def _update(dt=None, remaining=0):
            self.grid.cells = anim.next()
            remaining -= 1
            if remaining:
                Clock.schedule_once(partial(_update, remaining=remaining), timeout=(1/speed))
            elif callback is not None:
                callback()

        _update(remaining=iterations)

    def _end_turn_callback(self):
        self.set_turn(self.player.next())
        self.enable_interaction()

    def end_turn(self, *args):
        self.disable_interaction()
        self.evolve(self.app.iterations_per_turn, speed=self.app.speed,
                    callback=self._end_turn_callback)

    @property
    def player(self):
        return self._player

    @player.setter
    def player(self, value):
        self._player = Player(value)

    # Disable all touch events when evolution is in progress
    def on_touch_down(self, evt):
        if self.interactions_enabled:
            return super(CustomLayout, self).on_touch_down(evt)

    def on_touch_move(self, evt):
        if self.interactions_enabled:
            return super(CustomLayout, self).on_touch_move(evt)


class GameOfLifeApp(App):

    iterations_per_turn = NumericProperty()
    speed = NumericProperty

    def build_config(self, config):
        config.setdefaults("game", {
            "speed": 10,
            "iterations_per_turn": 15,
        })
        config.setdefaults("grid", {
            "rows": 30,
            "cols": 30,
            "cell_size": 15,
        })

    def build(self):
        config = self.config
        self.root.app = self

        # Game
        self.speed = config.getint("game", "speed")
        self.iterations_per_turn = config.getint("game", "iterations_per_turn")

        # Grid
        self.root.grid.rows = config.getint("grid", "rows")
        self.root.grid.cols = config.getint("grid", "cols")
        self.root.grid.cell_size = config.getint("grid", "cell_size")

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
    # TODO set title, icon
    GameOfLifeApp().run()
