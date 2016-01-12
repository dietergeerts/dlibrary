from unittest import TestCase

from dlibrary import ObjectTypeEnum, HatchVectorFill, TileVectorFill, ImageVectorFill, GradientVectorFill, Clazz, \
    LineStyle, SymbolDefinition
from dlibrary.object import Line, Rectangle, Locus, Symbol
from dlibrary.object_base import AbstractKeyedObject, ObjectRepository
import vs


class ObjectTypeEnumTest(TestCase):

    def test_none_object_type(self):
        """A non-existing handle or name should return NONE as object type.
        """
        # noinspection PyTypeChecker
        self.assertIs(ObjectTypeEnum.get(None), ObjectTypeEnum.NONE)
        self.assertIs(ObjectTypeEnum.get(''), ObjectTypeEnum.NONE)

    def test_hatch_fill_definition_object_type(self):
        # TODO: Replace creation by our own when implemented.
        vs.BeginVectorFillN('[LA] TEST', False, False, 0)
        vs.AddVectorFillLayer(0, 0, 1, 1, .25, -.25, .7, 3, 255)
        vs.EndVectorFill()
        hatch_fill = HatchVectorFill('[LA] TEST')
        self.assertIs(ObjectTypeEnum.get(hatch_fill.handle), ObjectTypeEnum.HATCH_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(hatch_fill.name), ObjectTypeEnum.HATCH_FILL_DEFINITION)
        # TODO: Replace deletion by our own when implemented.
        vs.DelVectorFill(hatch_fill.name)

    def test_tile_fill_definition_object_type(self):
        # TODO: Replace creation by our own when implemented.
        tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        self.assertIs(ObjectTypeEnum.get(tile_fill.handle), ObjectTypeEnum.TILE_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(tile_fill.name), ObjectTypeEnum.TILE_FILL_DEFINITION)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(tile_fill.handle)

    def test_image_fill_definition_object_type(self):
        # TODO: Replace creation by our own when implemented.
        # TODO: For some reason, it didn't work to create an image fill.
        # TODO: We'll investigate later, I'll add it to the doc for now.
        image_fill = ImageVectorFill('[AB] TEST')
        self.assertIs(ObjectTypeEnum.get(image_fill.handle), ObjectTypeEnum.IMAGE_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(image_fill.name), ObjectTypeEnum.IMAGE_FILL_DEFINITION)
        # TODO: Replace deletion by our own when implemented.
        # TODO: Delete image fill once we can create it.
        # TODO: vs.DelObject(cls.__image_fill_definition.handle)

    def test_gradient_fill_definition_object_type(self):
        # TODO: Replace creation by our own when implemented.
        gradient_fill = GradientVectorFill(vs.CreateGradient('[VL] TEST'))
        self.assertIs(ObjectTypeEnum.get(gradient_fill.handle), ObjectTypeEnum.GRADIENT_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(gradient_fill.name), ObjectTypeEnum.GRADIENT_FILL_DEFINITION)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(gradient_fill.handle)

    def test_line_style_definition_object_type(self):
        # TODO: Replace creation by our own when implemented.
        # TODO: Can't find functions to create line styles, add later. Added to doc now.
        line_style = LineStyle('[LS] test')
        self.assertIs(ObjectTypeEnum.get(line_style.handle), ObjectTypeEnum.LINE_STYLE_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(line_style.name), ObjectTypeEnum.LINE_STYLE_DEFINITION)
        # TODO: Replace deletion by our own when implemented.
        # TODO: Delete line style once we can create it.

    def test_clazz_definition_object_type(self):
        clazz = Clazz.create('TEST')
        self.assertIs(ObjectTypeEnum.get(clazz.handle), ObjectTypeEnum.CLASS_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(clazz.name), ObjectTypeEnum.CLASS_DEFINITION)
        # TODO: Replace deletion by our own when implemented.
        vs.DelClass(clazz.name)

    def test_symbol_definition_object_type(self):
        # TODO: Replace creation by our own when implemented.
        vs.BeginSym('TEST SYMBOL')
        Line.create((0, 0), (1, 1))
        vs.EndSym()
        symbol_definition = SymbolDefinition('TEST SYMBOL')
        self.assertIs(ObjectTypeEnum.get(symbol_definition.handle), ObjectTypeEnum.SYMBOL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(symbol_definition.name), ObjectTypeEnum.SYMBOL_DEFINITION)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(symbol_definition.handle)

    def test_locus_object_type(self):
        locus = Locus.create((0, 0))
        # TODO: Set name through property, once implemented.
        vs.SetName(locus.handle, 'LOCUS TEST')
        self.assertIs(ObjectTypeEnum.get(locus.handle), ObjectTypeEnum.LOCUS)
        self.assertIs(ObjectTypeEnum.get(locus.name), ObjectTypeEnum.LOCUS)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(locus.handle)

    def test_rectangle_object_type(self):
        rectangle = Rectangle.create((0, 0), (1, 0), 1, 1)
        # TODO: Set the name through the prop, once implemented.
        vs.SetName(rectangle.handle, 'RECTANGLE TEST')
        self.assertIs(ObjectTypeEnum.get(rectangle.handle), ObjectTypeEnum.RECTANGLE)
        self.assertIs(ObjectTypeEnum.get(rectangle.name), ObjectTypeEnum.RECTANGLE)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(rectangle.handle)

    def test_symbol_object_type(self):
        # TODO: Replace creation by our own when implemented.
        vs.BeginSym('TEST SYMBOL DEFINITION')
        Line.create((0, 0), (1, 1))
        vs.EndSym()
        symbol_definition = SymbolDefinition('TEST SYMBOL DEFINITION')
        symbol = Symbol.create(symbol_definition, (0, 0), 0)
        # TODO: Set the name through the prop, once implemented.
        vs.SetName(symbol.handle, 'SYMBOL TEST')
        self.assertIs(ObjectTypeEnum.get(symbol.handle), ObjectTypeEnum.SYMBOL)
        self.assertIs(ObjectTypeEnum.get(symbol.name), ObjectTypeEnum.SYMBOL)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(symbol.handle)
        vs.DelObject(symbol_definition.handle)


