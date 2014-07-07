from kivy_grid_cells.constants import States

class Colours(object):
    EMPTY = States.DEACTIVATED
    WHITE = States.FIRST
    BLACK = States.SECOND

    # FIXME this is quite numpy-specific, so should it belong in gol.py?
    UNKNOWN = WHITE + BLACK


class Types(object):
    PATTERN = "pattern"
    YESNO_WHITE = "yesno_white"
    YESNO_BLACK = "yesno_black"


class Patterns(object):
    SQUARE = [[True, False], [True, True]]
    DIAMOND = [[True, False], [True, True], [False, True]]
    OSCILLATOR = [[False, True, False], [True, True, True]]
    GLIDER = [[False, True, False], [True, False, False], [True, True, True]]


FIDUCIALS = {
    1: (Types.PATTERN, Patterns.DIAMOND),
    2: (Types.PATTERN, Patterns.SQUARE),
    3: (Types.PATTERN, Patterns.OSCILLATOR),
    4: (Types.PATTERN, Patterns.GLIDER),

    101: (Types.YESNO_WHITE, True),
    102: (Types.YESNO_WHITE, False),
    201: (Types.YESNO_BLACK, True),
    202: (Types.YESNO_BLACK, False),
}
