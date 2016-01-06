from dlibrary import TileVectorFill
from dlibrary.document import PatternFillEnum, HatchVectorFill, ImageVectorFill, GradientVectorFill, LineStyle
from dlibrary.object import IObjectAttributes, Line
from dlibrary_test.test_document import IAttributesTest
import vs


class TestObjectAttributes(IObjectAttributes):

    def __init__(self, handle: vs.Handle):
        self.__handle = handle

    @property
    def _object_handle(self) -> vs.Handle:
        return self.__handle


class IObjectAttributesTest(IAttributesTest):

    __rectangle = None
    __hatch_fill = None
    __tile_fill = None
    __image_fill = None
    __gradient_fill = None
    __line_style = None
    __attributes = None

    @classmethod
    def setUpClass(cls):
        # TODO: Replace creation by our own when implemented.\
        vs.Rect((0, 10), (10, 0))
        cls.__rectangle = vs.LNewObj()
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
        cls.__attributes = TestObjectAttributes(cls.__rectangle)

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__rectangle)
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
