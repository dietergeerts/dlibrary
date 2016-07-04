"""Used for all document related stuff, like units, layers, resources, ....
"""
from abc import ABCMeta, abstractmethod
from collections import OrderedDict

from dlibrary.object_base import ObjectRepository, AbstractKeyedObject, ObjectTypeEnum
from dlibrary.utility import SingletonMeta, ObservableList, SingletonABCMeta, Convert
import vs


class DataFieldTypeEnum(object):
    """Holds all data field type constants. There are for data records and worksheets, not for PIO field types.
    """

    INTEGER = 1
    BOOLEAN = 2
    TEXT = 4
    NUMBER_GENERAL = 3
    NUMBER_DECIMAL = 5
    NUMBER_PERCENTAGE = 6
    NUMBER_SCIENTIFIC = 7
    NUMBER_FRACTIONAL = 8
    NUMBER_DIMENSION = 9
    NUMBER_DIMENSION_AREA = 14
    NUMBER_DIMENSION_VOLUME = 15
    NUMBER_ANGLE = 10
    NUMBER_DATETIME = 11


class PioFieldTypeEnum(object):
    """Holds all data field type constants for PIO fields.
    """

    INTEGER = 1
    BOOLEAN = 2
    TEXT = 4
    TEXT_POPUP = 8
    TEXT_RADIO_BUTTON = 9
    TEXT_STATIC = 14
    TEXT_CLASS_POPUP = 18
    REAL = 3
    REAL_DIMENSION = 7
    REAL_X_COORDINATE = 10
    REAL_Y_COORDINATE = 11


class RecordField(object):
    """Class to handle record instance fields.
    """

    def __init__(self, record_handle: vs.Handle, index: int, record_name: str, object_handle: vs.Handle,
                 parametric: bool):
        self.__record_handle = record_handle
        self.__index = index
        self.__record_name = record_name
        self.__object_handle = object_handle
        self.__parametric = parametric

    @property
    def name(self) -> str:
        """:rtype: str"""
        return vs.GetFldName(self.__record_handle, self.__index)

    @property
    def type(self) -> int:
        """:rtype: DataFieldTypeEnum | PioFieldTypeEnum"""
        return vs.GetFldType(self.__record_handle, self.__index)

    @property
    def value(self):
        """:rtype: str | int | bool | float"""
        return {
            True: {
                PioFieldTypeEnum.INTEGER: self.__to_int,
                PioFieldTypeEnum.BOOLEAN: self.__to_bool,
                PioFieldTypeEnum.REAL: self.__to_float,
                PioFieldTypeEnum.REAL_DIMENSION: self.__to_float,
                PioFieldTypeEnum.REAL_X_COORDINATE: self.__to_float,
                PioFieldTypeEnum.REAL_Y_COORDINATE: self.__to_float
            },
            False: {
                DataFieldTypeEnum.INTEGER: self.__to_int,
                DataFieldTypeEnum.BOOLEAN: self.__to_bool,
                DataFieldTypeEnum.NUMBER_GENERAL: self.__to_float,
                DataFieldTypeEnum.NUMBER_DECIMAL: self.__to_float,
                DataFieldTypeEnum.NUMBER_PERCENTAGE: self.__to_float,
                DataFieldTypeEnum.NUMBER_SCIENTIFIC: self.__to_float,
                DataFieldTypeEnum.NUMBER_FRACTIONAL: self.__to_float,
                DataFieldTypeEnum.NUMBER_DIMENSION: self.__to_float,
                DataFieldTypeEnum.NUMBER_DIMENSION_AREA: self.__to_float_from_area,
                DataFieldTypeEnum.NUMBER_DIMENSION_VOLUME: self.__to_float_from_volume,
                DataFieldTypeEnum.NUMBER_ANGLE: self.__to_float_from_angle
            }
        }.get(self.__parametric).get(self.type, self.__to_str)(
            vs.GetRField(self.__object_handle, self.__record_name, self.name))

    @value.setter
    def value(self, value: str):
        """:type value: str"""
        vs.SetRField(self.__object_handle, self.__record_name, self.name, value)

    @staticmethod
    def __to_str(value: str) -> str:
        return value

    @staticmethod
    def __to_int(value: str) -> int:
        return int(vs.Str2Num(value))

    @staticmethod
    def __to_bool(value: str) -> bool:
        return Convert.str2bool(value)

    @staticmethod
    def __to_float(value: str) -> float:
        return Units.resolve_length_units(value)

    @staticmethod
    def __to_float_from_area(value: str) -> float:
        return vs.Str2Area(value)

    @staticmethod
    def __to_float_from_volume(value: str) -> float:
        return vs.Str2Volume(value)

    @staticmethod
    def __to_float_from_angle(value: str) -> float:
        return vs.Str2Angle(value)


