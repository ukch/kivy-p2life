from kivy_grid_cells.constants import States

class Colours(object):
    EMPTY = States.DEACTIVATED
    WHITE = States.FIRST
    BLACK = States.SECOND

    # FIXME this is quite numpy-specific, so should it belong in gol.py?
    UNKNOWN = WHITE + BLACK
