"""Used for all object related stuff, except for plug-in objects.
"""
from abc import ABCMeta, abstractmethod
from collections import OrderedDict

from dlibrary.document import Layer, Units, Clazz, IAttributes, AbstractVectorFill, SymbolDefinition, \
    DataFieldTypeEnum, PioFieldTypeEnum
from dlibrary.object_base import AbstractKeyedObject, ObjectRepository
from dlibrary.utility import VSException, Convert
import vs


class IObjectHandle(object, metaclass=ABCMeta):
    """Abstract interface to define the object handle field that all object interfaces need.
    """

    @property
    @abstractmethod
    def _object_handle(self) -> vs.Handle:
        """:rtype: vs.Handle"""
        pass


class IObjectAttributes(IObjectHandle, IAttributes, metaclass=ABCMeta):
    """Interface that handles object attributes.
    """

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


class IObjectOrder(IObjectHandle, metaclass=ABCMeta):
    """Interface that handles object stacking order.
    """

    def move_forward(self, count: int=1):
        self.__move_forward(False, count)

    def move_to_front(self):
        self.__move_forward(True)

    def move_backward(self, count: int=1):
        self.__move_backward(False, count)

    def move_to_back(self):
        self.__move_backward(True)

    def __move_forward(self, to_front: bool, count: int=1):
        for i in range(0, count):
            vs.HMoveForward(self._object_handle, to_front)

    def __move_backward(self, to_back: bool, count: int=1):
        for i in range(0, count):
            vs.HMoveBackward(self._object_handle, to_back)


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


class AbstractObject(AbstractKeyedObject, IObjectAttributes, IObjectRecords, IObjectOrder, metaclass=ABCMeta):

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
    def bb_top(self) -> float:
        """:rtype: float"""
        return vs.GetBBox(self.handle)[0][1]

    @property
    def bb_left(self) -> float:
        """:rtype: float"""
        return vs.GetBBox(self.handle)[0][0]

    @property
    def bb_right(self) -> float:
        """:rtype: float"""
        return vs.GetBBox(self.handle)[1][0]

    @property
    def bb_bottom(self) -> float:
        """:rtype: float"""
        return vs.GetBBox(self.handle)[1][1]

    @property
    def bb_width(self) -> float:
        """:rtype: float"""
        top_left, bottom_right = vs.GetBBox(self.handle)
        return bottom_right[0] - top_left[0]

    @property
    def bb_height(self) -> float:
        """:rtype: float"""
        top_left, bottom_right = vs.GetBBox(self.handle)
        return top_left[1] - bottom_right[1]

    @property
    def _object_handle(self) -> vs.Handle:
        return self.handle

    def move(self, delta_x: float, delta_y: float):
        vs.HMove(self.handle, delta_x, delta_y)

    def rotate(self, angle: float, origin: tuple=None):
        """Will rotate the object around it's own center point, relative to the drawing, not the plug-in!
        :type origin: (float, float)
        """
        vs.HRotate(self.handle, origin or vs.Get2DPt(self.handle, 0), angle)

    def reset(self):
        vs.ResetObject(self.handle)


class PluginObject(AbstractObject):
    """Wrapper for custom plugin objects."""

    @property
    def origin(self) -> tuple:
        """:rtype: (float, float)"""
        return vs.GetSymLoc(self.handle)

    @property
    def rotation(self) -> float:
        """:rtype: float"""
        return vs.GetSymRot(self.handle)


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


class TextHorizontalAlignmentEnum(object):

    LEFT = 1
    CENTER = 2
    RIGHT = 3
    JUSTIFY = 4


class TextVerticalAlignmentEnum(object):

    TOP = 1
    TOP_BASELINE = 2
    CENTER = 3
    BOTTOM_BASELINE = 4
    BOTTOM = 5


