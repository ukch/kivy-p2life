from .constants import Colours

class CustomEvent(object):

    EVENT_DISPATCH_NAME = NotImplemented

    def __init__(self, touch):
        self.touch = touch

    def __repr__(self):
        return "{}(\n\ttouch={}\n)".format(self.__class__.__name__, self.touch)

    def dispatch(self, widget):
        return widget.dispatch(self.EVENT_DISPATCH_NAME, self)


class PatternEvent(CustomEvent):

    def __init__(self, pattern, touch):
        super(PatternEvent, self).__init__(touch)
        self.pattern = pattern

    def __repr__(self):
        return "{}(\n\tpattern={},\n\ttouch={}\n)".format(
            self.__class__.__name__, self.pattern.tolist(), self.touch)

    @property
    def id(self):
        return self.touch.id

    @property
    def pos(self):
        return self.touch.pos


DragShapeEvent = type("DragShapeEvent", (PatternEvent, ),
                      {"EVENT_DISPATCH_NAME": "on_drag_shape"})
DropShapeEvent = type("DropShapeEvent", (PatternEvent, ),
                      {"EVENT_DISPATCH_NAME": "on_drop_shape"})

ConfirmEventWhite = type("ConfirmEventWhite", (CustomEvent, ), {
    "EVENT_DISPATCH_NAME": "on_confirm",
    "player": Colours.WHITE,
})
ConfirmEventBlack = type("ConfirmEventWhite", (CustomEvent, ), {
    "EVENT_DISPATCH_NAME": "on_confirm",
    "player": Colours.BLACK,
})
ResetEventWhite = type("ConfirmEventWhite", (CustomEvent, ), {
    "EVENT_DISPATCH_NAME": "on_reset",
    "player": Colours.WHITE,
})
ResetEventBlack = type("ConfirmEventWhite", (CustomEvent, ), {
    "EVENT_DISPATCH_NAME": "on_reset",
    "player": Colours.BLACK,
})


def propagate_events(widget, name, evt):
    """ Propagate the event to the widget's children.
    This is similar to how Window handles propagation, but more flexible."""
    for w in widget.children[:]:
        try:
            value = w.dispatch(name, evt)
        except KeyError:
            value = propagate_events(w, name, evt)
        if value:
            return True
