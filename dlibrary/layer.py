from dlibrary.units import to_area_units, to_inches
from dlibrary.utility.singleton import SingletonMeta
import vs


class Layer(object):

    def __init__(self, handle):
        self.__handle = handle

    @property
    def name(self) -> str:
        return vs.GetLName(self.__handle)

    @property
    def drawing_area(self) -> float:
        (p1x, p1y), (p2x, p2y) = vs.GetDrawingSizeRectN(self.__handle)
        return to_area_units(to_inches(p2x - p1x) * to_inches(p1y - p2y))


class LayerRepository(object, metaclass=SingletonMeta):

    @staticmethod
    def get_by_object(object_handle) -> Layer:
        return Layer(vs.GetLayer(object_handle))