class Record(AbstractKeyedObject):
    """Class to represent a record instance, aka attached record.
    """

    def __init__(self, handle: vs.Handle, object_handle: vs.Handle):
        super().__init__(handle)
        self.__object_handle = object_handle

    @property
    def parametric(self) -> bool:
        """:rtype: bool"""
        return vs.GetParametricRecord(self.__object_handle) == self.handle

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
        return RecordField(self.handle, index, self.name, self.__object_handle, self.parametric)


class IRecords(object, metaclass=ABCMeta):
    """Interface that handles attached records.
    """

    @property
    @abstractmethod
    def _handle(self) -> vs.Handle:
        """:rtype: vs.Handle"""
        pass

    @property
    def records(self) -> dict:
        """:rtype: dict[str, Record]"""
        return {record.name: record for record in (
            Record(vs.GetRecord(self._handle, index), self._handle)
            for index in range(1, vs.NumRecords(self._handle) + 1))}


class PatternFillEnum(object):
    """Holds the most important pattern fill indices in a human readable name.
    These are No fill, background color fill and foreground color fill. It is recommended to not use any other fills
    anymore, as there are several issues with them, especially with printing.
    """

    NONE = 0
    BACKGROUND_COLOR = 1
    FOREGROUND_COLOR = 2


class AbstractResource(AbstractKeyedObject, metaclass=ABCMeta):
    """Class to represent a document resource.
    """

    @staticmethod
    @abstractmethod
    def create_placeholder(name: str):
        pass

    def __init__(self, handle_or_name, name: str=''):
        """OBSOLETE name parameter. Will be removed and is now optional.
        :type handle_or_name: vs.Handle | str
        """
        # TODO: Remove name parameter in version 2017!
        super().__init__(handle_or_name)

    @property
    def _handle(self) -> str:
        """:rtype: str - OBSOLETE, use handle property instead."""
        # TODO: Remove this property in version 2017!
        return self.handle


class AbstractVectorFill(AbstractKeyedObject, metaclass=ABCMeta):
    """Abstract base class for vector fills = fill resources.
    """

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class AbstractVectorLine(AbstractKeyedObject, metaclass=ABCMeta):
    """Abstract base class for vector lines = line resources.
    """

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class IAttributes(object, metaclass=ABCMeta):
    """Abstract interface for handling attributes.
    """

    @property
    def fill(self):
        """:rtype: PatternFillEnum | T <= AbstractVectorFill"""
        return self._get_vector_fill() or self._get_pattern_fill()

    @fill.setter
    def fill(self, value):
        """:type value: PatternFillEnum | T <= AbstractVectorFill"""
        self._set_pattern_fill(value) if isinstance(value, int) else None
        self._set_vector_fill(value) if isinstance(value, AbstractVectorFill) else None

    @property
    def line(self):
        """":rtype: PatternFillEnum | T <= AbstractVectorLine"""
        return self._get_vector_line() or self._get_pattern_line()

    @line.setter
    def line(self, value):
        """:type value: PatternFillEnum | T <= AbstractVectorLine"""
        self._set_pattern_line(value) if isinstance(value, int) else None
        self._set_vector_line(value) if isinstance(value, AbstractVectorLine) else None

    @abstractmethod
    def _get_pattern_fill(self) -> int:
        pass

    @abstractmethod
    def _set_pattern_fill(self, value: int):
        pass

    @abstractmethod
    def _get_vector_fill(self):
        """Should return the vector fill, if any, otherwise None!
        :rtype: T <= AbstractVectorFill
        """
        pass

    @abstractmethod
    def _set_vector_fill(self, value):
        """
        :type value: T <= AbstractVectorFill
        """
        pass

    @abstractmethod
    def _get_pattern_line(self) -> int:
        pass

    @abstractmethod
    def _set_pattern_line(self, value: int):
        pass

    @abstractmethod
    def _get_vector_line(self):
        """Should return the vector line, if any, otherwise None!
        :rtype: T <= AbstractVectorLine
        """
        pass

    @abstractmethod
    def _set_vector_line(self, value):
        """
        :type value: T <= AbstractVectorLine
        """
        pass


