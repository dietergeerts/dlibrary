"""This is an example on how to work with object records, aka attached records.
"""
from dlibrary.object import DrawnObject


def run():

    # Get the object. Note that the way we get the object here is a temporary solution, because not all object types
    # can be retrieved through the object repository yet, because it's still in development.
    obj = DrawnObject('name_or_handle_of_drawn_object')

    # Get all records attached to this object.
    records = obj.records

    # Get a specific record attached to this object.
    record = obj.records['record_name']
    record = obj.records.get('record_name')  # For if you aren't sure the record is in there!

    # Get all fields within this record.
    # This is an OrderedDict, for if you need correct ordering.
    fields = record.fields

    # Get a specific field from this record.
    field = record.fields['field_name']
    field = record.fields.get('field_name')  # For if you aren't sure the field is in there!

    # Get the value from the field.
    value = field.value
    # And as a one-liner, with previous steps included:
    value = obj.records['record_name'].fields['field_name'].value

    # Put a new value in the field.
    field.value = 'A new value'
    # And as a one-liner, with previous steps included:
    obj.records['record_name'].fields['field_name'].value = 'A new value'
