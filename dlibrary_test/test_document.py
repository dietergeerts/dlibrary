from unittest import TestCase

from dlibrary.document import IAttributes, AbstractVectorFill, PatternFillEnum, TileVectorFill, IClazzAttributes, \
    IDocumentAttributes, HatchVectorFill, ImageVectorFill, GradientVectorFill, LineStyle, Clazz
from dlibrary.object import Line
import vs


class TestAttributes(IAttributes):

    def __init__(self):
        self.__pattern_fill = PatternFillEnum.NONE
        self.__vector_fill = None
        self.__pattern_line = PatternFillEnum.NONE
        self.__vector_line = None

    def _get_pattern_fill(self) -> int:
        return self.__pattern_fill

    def _set_pattern_fill(self, value: int):
        self.__pattern_fill = value
        self.__vector_fill = None

    def _get_vector_fill(self) -> AbstractVectorFill:
        return self.__vector_fill

    def _set_vector_fill(self, value: AbstractVectorFill):
        self.__vector_fill = value

    def _get_pattern_line(self) -> int:
        return self.__pattern_line

    def _set_pattern_line(self, value: int):
        self.__pattern_line = value

    def _get_vector_line(self):
        return self.__vector_line

    def _set_vector_line(self, value):
        self.__vector_line = value


class IAttributesTest(TestCase):

    __hatch_fill = None
    __tile_fill = None
    __image_fill = None
    __gradient_fill = None
    __line_style = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.
        vs.BeginVectorFillN('[LA] TEST', False, False, 0)
        vs.AddVectorFillLayer(0, 0, 1, 1, .25, -.25, .7, 3, 255)
        vs.EndVectorFill()
        cls.__hatch_fill = HatchVectorFill('[LA] TEST')
        cls.__tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(cls.__tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        # TODO: For some reason, it didn't work to create an image fill.
        # TODO: We'll investigate later, I'll add it to the doc for now.
        cls.__image_fill = ImageVectorFill('[AB] TEST')
        cls.__gradient_fill = GradientVectorFill(vs.CreateGradient('[VL] TEST'))
        # TODO: Can't find functions to create line styles, add later. Added to doc now.
        cls.__line_style = LineStyle('[LS] test')
        cls.__attributes = TestAttributes()

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__hatch_fill.handle)
        vs.DelObject(cls.__tile_fill.handle)
        # TODO: Delete image fill once we can create it.
        # TODO: vs.DelObject(cls.__image_fill_definition.handle)
        vs.DelObject(cls.__gradient_fill.handle)
        # TODO: Delete line style once we can create it.

    def test_set_pattern_fill_and_get(self):
        """Setting a pattern fill should give the same back.
        """
        self.__attributes.fill = PatternFillEnum.BACKGROUND_COLOR
        self.assertIs(self.__attributes.fill, PatternFillEnum.BACKGROUND_COLOR)
        self.__attributes.fill = PatternFillEnum.FOREGROUND_COLOR
        self.assertIs(self.__attributes.fill, PatternFillEnum.FOREGROUND_COLOR)
        self.__attributes.fill = PatternFillEnum.NONE
        self.assertIs(self.__attributes.fill, PatternFillEnum.NONE)

    def test_set_vector_fill_and_get(self):
        """Setting a vector fill should give the same back.
        """
        self.__attributes.fill = self.__hatch_fill
        self.assertEqual(self.__attributes.fill, self.__hatch_fill)
        self.__attributes.fill = self.__tile_fill
        self.assertEqual(self.__attributes.fill, self.__tile_fill)
        self.__attributes.fill = self.__image_fill
        self.assertEqual(self.__attributes.fill, self.__image_fill)
        self.__attributes.fill = self.__gradient_fill
        self.assertEqual(self.__attributes.fill, self.__gradient_fill)

    def test_set_pattern_line_and_get(self):
        """Setting a pattern line should give the same back.
        """
        self.__attributes.line = PatternFillEnum.BACKGROUND_COLOR
        self.assertIs(self.__attributes.line, PatternFillEnum.BACKGROUND_COLOR)
        self.__attributes.line = PatternFillEnum.FOREGROUND_COLOR
        self.assertIs(self.__attributes.line, PatternFillEnum.FOREGROUND_COLOR)
        self.__attributes.line = PatternFillEnum.NONE
        self.assertIs(self.__attributes.line, PatternFillEnum.NONE)

    def test_set_vector_line_and_get(self):
        """Setting a vector line should give the same back.
        """
        self.__attributes.line = self.__line_style
        self.assertEqual(self.__attributes.line, self.__line_style)


