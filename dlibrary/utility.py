from abc import ABCMeta, abstractmethod
from collections import UserList
from dlibrary.libs import xmltodict as xmltodict


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args)
        return cls._instances[cls]


class Event(object):

    def __init__(self):
        self.__handlers = set()

    def subscribe(self, handler: callable):
        if handler not in self.__handlers:
            self.__handlers.add(handler)

    def unsubscribe(self, handler: callable):
        if handler in self.__handlers:
            self.__handlers.remove(handler)

    def raise_event(self, *args, **kwargs):
        for handler in self.__handlers:
            handler(*args, **kwargs)


class XmlDict(object, metaclass=SingletonMeta):

    @staticmethod
    def get_elements(element: dict) -> dict:
        return {k: v for k, v in element.items() if k[:1] != '@' and k[:1] != '#'}

    @staticmethod
    def get_element_keys(element: dict) -> set:
        return (k for k in element.keys() if k[:1] != '@' and k[:1] != '#')


class AbstractXmlFile(object, metaclass=ABCMeta):
    """
    Class used for setting up files with properties through decorators. This way, plugins can decide how their xml
    files will behave by just setting the appropriate decorators, as these settings can be plugin version dependant.
    Loading will correct xmltodict output, so we can expect always the same things:
        - If an element has nothing (empty), xmltodict gives back None, we prefer an empty dict.
        - If an element has only inner text, xmltodict gives back a str, we prefer a dict with #text.
    So the contents will start with a dict and contains only dicts and lists down the road with no lists in lists!
    """

    def __init__(self, path: str):
        self.__path = path

    @property
    def path(self) -> str:
        return self.__path

    def load(self, create_if_not_found: bool=False) -> dict:
        try:
            with open(self.path) as file:
                return self.__correct(xmltodict.parse(file.read()))
        except FileNotFoundError:
            if create_if_not_found:
                return dict()
            else:
                raise
        except (PermissionError, OSError):
            raise

    def save(self, content: dict):
        try:
            with open(self.path, 'w') as file:
                xmltodict.unparse(content, file)
        except (FileNotFoundError, PermissionError, OSError):
            raise

    def __correct(self, elements: dict) -> dict:
        for name in XmlDict.get_element_keys(elements):

            # An element can be a dict (or OrderedDict), then correct that element!
            if isinstance(elements[name], dict):
                elements[name] = self.__correct(elements[name])

            # It can be a list instead if there where multiple, so correct every item! List in list can't happen!
            elif isinstance(elements[name], list):
                elements[name] = [self.__correct(element) if isinstance(element, dict) else
                                  self.__correct_element(element) for element in elements[name]]

            # If no dict and no list, then it will be None or a str, which must be corrected!
            else:
                elements[name] = self.__correct_element(elements[name])

        return elements

    @staticmethod
    def __correct_element(element):
        # If an element has nothing, we don't get a dict, but None instead!
        # If an element only has an inner text, we don't get a dict, but a str instead!
        return {} if element is None else {'#text': element} if isinstance(element, str) else element


class XmlFileVersioning(object):
    """
    Decorator to facilitate xml file versioning and to convert to the latest version if needed.
    """

    def __init__(self, converters: dict):
        """
        :type converters: dict {int: callable}, which represents version number and converter from previous version.
        """
        self.__converters = converters

    def __call__(self, cls):
        original_load = cls.load
        original_save = cls.save

        def load_with_versioning(*args, **kwargs):
            return self.__apply(original_load(*args, **kwargs), self.__converters)

        def save_with_versioning(self_ref, content: dict):
            return original_save(self_ref, self.__set_version(content, self.__converters))

        cls.load = load_with_versioning
        cls.save = save_with_versioning
        return cls

    def __apply(self, content: dict, converters: dict) -> dict:
        # First find the content version, or 0 if non is set.
        root_element = self.__get_root(content)
        content_version = root_element['@version'] if '@version' in root_element else 0

        # Then go through the versions list and apply converters if needed.
        for version in sorted([version for version in converters.keys()]):
            content = converters[version](content) if version > content_version else content

        return content

    def __set_version(self, content: dict, converters: dict) -> dict:
        self.__get_root(content)['@version'] = sorted([version for version in converters.keys()], reverse=True)[0]
        return content

    @staticmethod
    def __get_root(content: dict) -> dict:
        return content[[k for k in content.keys()][0]]