class IClazzAttributes(IAttributes, metaclass=ABCMeta):
    """Interface for handling class attributes.
    """

    @property
    @abstractmethod
    def _clazz_name(self) -> str:
        pass

    def _get_pattern_fill(self) -> int:
        return vs.GetClFPat(self._clazz_name)

    def _set_pattern_fill(self, value: int):
        vs.SetClFPat(self._clazz_name, value)

    def _get_vector_fill(self):
        """Should return the vector fill, if any, otherwise None!
        :rtype: T <= AbstractVectorFill
        """
        has_vector_fill, name = vs.GetClVectorFill(self._clazz_name)
        return ObjectRepository().get(name) if has_vector_fill else None

    def _set_vector_fill(self, value):
        """
        :type value: T <= AbstractVectorFill
        """
        vs.SetObjectVariableLongInt(vs.GetObject(self._clazz_name), 695, vs.Name2Index(value.name) * -1)

    def _get_pattern_line(self) -> int:
        return vs.GetClLSN(self._clazz_name)

    def _set_pattern_line(self, value: int):
        vs.SetClLSN(self._clazz_name, value)

    def _get_vector_line(self):
        """Should return the vector line, if any, otherwise None!
        :rtype: T <= AbstractVectorLine
        """
        line_type = vs.GetClLSN(self._clazz_name)
        return ObjectRepository().get(vs.Index2Name(line_type * -1)) if line_type < 0 else None

    def _set_vector_line(self, value):
        """
        :type value: T <= AbstractVectorLine
        """
        vs.SetClLSN(self._clazz_name, vs.Name2Index(value.name) * -1)


class Clazz(AbstractKeyedObject, IClazzAttributes):
    """Class for working with class definitions.
    """

    @staticmethod
    def create(name: str):
        """Creates a new class with the given name.
        :rtype: Clazz
        """
        active_clazz = vs.ActiveClass()
        vs.NameClass(name)
        vs.NameClass(active_clazz)
        return ObjectRepository().get(name)

    @staticmethod
    def get_or_create(name: str):
        """Gets the class, creates if not found.
        :rtype: Clazz
        """
        clazz = ObjectRepository().get(name)
        return clazz if clazz is not None and isinstance(clazz, Clazz) else Clazz.create(name)

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)

    @property
    def _clazz_name(self) -> str:
        """:rtype: str"""
        return self.name


class Layer(object):

    @staticmethod
    def get(layer_handle):
        return {1: DesignLayer, 2: SheetLayer}.get(vs.GetObjectVariableInt(layer_handle, 154))(layer_handle)

    def __init__(self, handle: vs.Handle):
        self.__handle = handle

    @property
    def _handle(self):
        return self.__handle

    @property
    def name(self) -> str:
        """For a sheet layer, VW calls this the number!
        """
        return vs.GetLName(self._handle)

    @property
    def description(self) -> str:
        return vs.GetDescriptionText(self._handle)

    @property
    def drawing_area(self) -> float:
        (p1x, p1y), (p2x, p2y) = vs.GetDrawingSizeRectN(self._handle)
        return Units.to_area_units(Units.to_inches(p2x - p1x) * Units.to_inches(p1y - p2y))


class DesignLayer(Layer):

    def __init__(self, handle: vs.Handle):
        super().__init__(handle)

    @property
    def scale(self) -> float:
        return vs.GetLScale(self._handle)


