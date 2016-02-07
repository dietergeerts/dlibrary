"""This is an example on how to work with object order.
"""
from dlibrary.object import DrawnObject


def run():

    # Get the object. Note that the way we get the object here is a temporary solution, because not all object types
    # can be retrieved through the object repository yet, because it's still in development.
    obj = DrawnObject('name_or_handle_of_drawn_object')

    # Send the object backwards, where you can specify how many times.
    obj.move_backward()
    obj.move_backward(5)

    # Or send the object completely to the back of the stacking order.
    obj.move_to_back()

    # Send the object forwards, where you can specify how many times.
    obj.move_forward()
    obj.move_forward(5)

    # Or send the object completely to the front of the stacking order.
    obj.move_to_front()
