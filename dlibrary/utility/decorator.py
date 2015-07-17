from abc import ABCMeta


class AbstractPropertyClassDecorator(object, metaclass=ABCMeta):
    """
    Abstract base class for class decorators which adds a property to the class.
    """
    __get_property_name_name = '__get_property_name'  # Needs to be a function for class method access.

    def __init__(self, property_value):
        setattr(type(self), self.__get_property_name_name, lambda *args: 'at_%s' % type(self).__name__.lower())
        self.__property_value = property_value

    def __call__(self, cls):
        setattr(cls, getattr(self, self.__get_property_name_name)(), property(lambda _: self.__property_value))
        return cls

    @classmethod
    def has_decorator(cls, control: object):
        return hasattr(control, getattr(cls, cls.__get_property_name_name)())

    @classmethod
    def _get_property_value(cls, control: object):
        return getattr(control, getattr(cls, cls.__get_property_name_name)())
