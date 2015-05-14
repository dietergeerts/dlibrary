import vs


class Record(object):
    def __init__(self, object_handle, name: str):
        self.__object_handle = object_handle
        self.__name = name

    def set_field(self, field: str, value: str):
        vs.SetRField(self.__object_handle, self.__name, field, value)