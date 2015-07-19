from abc import ABCMeta

from dlibrary.document import Layer
import vs


class AbstractObject(object, metaclass=ABCMeta):

    def __init__(self, handle):
        self.__handle = handle

    @property
    def handle(self):
        return self.__handle

    @property
    def layer(self) -> Layer:
        return Layer.create(vs.GetLayer(self.handle))


class Viewport(AbstractObject):

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return vs.GetObjectVariableString(self.handle, 1032)

    @property
    def scale(self) -> float:
        return vs.GetObjectVariableReal(self.handle, 1003)
