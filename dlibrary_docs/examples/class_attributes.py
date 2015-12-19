"""This is an example on how to work with class attributes.
"""
from dlibrary import ObjectRepository
from dlibrary.document import PatternFillEnum, HatchVectorFill, TileVectorFill, ImageVectorFill, \
    GradientVectorFill, Clazz


def run():

    # Get the class definition.
    clazz = ObjectRepository().get('clazz-name')
    if clazz is None or not isinstance(clazz, Clazz):
        return

    # Get the class fill attribute.
    clazz_fill = clazz.fill

    # Set the class fill attribute to a pattern fill.
    # Pattern fills include no fill, background- and foreground color!
    clazz.fill = PatternFillEnum.NONE
    clazz.fill = PatternFillEnum.BACKGROUND_COLOR
    clazz.fill = PatternFillEnum.FOREGROUND_COLOR

    # Set the class fill attribute to a hatch fill.
    hatch_fill = ObjectRepository().get('Hatch Resource Name')
    if hatch_fill is not None and isinstance(hatch_fill, HatchVectorFill):
        clazz.fill = hatch_fill

    # Set the class fill attribute to a tile fill.
    tile_fill = ObjectRepository().get('Tile Resource Name')
    if tile_fill is not None and isinstance(tile_fill, TileVectorFill):
        clazz.fill = tile_fill

    # Set the class fill attribute to a gradient fill.
    gradient_fill = ObjectRepository().get('Gradient Resource Name')
    if gradient_fill is not None and isinstance(gradient_fill, GradientVectorFill):
        clazz.fill = gradient_fill

    # Set the class fill attribute to an image fill.
    image_fill = ObjectRepository().get('Image Resource Name')
    if image_fill is not None and isinstance(image_fill, ImageVectorFill):
        clazz.fill = image_fill