class Text(AbstractObject):

    @staticmethod
    def create(text: str, origin: tuple, horizontal_alignment: int=None, vertical_alignment: int=None):
        """
        :type origin: (float | str, float | str)
        :type horizontal_alignment: TextHorizontalAlignmentEnum
        :type vertical_alignment: TextVerticalAlignmentEnum
        :rtype: Text
        """
        vs.TextOrigin(Units.resolve_length_units(origin))
        vs.TextJust(horizontal_alignment) if horizontal_alignment else None
        vs.TextVerticalAlign(vertical_alignment) if vertical_alignment else None
        vs.CreateText(text)
        return Text(vs.LNewObj())

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)

    @property
    def horizontal_alignment(self) -> int:
        """:rtype: TextHorizontalAlignmentEnum"""
        return vs.GetTextJust(self.handle)

    @horizontal_alignment.setter
    def horizontal_alignment(self, value: int):
        """:type value: TextHorizontalAlignmentEnum"""
        vs.SetTextJustN(self.handle, value)

    @property
    def vertical_alignment(self) -> int:
        """:rtype: TextVerticalAlignmentEnum"""
        return vs.GetTextVerticalAlign(self.handle)

    @vertical_alignment.setter
    def vertical_alignment(self, value: int):
        """:type value: TextVerticalAlignmentEnum"""
        vs.SetTextVertAlignN(self.handle, value)

    @property
    def font_size(self) -> int:
        return int(vs.GetTextSize(self.handle, 0))

    @font_size.setter
    def font_size(self, value: int):
        vs.SetTextSize(self.handle, 0, vs.GetTextLength(self.handle), value)


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


class Group(AbstractObject):

    @staticmethod
    def create(content_creator: callable):
        """
        :type content_creator: () -> None
        :rtype: Group
        """
        vs.BeginGroup()
        content_creator()
        vs.EndGroup()
        return Group(vs.LNewObj())

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class SymbolScalingEnum(object):
    """Holds all possible scaling options for symbol instances.
    """

    NONE = 1
    SYMMETRIC = 2
    ASYMMETRIC = 3


class Symbol(AbstractObject):

    @staticmethod
    def create(definition: SymbolDefinition, insertion_point: tuple, rotation: float):
        """
        :type insertion_point: (float | str, float | str)
        :rtype: Symbol
        """
        vs.Symbol(definition.name, Units.resolve_length_units(insertion_point), rotation)
        return Symbol(vs.LNewObj())

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)

    @property
    def scaling(self) -> int:
        """:rtype: SymbolScalingEnum"""
        return vs.GetObjectVariableInt(self.handle, 101)

    @scaling.setter
    def scaling(self, value: int):
        """:type value: SymbolScalingEnum"""
        vs.SetObjectVariableInt(self.handle, 101, value)

    @property
    def __asymmetric_scaling(self) -> bool:
        return self.scaling == SymbolScalingEnum.ASYMMETRIC

    @property
    def scale_x(self) -> float:
        """:rtype: float"""
        return vs.GetObjectVariableReal(self.handle, 102)

    @scale_x.setter
    def scale_x(self, value: float):
        """:type value: float"""
        vs.SetObjectVariableReal(self.handle, 102, value)
        vs.ResetObject(self.handle)

    @property
    def scale_y(self) -> float:
        """:rtype: float"""
        return vs.GetObjectVariableReal(self.handle, 103) if self.__asymmetric_scaling else self.scale_x

    @scale_y.setter
    def scale_y(self, value: float):
        """:type value: float"""
        if self.__asymmetric_scaling:
            vs.SetObjectVariableReal(self.handle, 103, value)
            vs.ResetObject(self.handle)
        else:
            self.scale_x = value

    @property
    def scale_z(self) -> float:
        """:rtype: float"""
        return vs.GetObjectVariableReal(self.handle, 104) if self.__asymmetric_scaling else self.scale_x

    @scale_z.setter
    def scale_z(self, value: float):
        """:type value: float"""
        if self.__asymmetric_scaling:
            vs.SetObjectVariableReal(self.handle, 104, value)
            vs.ResetObject(self.handle)
        else:
            self.scale_x = value


class Viewport(AbstractObject):

    def __init__(self, handle: vs.Handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return vs.GetObjectVariableString(self.handle, 1032)

    @property
    def scale(self) -> float:
        return vs.GetObjectVariableReal(self.handle, 1003)
