from unittest import TestCase

from dlibrary.document import IAttributes, AbstractVectorFill, PatternFillEnum, TileVectorFill, IClazzAttributes, \
    IDocumentAttributes
from dlibrary.object import Line
import vs


class TestAttributes(IAttributes):

    def __init__(self):
        self.__pattern_fill = PatternFillEnum.NONE
        self.__vector_fill = None

    def _get_pattern_fill(self) -> int:
        return self.__pattern_fill

    def _set_pattern_fill(self, value: int):
        self.__pattern_fill = value
        self.__vector_fill = None

    def _get_vector_fill(self) -> AbstractVectorFill:
        return self.__vector_fill

    def _set_vector_fill(self, value: AbstractVectorFill):
        self.__vector_fill = value


class IAttributesTest(TestCase):

    __tile_fill = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.
        cls.__tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(cls.__tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        cls.__attributes = TestAttributes()

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__tile_fill.handle)

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
        self.__attributes.fill = self.__tile_fill
        self.assertEqual(self.__attributes.fill, self.__tile_fill)


class TestClazzAttributes(IClazzAttributes):

    def __init__(self, name: str):
        self.__name = name

    @property
    def _clazz_name(self) -> str:
        return self.__name


class IClazzAttributesTest(IAttributesTest):

    __clazz_name = 'TEST'
    __tile_fill = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.
        vs.NameClass(cls.__clazz_name)
        cls.__tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(cls.__tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        cls.__attributes = TestClazzAttributes(cls.__clazz_name)

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelClass(cls.__clazz_name)
        vs.DelObject(cls.__tile_fill.handle)

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
        self.__attributes.fill = self.__tile_fill
        self.assertEqual(self.__attributes.fill, self.__tile_fill)


class TestDocumentAttributes(IDocumentAttributes):
    pass


class IDocumentAttributesTest(IAttributesTest):

    __tile_fill = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.
        cls.__tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(cls.__tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        cls.__attributes = TestDocumentAttributes()

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__tile_fill.handle)

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
        self.__attributes.fill = self.__tile_fill
        self.assertEqual(self.__attributes.fill, self.__tile_fill)
