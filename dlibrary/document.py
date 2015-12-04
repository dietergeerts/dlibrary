"""Used for all document related stuff, like units, layers, resources, ....
"""
from abc import ABCMeta, abstractmethod

from dlibrary.object_base import ObjectRepository, AbstractKeyedObject
from dlibrary.utility import SingletonMeta, ObservableList, VSException, SingletonABCMeta
import vs


# ---------------------------------------------------------------------------------------------------------- ATTRIBUTES


class PatternFillEnum(object):
    """"Holds the most important pattern fill indices in a human readable name.
    These are No fill, background color fill and foreground color fill. It is recommended to not use any other fills
    anymore, as there are several issues with them, especially with printing.
    """

    NONE = 0
    BACKGROUND_COLOR = 1
    FOREGROUND_COLOR = 2


class AbstractVectorFill(AbstractKeyedObject, metaclass=ABCMeta):

    def __init__(self, handle_or_name):
        super().__init__(handle_or_name)


class IAttributes(object, metaclass=ABCMeta):

    @property
    def fill(self):
        """
        :rtype: PatternFillEnum|AbstractVectorFill
        """
        return self._get_vector_fill() or self._get_pattern_fill()

    @fill.setter
    def fill(self, value):
        """
        :type value: PatternFillEnum|AbstractVectorFill
        """
        self._set_pattern_fill(value) if isinstance(value, int) else None
        self._set_vector_fill(value) if isinstance(value, AbstractVectorFill) else None

    @abstractmethod
    def _get_pattern_fill(self) -> int:
        pass

    @abstractmethod
    def _get_vector_fill(self) -> AbstractVectorFill:
        """Should return the vector fill, if any, otherwise None!
        """
        pass

    @abstractmethod
    def _set_pattern_fill(self, value: int):
        pass

    @abstractmethod
    def _set_vector_fill(self, value: AbstractVectorFill):
        pass


# ------------------------------------------------------------------------------------------------------------- CLASSES


class IClazzAttributes(IAttributes, metaclass=ABCMeta):

    @property
    @abstractmethod
    def _clazz_name(self) -> str:
        pass

    def _get_pattern_fill(self) -> int:
        return vs.GetClFPat(self._clazz_name)

    def _get_vector_fill(self) -> AbstractVectorFill:
        has_vector_fill, name = vs.GetClVectorFill(self._clazz_name)
        return ObjectRepository().get(name) if has_vector_fill else None

    def _set_pattern_fill(self, value: int):
        vs.SetClFPat(self._clazz_name, value)

    def _set_vector_fill(self, value: AbstractVectorFill):
        if not vs.SetClVectorFill(self._clazz_name, value.name):
            raise VSException('SetClVectorFill(%s, %s)' % (self._clazz_name, value.name))


class Clazz(IClazzAttributes):

    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self):
        return self.__name

    def _clazz_name(self) -> str:
        return self.name


# -------------------------------------------------------------------------------------------------------------- LAYERS


