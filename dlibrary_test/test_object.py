from dlibrary import TileVectorFill
from dlibrary.document import PatternFillEnum
from dlibrary.object import IObjectAttributes, Line
from dlibrary_test.test_document import IAttributesTest
import vs


class TestObjectAttributes(IObjectAttributes):

    def __init__(self, handle):
        self.__handle = handle

    @property
    def _object_handle(self):
        return self.__handle


class IObjectAttributesTest(IAttributesTest):

    __rectangle = None
    __tile_fill = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.\
        vs.Rect((0, 10), (10, 0))
        cls.__rectangle = vs.LNewObj()
        cls.__tile_fill = TileVectorFill(vs.CreateTile('[MO] TEST'))
        vs.AddTileGeometryObject(cls.__tile_fill.handle, Line.create((0, 0), (10, 10)).handle)
        cls.__attributes = TestObjectAttributes(cls.__rectangle)

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__rectangle)
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
