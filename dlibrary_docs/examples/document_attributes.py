"""This is an example on how to work with document attributes.
"""
from dlibrary import ObjectRepository
from dlibrary.document import Document, PatternFillEnum, ImageVectorFill, GradientVectorFill, TileVectorFill, \
    HatchVectorFill, LineStyle


def run():

    # Get the document default fill attribute.
    document_fill = Document().fill
    document_line = Document().line

    # Set the document default fill attribute to a pattern fill.
    # Pattern fills include no fill, background- and foreground color!
    Document().fill = PatternFillEnum.NONE
    Document().fill = PatternFillEnum.BACKGROUND_COLOR
    Document().fill = PatternFillEnum.FOREGROUND_COLOR

    # Set the document default fill attribute to a hatch fill.
    hatch_fill = ObjectRepository().get('Hatch Resource Name')
    if hatch_fill is not None and isinstance(hatch_fill, HatchVectorFill):
        Document().fill = hatch_fill

    # Set the document default fill attribute to a tile fill.
    tile_fill = ObjectRepository().get('Tile Resource Name')
    if tile_fill is not None and isinstance(tile_fill, TileVectorFill):
        Document().fill = tile_fill

    # Set the document default fill attribute to a gradient fill.
    gradient_fill = ObjectRepository().get('Gradient Resource Name')
    if gradient_fill is not None and isinstance(gradient_fill, GradientVectorFill):
        Document().fill = gradient_fill

    # Set the document default fill attribute to an image fill.
    image_fill = ObjectRepository().get('Image Resource Name')
    if image_fill is not None and isinstance(image_fill, ImageVectorFill):
        Document().fill = image_fill

    # Set the document default line attribute to a pattern fill.
    # Pattern fills include no fill, background- and foreground color!
    Document().line = PatternFillEnum.NONE
    Document().line = PatternFillEnum.BACKGROUND_COLOR
    Document().line = PatternFillEnum.FOREGROUND_COLOR

    # Set the document default line attribute to a line style.
    line_style = ObjectRepository().get('Line Style Name')
    if line_style is not None and isinstance(line_style, LineStyle):
        Document().line = line_style