class TestKeyedObject(AbstractKeyedObject):

    def __init__(self, handle_or_name):
        """
        :type handle_or_name: vs.Handle | str
        """
        super().__init__(handle_or_name)


class AbstractKeyedObjectTest(TestCase):

    __tile_name = '[MO] TEST'
    __tile_handle = None
    __line_handle = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.
        cls.__tile_handle = vs.CreateTile(cls.__tile_name)
        vs.AddTileGeometryObject(cls.__tile_handle, Line.create((0, 0), (10, 10)).handle)
        cls.__line_handle = Line.create((0, 0), (10, 10)).handle

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__tile_handle)
        vs.DelObject(cls.__line_handle)

    def test_handle_from_handle(self):
        """When using the handle to create a wrapper, it should be gotten.
        """
        self.assertEqual(TestKeyedObject(self.__tile_handle).handle, self.__tile_handle)

    def test_name_from_handle(self):
        """When using the handle to create a wrapper, the name should be gotten.
        """
        self.assertEqual(TestKeyedObject(self.__tile_handle).name, self.__tile_name)

    def test_name_from_name(self):
        """When using the name to create a wrapper, it should be gotten.
        """
        self.assertEqual(TestKeyedObject(self.__tile_name).name, self.__tile_name)

    def test_handle_from_name(self):
        """When using the name to create a wrapper, the handle should be gotten.
        """
        self.assertEqual(TestKeyedObject(self.__tile_name).handle, self.__tile_handle)

    def test_none_name(self):
        """The handle is the primary key, and will always be there, but the name is optional, so can be None.
        """
        self.assertIsNone(TestKeyedObject(self.__line_handle).name)

    def test_equality(self):
        """Two objects are the same if their handles are the same.
        """
        self.assertEqual(TestKeyedObject(self.__tile_name), TestKeyedObject(self.__tile_name))
        self.assertEqual(TestKeyedObject(self.__tile_name), TestKeyedObject(self.__tile_handle))
        self.assertNotEqual(TestKeyedObject(self.__tile_name), TestKeyedObject(self.__line_handle))


