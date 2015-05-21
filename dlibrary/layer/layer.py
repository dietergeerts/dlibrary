class Layer(object):
    def __init__(self, handle):
        self.__handle = handle

    @property
    def handle(self):
        return self.__handle