class XmlFileLists(object):
    """
    Decorator to correct the contents of an xml file, so that we got actual lists where we expect them.
    Else, xmltodict will set different types for it depending on how many times it appears in the file.
    """

    def __init__(self, lists: set):
        self.__lists = lists

    def __call__(self, cls):
        original_load = cls.load

        def load_with_lists(*args, **kwargs):
            return self.__apply(original_load(*args, **kwargs), self.__lists)

        cls.load = load_with_lists
        return cls

    def __apply(self, elements: dict, lists: set) -> dict:
        for name in XmlDict.get_element_keys(elements):

            # If an element is a list, then we check each item, which will be a dict!
            if isinstance(elements[name], list):
                elements[name] = [self.__apply(element, lists) for element in elements[name]]

            # If there is only one of an element, we don't get a list but an OrderedDict or dict instead!
            # So for elements we can have a list of, we will make it a list instead, or just leave the dict!
            elif isinstance(elements[name], dict):
                elements[name] = self.__apply(elements[name], lists)
                elements[name] = [elements[name]] if name in lists else elements[name]

        return elements


class XmlFileDefaults(object):
    """
    Decorator to specify default values for items, so they can be applied if no value is present.
    """

    def __init__(self, defaults: dict):
        self.__defaults = defaults

    def __call__(self, cls):
        original_load = cls.load

        def load_with_defaults(*args, **kwargs):
            return self.__apply(original_load(*args, **kwargs), self.__defaults)

        cls.load = load_with_defaults
        return cls

    def __apply(self, elements: dict, defaults: dict) -> dict:
        for name in defaults.keys():

            # The default value could be a dict, with it's own possible defaults.
            if isinstance(defaults[name], dict):
                elements[name] = self.__apply(elements[name] if name in elements else dict(), defaults[name])

            # The default value could be a list, with a possible dict to set defaults.
            elif isinstance(defaults[name], list):
                elements[name] = [self.__apply(element, defaults[name][0]) if len(defaults[name]) == 1 else element
                                  for element in (elements[name] if name in elements else [])]

            # The default value will be a text otherwise.
            elif name not in elements:
                elements[name] = defaults[name]

        return elements


class AbstractViewModel(object):
    def __init__(self, model: object):
        self.__model = model

    @property
    def model(self) -> object:
        return self.__model


class ObservableField(object):
    def __init__(self, default_value=None):
        self.__value = default_value
        self.__field_changed_event = Event()

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if self.__value != value:
            old_value = self.__value
            self.__value = value
            self._on_value_changed(old_value, value)
            self.__field_changed_event.raise_event(old_value, value)

    @property
    def field_changed_event(self) -> Event:
        return self.__field_changed_event

    def _on_value_changed(self, old, new):
        pass


class LinkedObservableField(ObservableField):
    def __init__(self, model: dict, key: str):
        super().__init__(model[key])
        self.__model = model
        self.__key = key

    def _on_value_changed(self, old, new):
        self.__model[self.__key] = new


class ObservableList(UserList):
    def __init__(self, default_list=None):
        super().__init__(default_list)
        self.__raise_events = True
        self.__suspended_state = None
        self.__list_changed_event = Event()
        self.__list_reordered_event = Event()

    @property
    def list_changed_event(self) -> Event:
        return self.__list_changed_event

    @property
    def list_reordered_event(self) -> Event:
        return self.__list_reordered_event

    def suspend_events(self):
        self.__raise_events = False
        self.__suspended_state = tuple(self.data)

    def resume_events(self):
        self.__raise_events = True
        # noinspection PyTypeChecker
        self.__raise_event_if_changed(self.__suspended_state, self.data)
        self.__suspended_state = None

    def __raise_event_if_changed(self, suspended: tuple, current: list):
        if suspended != current:
            if len(suspended) == len(current) and all(item in current for item in suspended):
                self.__list_reordered_event.raise_event()
            else:
                self.__list_changed_event.raise_event(
                    {index: item for index, item in enumerate(suspended) if item not in current},
                    {index: item for index, item in enumerate(current) if item not in suspended})

    def __setitem__(self, i, item):
        old_item = self.data[i]
        super().__setitem__(i, item)
        if self.__raise_events:
            self.__list_changed_event.raise_event({i: old_item}, {i: item})

    def __delitem__(self, i):
        old_item = self.data[i]
        super().__delitem__(i)
        if self.__raise_events:
            self.__list_changed_event.raise_event({i: old_item}, {})

    def __iadd__(self, other):
        si = len(self.data)
        super().__iadd__(other)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {si+i: item for i, item in enumerate(other)})
        return self

    def append(self, item):
        index = len(self.data)
        super().append(item)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {index: item})

    def insert(self, i, item):
        super().insert(i, item)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {i: item})

    def pop(self, i=-1):
        item = super().pop(i)
        if self.__raise_events:
            self.__list_changed_event.raise_event({(len(self.data) if i == -1 else i): item}, {})
        return item

    def remove(self, item):
        index = self.data.index(item)
        super().remove(item)
        if self.__raise_events:
            self.__list_changed_event.raise_event({index: item}, {})

    def clear(self):
        items = list(self.data)
        super().clear()
        if self.__raise_events:
            self.__list_changed_event.raise_event({i: item for i, item in enumerate(items)}, {})

    def index(self, item, *args):
        try:
            return super().index(item, *args)
        except ValueError:
            return -1

    def reverse(self):
        super().reverse()
        if self.__raise_events:
            self.__list_reordered_event.raise_event()

    def sort(self, *args, **kwds):
        super().sort(*args, **kwds)
        if self.__raise_events:
            self.__list_reordered_event.raise_event()

    def extend(self, other):
        si = len(self.data)
        super().extend(other)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {si+i: item for i, item in enumerate(other)})


