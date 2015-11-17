"""Used for getting stuff (objects or properties of objects) based on some criteria.
"""

from dlibrary.document import Layer
from dlibrary.object import AbstractObject, Viewport
import vs


class Criteria(object):
    def __init__(self):
        self.__criteria = []
        self.__objects = set()

    def on_layer(self, layer: Layer):
        self.__criteria.append('L=\'' + layer.name + '\'')
        return self

    def is_viewport(self):
        self.__criteria.append('T=VIEWPORT')
        return self

    def has_record(self, record_name: str):
        self.__criteria.append('R in [\'' + record_name + '\']')
        return self

    def get(self) -> set:
        """
        :rtype: set(AbstractObject)
        """
        vs.ForEachObject(self.__get_object, ' & '.join(['(' + criteria + ')' for criteria in self.__criteria]))
        return self.__objects

    def __get_object(self, object_handle):
        # noinspection PyTypeChecker
        self.__objects.add({
            122: Viewport
        }.get(vs.GetTypeN(object_handle), AbstractObject)(object_handle))
