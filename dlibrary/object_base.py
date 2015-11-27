"""Used for all base stuff concerning objects, which are also resources, class definitions, etc....
"""
from abc import ABCMeta
from dlibrary.utility import SingletonMeta
import vs


class ObjectTypeEnum(object):
    """Holds all object type constants in human readable/understandable names.
    """

    NONE = 0
    HATCH_FILL_DEFINITION = 66
    TILE_FILL_DEFINITION = 108
    IMAGE_FILL_DEFINITION = 119
    GRADIENT_FILL_DEFINITION = 120

    @staticmethod
    def get(handle_or_name) -> int:
        """Gets the object type based on the handle or name.
        In VW, both are keys, but name isn't always provided. Also, some vs calls work with handles, others with names.

        :type handle_or_name: handle|str
        """
        return vs.GetTypeN(vs.GetObject(handle_or_name) if isinstance(handle_or_name, str) else handle_or_name)
        # vs.GetObject will return None if not found, vs.GetTypeN will return 0 for None!


class ObjectRepository(object, metaclass=SingletonMeta):
    """Singleton to get our objects (wrappers) based on the handle or name, which are identifiers for VW.
    To work more easily with all objects in VW, we have specialized classes as kind of wrappers for the vs calls that
    can be done about the object. For easy retrieval, we have this factory, as we don't always know the type.
    """

    def __init__(self):
        self.__constructors = dict()

    def register(self, object_type: int, constructor: callable):
        """Register an object constructor method, so it can be created and returned in the get method.
        """
        self.__constructors[object_type] = constructor

    def get(self, handle_or_name) -> AbstractObjectKey:
        """Get a wrapper object, based on the handle or name, which identifies the object in VW.
        If no constructor for the type is present, or the type can't be retrieved, None is returned.

        :type handle_or_name: handle|str
        """
        self.__constructors.get(ObjectTypeEnum.get(handle_or_name), lambda h_o_n: None)(handle_or_name)


class AbstractObjectKey(object, metaclass=ABCMeta):
    """Base class for all objects, which will hold the identifiers for a VW object: handle and/or name.
    """

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: handle|str
        """
        self.__handle = handle_or_name if not isinstance(handle_or_name, str) else vs.GetObject(handle_or_name)
        self.__name = handle_or_name if isinstance(handle_or_name, str) else vs.GetName(handle_or_name)

    @property
    def handle(self):
        return self.__handle

    @property
    def name(self) -> str:
        return self.__name