class LinkedObservableList(ObservableList):
    def __init__(self, model_list: list, pack: callable, unpack: callable):
        super().__init__(pack(model) for model in model_list)
        self.__model_list = model_list
        self.__pack = pack
        self.__unpack = unpack

    def __setitem__(self, i, item):
        super().__setitem__(i, item)
        self.__model_list[i] = self.__unpack(item)

    def __delitem__(self, i):
        super().__delitem__(i)
        del self.__model_list[i]

    def __iadd__(self, other):
        if isinstance(other, UserList):
            self.__model_list += (self.__unpack(item) for item in other.data)
        elif isinstance(other, type(self.data)):
            self.__model_list += (self.__unpack(item) for item in other)
        else:
            self.__model_list += (self.__unpack(item) for item in list(other))
        return super().__iadd__(other)

    def __imul__(self, n):
        self.__model_list *= n
        return super().__imul__(n)

    def append(self, item):
        super().append(item)
        self.__model_list.append(self.__unpack(item))

    def insert(self, i, item):
        super().insert(i, item)
        self.__model_list.insert(i, self.__unpack(item))

    def pop(self, i=-1):
        self.__model_list.pop(i)
        return super().pop(i)

    def remove(self, item):
        super().remove(item)
        self.__model_list.remove(self.__unpack(item))

    def clear(self):
        super().clear()
        self.__model_list.clear()

    def reverse(self):
        super().reverse()
        self.__model_list.reverse()

    def sort(self, *args, **kwds):
        super().sort(*args, **kwds)
        self.__model_list.sort(*args, **kwds)

    def extend(self, other):
        super().extend(other)
        if isinstance(other, UserList):
            self.__model_list.extend(self.__unpack(item) for item in other.data)
        else:
            self.__model_list.extend(self.__unpack(item) for item in other)


class AbstractObservableWithDependencies(object, metaclass=ABCMeta):
    def __init__(self, dependant_observables: list=None):
        if dependant_observables is not None:
            self.__subscribe_to_dependant_observables(dependant_observables)

    def __subscribe_to_dependant_observables(self, dependant_observables: list):
        for observable in dependant_observables:
            if isinstance(observable, ObservableField):
                observable.field_changed_event.subscribe(self._on_dependencies_changed)
            elif isinstance(observable, ObservableList):
                observable.list_changed_event.subscribe(self._on_dependencies_changed)
                observable.list_reordered_event.subscribe(self._on_dependencies_changed)

    @abstractmethod
    def _on_dependencies_changed(self, *args, **kwargs):
        raise NotImplementedError


class ObservableMethod(AbstractObservableWithDependencies):
    def __init__(self, method: callable, dependant_observables: list=None):
        super().__init__(dependant_observables)
        self.__method = method
        self.__method_changed_event = Event()

    @property
    def method_changed_event(self) -> Event:
        return self.__method_changed_event

    def apply(self, *args):
        self.__method(*args)

    # noinspection PyUnusedLocal
    def _on_dependencies_changed(self, *args, **kwargs):
        self.__method_changed_event.raise_event()


class ObservableCommand(AbstractObservableWithDependencies):
    def __init__(self, execute: callable, can_execute: callable=None, dependant_observables: list=None):
        super().__init__(dependant_observables)
        self.__execute = execute
        self.__can_execute = can_execute
        self.__can_execute_changed_event = Event()

    @property
    def can_execute_changed_event(self) -> Event:
        return self.__can_execute_changed_event

    def can_execute(self):
        return self.__can_execute() if self.__can_execute is not None else True

    def execute(self):
        if self.can_execute():
            self.__execute()

    # noinspection PyUnusedLocal
    def _on_dependencies_changed(self, *args, **kwargs):
        self.__can_execute_changed_event.raise_event()