class Layer(object):

    @staticmethod
    def get(layer_handle):
        return {1: DesignLayer, 2: SheetLayer}.get(vs.GetObjectVariableInt(layer_handle, 154))(layer_handle)

    def __init__(self, handle):
        self.__handle = handle

    @property
    def _handle(self):
        return self.__handle

    @property
    def name(self) -> str:
        """
        For a sheet layer, VW calls this the number!
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

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def scale(self) -> float:
        return vs.GetLScale(self._handle)


class SheetLayer(Layer):

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return vs.GetObjectVariableString(self._handle, 159)


# ------------------------------------------------------------------------------------------------------------ DOCUMENT


class IDocumentAttributes(IAttributes, metaclass=ABCMeta):

    def _get_pattern_fill(self) -> int:
        return vs.FFillPat()

    def _get_vector_fill(self) -> AbstractVectorFill:
        has_vector_fill, name = vs.GetVectorFillDefault()
        return ObjectRepository().get(name) if has_vector_fill else None

    def _set_pattern_fill(self, value: int):
        vs.FillPat(value)

    def _set_vector_fill(self, value: AbstractVectorFill):
        if not vs.SetVectorFillDefault(value.name):
            raise VSException('SetVectorFillDefault(%s)' % value.name)


class Document(IDocumentAttributes, metaclass=SingletonABCMeta):

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


# --------------------------------------------------------------------------------------------------------------- UNITS


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
        return num

    @staticmethod
    def __to_str(units: float, precision: int, with_unit_mark: bool, unit_mark: str) -> str:
        return '%%.%sf%%s' % precision % (units, unit_mark if with_unit_mark else '')

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


# ----------------------------------------------------------------------------------------------------------- RESOURCES


class HatchVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        super().__init__(handle_or_name)


class TileVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        super().__init__(handle_or_name)


class GradientVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        super().__init__(handle_or_name)


class ImageVectorFill(AbstractVectorFill):

    def __init__(self, handle_or_name):
        super().__init__(handle_or_name)


class AbstractResource(object, metaclass=ABCMeta):

    @staticmethod
    @abstractmethod
    def create_placeholder(name: str):
        pass

    def __init__(self, handle, name: str):
        self.__handle = handle
        self.__name = name

    @property
    def _handle(self) -> str:
        return self.__handle

    @property
    def name(self) -> str:
        return self.__name


class AbstractResourceList(object, metaclass=ABCMeta):

    def __init__(self, resource_type: int, abstract_resource: callable):
        self.__resource_type = resource_type
        self.__abstract_resource = abstract_resource
        self.__resource_names = ObservableList()
        self.__resource_list_id, count = vs.BuildResourceList(resource_type, 0, '')
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

    def get_resource(self, name: str) -> AbstractResource:
        index = self.__resource_names.index(name)
        if index == -1:
            return None
        else:
            handle = self.__get_resource(index) or self.__import_resource(index)
            name = self.__resource_names[index]  # Name could be changed due to import!
            return self.__abstract_resource(handle, name)

    def __get_resource(self, index) -> object:
        return vs.GetResourceFromList(self.__resource_list_id, index + 1)

    def __get_resource_name(self, index) -> str:
        return vs.GetNameFromResourceList(self.__resource_list_id, index + 1)

    def __import_resource(self, index) -> object:
        handle = vs.ImportResToCurFileN(self.__resource_list_id, index + 1, lambda s: 1)  # 1 >> Replace if needed!
        self.__resource_names[index] = vs.GetActualNameFromResourceList(self.__resource_list_id, index + 1)
        return handle

    def __remove_resource(self, index):
        vs.DeleteResourceFromList(self.__resource_list_id, index + 1)

    def get_abstract_resource_clazz(self) -> callable:
        return self.__abstract_resource


class DefinitionTypeEnum(object):
    SYMBOL_DEFINITION = 16
    RECORD_DEFINITION = 47


class SymbolDefinition(AbstractResource):

    @staticmethod
    def create_placeholder(name: str):
        if vs.GetObject(name) is None:
            vs.BeginSym(name)
            vs.EndSym()
            vs.SetObjectVariableBoolean(vs.GetObject(name), 900, False)
        return SymbolDefinition(vs.GetObject(name), name)

    @staticmethod
    def get_by_name(name: str):
        obj_handle = vs.GetObject(name)
        obj_handle = obj_handle if vs.GetTypeN(obj_handle) == 16 else None  # 16 = symbol definition.
        return SymbolDefinition(obj_handle, name) if obj_handle is not None else None

    def __init__(self, handle, name: str):
        super().__init__(handle, name)

    def place_symbol(self, insertion_point: tuple, rotation: float):
        vs.Symbol(self.name, insertion_point, rotation)


class SymbolDefinitionResourceList(AbstractResourceList):

    def __init__(self):
        super().__init__(DefinitionTypeEnum.SYMBOL_DEFINITION, SymbolDefinition)


class RecordDefinition(AbstractResource):

    @staticmethod
    def create_placeholder(name: str):
        if vs.GetObject(name) is None:
            vs.NewField(name, 'placeholder', '', 4, 0)
            vs.SetObjectVariableBoolean(vs.GetObject(name), 900, False)
        return RecordDefinition(vs.GetObject(name), name)

    def __init__(self, handle, name: str):
        super().__init__(handle, name)
        self.__fields = ObservableList(vs.GetFldName(self._handle, index)
                                       for index in range(1, vs.NumFields(self._handle) + 1))

    @property
    def fields(self) -> ObservableList:
        return self.__fields


class RecordDefinitionResourceList(AbstractResourceList):

    def __init__(self):
        super().__init__(DefinitionTypeEnum.RECORD_DEFINITION, RecordDefinition)
