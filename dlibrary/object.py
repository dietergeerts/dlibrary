"""Used for all object related stuff, except for plug-in objects.
"""

from abc import ABCMeta

from dlibrary.document import Layer
import vs


class AbstractHandle(object, metaclass=ABCMeta):

    def __init__(self, handle):
        self.__handle = handle

    @property
    def handle(self):
        return self.__handle


class RecordField(AbstractHandle):
    """
    We will use the record handle to get the data out of the field.
    """

    def __init__(self, handle, index: int):
        super().__init__(handle)
        self.__index = index

    @property
    def name(self) -> str:
        return vs.GetFldName(self.handle, self.__index)


class Record(AbstractHandle):

    def get_field(self, index: int) -> RecordField:
        return RecordField(self.handle, index)


class AbstractObject(AbstractHandle, metaclass=ABCMeta):

    @property
    def layer(self) -> Layer:
        return Layer.get(vs.GetLayer(self.handle))

    def move(self, delta_x: float, delta_y: float):
        vs.HMove(self.handle, delta_x, delta_y)


class Line(AbstractObject):

    @staticmethod
    def get(line_handle):
        return Line(line_handle)

    @staticmethod
    def create(point1: tuple, point2: tuple):
        vs.MoveTo(point1)
        vs.LineTo(point2)
        return Line(vs.LNewObj())

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def begin(self) -> tuple:
        return vs.GetSegPt1(self.handle)

    @property
    def end(self) -> tuple:
        return vs.GetSegPt2(self.handle)


class Viewport(AbstractObject):

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return vs.GetObjectVariableString(self.handle, 1032)

    @property
    def scale(self) -> float:
        return vs.GetObjectVariableReal(self.handle, 1003)