class ViewModelList(object):
    # noinspection PyDefaultArgument
    def __init__(self, model_list: list, abstract_view_model: callable, create_new_model: callable,
                 can_add_new_model: callable=None, can_add_dependent_property_observables: set={}):
        self.__items = LinkedObservableList(model_list, abstract_view_model, lambda view_model: view_model.model)
        self.__selected_items = ObservableList()
        self.__abstract_view_model = abstract_view_model
        self.__create_new_model = create_new_model
        self.__can_add_new_model = can_add_new_model
        self.__can_add_dependency = ObservableField()
        self.__can_add_dependencies = can_add_dependent_property_observables
        self.__new_item = ObservableField()
        # noinspection PyTypeChecker
        self.__add_item = ObservableCommand(self.__on_add_item, self.__can_add_item, {self.__can_add_dependency})
        self.__setup_new_item()

    @property
    def items(self) -> ObservableList:
        return self.__items

    @property
    def selected_items(self) -> ObservableList:
        return self.__selected_items

    @property
    def new_item(self) -> ObservableField:
        return self.__new_item

    @property
    def add_item(self) -> ObservableCommand:
        return self.__add_item

    def __can_add_item(self):
        return self.__can_add_new_model(self.new_item.value.model) if self.__can_add_new_model is not None else True

    def __on_add_item(self):
        self.items.append(self.new_item.value)
        self.__setup_new_item()

    def __setup_new_item(self):
        if self.new_item.value:
            self.__unsubscribe_to_dependencies(self.new_item.value)
        self.new_item.value = self.__abstract_view_model(self.__create_new_model())
        self.__subscribe_to_dependencies(self.new_item.value)
        self.__on_new_item_dependency_changed()  # To reset check with the new item!

    def __subscribe_to_dependencies(self, view_model: AbstractViewModel):
        for dependency in self.__can_add_dependencies:
            observable = getattr(view_model, dependency)
            if isinstance(observable, ObservableField):
                observable.field_changed_event.subscribe(self.__on_new_item_dependency_changed)
            elif isinstance(observable, ObservableList):
                observable.list_changed_event.subscribe(self.__on_new_item_dependency_changed)
                observable.list_reordered_event.subscribe(self.__on_new_item_dependency_changed)

    def __unsubscribe_to_dependencies(self, view_model: AbstractViewModel):
        for dependency in self.__can_add_dependencies:
            observable = getattr(view_model, dependency)
            if isinstance(observable, ObservableField):
                observable.field_changed_event.unsubscribe(self.__on_new_item_dependency_changed)
            elif isinstance(observable, ObservableList):
                observable.list_changed_event.unsubscribe(self.__on_new_item_dependency_changed)
                observable.list_reordered_event.unsubscribe(self.__on_new_item_dependency_changed)

    # noinspection PyUnusedLocal
    def __on_new_item_dependency_changed(self, *args, **kwargs):
        self.__can_add_dependency.field_changed_event.raise_event()


class VSException(BaseException):
    def __init__(self, function: str):
        self.__function = function


class AbstractPropertyClassDecorator(object, metaclass=ABCMeta):
    """
    Abstract base class for class decorators which adds a property to the class.
    """
    __get_property_name_name = '__get_property_name'  # Needs to be a function for class method access.

    def __init__(self, property_value):
        setattr(type(self), self.__get_property_name_name, lambda *args: 'at_%s' % type(self).__name__.lower())
        self.__property_value = property_value

    def __call__(self, cls):
        setattr(cls, getattr(self, self.__get_property_name_name)(), property(lambda v: self.__property_value))
        return cls

    @classmethod
    def has_decorator(cls, obj: object):
        return hasattr(obj, getattr(cls, cls.__get_property_name_name)())

    @classmethod
    def _get_property_value(cls, obj: object):
        return getattr(obj, getattr(cls, cls.__get_property_name_name)())


class Convert(object, metaclass=SingletonMeta):

    @staticmethod
    def str2bool(value: str) -> bool:
        return value.lower() in ('true', 'yes', 'y', '1')


class Math(object):

    @staticmethod
    def float_equal(float_a: float, float_b: float) -> bool:
        return abs(float_a - float_b) < 0.000001  # VW stores up to 6 digits in some situations!

    @staticmethod
    def point_equal(point_a: tuple, point_b: tuple) -> bool:
        return Math.float_equal(point_a[0], point_b[0]) and Math.float_equal(point_a[1], point_b[1])
