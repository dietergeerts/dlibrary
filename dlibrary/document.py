"""Used for all document related stuff, like units, layers, ....
"""

from abc import ABCMeta
from dlibrary.utility import SingletonMeta, ObservableList
import vs


class Document(object, metaclass=SingletonMeta):

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


class AbstractResource(object, metaclass=ABCMeta):
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
        self.__abstract_resource = abstract_resource
        self.__resource_names = ObservableList()
        self.__resource_list, count = vs.BuildResourceList(resource_type, 0, '')
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
        return vs.GetResourceFromList(self.__resource_list, index + 1)

    def __get_resource_name(self, index) -> str:
        return vs.GetNameFromResourceList(self.__resource_list, index + 1)

    def __import_resource(self, index) -> object:
        handle = vs.ImportResToCurFileN(self.__resource_list, index + 1, lambda s: 1)  # 1 >> Replace if needed!
        self.__resource_names[index] = vs.GetActualNameFromResourceList(self.__resource_list, index + 1)
        return handle

    def __remove_resource(self, index):
        vs.DeleteResourceFromList(self.__resource_list, index + 1)


class DefinitionTypeEnum(object):
    RECORD_DEFINITION = 47


class RecordDefinition(AbstractResource):
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
