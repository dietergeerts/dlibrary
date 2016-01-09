from unittest import TestCase

from dlibrary import TileVectorFill
from dlibrary.document import PatternFillEnum, HatchVectorFill, ImageVectorFill, GradientVectorFill, LineStyle
from dlibrary.object import IObjectAttributes, Line, DrawnObject, Rectangle
from dlibrary_test.test_document import IAttributesTest
import vs


class RecordFieldTest(TestCase):

    __rectangle = None
    __record_name = '[RD] TEST'
    __record_handle = None
    __field_name = 'First Field'
    __field_value = 'Een'
    __field = None

    @classmethod
    def setUpClass(cls):
        cls.__rectangle = Rectangle.create((0, 0), (1, 0), 1, 1)
        # TODO: Replace creation by our own when implemented.
        vs.NewField(cls.__record_name, cls.__field_name, cls.__field_value, 4, 0)
        cls.__record_handle = vs.GetObject(cls.__record_name)
        # TODO: Replace attachment with our own when implemented.
        vs.SetRecord(cls.__rectangle.handle, cls.__record_name)
        cls.__field = cls.__rectangle.records[cls.__record_name].fields[cls.__field_name]

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__rectangle.handle)
        vs.DelObject(cls.__record_handle)

    def test_field_there_with_default_value(self):
        """When a record is attached, all fields should have there default value.
        """
        self.assertEqual(self.__field.name, self.__field_name)
        self.assertEqual(self.__field.value, self.__field_value)

    def test_setting_field_value_should_give_it_back(self):
        """Setting the value should properly store it, so it will give back the same.
        """
        self.__field.value = new_value = 'Some new field value'
        self.assertEqual(self.__field.value, new_value)


class RecordTest(TestCase):

    __rectangle = None
    __record_name = '[RD] TEST'
    __record_handle = None
    __record = None
    __field_1_name = 'First Field'
    __field_2_name = 'Second Field'
    __field_3_name = 'Third Field'

    @classmethod
    def setUpClass(cls):
        cls.__rectangle = Rectangle.create((0, 0), (1, 0), 1, 1)
        # TODO: Replace creation by our own when implemented.
        vs.NewField(cls.__record_name, cls.__field_1_name, '', 4, 0)
        vs.NewField(cls.__record_name, cls.__field_2_name, '', 4, 0)
        vs.NewField(cls.__record_name, cls.__field_3_name, '', 4, 0)
        cls.__record_handle = vs.GetObject(cls.__record_name)
        # TODO: Replace attachment with our own when implemented.
        vs.SetRecord(cls.__rectangle.handle, cls.__record_name)
        cls.__record = cls.__rectangle.records[cls.__record_name]

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__rectangle.handle)
        vs.DelObject(cls.__record_handle)

    def test_record_there_with_all_fields(self):
        """When a record is attached, we should be able to get all fields.
        """
        self.assertEqual(len(self.__record.fields), 3)
        self.assertEqual(self.__record.fields[self.__field_1_name].name, self.__field_1_name)
        self.assertEqual(self.__record.fields[self.__field_2_name].name, self.__field_2_name)
        self.assertEqual(self.__record.fields[self.__field_3_name].name, self.__field_3_name)

    def test_get_field_by_index(self):
        """The method get_field should give a field by it's index, which is 1-n based.
        """
        self.assertEqual(self.__record.get_field(1).name, self.__field_1_name)
        self.assertEqual(self.__record.get_field(2).name, self.__field_2_name)
        self.assertEqual(self.__record.get_field(3).name, self.__field_3_name)


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
        cls.__rectangle = Rectangle.create((0, 0), (1, 0), 1, 1)
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
        cls.__attributes = TestObjectAttributes(cls.__rectangle.handle)

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__rectangle.handle)
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


class IObjectRecordsTest(TestCase):

    __rectangle = None
    __record_name = '[RD] TEST'
    __record_handle = None

    @classmethod
    def setUpClass(cls):
        cls.__rectangle = Rectangle.create((0, 0), (1, 0), 1, 1)
        # TODO: Replace creation by our own when implemented.
        vs.NewField(cls.__record_name, 'Field', '', 4, 0)
        cls.__record_handle = vs.GetObject(cls.__record_name)

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelObject(cls.__rectangle.handle)
        vs.DelObject(cls.__record_handle)

    def test_no_records_at_first(self):
        """An object should have no records attached to it when first created.
        """
        self.assertEqual(len(self.__rectangle.records), 0)

    def test_record_there_after_attached(self):
        """After attaching a record, it should be there.
        """
        # TODO: Replace attachment with our own when implemented.
        vs.SetRecord(self.__rectangle.handle, self.__record_name)
        self.assertEqual(len(self.__rectangle.records), 1)
        self.assertEqual(self.__rectangle.records[self.__record_name].name, self.__record_name)


class RectangleTest(TestCase):

    def setUp(self):
        self.__rectangle = Rectangle.create((0, 0), (1, 0), 1, 2)

    def tearDown(self):
        vs.DelObject(self.__rectangle.handle)

    def test_create_method(self):
        vs.DelObject(self.__rectangle.handle)
        self.__rectangle = Rectangle.create((0, 0), (1, 0), 1, 2)
        self.assertEqual(self.__rectangle.width, 1)
        self.assertEqual(self.__rectangle.height, 2)
        self.assertEqual(self.__rectangle.center, (0.5, 1))

    def test_create_by_diagonal_method(self):
        vs.DelObject(self.__rectangle.handle)
        self.__rectangle = Rectangle.create_by_diagonal((0, 2), (1, 0))
        self.assertEqual(self.__rectangle.width, 1)
        self.assertEqual(self.__rectangle.height, 2)
        self.assertEqual(self.__rectangle.center, (0.5, 1))

    def test_width_property(self):
        self.__rectangle.width = 100
        self.assertEqual(self.__rectangle.width, 100)
        self.assertEqual(self.__rectangle.center, (50, 1))

    def test_height_property(self):
        self.__rectangle.height = 100
        self.assertEqual(self.__rectangle.height, 100)
        self.assertEqual(self.__rectangle.center, (0.5, 50))
