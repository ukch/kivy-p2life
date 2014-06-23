class PatternEvent(object):

    def __init__(self, pattern, touch):
        self.pattern = pattern
        self.touch = touch

    def __repr__(self):
        return "{}(\n\tpattern={},\n\ttouch={}\n)".format(
            self.__class__.__name__, self.pattern.tolist(), self.touch)

    @property
    def pos(self):
        return self.touch.pos


DragShapeEvent = type("DragShapeEvent", (PatternEvent, ), {})
DropShapeEvent = type("DropShapeEvent", (PatternEvent, ), {})


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
