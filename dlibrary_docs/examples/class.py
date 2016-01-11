"""This is an example on how to work with class (definitions).
"""
from dlibrary import ObjectRepository, Clazz


def run():

    # Create a new class.
    clazz = Clazz.create('new-clazz-name')

    # Get the class by it's name.
    clazz = ObjectRepository().get('clazz-name')
    if clazz is None or not isinstance(clazz, Clazz):
        return
