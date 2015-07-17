import vs


class Viewport(object):

    def __init__(self, handle):
        self.__handle = handle

    @property
    def scale(self) -> float:
        return vs.GetObjectVariableReal(self.__handle, 1003)
