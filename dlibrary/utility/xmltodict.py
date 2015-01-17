from collections import OrderedDict


def correct_elements(elements: dict) -> dict:
    # If there is only one control, we don't get a list but an OrderedDict instead!
    if 'control' in elements:
        if isinstance(elements['control'], OrderedDict): elements['control'] = [elements['control']]

    for name in (k for k in elements.keys() if k[:1] != '@' and k[:1] != '#'):

        # If an element has nothing, we don't get a dict, but None instead!
        if elements[name] is None: elements[name] = {}

        # If an element only has an inner text, we don't get a dict, but a str instead!
        if isinstance(elements[name], str): elements[name] = {'#text': elements[name]}

        # An element can be a list if there where multiple, or the actual element itself!
        if isinstance(elements[name], list):
            for element in elements[name]: correct_elements(element)
        else:
            correct_elements(elements[name])
    return elements

def filter_elements(element: dict) -> dict:
    return {k: v for k, v in element.items() if k[:1] != '@' and k[:1] != '#'}