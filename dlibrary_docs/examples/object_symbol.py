"""This is an example on how to work with symbol objects.
"""
from dlibrary import ObjectRepository, SymbolDefinition, Symbol


def run():

    # Get the symbol definition you want to use to create your symbol from.
    symbol_definition = ObjectRepository().get('name_of_symbol_definition')
    if symbol_definition is None or not isinstance(symbol_definition, SymbolDefinition):
        return

    # Create a symbol instance based on the symbol definition.
    # You can use length strings to define the insertion point like '10cm' instead of 10.
    symbol = Symbol.create(symbol_definition, (10, 20), 0)
