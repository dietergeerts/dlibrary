"""Used for all object related stuff, except for plug-in objects.
"""
from abc import ABCMeta, abstractmethod
from collections import OrderedDict

from dlibrary.document import Layer, Units, Clazz, IAttributes, AbstractVectorFill
from dlibrary.object_base import AbstractKeyedObject, ObjectRepository
from dlibrary.utility import VSException
import vs


class RecordField(AbstractKeyedObject):
    """Class to handle record instance fields.
    """
    # TODO: Remove inheritance from AbstractKeyedObject! Inherit from object in version 2017!

    @property
    def handle(self) -> vs.Handle:
        """:rtype: vs.Handle OBSOLETE!"""
        # TODO: Remove in version 2017!
        return self.__handle

    def __init__(self, record_handle: vs.Handle, index: int, record_name: str=None, object_handle: vs.Handle=None):
        """Use the record_name and object_handle, as they will become mandatory in future versions!
        Not using them will render most things in this class useless!
        """
        # TODO: Make record_name and object_handle mandatory in version 2017!
        super().__init__(record_handle)
        self.__record_handle = record_handle
        self.__index = index
        self.__record_name = record_name
        self.__object_handle = object_handle

    @property
    def name(self) -> str:
        """:rtype: str"""
        return vs.GetFldName(self.__record_handle, self.__index)

    @property
    def value(self) -> str:
        """:rtype: str"""
        if self.__record_name is None or self.__object_handle is None:
            raise VSException('RecordField.value can\'t be used without record_name and object_handle!')
        # TODO: Remove check in version 2017, as then they will be mandatory!
        return vs.GetRField(self.__object_handle, self.__record_name, self.name)

    @value.setter
    def value(self, value: str):
        """:type value: str"""
        if self.__record_name is None or self.__object_handle is None:
            raise VSException('RecordField.value can\'t be used without record_name and object_handle!')
        # TODO: Remove check in version 2017, as then they will be mandatory!
        vs.SetRField(self.__object_handle, self.__record_name, self.name, value)


class Record(AbstractKeyedObject):
    """Class to represent a record instance, aka attached record.
    """

    def __init__(self, handle: vs.Handle, object_handle: vs.Handle=None):
        """Use the object_handle, as it will become mandatory in future versions!
        Not using the object_handle will make working with the record instance very limited!
        """
        # TODO: Make object_handle mandatory in version 2017!
        super().__init__(handle)
        self.__object_handle = object_handle

    @property
    def fields(self) -> OrderedDict:
        """:rtype: OrderedDict[str, RecordField]"""
        fields = OrderedDict()
        for index in range(1, vs.NumFields(self.handle) + 1):
            field = self.get_field(index)
            fields[field.name] = field
        return fields

    def get_field(self, index: int) -> RecordField:
        """Get the field based on it's index, 1-n based."""
        return RecordField(self.handle, index, self.name, self.__object_handle)


class IObjectAttributes(IAttributes, metaclass=ABCMeta):
    """Interface that handles object attributes.
    """

    @property
    @abstractmethod
    def _object_handle(self) -> vs.Handle:
        """:rtype: vs.Handle"""
        pass

    def _get_pattern_fill(self) -> int:
        return vs.GetFPat(self._object_handle)

    def _set_pattern_fill(self, value: int):
        vs.SetFPat(self._object_handle, value)

    def _get_vector_fill(self):
        """Should return the vector fill, if any, otherwise None!
        :rtype: T <= AbstractVectorFill
        """
        has_vector_fill, name = vs.GetVectorFill(self._object_handle)
        return ObjectRepository().get(name) if has_vector_fill else None

    def _set_vector_fill(self, value):
        """
        :type value: T <= AbstractVectorFill
        """
        vs.SetObjectVariableLongInt(self._object_handle, 695, vs.Name2Index(value.name) * -1)

    def _get_pattern_line(self) -> int:
        return vs.GetLSN(self._object_handle)

    def _set_pattern_line(self, value: int):
        vs.SetLSN(self._object_handle, value)

    def _get_vector_line(self):
        """Should return the vector line, if any, otherwise None!
        :rtype: T <= AbstractVectorLine
        """
        line_type = vs.GetLSN(self._object_handle)
        return ObjectRepository().get(vs.Index2Name(line_type * -1)) if line_type < 0 else None

    def _set_vector_line(self, value):
        """
        :type value: T <= AbstractVectorLine
        """
        vs.SetLSN(self._object_handle, vs.Name2Index(value.name) * -1)


