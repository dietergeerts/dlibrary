from dlibrary.units import to_area_units, to_inches
from dlibrary.utility.singleton import SingletonMeta
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
        return {Layer.create(layer_handle) for layer_handle in layer_handles}

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


class Layer(object):

    @staticmethod
    def create(layer_handle):
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
