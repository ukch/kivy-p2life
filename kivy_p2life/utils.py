from kivy_p2life.constants import Colours


class Player(int):

    """An easier way to find the next player"""

    def next(self):
        if self == Colours.WHITE:
            return Colours.BLACK
        elif self == Colours.BLACK:
            return Colours.WHITE
        raise ValueError("No .next() value for {}".format(self))
