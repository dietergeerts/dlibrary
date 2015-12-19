"""This is an example on how to work with object attributes.
"""
from dlibrary import ObjectRepository
from dlibrary.document import PatternFillEnum, HatchVectorFill, TileVectorFill, GradientVectorFill, ImageVectorFill
from dlibrary.object import DrawnObject


def run():

    # Get the object. Note that the way we get the object here is a temporary solution, because not all object types
    # can be retrieved through the object repository yet, because it's still in development.
    obj = DrawnObject('name_or_handle_of_drawn_object')

    # Get the object fill attribute.
    obj_fill = obj.fill

    # Set the object fill attribute to a pattern fill.
    # Pattern fills include no fill, background- and foreground color!
    obj.fill = PatternFillEnum.NONE
    obj.fill = PatternFillEnum.BACKGROUND_COLOR
    obj.fill = PatternFillEnum.FOREGROUND_COLOR

    # Set the object fill attribute to a hatch fill.
    hatch_fill = ObjectRepository().get('Hatch Resource Name')
    if hatch_fill is not None and isinstance(hatch_fill, HatchVectorFill):
        obj.fill = hatch_fill

    # Set the object fill attribute to a tile fill.
    tile_fill = ObjectRepository().get('Tile Resource Name')
    if tile_fill is not None and isinstance(tile_fill, TileVectorFill):
        obj.fill = tile_fill

    # Set the object fill attribute to a gradient fill.
    gradient_fill = ObjectRepository().get('Gradient Resource Name')
    if gradient_fill is not None and isinstance(gradient_fill, GradientVectorFill):
        obj.fill = gradient_fill

    # Set the object fill attribute to an image fill.
    image_fill = ObjectRepository().get('Image Resource Name')
    if image_fill is not None and isinstance(image_fill, ImageVectorFill):
        obj.fill = image_fill
