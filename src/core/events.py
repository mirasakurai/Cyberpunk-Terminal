from collections import defaultdict

# simple event system so components can talk
class Events:
    def __init__(self):
        self._subs = defaultdict(list)

    def subscribe(self, name, cb):
        # add listener for event
        self._subs[name].append(cb)

    def emit(self, name, data=None):
        # trigger event
        for cb in self._subs[name]:
            cb(data)
