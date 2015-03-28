from collections import OrderedDict
import os
import dlibrary.libs.xmltodict as xmltodict


def load(path: str, list_elements: set, defaults: dict):
    try:
        with open(path) as file: return __set_defaults(__correct(xmltodict.parse(file.read()), list_elements), defaults)
    except (FileNotFoundError, PermissionError, OSError): raise
    # TODO: Check contents of file with an xml schema?


def load_or_create_if_not_found(path: str, list_elements: set, defaults: dict):
    try:
        if os.path.isfile(path): return load(path, list_elements, defaults)
        else: return __set_defaults(dict(), defaults)
    except (FileNotFoundError, PermissionError, OSError): raise


def save(elements: dict, path: str): xmltodict.unparse(elements, path)


def filter_elements(element: dict) -> dict:
    return {k: v for k, v in element.items() if k[:1] != '@' and k[:1] != '#'}


def __correct(elements: dict, list_elements: set) -> dict:
    for name in (k for k in elements.keys() if k[:1] != '@' and k[:1] != '#'):
        # If an element has nothing, we don't get a dict, but None instead!
        if elements[name] is None: elements[name] = {}
        # If an element only has an inner text, we don't get a dict, but a str instead!
        if isinstance(elements[name], str): elements[name] = {'#text': elements[name]}
        # If there is only one of an element, we don't get a list but an OrderedDict instead!
        # So for elements we can have a list, we will make it a list instead!
        if isinstance(elements[name], OrderedDict) and name in list_elements: elements[name] = [elements[name]]
        # An element can be a list if there where multiple, or the actual element itself!
        if isinstance(elements[name], list):
            for element in elements[name]: __correct(element, list_elements)
        else: __correct(elements[name], list_elements)
    return elements


def __set_defaults(elements: dict, defaults: dict=None) -> dict:
    for name in defaults.keys():
        # The default value could be a dict, with it's own possible defaults.
        if isinstance(defaults[name], dict):
            if not name in elements: elements[name] = dict()
            __set_defaults(elements[name], defaults[name])
        # The default value could be a list, with a possible dict to set defaults.
        elif isinstance(defaults[name], list):
            if not name in elements: elements[name] = []
            elif len(defaults[name]) == 1:
                for element in elements[name]: __set_defaults(element, defaults[name][0])
        # The default value will be a text otherwise.
        elif not name in elements: elements[name] = defaults[name]
    return elements