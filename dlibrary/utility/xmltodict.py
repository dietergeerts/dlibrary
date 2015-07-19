from abc import ABCMeta

import dlibrary.libs.xmltodict as xmltodict


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
        for name in (k for k in elements.keys() if k[:1] != '@' and k[:1] != '#'):

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
        for name in (k for k in elements.keys() if k[:1] != '@' and k[:1] != '#'):

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


def filter_elements(element: dict) -> dict:
    return {k: v for k, v in element.items() if k[:1] != '@' and k[:1] != '#'}