class SheetLayer(Layer):

    def __init__(self, handle: vs.Handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return vs.GetObjectVariableString(self._handle, 159)


class IDocumentAttributes(IAttributes, metaclass=ABCMeta):
    """Interface for handling document attributes.
    """

    def _get_pattern_fill(self) -> int:
        return vs.FFillPat()

    def _set_pattern_fill(self, value: int):
        vs.FillPat(value)

    def _get_vector_fill(self):
        """Should return the vector fill, if any, otherwise None!
        :rtype: T <= AbstractVectorFill
        """
        # We'll get the correct pref index through the currently set fill type.
        pref_index = {4: 530, 5: 528, 6: 508, 7: 518}.get(vs.GetPrefInt(529), 0)
        return None if pref_index == 0 else ObjectRepository().get(vs.Index2Name(vs.GetPrefLongInt(pref_index) * -1))

    def _set_vector_fill(self, value):
        """
        :type value: T <= AbstractVectorFill
        """
        vs.SetPrefLongInt(
            {HatchVectorFill: 530, TileVectorFill: 528, GradientVectorFill: 508, ImageVectorFill: 518}.get(type(value)),
            vs.Name2Index(value.name) * -1)

    def _get_pattern_line(self) -> int:
        return vs.FPenPatN()

    def _set_pattern_line(self, value: int):
        vs.PenPatN(value)

    def _get_vector_line(self):
        """Should return the vector line, if any, otherwise None!
        :rtype: T <= AbstractVectorLine
        """
        line_type = vs.FPenPatN()
        return ObjectRepository().get(vs.Index2Name(line_type * -1)) if line_type < 0 else None

    def _set_vector_line(self, value):
        """
        :type value: T <= AbstractVectorLine
        """
        vs.PenPatN(vs.Name2Index(value.name) * -1)


class Document(IDocumentAttributes, metaclass=SingletonABCMeta):
    """Class to represent the active document.
    Python scripts are always executed in context of the currently active document, that's why this is a singleton.
    """

    @property
    def saved(self) -> bool:
        return vs.GetFName() != vs.GetFPathName()

    @property
    def filename(self) -> str:
        return vs.GetFName()

    @property
    def layers(self) -> set:
        """
        :rtype: set(Layer)
        """
        layer_handles = []
        for count in range(vs.NumLayers()):
            layer_handles.append(vs.FLayer() if count == 0 else vs.NextLayer(layer_handles[count - 1]))
        return {Layer.get(layer_handle) for layer_handle in layer_handles}

    @property
    def design_layers(self) -> set:
        """
        :rtype: set(DesignLayer)
        """
        return {layer for layer in self.layers if isinstance(layer, DesignLayer)}

    @property
    def sheet_layers(self) -> set:
        """
        :rtype: set(SheetLayer)
        """
        return {layer for layer in self.layers if isinstance(layer, SheetLayer)}

    @property
    def text_size(self) -> float:
        """Text size in points
        :rtype: float
        """
        return vs.GetPrefReal(57) / 42.42424

    @text_size.setter
    def text_size(self, value: float):
        vs.SetPrefReal(57, value * 42.42424)


class Units(object, metaclass=SingletonMeta):

    @staticmethod
    def __get_length_units_per_inch() -> float:
        return vs.GetPrefReal(152)

    @staticmethod
    def __get_area_units_per_square_inch() -> float:
        return vs.GetPrefReal(176)

    @staticmethod
    def __get_volume_units_per_cubic_inch() -> float:
        return vs.GetPrefReal(180)

    @staticmethod
    def __validate_length_str_to_inches(length: str) -> float:
        return Units.to_inches(Units.__validate_length_str_to_length_units(length))

    @staticmethod
    def __validate_length_str_to_length_units(length: str) -> float:
        ok, num = vs.ValidNumStr(length)
        # VW has rounding errors: vs.ValidNumStr('4605mm') gives 460.5000000000001!
        # So we'll round the length off by the document unit length precision, which is set by the user.
        return round(num, Units().length_precision)

    @staticmethod
    def __to_str(units: float, precision: int, with_unit_mark: bool, unit_mark: str) -> str:
        return '%%.%sf%%s' % precision % (units, unit_mark if with_unit_mark else '')

    @staticmethod
    def resolve_length_units(dimension):
        """Will return the same, but length unit strings will be transformed to floats.
        For a float or str dimension, this will return a float.
        For a tuple, which would be a point, this will return a tuple of floats.

        :type dimension: float | str | tuple
        :rtype: float | tuple
        """
        if isinstance(dimension, str):
            return Units.__validate_length_str_to_length_units(dimension)
        elif isinstance(dimension, tuple):
            return tuple((Units.__validate_length_str_to_length_units(item) if isinstance(item, str) else item)
                         for item in dimension)
        else:
            return dimension

    @staticmethod
    def to_inches(length_in_length_units_or_str: float) -> float:
        """
        :type length_in_length_units_or_str: float || str
        """
        if isinstance(length_in_length_units_or_str, str):
            return Units.__validate_length_str_to_inches(length_in_length_units_or_str)
        else:
            return length_in_length_units_or_str / Units.__get_length_units_per_inch()

    @staticmethod
    def to_length_units(length_in_inches_or_str: float) -> float:
        """
        :type length_in_inches_or_str: float || str
        """
        if isinstance(length_in_inches_or_str, str):
            return Units.__validate_length_str_to_length_units(length_in_inches_or_str)
        else:
            return length_in_inches_or_str * Units.__get_length_units_per_inch()

    @staticmethod
    def to_length_string(length_in_length_units: float, with_unit_mark: bool=False) -> str:
        return Units.__to_str(length_in_length_units, vs.GetPrefLongInt(162), with_unit_mark, vs.GetPrefString(154))

    @staticmethod
    def to_square_inches(area_in_area_units: float) -> float:
        return area_in_area_units / Units.__get_area_units_per_square_inch()

    @staticmethod
    def to_area_units(area_in_square_inches: float) -> float:
        return area_in_square_inches * Units.__get_area_units_per_square_inch()

    @staticmethod
    def to_area_string(araa_in_area_units: float, with_unit_mark: bool=False) -> str:
        return Units.__to_str(araa_in_area_units, vs.GetPrefLongInt(179), with_unit_mark, vs.GetPrefString(178))

    @staticmethod
    def to_cubic_inches(volume_in_volume_units: float) -> float:
        return volume_in_volume_units / Units.__get_volume_units_per_cubic_inch()

    @staticmethod
    def to_volume_units(volume_in_cubic_inches: float) -> float:
        return volume_in_cubic_inches * Units.__get_volume_units_per_cubic_inch()

    @staticmethod
    def to_volume_string(volume_in_volume_units: float, with_unit_mark: bool=False) -> str:
        return Units.__to_str(volume_in_volume_units, vs.GetPrefLongInt(183), with_unit_mark, vs.GetPrefString(182))

    @property
    def length_precision(self) -> int:
        """:rtype: int"""
        return vs.GetPrefLongInt(162)


class HatchVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class TileVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class GradientVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class ImageVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class LineStyle(AbstractVectorLine):

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class ResourceLocation(object):
    """"Constants that reflect where to get the asked resources from."""

    DOC = 0      # Get resources from current document.
    DOC_APP = 1  # Get resources from current document and application folders.
    APP = -1     # Get resources from application folders.


class ResourceFolder(object):
    """"Constants for all possible application resource folders."""

    NONE = 0
    DEFAULTS = 14


class AbstractResourceList(object, metaclass=ABCMeta):

    def __init__(self, resource_type: int, abstract_resource: callable, location: int=0, folder: int=0, path: str= ''):
        """
        :type location: ResourceLocation
        :type folder: ResourceFolder
        """
        self.__resource_type = resource_type
        self.__abstract_resource = abstract_resource
        self.__resource_names = ObservableList()
        self.__resource_list_id, count = vs.BuildResourceList(resource_type, folder * location, path)
        resources_to_delete = list()
        for index in range(count):
            handle = self.__get_resource(index)
            name = self.__get_resource_name(index)
            # '__' Indicates a 'hidden' record, mostly __NNA...
            if name.startswith('__') or (handle is not None and vs.IsPluginFormat(handle)):
                resources_to_delete.append(index)
            else:
                self.__resource_names.append(name)
        for index in resources_to_delete:
            self.__remove_resource(index)

    @property
    def id(self) -> int:
        return self.__resource_list_id

    @property
    def type(self) -> int:
        return self.__resource_type

    @property
    def names(self) -> ObservableList:
        return self.__resource_names

    def is_resource_in_list(self, name: str) -> bool:
        index = self.__resource_names.index(name)
        return index != -1 and (self.__get_resource_name(index) != '-')  # A separator is '-'.

    def is_resource_in_document(self, name: str) -> bool:
        index = self.__resource_names.index(name)
        return index != -1 and self.__get_resource(index)

    def get_resource(self, name: str) -> AbstractResource:
        index = self.__resource_names.index(name)
        if index == -1:
            return None
        else:
            handle = self.__get_resource(index) or self.__import_resource(index)
            name = self.__resource_names[index]  # Name could be changed due to import!
            return self.__abstract_resource(handle, name)

    def remove_resource(self, name: str):
        if name in self.names:
            self.__remove_resource(self.names.index(name))
            self.names.remove(name)

    def __get_resource(self, index) -> vs.Handle:
        resource_handle = vs.GetResourceFromList(self.__resource_list_id, index + 1)
        return resource_handle if resource_handle != 0 else None  # VW returns 0 instead of None!

    def __get_resource_name(self, index) -> str:
        return vs.GetNameFromResourceList(self.__resource_list_id, index + 1)

    def __import_resource(self, index) -> vs.Handle:
        handle = vs.ImportResToCurFileN(self.__resource_list_id, index + 1, lambda s: 1)  # 1 >> Replace if needed!
        self.__resource_names[index] = vs.GetActualNameFromResourceList(self.__resource_list_id, index + 1)
        return handle

    def __remove_resource(self, index):
        vs.DeleteResourceFromList(self.__resource_list_id, index + 1)

    def get_abstract_resource_clazz(self) -> callable:
        return self.__abstract_resource


class DefinitionTypeEnum(object):
    """SYMBOL_DEFINITION is OBSOLETE. Use ObjectTypeEnum from object_base!
    """
    SYMBOL_DEFINITION = 16  # TODO: Remove in v2017!
    RECORD_DEFINITION = 47


class SymbolDefinition(AbstractResource, IRecords):
    """Class to represent a symbol definition.
    """

    @staticmethod
    def create_placeholder(name: str):
        if vs.GetObject(name) is None:
            vs.BeginSym(name)
            vs.EndSym()
            vs.SetObjectVariableBoolean(vs.GetObject(name), 900, False)
        return SymbolDefinition(vs.GetObject(name), name)

    @staticmethod
    def get_by_name(name: str):
        """OBSOLETE. Use ObjectRepository().get(handle_or_name) from object_base instead.
        """
        obj_handle = vs.GetObject(name)
        obj_handle = obj_handle if vs.GetTypeN(obj_handle) == 16 else None  # 16 = symbol definition.
        return SymbolDefinition(obj_handle, name) if obj_handle is not None else None

    def __init__(self, handle_or_name, name: str=''):
        """OBSOLETE name parameter. This will be removed and is now optional.
        :type handle: vs.Handle | str
        """
        # TODO: Remove name parameter in version 2017!
        super().__init__(handle_or_name)

    @property
    def _handle(self) -> vs.Handle:
        """:rtype: vs.Handle"""
        return self.handle

    def place_symbol(self, insertion_point: tuple, rotation: float):
        """OBSOLETE, use Symbol.create instead!
        """
        # TODO: Remove in version 2017!
        vs.Symbol(self.name, Units.resolve_length_units(insertion_point), rotation)


class SymbolDefinitionResourceList(AbstractResourceList):

    def __init__(self, location: int=0, folder: int=0, path: str=''):
        """
        :type location: ResourceLocation
        :type folder: ResourceFolder
        """
        super().__init__(ObjectTypeEnum.SYMBOL_DEFINITION, SymbolDefinition, location, folder, path)


class RecordDefinition(AbstractResource):
    """Class to represent a record definition.
    """

    @staticmethod
    def create_placeholder(name: str):
        if vs.GetObject(name) is None:
            vs.NewField(name, 'placeholder', '', 4, 0)
            vs.SetObjectVariableBoolean(vs.GetObject(name), 900, False)
        return RecordDefinition(vs.GetObject(name), name)

    def __init__(self, handle_or_name, name: str=''):
        """OBSOLETE name parameter. Will be removed and is now made optional.
        :type handle_or_name: vs.Handle | str
        """
        # TODO: Remove name parameter in version 2017!
        super().__init__(handle_or_name)
        self.__fields = ObservableList(vs.GetFldName(self.handle, index)
                                       for index in range(1, vs.NumFields(self.handle) + 1))

    @property
    def fields(self) -> ObservableList:
        return self.__fields


class RecordDefinitionResourceList(AbstractResourceList):

    def __init__(self, location: int=0, folder: int=0, path: str=''):
        """
        :type location: ResourceLocation
        :type folder: ResourceFolder
        """
        super().__init__(DefinitionTypeEnum.RECORD_DEFINITION, RecordDefinition, location, folder, path)
