"""This is an example on how to work with symbol definitions.
"""
from dlibrary import ObjectRepository, SymbolDefinition


def run():

    # Get the symbol definition by it's name.
    symbol_definition = ObjectRepository().get('symbol-name')
    if symbol_definition is None or not isinstance(symbol_definition, SymbolDefinition):
        return
