"""This is an example on how to work with rectangle objects.
"""
from dlibrary.object import Rectangle


def run():

    # Create a rectangle by specifying the start point, direction, width and height.
    # This is the only way to create a rotated rectangle, the other methods create one at 0°.
    rectangle = Rectangle.create((0, 0), (1, 0), 20, 10)

    # The direction is a point to indicate the angle at which the first side (= width) has to be drawn.
    # See it as a point on a circle, where the angle is taken from the line drawn from the center to that point.
    # Some examples:
    #   (1, 0)  = 0°    = the width will be horizontal
    #   (0, 1)  = 90°   = the width will be vertical
    #   (1, 1)  = 45°
    #   ...
    # So the width will be drawn in that direction, while the height will then be drawn at +90° degrees!

    # Create a rectangle by specifying the top-left and bottom-right corners.
    rectangle = Rectangle.create_by_diagonal((0, 10), (20, 0))

    # You can also use length strings to create the rectangle, instead of specifying them in document length units.
    # You can even use a mixture of both, so you can create the rectangle in a convenient way.
    rectangle = Rectangle.create((0, 0), (1, 0), '20cm', '10cm')
    rectangle = Rectangle.create_by_diagonal((0, '10cm'), ('20cm', 0))

    # You can get the width and the height of a rectangle by it's property.
    width = rectangle.width
    height = rectangle.height

    # Keep in mind that these are the original values, and not the ones you see in the OIP!
    # For example, if you use (0, 1) as direction, VW will display the height as width,
    # while in code, the height and width stay the same as you entered them at creation.

    # You can even get the center of the rectangle by it's property.
    center_x, center_y = center = rectangle.center
