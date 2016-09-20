"""The DLibrary package, which serves as OOP wrapper around vs calls, to make plugin development way easier.

This file should contain only setup stuff, and will only be executed once when VW starts up.
"""
from dlibrary.document import HatchVectorFill, TileVectorFill, ImageVectorFill, GradientVectorFill, Clazz, LineStyle, \
    SymbolDefinition, RecordDefinition
from dlibrary.object import Rectangle, Locus, Symbol, Group, PluginObject
from dlibrary.object_base import ObjectRepository, ObjectTypeEnum

__author__ = 'Dieter Geerts <dieter@dworks.be>'
__version__ = '2017.0.0'
__license__ = 'MIT'

ObjectRepository().register(ObjectTypeEnum.HATCH_FILL_DEFINITION, HatchVectorFill)
ObjectRepository().register(ObjectTypeEnum.TILE_FILL_DEFINITION, TileVectorFill)
ObjectRepository().register(ObjectTypeEnum.IMAGE_FILL_DEFINITION, ImageVectorFill)
ObjectRepository().register(ObjectTypeEnum.GRADIENT_FILL_DEFINITION, GradientVectorFill)
ObjectRepository().register(ObjectTypeEnum.LINE_STYLE_DEFINITION, LineStyle)
ObjectRepository().register(ObjectTypeEnum.CLASS_DEFINITION, Clazz)
ObjectRepository().register(ObjectTypeEnum.RECORD_DEFINITION, RecordDefinition)
ObjectRepository().register(ObjectTypeEnum.SYMBOL_DEFINITION, SymbolDefinition)
ObjectRepository().register(ObjectTypeEnum.LOCUS, Locus)
ObjectRepository().register(ObjectTypeEnum.RECTANGLE, Rectangle)
ObjectRepository().register(ObjectTypeEnum.GROUP, Group)
ObjectRepository().register(ObjectTypeEnum.SYMBOL, Symbol)
ObjectRepository().register(ObjectTypeEnum.PLUGIN_OBJECT, PluginObject)