class IObjectRecords(object, metaclass=ABCMeta):
    """Interface that handles attached records.
    """

    @property
    @abstractmethod
    def _object_handle(self) -> vs.Handle:
        """:rtype: vs.Handle"""
        pass

    @property
    def records(self) -> dict:
        """:rtype: dict[str, Record]"""
        return {record.name: record for record in (
            Record(vs.GetRecord(self._object_handle, index), self._object_handle)
            for index in range(1, vs.NumRecords(self._object_handle) + 1))}


class Attributes(AbstractKeyedObject):
    """We will use the object handle to get/set the attributes for it.
    """

    def __init__(self, handle: vs.Handle):
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


class AbstractObject(AbstractKeyedObject, IObjectAttributes, IObjectRecords, metaclass=ABCMeta):

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
    def _object_handle(self) -> vs.Handle:
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
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class Locus(AbstractObject):

    @staticmethod
    def create(origin: tuple):
        """
        :type origin: (float | str, float | str)
        :rtype: Locus
        """
        vs.Locus(Units.resolve_length_units(origin))
        return Locus(vs.LNewObj())

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class Line(AbstractObject):

    @staticmethod
    def create(point1: tuple, point2: tuple):
        """
        :type point1: (float | str, float | str)
        :type point2: (float | str, float | str)
        :rtype: Line
        """
        vs.MoveTo(Units.resolve_length_units(point1))
        vs.LineTo(Units.resolve_length_units(point2))
        return Line(vs.LNewObj())

    def __init__(self, handle: vs.Handle):
        super().__init__(handle)

    @property
    def begin(self) -> tuple:
        return vs.GetSegPt1(self.handle)

    @property
    def end(self) -> tuple:
        return vs.GetSegPt2(self.handle)


class Rectangle(AbstractObject):
    """Class that represents a rectangle object.
    """

    @staticmethod
    def create(origin: tuple, direction: tuple, width, height):
        """
        :type origin: (float | str, float | str)
        :type direction: (float | str, float | str)
        :type width: float | str
        :type height: float | str
        :rtype: Rectangle
        """
        vs.RectangleN(Units.resolve_length_units(origin), Units.resolve_length_units(direction),
                      Units.resolve_length_units(width), Units.resolve_length_units(height))
        return Rectangle(vs.LNewObj())

    @staticmethod
    def create_by_diagonal(top_left: tuple, bottom_right: tuple):
        """
        :type top_left: (float | str, float | str)
        :type bottom_right: (float | str, float | str)
        :rtype: Rectangle
        """
        vs.Rect(Units.resolve_length_units(top_left), Units.resolve_length_units(bottom_right))
        return Rectangle(vs.LNewObj())

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)

    @property
    def width(self) -> float:
        """:rtype: float"""
        return vs.HWidth(self.handle)

    @width.setter
    def width(self, value):
        """:type value: float | str"""
        vs.SetWidth(self.handle, Units.resolve_length_units(value))
        vs.ResetBBox(self.handle)  # Needed, or the object doesn't reflect the change!

    @property
    def height(self) -> float:
        """:rtype: float"""
        return vs.HHeight(self.handle)

    @height.setter
    def height(self, value):
        """:type value: float | str"""
        vs.SetHeight(self.handle, Units.resolve_length_units(value))
        vs.ResetBBox(self.handle)  # Needed, or the object doesn't reflect the change!

    @property
    def center(self) -> tuple:
        """:rtype: (float, float)"""
        return vs.Get2DPt(self.handle, 5)  # 5 is the actual center of the rectangle, 1-4 are the corners!


class Polygon(AbstractObject):

    @staticmethod
    def create(vertices: tuple, closed: bool=True):
        """
        :type vertices: tuple[tuple[x: float|str, y: float|str]]
        """
        vs.ClosePoly() if closed else vs.OpenPoly()
        vs.Poly(*[Units.to_length_units(c) if isinstance(c, str) else c for vertex in vertices for c in vertex])
        return Polygon(vs.LNewObj())

    def __init__(self, handle: vs.Handle):
        super().__init__(handle)


class Viewport(AbstractObject):

    def __init__(self, handle: vs.Handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return vs.GetObjectVariableString(self.handle, 1032)

    @property
    def scale(self) -> float:
        return vs.GetObjectVariableReal(self.handle, 1003)
