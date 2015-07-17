from dlibrary.units import to_area_units, to_inches
from dlibrary.utility.singleton import SingletonMeta
import vs


class Layer(object):

    def __init__(self, handle):
        self.__handle = handle

    @property
    def name(self) -> str:
        """
        For a sheet layer, VW calls this the number!
        """
        return vs.GetLName(self.__handle)

    @property
    def drawing_area(self) -> float:
        (p1x, p1y), (p2x, p2y) = vs.GetDrawingSizeRectN(self.__handle)
        return to_area_units(to_inches(p2x - p1x) * to_inches(p1y - p2y))


class DesignLayer(Layer):

    def __init__(self, handle):
        super().__init__(handle)


class SheetLayer(Layer):

    def __init__(self, handle):
        super().__init__(handle)

    @property
    def title(self) -> str:
        return ''


class LayerRepository(object, metaclass=SingletonMeta):

    def get_by_object(self, object_handle) -> Layer:
        return self.__create_layer(vs.GetLayer(object_handle))

    @staticmethod
    def __create_layer(layer_handle) -> Layer:
        return {1: DesignLayer, 2: SheetLayer}.get(vs.GetObjectVariableInt(layer_handle, 154))(layer_handle)
