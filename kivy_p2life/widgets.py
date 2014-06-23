from hashlib import md5
import os

import numpy as np

from kivy.core.window import Window
from kivy.properties import (
    ListProperty,
    NumericProperty,
    ObjectProperty,
)
from kivy.uix.behaviors import ButtonBehavior, DragBehavior
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout

from kivy_grid_cells.widgets import DrawableGrid

from .events import DragShapeEvent, DropShapeEvent


def _get_root_widget():
    # FIXME there must be a better way to do this!
    assert len(Window.children) == 1, Window.children
    return Window.children[0]


class GOLGrid(DrawableGrid):

    """Subclassed DrawableGrid to allow drag-drop behaviour"""

    PREVIEW_GRID = 1

    def __init__(self, *args, **kwargs):
        self.register_event_type("on_drag_shape")
        self.register_event_type("on_drop_shape")
        super(GOLGrid, self).__init__(*args, **kwargs)

    def set_cell_state(self, cell, y, x):
        super(GOLGrid, self).set_cell_state(cell, y, x)
        grid = self.grids[self.PREVIEW_GRID]
        cell.set_border_state(grid[y, x])

    def drag_or_drop_shape(self, evt, grid_index):
        pattern = evt.pattern.astype(int) * _get_root_widget().player
        x, y = pattern.shape
        adj_x, adj_y = self.cell_coordinates(evt.pos)
        adj_x_end = adj_x + x
        adj_y_end = adj_y + y
        with self._writable_grid(grid_index):
            # TODO refuse to do this if cells are already set
            self.grids[grid_index][adj_x:adj_x_end, adj_y:adj_y_end] = pattern
        self.update_cell_widgets()

    def on_drag_shape(self, evt):
        if not self.collide_point(*evt.pos):
            return False
        self.clear_grid(self.PREVIEW_GRID)
        return self.drag_or_drop_shape(evt, self.PREVIEW_GRID)

    def on_drop_shape(self, evt):
        if not self.collide_point(*evt.pos):
            return False
        self.clear_grid(self.PREVIEW_GRID)
        return self.drag_or_drop_shape(evt, self.CELLS_GRID)


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
            evt = DragShapeEvent(self.parent.pattern, touch)
            _get_root_widget().dispatch("on_drag_shape", evt)
            return True
        return False

    def on_touch_up(self, touch):
        if super(PatternVisualisation, self).on_touch_up(touch):
            self.pos = self.original_position
            evt = DropShapeEvent(self.parent.pattern, touch)
            _get_root_widget().dispatch("on_drop_shape", evt)
            return True
        return False

    def on_release(self):
        with self.canvas:
            self.angle -= 90
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
