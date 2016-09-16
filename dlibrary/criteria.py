"""Module for criteria, which is used for getting stuff (objects or properties of objects), based on criteria.
"""
import vs
from dlibrary.document import Layer, Record
from dlibrary.object_base import ObjectRepository


class Criteria(object):
    """Class to build up criteria and get stuff out of it.

    Though fluid interfaces aren't a best practice in Python, we did choose for it in this class because the usage case
    for criteria is building them to get something in return, so a fluid interface is more readable and shorter in code.
    """

    def __init__(self):
        self.__criteria = set()

    def is_viewport(self):
        self.__criteria.add('T=VIEWPORT')
        return self

    def has_record(self, record: Record):
        self.__criteria.add('R in [\'' + record.name + '\']')
        return self

    def on_layer(self, layer: Layer):
        self.__criteria.add('L=\'' + layer.name + '\'')
        return self

    def in_objects(self):
        self.__criteria.add('INOBJECT')
        return self

    def in_symbols(self):
        self.__criteria.add('INSYMBOL')
        return self

    def get(self) -> set:
        """Get all objects that meet the criteria set.

        :rtype: set(AbstractKeyedObject)
        """
        objects = set()
        vs.ForEachObject(
            lambda h: objects.add(ObjectRepository().get(h)),
            ' & '.join('(%s)' % c for c in self.__criteria))
        return objects