class TestClazzAttributes(IClazzAttributes):

    def __init__(self, name: str):
        self.__name = name

    @property
    def _clazz_name(self) -> str:
        return self.__name


class IClazzAttributesTest(IAttributesTest):

    __clazz_name = 'TEST'
    __hatch_fill = None
    __tile_fill = None
    __image_fill = None
    __gradient_fill = None
    __line_style = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.
        vs.NameClass(cls.__clazz_name)
        vs.BeginVectorFillN('[LA] TEST', False, False, 0)
        vs.AddVectorFillLayer(0, 0, 1, 1, .25, -.25, .7, 3, 255)
        vs.EndVectorFill()
        cls.__hatch_fill = HatchVectorFill('[LA] TEST')
        cls.__tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(cls.__tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        # TODO: For some reason, it didn't work to create an image fill.
        # TODO: We'll investigate later, I'll add it to the doc for now.
        cls.__image_fill = ImageVectorFill('[AB] TEST')
        cls.__gradient_fill = GradientVectorFill(vs.CreateGradient('[VL] TEST'))
        # TODO: Can't find functions to create line styles, add later. Added to doc now.
        cls.__line_style = LineStyle('[LS] test')
        cls.__attributes = TestClazzAttributes(cls.__clazz_name)

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelClass(cls.__clazz_name)
        vs.DelObject(cls.__hatch_fill.handle)
        vs.DelObject(cls.__tile_fill.handle)
        # TODO: Delete image fill once we can create it.
        # TODO: vs.DelObject(cls.__image_fill_definition.handle)
        vs.DelObject(cls.__gradient_fill.handle)
        # TODO: Delete line style once we can create it.

    def test_set_pattern_fill_and_get(self):
        """Setting a pattern fill should give the same back.
        """
        self.__attributes.fill = PatternFillEnum.BACKGROUND_COLOR
        self.assertIs(self.__attributes.fill, PatternFillEnum.BACKGROUND_COLOR)
        self.__attributes.fill = PatternFillEnum.FOREGROUND_COLOR
        self.assertIs(self.__attributes.fill, PatternFillEnum.FOREGROUND_COLOR)
        self.__attributes.fill = PatternFillEnum.NONE
        self.assertIs(self.__attributes.fill, PatternFillEnum.NONE)

    def test_set_vector_fill_and_get(self):
        """Setting a vector fill should give the same back.
        """
        self.__attributes.fill = self.__hatch_fill
        self.assertEqual(self.__attributes.fill, self.__hatch_fill)
        self.__attributes.fill = self.__tile_fill
        self.assertEqual(self.__attributes.fill, self.__tile_fill)
        self.__attributes.fill = self.__image_fill
        self.assertEqual(self.__attributes.fill, self.__image_fill)
        self.__attributes.fill = self.__gradient_fill
        self.assertEqual(self.__attributes.fill, self.__gradient_fill)

    def test_set_pattern_line_and_get(self):
        """Setting a pattern line should give the same back.
        """
        self.__attributes.line = PatternFillEnum.BACKGROUND_COLOR
        self.assertIs(self.__attributes.line, PatternFillEnum.BACKGROUND_COLOR)
        self.__attributes.line = PatternFillEnum.FOREGROUND_COLOR
        self.assertIs(self.__attributes.line, PatternFillEnum.FOREGROUND_COLOR)
        self.__attributes.line = PatternFillEnum.NONE
        self.assertIs(self.__attributes.line, PatternFillEnum.NONE)

    def test_set_vector_line_and_get(self):
        """Setting a vector line should give the same back.
        """
        self.__attributes.line = self.__line_style
        self.assertEqual(self.__attributes.line, self.__line_style)


class ClazzTest(TestCase):

    __clazz_name = 'CLAZZ TEST'

    def test_create_method(self):
        """A class can be created by it's name.
        """
        clazz = Clazz.create(self.__clazz_name)
        self.assertIsNotNone(clazz)
        self.assertIsInstance(clazz, Clazz)
        self.assertEqual(clazz.name, self.__clazz_name)
        vs.DelClass(self.__clazz_name)


class TestDocumentAttributes(IDocumentAttributes):
    pass


class IDocumentAttributesTest(IAttributesTest):

    __hatch_fill = None
    __tile_fill = None
    __image_fill = None
    __gradient_fill = None
    __line_style = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.
        vs.BeginVectorFillN('[LA] TEST', False, False, 0)
        vs.AddVectorFillLayer(0, 0, 1, 1, .25, -.25, .7, 3, 255)
        vs.EndVectorFill()
        cls.__hatch_fill = HatchVectorFill('[LA] TEST')
        cls.__tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(cls.__tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        # TODO: For some reason, it didn't work to create an image fill.
        # TODO: We'll investigate later, I'll add it to the doc for now.
        cls.__image_fill = ImageVectorFill('[AB] TEST')
        cls.__gradient_fill = GradientVectorFill(vs.CreateGradient('[VL] TEST'))
        # TODO: Can't find functions to create line styles, add later. Added to doc now.
        cls.__line_style = LineStyle('[LS] test')
        cls.__attributes = TestDocumentAttributes()

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__hatch_fill.handle)
        vs.DelObject(cls.__tile_fill.handle)
        # TODO: Delete image fill once we can create it.
        # TODO: vs.DelObject(cls.__image_fill_definition.handle)
        vs.DelObject(cls.__gradient_fill.handle)
        # TODO: Delete line style once we can create it.

    def test_set_pattern_fill_and_get(self):
        """Setting a pattern fill should give the same back.
        """
        self.__attributes.fill = PatternFillEnum.BACKGROUND_COLOR
        self.assertIs(self.__attributes.fill, PatternFillEnum.BACKGROUND_COLOR)
        self.__attributes.fill = PatternFillEnum.FOREGROUND_COLOR
        self.assertIs(self.__attributes.fill, PatternFillEnum.FOREGROUND_COLOR)
        self.__attributes.fill = PatternFillEnum.NONE
        self.assertIs(self.__attributes.fill, PatternFillEnum.NONE)

    def test_set_vector_fill_and_get(self):
        """Setting a vector fill should give the same back.
        """
        self.__attributes.fill = self.__hatch_fill
        self.assertEqual(self.__attributes.fill, self.__hatch_fill)
        self.__attributes.fill = self.__tile_fill
        self.assertEqual(self.__attributes.fill, self.__tile_fill)
        self.__attributes.fill = self.__image_fill
        self.assertEqual(self.__attributes.fill, self.__image_fill)
        self.__attributes.fill = self.__gradient_fill
        self.assertEqual(self.__attributes.fill, self.__gradient_fill)

    def test_set_pattern_line_and_get(self):
        """Setting a pattern line should give the same back.
        """
        self.__attributes.line = PatternFillEnum.BACKGROUND_COLOR
        self.assertIs(self.__attributes.line, PatternFillEnum.BACKGROUND_COLOR)
        self.__attributes.line = PatternFillEnum.FOREGROUND_COLOR
        self.assertIs(self.__attributes.line, PatternFillEnum.FOREGROUND_COLOR)
        self.__attributes.line = PatternFillEnum.NONE
        self.assertIs(self.__attributes.line, PatternFillEnum.NONE)

    def test_set_vector_line_and_get(self):
        """Setting a vector line should give the same back.
        """
        self.__attributes.line = self.__line_style
        self.assertEqual(self.__attributes.line, self.__line_style)
