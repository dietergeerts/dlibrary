from unittest import TestCase

from dlibrary import ObjectTypeEnum, HatchVectorFill, TileVectorFill, ImageVectorFill, GradientVectorFill
from dlibrary.object import Line
from dlibrary.object_base import AbstractKeyedObject, ObjectRepository
import vs


class ObjectTypeEnumTest(TestCase):

    __hatch_fill = None
    __tile_fill = None
    __image_fill = None
    __gradient_fill = None

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

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelVectorFill(cls.__hatch_fill.name)
        vs.DelObject(cls.__tile_fill.handle)
        # TODO: Delete image fill once we can create it.
        # TODO: vs.DelObject(cls.__image_fill_definition.handle)
        vs.DelObject(cls.__gradient_fill.handle)

    def test_none_object_type(self):
        """A non-existing handle or name should return NONE as object type.
        """
        self.assertIs(ObjectTypeEnum.get(None), ObjectTypeEnum.NONE)
        self.assertIs(ObjectTypeEnum.get(''), ObjectTypeEnum.NONE)

    def test_hatch_fill_definition_object_type(self):
        self.assertIs(ObjectTypeEnum.get(self.__hatch_fill.handle), ObjectTypeEnum.HATCH_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(self.__hatch_fill.name), ObjectTypeEnum.HATCH_FILL_DEFINITION)

    def test_tile_fill_definition_object_type(self):
        self.assertIs(ObjectTypeEnum.get(self.__tile_fill.handle), ObjectTypeEnum.TILE_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(self.__tile_fill.name), ObjectTypeEnum.TILE_FILL_DEFINITION)

    def test_image_fill_definition_object_type(self):
        self.assertIs(ObjectTypeEnum.get(self.__image_fill.handle), ObjectTypeEnum.IMAGE_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(self.__image_fill.name), ObjectTypeEnum.IMAGE_FILL_DEFINITION)

    def test_gradient_fill_definition_object_type(self):
        self.assertIs(ObjectTypeEnum.get(self.__gradient_fill.handle), ObjectTypeEnum.GRADIENT_FILL_DEFINITION)
        self.assertIs(ObjectTypeEnum.get(self.__gradient_fill.name), ObjectTypeEnum.GRADIENT_FILL_DEFINITION)


class TestKeyedObject(AbstractKeyedObject):

    def __init__(self, handle_or_name):
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

    __hatch_fill = None
    __tile_fill = None
    __image_fill = None
    __gradient_fill = None

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

    @classmethod
    def tearDownClass(cls):
        # TODO: Replace deletion by our own when implemented.
        vs.DelVectorFill(cls.__hatch_fill.name)
        vs.DelObject(cls.__tile_fill.handle)
        # TODO: Delete image fill once we can create it.
        # TODO: vs.DelObject(cls.__image_fill_definition.handle)
        vs.DelObject(cls.__gradient_fill.handle)

    def test_none_object(self):
        """A non-existing handle or name should return None.
        """
        self.assertIsNone(ObjectRepository().get(None))
        self.assertIsNone(ObjectRepository().get(''))

    def test_hatch_vector_fill(self):
        self.assertIsInstance(ObjectRepository().get(self.__hatch_fill.handle), HatchVectorFill)
        self.assertIsInstance(ObjectRepository().get(self.__hatch_fill.name), HatchVectorFill)

    def test_tile_vector_fill(self):
        self.assertIsInstance(ObjectRepository().get(self.__tile_fill.handle), TileVectorFill)
        self.assertIsInstance(ObjectRepository().get(self.__tile_fill.name), TileVectorFill)

    def test_image_vector_fill(self):
        self.assertIsInstance(ObjectRepository().get(self.__image_fill.handle), ImageVectorFill)
        self.assertIsInstance(ObjectRepository().get(self.__image_fill.name), ImageVectorFill)

    def test_gradient_vector_fill(self):
        self.assertIsInstance(ObjectRepository().get(self.__gradient_fill.handle), GradientVectorFill)
        self.assertIsInstance(ObjectRepository().get(self.__gradient_fill.name), GradientVectorFill)