class ObjectRepositoryTest(TestCase):

    def test_none_object(self):
        """A non-existing handle or name should return None.
        """
        # noinspection PyTypeChecker
        self.assertIsNone(ObjectRepository().get(None))
        self.assertIsNone(ObjectRepository().get(''))

    def test_hatch_vector_fill(self):
        # TODO: Replace creation by our own when implemented.
        vs.BeginVectorFillN('[LA] TEST', False, False, 0)
        vs.AddVectorFillLayer(0, 0, 1, 1, .25, -.25, .7, 3, 255)
        vs.EndVectorFill()
        hatch_fill = HatchVectorFill('[LA] TEST')
        self.assertIsInstance(ObjectRepository().get(hatch_fill.handle), HatchVectorFill)
        self.assertIsInstance(ObjectRepository().get(hatch_fill.name), HatchVectorFill)
        # TODO: Replace deletion by our own when implemented.
        vs.DelVectorFill(hatch_fill.name)

    def test_tile_vector_fill(self):
        # TODO: Replace creation by our own when implemented.
        tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        self.assertIsInstance(ObjectRepository().get(tile_fill.handle), TileVectorFill)
        self.assertIsInstance(ObjectRepository().get(tile_fill.name), TileVectorFill)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(tile_fill.handle)

    def test_image_vector_fill(self):
        # TODO: Replace creation by our own when implemented.
        # TODO: For some reason, it didn't work to create an image fill.
        # TODO: We'll investigate later, I'll add it to the doc for now.
        image_fill = ImageVectorFill('[AB] TEST')
        self.assertIsInstance(ObjectRepository().get(image_fill.handle), ImageVectorFill)
        self.assertIsInstance(ObjectRepository().get(image_fill.name), ImageVectorFill)
        # TODO: Replace deletion by our own when implemented.
        # TODO: Delete image fill once we can create it.
        # TODO: vs.DelObject(cls.__image_fill_definition.handle)

    def test_gradient_vector_fill(self):
        # TODO: Replace creation by our own when implemented.
        gradient_fill = GradientVectorFill(vs.CreateGradient('[VL] TEST'))
        self.assertIsInstance(ObjectRepository().get(gradient_fill.handle), GradientVectorFill)
        self.assertIsInstance(ObjectRepository().get(gradient_fill.name), GradientVectorFill)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(gradient_fill.handle)

    def test_line_style(self):
        # TODO: Replace creation by our own when implemented.
        # TODO: Can't find functions to create line styles, add later. Added to doc now.
        line_style = LineStyle('[LS] test')
        self.assertIsInstance(ObjectRepository().get(line_style.handle), LineStyle)
        self.assertIsInstance(ObjectRepository().get(line_style.name), LineStyle)
        # TODO: Replace deletion by our own when implemented.
        # TODO: Delete line style once we can create it.

    def test_clazz(self):
        clazz = Clazz.create('CLAZZ TEST')
        self.assertIsInstance(ObjectRepository().get(clazz.handle), Clazz)
        self.assertIsInstance(ObjectRepository().get(clazz.name), Clazz)
        # TODO: Replace deletion by our own when implemented.
        vs.DelClass(clazz.name)

    def test_symbol_definition(self):
        # TODO: Replace creation by our own when implemented.
        vs.BeginSym('TEST SYMBOL')
        Line.create((0, 0), (1, 1))
        vs.EndSym()
        symbol_definition = SymbolDefinition('TEST SYMBOL')
        self.assertIsInstance(ObjectRepository().get(symbol_definition.handle), SymbolDefinition)
        self.assertIsInstance(ObjectRepository().get(symbol_definition.name), SymbolDefinition)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(symbol_definition.handle)

    def test_locus(self):
        locus = Locus.create((0, 0))
        # TODO: Set name through property, once implemented.
        vs.SetName(locus.handle, 'LOCUS TEST')
        self.assertIsInstance(ObjectRepository().get(locus.handle), Locus)
        self.assertIsInstance(ObjectRepository().get(locus.name), Locus)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(locus.handle)

    def test_rectangle(self):
        rectangle = Rectangle.create((0, 0), (1, 0), 1, 1)
        # TODO: Set name through property, once implemented.
        vs.SetName(rectangle.handle, 'RECTANGLE TEST')
        self.assertIsInstance(ObjectRepository().get(rectangle.handle), Rectangle)
        self.assertIsInstance(ObjectRepository().get(rectangle.name), Rectangle)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(rectangle.handle)

    def test_symbol(self):
        # TODO: Replace creation by our own when implemented.
        vs.BeginSym('TEST SYMBOL DEFINITION')
        Line.create((0, 0), (1, 1))
        vs.EndSym()
        symbol_definition = SymbolDefinition('TEST SYMBOL DEFINITION')
        symbol = Symbol.create(symbol_definition, (0, 0), 0)
        # TODO: Set the name through the prop, once implemented.
        vs.SetName(symbol.handle, 'SYMBOL TEST')
        self.assertIsInstance(ObjectRepository().get(symbol.handle), Symbol)
        self.assertIsInstance(ObjectRepository().get(symbol.name), Symbol)
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(symbol.handle)
        vs.DelObject(symbol_definition.handle)
