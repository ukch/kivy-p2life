from __future__ import division

import functools
from hashlib import md5
from itertools import product
import logging
import os

import numpy as np

from kivy.base import EventLoop
from kivy.graphics import Color, Rectangle
from kivy.properties import (
    AliasProperty,
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.behaviors import ButtonBehavior, DragBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from kivy_grid_cells.constants import States, Colours
from kivy_p2life.constants import Types, FIDUCIALS
from kivy_grid_cells.widgets import GridCell, DrawableGrid

from . import events
from .exceptions import UnknownFiducialError


def _get_root_widget():
    EventLoop.ensure_window()
    return EventLoop.window.children[0]


class LimitedGridCell(GridCell):

    """Subclassed GridCell to allow limiting on/off switch behaviour"""

    def _get_player_pieces(self):
        return self.parent.player_pieces[_get_root_widget().player - 1]

    def should_ignore_touch(self):
        # TODO ignore touch when in TUIO-mode
        if self.state == self.parent.selected_state:
            return False
        return self._get_player_pieces().pieces < 1

    def handle_touch(self):
        """ Flip the cell's state between on and off, then update player_pieces

        >>> import mock
        >>> cell = LimitedGridCell(1, (0, 0))
        >>> cell._get_player_pieces = mock.Mock()
        >>> cell.parent = mock.Mock(selected_state=States.FIRST)
        >>> cell.handle_touch()
        >>> cell._get_player_pieces.return_value.update_pieces.call_args
        call(-1)
        """
        if self.should_ignore_touch():
            return
        new_state = super(LimitedGridCell, self).handle_touch()
        if new_state == States.DEACTIVATED:
            value = 1
        else:
            value = -1
        self._get_player_pieces().update_pieces(value)


class TUIODragDropMixin(object):

    """Create drag_shape/drop_shape events from TUIO events"""

    def _require_fiducial(method):
        @functools.wraps(method)
        def wrapper(self, touch):
            if not hasattr(touch, "fid"):
                # touch is not a TUIO event
                return getattr(super(TUIODragDropMixin, self), method.__name__)(touch)
            return method(self, touch)
        return wrapper

    pattern_locations = DictProperty()

    def __init__(self, *args, **kwargs):
        self.register_event_type("on_confirm")
        self.register_event_type("on_reset")
        self.register_event_type("on_admin_reset")
        super(TUIODragDropMixin, self).__init__(*args, **kwargs)
        half_pi = np.pi / 2
        self.rotation_array = np.array(
            # [full circle, 3/4, half, 1/4, nothing]
            [np.pi * 2, np.pi + half_pi, np.pi, half_pi, 0])

    def touch_to_pattern(self, touch):
        """ Find the related pattern from the touch and return it
        Arguments:
            touch; object; Kivy touch event with fiducial

        Touch with pattern fiducial
        >>> import mock
        >>> thing = type("Thing", (TUIODragDropMixin, Widget), {})()
        >>> thing.touch_to_pattern(mock.Mock(fid=2, angle=0))
        array([[ True, False],
               [ True,  True]], dtype=bool)
        >>> thing.touch_to_pattern(mock.Mock(fid=2, angle=3))
        array([[ True,  True],
               [False,  True]], dtype=bool)

        Touch with non-pattern fiducial
        >>> event = mock.Mock(fid=101)
        >>> event.__repr__ = lambda *a: "Mock event"
        >>> thing.touch_to_pattern(event)
        Traceback (most recent call last):
        UnknownFiducialError: Mock event
        """

        fid_type, pattern = FIDUCIALS.get(touch.fid, (None, None))
        if fid_type != Types.PATTERN:
            raise UnknownFiducialError(touch)
        pattern = np.array(pattern)
        # Use the (radian) angle to find out optimum rotation. This uses the
        # index of self.rotation_array, eg. array[2] == np.pi (180deg); to
        # rotate 180deg, rot90 needs to be called with argument 2.
        rotations = np.abs(self.rotation_array - touch.angle).argmin()
        return np.rot90(pattern, rotations)

    @_require_fiducial
    def on_touch_down(self, touch):
        """ TUIO touch down event

        No fiducial
        >>> import mock
        >>> logging.root._log = mock.Mock()
        >>> thing = type("Thing", (TUIODragDropMixin, Widget), { \
            "cell_coordinates": lambda s, a: a, \
        })()
        >>> thing.on_touch_down(object())

        Event fiducial
        >>> events.CustomEvent.dispatch = mock.Mock()
        >>> thing.on_touch_down(mock.Mock(fid=101, pos=(0, 0), angle=0))
        False
        >>> events.ConfirmEventWhite.dispatch.call_count
        1

        Pattern fiducial
        >>> thing.on_touch_down(mock.Mock(id=100, fid=2, pos=(0, 0), angle=0))
        >>> thing.pattern_locations
        {100: (0, 0, 2, 2)}

        Unknown fiducial
        >>> thing.on_touch_down(mock.Mock(fid=234, pos=(0, 0), angle=0))
        False
        >>> logging.root._log.call_count
        1
        >>> logging.root._log.call_args
        call(30, 'Unrecognised fiducial 234 on down', ())
        """

        # Fire custom events
        fid_type, data = FIDUCIALS.get(touch.fid, (None, None))
        if fid_type == Types.EVENT_DISPATCHER:
            Event = getattr(events, data)
            Event(touch).dispatch(self)
            return False

        # Set pattern location data
        try:
            pattern = self.touch_to_pattern(touch)
        except UnknownFiducialError:
            logging.warning("Unrecognised fiducial {} on down".format(touch.fid))
            return False
        if self.collide_point(*touch.pos):
            self.pattern_locations[touch.id] = \
                self.cell_coordinates(touch.pos) + pattern.shape
        else:
            self.pattern_locations[touch.id] = (None, None, None, None)

    @_require_fiducial
    def on_touch_up(self, touch):
        if not self.collide_point(*touch.pos):
            # Remove associated shape
            self.clear_grid_for_event(self.PREVIEW_GRID, touch)
        # Deregister this touch
        if touch.id in self.pattern_locations:
            del self.pattern_locations[touch.id]

    @_require_fiducial
    def on_touch_move(self, touch):
        """ TUIO touch move event

        No fiducial
        >>> import mock
        >>> logging.root._log = mock.Mock()
        >>> thing = type("Thing", (TUIODragDropMixin, Widget), { \
            "cell_coordinates": lambda s, a: a, \
        })()
        >>> thing.on_touch_move(object())

        Pattern fiducial
        >>> events.CustomEvent.dispatch = mock.Mock()
        >>> thing.on_touch_move(mock.Mock(id=100, fid=2, pos=(0, 0), angle=0))
        False
        >>> events.DragShapeEvent.dispatch.call_count
        1
        >>> events.DragShapeEvent.dispatch.call_args == [(thing, ), {}]
        True
        >>> thing.pattern_locations
        {100: (0, 0, 2, 2)}

        Unknown fiducial
        >>> thing.on_touch_move(mock.Mock(fid=234, pos=(0, 0), angle=0))
        False
        >>> logging.root._log.call_count
        1
        >>> logging.root._log.call_args
        call(30, 'Unrecognised fiducial 234 on move', ())
        """
        if not self.collide_point(*touch.pos):
            return False
        try:
            pattern = self.touch_to_pattern(touch)
        except UnknownFiducialError:
            logging.warning("Unrecognised fiducial {} on move".format(touch.fid))
            return False
        events.DragShapeEvent(pattern, touch).dispatch(self)
        self.pattern_locations[touch.id] = \
            self.cell_coordinates(touch.pos) + pattern.shape
        return False

    def clear_grid_for_event(self, grid_index, evt):
        if evt.id not in self.pattern_locations:
            return super(TUIODragDropMixin, self).clear_grid_for_event(grid_index, evt)
        adj_x, adj_y, x, y = self.pattern_locations[evt.id]
        if None in (adj_x, adj_y, x, y):
            return False
        empty = np.zeros(shape=(x, y), dtype=int)
        adj_x_end = adj_x + x
        adj_y_end = adj_y + y
        with self._writable_grid(grid_index):
            self.grids[grid_index][adj_x:adj_x_end, adj_y:adj_y_end] = empty

    def combine_with_cells(self, grid):
        """Add the given grid to the live grid

        >>> thing = type("Thing", (TUIODragDropMixin, Widget), {})()
        >>> thing.cells = np.array([1, 0, 1])
        >>> thing.combine_with_cells(np.array([0, 1, 0]))
        >>> thing.cells
        array([1, 1, 1])
        """
        assert (States.ILLEGAL not in grid)
        self.cells = grid + self.cells

    def on_confirm(self, evt):
        """ Confirm event handler
        Arguments:
            evt; object; ConfirmEventBlack or ConfirmEventWhite

        >>> import mock
        >>> logging.root._log = mock.Mock()
        >>> thing = type("Thing", (TUIODragDropMixin, Widget), {})()
        >>> EventLoop.window = mock.Mock(children=[mock.Mock(player=1)])

        With bad player:
        >>> thing.on_confirm(mock.Mock(player=2))
        False
        >>> logging.root._log.call_count
        1
        >>> logging.root._log.call_args
        call(30, 'Caught unauthorised confirm for player 2', ())
        """
        root = _get_root_widget()
        if evt.player != root.player:
            logging.warning("Caught unauthorised confirm for player {}".format(evt.player))
            return False
        grid = self.grids[self.PREVIEW_GRID].copy()
        grid[grid == States.ILLEGAL] = States.DEACTIVATED
        self.player_pieces[root.player - 1].update_pieces(-np.count_nonzero(grid))
        self.combine_with_cells(grid)
        self.clear_grid(self.PREVIEW_GRID)
        self.update_cell_widgets()
        root.end_turn()

    def on_reset(self, evt):
        """ Reset event handler
        Arguments:
            evt; object; ConfirmEventBlack or ConfirmEventWhite

        >>> import mock
        >>> logging.root._log = mock.Mock()
        >>> thing = type("Thing", (TUIODragDropMixin, Widget), {})()
        >>> EventLoop.window = mock.Mock(children=[mock.Mock(player=1)])

        With bad player:
        >>> thing.on_reset(mock.Mock(player=2))
        False
        >>> logging.root._log.call_count
        1
        >>> logging.root._log.call_args
        call(30, 'Caught unauthorised reset for player 2', ())
        """
        if evt.player != _get_root_widget().player:
            logging.warning("Caught unauthorised reset for player {}".format(evt.player))
            return False
        self.clear_grid(self.PREVIEW_GRID)
        self.update_cell_widgets()

    def on_admin_reset(self, evt):
        _get_root_widget().app.reset_ui()


class PiecesContainer(Widget):

    number = NumericProperty(States.DEACTIVATED)
    pieces = NumericProperty(0)

    def __init__(self, *args, **kwargs):
        super(PiecesContainer, self).__init__(*args, **kwargs)
        self._colour_cache = {}

    def redraw(self, old_amount=None):
        """ Ensure the pieces in the container are the correct colour
        Arguments:
            old_amount; int; For efficiency's sake, only redraw this many boxes

        # Five pieces in a ten-piece cache
        >>> pieces = PiecesContainer(number=States.FIRST, pieces=5)
        >>> pieces._colour_cache
        {}
        >>> pieces.redraw(10)
        >>> for key, (colour, shape) in sorted(pieces._colour_cache.items()):
        ...     key, colour.rgb
        ((0, 0), [1.0, 1.0, 1.0])
        ((0, 1), [1.0, 1.0, 1.0])
        ((0, 2), [1.0, 1.0, 1.0])
        ((0, 3), [0.4, 0.4, 0.4])
        ((0, 4), [0.4, 0.4, 0.4])
        ((1, 0), [1.0, 1.0, 1.0])
        ((1, 1), [1.0, 1.0, 1.0])
        ((1, 2), [0.4, 0.4, 0.4])
        ((1, 3), [0.4, 0.4, 0.4])
        ((1, 4), [0.4, 0.4, 0.4])

        Remove all pieces but only redraw the first two
        >>> pieces.pieces = 0
        >>> pieces.redraw(2)
        >>> for key, (colour, shape) in sorted(pieces._colour_cache.items()):
        ...     key, colour.rgb
        ((0, 0), [0.4, 0.4, 0.4])
        ((0, 1), [1.0, 1.0, 1.0])
        ((0, 2), [1.0, 1.0, 1.0])
        ((0, 3), [0.4, 0.4, 0.4])
        ((0, 4), [0.4, 0.4, 0.4])
        ((1, 0), [0.4, 0.4, 0.4])
        ((1, 1), [1.0, 1.0, 1.0])
        ((1, 2), [0.4, 0.4, 0.4])
        ((1, 3), [0.4, 0.4, 0.4])
        ((1, 4), [0.4, 0.4, 0.4])

        Redraw the whole 10-piece cache
        >>> pieces.redraw(10)
        >>> for key, (colour, shape) in sorted(pieces._colour_cache.items()):
        ...     key, colour.rgb
        ((0, 0), [0.4, 0.4, 0.4])
        ((0, 1), [0.4, 0.4, 0.4])
        ((0, 2), [0.4, 0.4, 0.4])
        ((0, 3), [0.4, 0.4, 0.4])
        ((0, 4), [0.4, 0.4, 0.4])
        ((1, 0), [0.4, 0.4, 0.4])
        ((1, 1), [0.4, 0.4, 0.4])
        ((1, 2), [0.4, 0.4, 0.4])
        ((1, 3), [0.4, 0.4, 0.4])
        ((1, 4), [0.4, 0.4, 0.4])
        """

        # constants
        CELL_SIZE = 25
        MAX_COLUMNS = 18
        GREY = [0.4, 0.4, 0.4, 1]

        if (old_amount and old_amount >= MAX_COLUMNS * 2
                and self.pieces >= MAX_COLUMNS * 2):
            # Container is full so there's no sense in redrawing it
            return

        if old_amount is None:
            old_amount = MAX_COLUMNS * 2
        max_iteration = max(old_amount, self.pieces)
        cache = self._colour_cache

        iterator = product(xrange(MAX_COLUMNS), xrange(2))  # left, right
        for piece_number, (col, row) in enumerate(iterator):
            if piece_number >= max_iteration:
                break
            if (row, col) not in cache:
                # new rectangle
                with self.canvas:
                    cache[(row, col)] = (
                        Color(*GREY),
                        Rectangle(size=(CELL_SIZE - 1, CELL_SIZE - 1)),
                    )
            colour, rect = cache[(row, col)]
            rect.pos = (self.x + row * CELL_SIZE, self.y + col * CELL_SIZE + 1)
            if piece_number < self.pieces:
                colour.rgb = Colours[self.number]
            else:
                colour.rgb = GREY

    def update_pieces(self, by_amount):
        old_amount = self.pieces
        self.pieces += by_amount
        self.redraw(old_amount)


class GOLGrid(TUIODragDropMixin, DrawableGrid):

    """Subclassed DrawableGrid to allow drag-drop behaviour"""

    GRID_CELL_CLASS = LimitedGridCell
    PREVIEW_GRID = 1

    player_uis = ListProperty()
    player_pieces = ListProperty()  # TODO a better way to get player_pieces

    def __init__(self, *args, **kwargs):
        self.register_event_type("on_drag_shape")
        self.register_event_type("on_drop_shape")
        super(GOLGrid, self).__init__(*args, **kwargs)

    def set_cell_state(self, cell, y, x):
        super(GOLGrid, self).set_cell_state(cell, y, x)
        grid = self.grids[self.PREVIEW_GRID]
        cell.set_border_state(grid[y, x])

    def get_player_ui(self, number):
        for ui in self.player_uis:
            if ui.number == number:
                return ui
        else:
            raise KeyError("No Player found with number {}".format(number))

    def drag_or_drop_shape(self, evt, grid_index, tolerate_illegal=False):
        """ Draw a shape on the grid
        Arguments:
            evt; object; Touch event
            grid_index; int; Index of the grid to update
            tolerate_illegal; bool; If specified, illegal moves will draw a red
                box on the grid. Otherwise nothing will happen.

        >>> import mock
        >>> EventLoop.window = mock.Mock(children=[mock.Mock(player=1)])
        >>> grid = GOLGrid(rows=3, cols=1, num_grids=2)
        >>> grid.player_pieces.append(mock.Mock(pieces=1))
        >>> grid.init_cells()
        >>> event = mock.Mock(pattern=np.array([[True]]), pos=(0, 0))

        Put shape on live grid
        >>> grid.drag_or_drop_shape(event, 0, tolerate_illegal=False)
        >>> grid.grids
        [array([[1, 0, 0]]), array([[0, 0, 0]])]

        Illegal shape on preview grid
        >>> grid.drag_or_drop_shape(event, 1, tolerate_illegal=False)
        >>> grid.grids
        [array([[1, 0, 0]]), array([[0, 0, 0]])]

        Illegal shape on preview grid; tolerate_illegal=True
        >>> grid.drag_or_drop_shape(event, 1, tolerate_illegal=True)
        >>> grid.grids
        [array([[1, 0, 0]]), array([[-1,  0,  0]])]
        """
        root = _get_root_widget()
        pattern = evt.pattern.astype(int) * root.player
        x, y = pattern.shape
        adj_x, adj_y = self.cell_coordinates(evt.pos)
        adj_x_end = adj_x + x
        adj_y_end = adj_y + y
        player_pieces = self.player_pieces[root.player - 1]
        grid = self.grids[grid_index]
        counters = np.count_nonzero(grid[grid != States.ILLEGAL])
        counters += np.count_nonzero(pattern)
        overlaps = (self._cells[adj_x:adj_x_end, adj_y:adj_y_end]
                    != States.DEACTIVATED)
        if counters > player_pieces.pieces or overlaps.any():
            if tolerate_illegal:
                # Change the whole pattern into a red grid
                np.core.multiarray.copyto(pattern, States.ILLEGAL,
                                          casting="unsafe")
            else:
                self.update_cell_widgets()  # Clear any existing pattern
                return
        with self._writable_grid(grid_index):
            grid[adj_x:adj_x_end, adj_y:adj_y_end] = pattern
        if grid_index == self.CELLS_GRID:
            player_pieces.update_pieces(-counters)
        self.update_cell_widgets()

    def on_drag_shape(self, evt):
        if not self.collide_point(*evt.pos):
            return False
        self.clear_grid_for_event(self.PREVIEW_GRID, evt)
        return self.drag_or_drop_shape(evt, self.PREVIEW_GRID,
                                       tolerate_illegal=True)

    def on_drop_shape(self, evt):
        self.clear_grid_for_event(self.PREVIEW_GRID, evt)
        if not self.collide_point(*evt.pos):
            self.update_cell_widgets()  # Clear any existing pattern
            return False
        return self.drag_or_drop_shape(evt, self.CELLS_GRID)

    def on_cells_updated(self):
        """ Update player scores with new values

        >>> import mock
        >>> grid = GOLGrid(rows=3, cols=1, num_grids=2)
        >>> grid.player_uis.append(mock.Mock(number=1, score=0))
        >>> grid.player_uis.append(mock.Mock(number=2, score=0))
        >>> grid.init_cells()
        >>> grid.cells = [[1, 2, 1]]
        >>> grid.on_cells_updated()
        >>> grid.player_uis[0].score
        2
        >>> grid.player_uis[1].score
        1
        """
        cells = self.cells
        for ui in self.player_uis:
            ui.score = np.count_nonzero(cells == ui.number)

    def get_new_pieces_for_player(self, player):
        return np.count_nonzero(self.cells == player) // 3


class PlayerUI(Label):

    app = ObjectProperty()
    colour = ListProperty(Colours[States.DEACTIVATED])
    completeness = NumericProperty(0)

    def get_score(self):
        return getattr(self, "_score", 0)

    def set_score(self, score):
        if self.app is None:
            top_score = 0
        else:
            top_score = self.app.top_score
        score = min(score, top_score)
        self._score = score
        self.completeness = score / top_score

    score = AliasProperty(get_score, set_score)

    def get_number(self):
        return getattr(self, "_number", States.DEACTIVATED)

    def set_number(self, number):
        assert number in [States.FIRST, States.SECOND], "Unknown state {}!".format(number)
        self._number = number
        self.colour = Colours[number]

    number = AliasProperty(get_number, set_number)

    @property
    def has_maximum_score(self):
        return (self.score == self.app.top_score)

    # Not to be confused with has_maximum_score. This is set when a player had
    # the maximum score at the last count, but they may not still have the
    # maximum score.
    had_maximum_score = BooleanProperty(False)


class RotatedImage(Image):

    angle = NumericProperty()


class PatternVisualisation(DragBehavior, ButtonBehavior, RotatedImage):

    original_position = ListProperty()

    def show_pattern(self, pattern):
        # TODO autogenerate assets
        # TODO different assets for different players
        # TODO asset caching (if possible)
        digest = md5(np.array_str(pattern)).hexdigest()
        self.source = os.path.join("assets", "{}.png".format(digest))

    def setup(self):
        assert self.parent.pattern is not None, "parent.pattern is not set!"
        self.show_pattern(self.parent.pattern)
        self.drag_rect_x = self.parent.x
        self.drag_rect_y = self.parent.y
        self.original_position = self.parent.pos

    def on_touch_move(self, touch):
        if super(PatternVisualisation, self).on_touch_move(touch):
            evt = events.DragShapeEvent(self.parent.pattern, touch)
            evt.dispatch(_get_root_widget())
            return True
        return False

    def on_touch_up(self, touch):
        if super(PatternVisualisation, self).on_touch_up(touch):
            self.pos = self.original_position
            evt = events.DropShapeEvent(self.parent.pattern, touch)
            evt.dispatch(_get_root_widget())
            return True
        return False

    def on_release(self):
        with self.canvas:
            self.angle -= 90
        # For some reason np.rot90 rotates anti-clockwise, so we need to call
        # it with argument 3 (to rotate 270 degrees instead of 90)
        self.parent.pattern = np.rot90(self.parent.pattern, 3)


class CellShape(BoxLayout):

    visualisation = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(CellShape, self).__init__(*args, **kwargs)
        self._pattern = None

    @property
    def pattern(self):
        return self._pattern

    @pattern.setter
    def pattern(self, pattern):
        if hasattr(pattern, "copy"):
            # Assume cells is a numpy array
            pattern = pattern.copy()
        else:
            pattern = np.array(pattern)
        self._pattern = pattern

    def setup(self):
        self.visualisation = PatternVisualisation(size=self.size)
        self.add_widget(self.visualisation)
        self.visualisation.setup()
