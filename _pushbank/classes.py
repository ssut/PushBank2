class Plugin:
    def __init__(self, options={}):
        self._options = options

    @property
    def options(self):
        return self._options

