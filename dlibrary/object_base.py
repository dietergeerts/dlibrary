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
    GRADIENT_FILL_DEFINITION = 120
    IMAGE_FILL_DEFINITION = 119
    LINE_STYLE_DEFINITION = 96
    CLASS_DEFINITION = 94
    SYMBOL_DEFINITION = 16
    LOCUS = 17
    RECTANGLE = 3
    GROUP = 11
    SYMBOL = 15
    PLUGIN_OBJECT = 86

    @staticmethod
    def get(handle_or_name) -> int:
        """Gets the object type based on the handle or name.
        In VW, both are keys, but name isn't always provided. Also, some vs calls work with handles, others with names.

        :type handle_or_name: vs.Handle | str
        :returns: None if the handle or name doesn't references an actual object.
        """
        return vs.GetTypeN(vs.GetObject(handle_or_name) if isinstance(handle_or_name, str) else handle_or_name)
        # vs.GetObject will return None if not found, vs.GetTypeN will return 0 for None!


class AbstractKeyedObject(object, metaclass=ABCMeta):
    """Base class for all objects, which will hold the identifiers for a VW object: handle and/or name.
    """

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        # The name can be changed during script execution, the handle can't!
        # So we only save the handle, gotten by the parameter, or found by it's name!
        self.__handle = handle_or_name if not isinstance(handle_or_name, str) else vs.GetObject(handle_or_name)

    @property
    def handle(self) -> vs.Handle:
        """:rtype: vs.Handle"""
        return self.__handle

    @property
    def name(self) -> str:
        """:rtype: str"""
        name = vs.GetName(self.handle)
        return None if name == 'none' or name == '' else name

    def __hash__(self):
        """We need to override this, as we have custom object equality implemented!
        The Handle class isn't hashable, so we'll use the string representation instead.
        """
        return hash(str(self.handle))

    def __eq__(self, other):
        """Two objects are the same if they are from the same type and both have the same handle.
        The handle is what Vectorworks sees as the primary key for an object (which is session based!)
        """
        return isinstance(other, self.__class__) and self.handle == other.handle

    def __ne__(self, other):
        return not self.__eq__(other)


class ObjectRepository(object, metaclass=SingletonMeta):
    """Singleton to get our objects (wrappers) based on the handle or name, which are identifiers for VW.
    To work more easily with all objects in VW, we have specialized classes as kind of wrappers for the vs calls that
    can be done about the object. For easy retrieval, we have this factory, as we don't always know the type.
    """

    def __init__(self):
        self.__constructors = dict()

    def register(self, object_type: int, constructor):
        """Register an object constructor method, so it can be created and returned in the get method.
        This is done in the __init__ file of dlibrary, so all types are registered when loaded by VW.

        :type constructor: (vs.Handle | str) -> T <= AbstractKeyedObject
        """
        self.__constructors[object_type] = constructor

    def get(self, handle_or_name):
        """Get a wrapper object, based on the handle or name, which identifies the object in VW.
        If no constructor for the type is present, or the type can't be retrieved, None is returned.

        :type handle_or_name: vs.Handle | str
        :rtype: T <= AbstractKeyedObject
        """
        return self.__constructors.get(ObjectTypeEnum.get(handle_or_name), lambda h_o_n: None)(handle_or_name)

# TODO: create abstract record and field classes for use in the different record types (parameteric, ifc, normal)!?
