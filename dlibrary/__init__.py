from dlibrary.document import HatchVectorFill, TileVectorFill, ImageVectorFill, GradientVectorFill, Clazz, LineStyle, \
    SymbolDefinition
from dlibrary.object import Rectangle
from dlibrary.object_base import ObjectRepository, ObjectTypeEnum

__author__ = 'Dieter Geerts <dieter@dworks.be>'
__version__ = '2016.4.0'
__license__ = 'MIT'

ObjectRepository().register(ObjectTypeEnum.HATCH_FILL_DEFINITION, HatchVectorFill)
ObjectRepository().register(ObjectTypeEnum.TILE_FILL_DEFINITION, TileVectorFill)
ObjectRepository().register(ObjectTypeEnum.IMAGE_FILL_DEFINITION, ImageVectorFill)
ObjectRepository().register(ObjectTypeEnum.GRADIENT_FILL_DEFINITION, GradientVectorFill)
ObjectRepository().register(ObjectTypeEnum.LINE_STYLE_DEFINITION, LineStyle)
ObjectRepository().register(ObjectTypeEnum.CLASS_DEFINITION, Clazz)
ObjectRepository().register(ObjectTypeEnum.SYMBOL_DEFINITION, SymbolDefinition)
ObjectRepository().register(ObjectTypeEnum.RECTANGLE, Rectangle)
