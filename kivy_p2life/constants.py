from kivy_grid_cells.constants import States

class Colours(object):
    EMPTY = States.DEACTIVATED
    WHITE = States.FIRST
    BLACK = States.SECOND

    # FIXME this is quite numpy-specific, so should it belong in gol.py?
    UNKNOWN = WHITE + BLACK


class Types(object):
    PATTERN = "pattern"
    EVENT_DISPATCHER = "event dispatcher"


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

    101: (Types.EVENT_DISPATCHER, "ConfirmEventWhite"),
    102: (Types.EVENT_DISPATCHER, "ResetEventWhite"),
    201: (Types.EVENT_DISPATCHER, "ConfirmEventBlack"),
    202: (Types.EVENT_DISPATCHER, "ResetEventBlack"),

    500: (Types.EVENT_DISPATCHER, "AdminResetEvent"),
}
