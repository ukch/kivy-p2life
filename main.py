from __future__ import division

from ConfigParser import NoSectionError, NoOptionError
from functools import partial

import kivy
kivy.require('1.8.0')

from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config as KivyConfig
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout

from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
)

from kivy_grid_cells.constants import Colours
from kivy_p2life.constants import Colours as Players
from kivy_p2life.events import propagate_events
from kivy_p2life.gol import life_animation
from kivy_p2life.utils import Player


class CustomLayoutMixin(object):
    app = ObjectProperty(None)
    grid = ObjectProperty(None)
    shapes = ObjectProperty(None)
    end_turn_button = ObjectProperty(None)
    interactions_enabled = BooleanProperty(True)

    def __init__(self, *args, **kwargs):
        self.register_event_type("on_drag_shape")
        self.register_event_type("on_drop_shape")
        super(CustomLayoutMixin, self).__init__(*args, **kwargs)
        self._player = None

    def on_drag_shape(self, evt):
        return propagate_events(self, "on_drag_shape", evt)

    def on_drop_shape(self, evt):
        return propagate_events(self, "on_drop_shape", evt)

    def disable_interaction(self):
        self.interactions_enabled = False
        if self.end_turn_button:
            self.end_turn_button.text = "Waiting..."

    def enable_interaction(self):
        self.interactions_enabled = True
        if self.end_turn_button:
            self.end_turn_button.text = "End turn"

    def set_turn(self, player):
        other_colour = Player(player).next()  # TODO something more clever?
        if self.end_turn_button:
            self.end_turn_button.color = Colours[other_colour]
            self.end_turn_button.background_color = Colours[player]
        self.player = player
        self.grid.selected_state = player
        # TODO intelligently work out this value
        self.grid.player_pieces[player - 1].update_pieces(self.app.minimum_pieces)

    def set_winner(self, player, ui):
        # Override this method on a per-UI basis
        pass

    def evolve(self, iterations, speed, callback=None):
        anim = life_animation(self.grid.cells)

        def _update(dt=None, remaining=0):
            self.grid.cells = anim.next()
            remaining -= 1
            if remaining:
                Clock.schedule_once(partial(_update, remaining=remaining),
                                    timeout=(1 / speed))
            elif callback is not None:
                callback()

        _update(remaining=iterations)

    def _end_turn_callback(self):
        self.set_turn(self.player.next())
        ui = self.grid.get_player_ui(self.player)
        if ui.had_maximum_score and ui.has_maximum_score:
            self.set_winner(self.player, ui)
            return
        else:
            self.enable_interaction()

    def end_turn(self, *args):
        self.disable_interaction()
        ui = self.grid.get_player_ui(self.player)
        if ui.has_maximum_score:
            ui.had_maximum_score = True
        else:
            ui.had_maximum_score = False
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
            return super(CustomLayoutMixin, self).on_touch_down(evt)

    def on_touch_move(self, evt):
        if self.interactions_enabled:
            return super(CustomLayoutMixin, self).on_touch_move(evt)


class CustomBoxLayout(CustomLayoutMixin, BoxLayout):

    pass


class CustomAnchorLayout(CustomLayoutMixin, AnchorLayout):

    def set_winner(self, player, ui):
        ui.text = "You win!"



class GameOfLifeApp(App):

    iterations_per_turn = NumericProperty()
    speed = NumericProperty

    def build_config(self, config):
        config.setdefaults("game", {
            "speed": 10,
            "iterations_per_turn": 15,
            "top_score": 100,
            "minimum_pieces": 3,
        })
        config.setdefaults("grid", {
            "rows": 30,
            "cols": 30,
            "cell_size": 15,
        })
        config.setdefaults("input", {
            # 'touch' can be a finger or a mouse, depending on the platform
            "touch": True,
            "tuio": False,
        })

    def build(self):
        config = self.config

        # Input
        if config.getboolean("input", "tuio"):
            try:
                KivyConfig.get("input", "tuiotouchscreen")
            except (NoSectionError, NoOptionError):
                KivyConfig.set('input', 'tuiotouchscreen', 'tuio,0.0.0.0:3333')
                KivyConfig.write()
        if config.getboolean("input", "touch"):
            # Enable mouse interface
            kv_filename = 'gameoflife-mouse.kv'
        else:
            kv_filename = 'gameoflife-nomouse.kv'

        # Game
        self.speed = config.getint("game", "speed")
        self.iterations_per_turn = config.getint("game", "iterations_per_turn")
        self.top_score = config.getint("game", "top_score")
        self.minimum_pieces = config.getint("game", "minimum_pieces")

        # Root widget
        self.root = Builder.load_file(kv_filename)
        self.root.app = self

        # Grid
        self.root.grid.rows = config.getint("grid", "rows")
        self.root.grid.cols = config.getint("grid", "cols")
        self.root.grid.cell_size = config.getint("grid", "cell_size")

    def on_start(self):
        self.root.grid.init_cells()

        self.root.set_turn(Players.WHITE)
        if self.root.end_turn_button:
            self.root.end_turn_button.bind(on_press=self.root.end_turn)

        Clock.schedule_once(self.after_start, timeout=1)

    def after_start(self, *args):
        if self.root.shapes:
            for shape in self.root.shapes.children:
                shape.setup()


if __name__ == '__main__':
    # TODO set title, icon
    GameOfLifeApp().run()
