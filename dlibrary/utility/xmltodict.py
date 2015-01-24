from collections import OrderedDict
import dlibrary.libs.xmltodict as xmltodict


def load(path: str, list_elements: set):
    try:
        with open(path) as file: return __correct(xmltodict.parse(file.read()), list_elements)
    except FileNotFoundError: raise
    except PermissionError: raise
    except OSError: raise
    # TODO: Check contents of file with an xml schema?


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
            for element in elements[name]: __correct(element)
        else: __correct(elements[name])
    return elements