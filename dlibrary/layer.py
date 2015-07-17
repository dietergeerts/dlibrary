from dlibrary.units import to_area_units, to_inches
from dlibrary.utility.singleton import SingletonMeta
import vs


class Layer(object):

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
        return vs.GetLName(self.__handle)

    @property
    def description(self) -> str:
        return vs.GetObjectVariableString(self.__handle, 159)

    @property
    def drawing_area(self) -> float:
        (p1x, p1y), (p2x, p2y) = vs.GetDrawingSizeRectN(self.__handle)
        return to_area_units(to_inches(p2x - p1x) * to_inches(p1y - p2y))


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
        return ''


class LayerRepository(object, metaclass=SingletonMeta):

    def get_by_object(self, object_handle) -> Layer:
        return self.__create_layer(vs.GetLayer(object_handle))

    @staticmethod
    def __create_layer(layer_handle) -> Layer:
        return {1: DesignLayer, 2: SheetLayer}.get(vs.GetObjectVariableInt(layer_handle, 154))(layer_handle)
