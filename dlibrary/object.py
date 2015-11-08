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
        return Layer.get(vs.GetLayer(self.handle))


class Line(AbstractObject):

    @staticmethod
    def create(point1: tuple, point2: tuple) -> AbstractObject:
        vs.MoveTo(point1)
        vs.LineTo(point2)
        return Line(vs.LNewObj())

    def __init__(self, handle):
        super().__init__(handle)


class Viewport(AbstractObject):

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return vs.GetObjectVariableString(self.handle, 1032)

    @property
    def scale(self) -> float:
        return vs.GetObjectVariableReal(self.handle, 1003)


class Record(object):
    def __init__(self, object_handle, name: str):
        self.__object_handle = object_handle
        self.__name = name

    def set_field(self, field: str, value: str):
        vs.SetRField(self.__object_handle, self.__name, field, value)
