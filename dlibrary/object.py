"""Used for all object related stuff, except for plug-in objects.
"""
from abc import ABCMeta, abstractmethod

from dlibrary.document import Layer, Units, Clazz, IAttributes, AbstractVectorFill
from dlibrary.object_base import AbstractKeyedObject, ObjectRepository
import vs


class IObjectAttributes(IAttributes, metaclass=ABCMeta):
    """Interface that handles object attributes.
    """

    @property
    @abstractmethod
    def _object_handle(self):
        pass

    def _get_pattern_fill(self) -> int:
        return vs.GetFPat(self._object_handle)

    def _set_pattern_fill(self, value: int):
        vs.SetFPat(self._object_handle, value)

    def _get_vector_fill(self):
        """
        :rtype: T <= AbstractVectorFill
        """
        has_vector_fill, name = vs.GetVectorFill(self._object_handle)
        return ObjectRepository().get(name) if has_vector_fill else None

    def _set_vector_fill(self, value):
        """
        :type value: T <= AbstractVectorFill
        """
        vs.SetObjectVariableLongInt(self._object_handle, 695, vs.Name2Index(value.name) * -1)


class RecordField(AbstractKeyedObject):
    """We will use the record handle to get the data out of the field.
    """

    def __init__(self, handle, index: int):
        super().__init__(handle)
        self.__index = index

    @property
    def name(self) -> str:
        return vs.GetFldName(self.handle, self.__index)


class Record(AbstractKeyedObject):

    def get_field(self, index: int) -> RecordField:
        return RecordField(self.handle, index)


class Attributes(AbstractKeyedObject):
    """We will use the object handle to get/set the attributes for it.
    """

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def by_clazz(self):
        return vs.IsLSByClass(self.handle) and \
               vs.IsLWByClass(self.handle) and \
               vs.IsPenColorByClass(self.handle) and \
               vs.IsFillColorByClass(self.handle) and \
               vs.IsFPatByClass(self.handle) and \
               vs.GetOpacityByClass(self.handle) and \
               vs.IsMarkerByClass(self.handle)

    @by_clazz.setter
    def by_clazz(self, value):
        self.__set_by_clazz() if value else (self.__set_not_by_clazz() if self.by_clazz else None)

    def __set_by_clazz(self):
        vs.SetLSByClass(self.handle)
        vs.SetLWByClass(self.handle)
        vs.SetPenColorByClass(self.handle)
        vs.SetFillColorByClass(self.handle)
        vs.SetFPatByClass(self.handle)
        vs.SetOpacityByClass(self.handle)
        vs.SetMarkerByClass(self.handle)

    def __set_not_by_clazz(self):
        """We'll just 'undo' by class by setting the attributes it had from the class."""
        vs.SetLSN(self.handle, vs.GetLSN(self.handle))
        vs.SetLW(self.handle, vs.GetLW(self.handle))
        vs.SetPenFore(self.handle, vs.GetPenFore(self.handle))
        vs.SetPenBack(self.handle, vs.GetPenBack(self.handle))
        vs.SetFillFore(self.handle, vs.GetFillFore(self.handle))
        vs.SetFillBack(self.handle, vs.GetFillBack(self.handle))
        vs.SetFPat(self.handle, vs.GetFPat(self.handle))
        vs.SetOpacity(self.handle, vs.GetOpacity(self.handle))
        ok, style, angle, size, width, thickness_basis, thickness, visibility = vs.GetObjBeginningMarker(self.handle)
        vs.SetObjBeginningMarker(self.handle, style, angle, size, width, thickness_basis, thickness, visibility)
        ok, style, angle, size, width, thickness_basis, thickness, visibility = vs.GetObjEndMarker(self.handle)
        vs.SetObjEndMarker(self.handle, style, angle, size, width, thickness_basis, thickness, visibility)


class AbstractObject(AbstractKeyedObject, IObjectAttributes, metaclass=ABCMeta):

    @property
    def layer(self) -> Layer:
        return Layer.get(vs.GetLayer(self.handle))

    @property
    def clazz(self) -> Clazz:
        return Clazz(vs.GetClass(self.handle))

    @clazz.setter
    def clazz(self, clazz: Clazz):
        vs.SetClass(self.handle, clazz.name)

    @property
    def attributes(self):
        return Attributes(self.handle)

    @property
    def _object_handle(self):
        return self.handle

    def move(self, delta_x: float, delta_y: float):
        vs.HMove(self.handle, delta_x, delta_y)


class DrawnObject(AbstractObject):
    """You can use this wrapper for objects that aren't yet in this library.
    As the object repository will not always know all possible object types, due to the fact that we are still working
    on DLibrary, and that Vectorworks can introduce new types, this class can be used for it's general properties.
    """

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: handle | str
        """
        super().__init__(handle_or_name)


class Line(AbstractObject):

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


class Polygon(AbstractObject):

    @staticmethod
    def create(vertices: tuple, closed: bool=True):
        """
        :type vertices: tuple[tuple[x: float|str, y: float|str]]
        """
        vs.ClosePoly() if closed else vs.OpenPoly()
        vs.Poly(*[Units.to_length_units(c) if isinstance(c, str) else c for vertex in vertices for c in vertex])
        return Polygon(vs.LNewObj())

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
