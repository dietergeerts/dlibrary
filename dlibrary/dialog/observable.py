from collections import UserList

from dlibrary.utility.eventing import Event


class ObservableField(object):
    def __init__(self, default_value=None):
        self.__value = default_value
        self.__field_changed_event = Event()

    @property
    def value(self): return self.__value

    @value.setter
    def value(self, value):
        if self.__value != value:
            old_value = self.__value; self.__value = value
            self.__field_changed_event.raise_event(old_value, value)

    @property
    def field_changed_event(self) -> Event: return self.__field_changed_event


class ObservableList(UserList):
    def __init__(self, default_list=None):
        super().__init__(default_list)
        self.__raise_events = True
        self.__suspended_state = None
        self.__list_changed_event = Event()
        self.__list_reordered_event = Event()

    @property
    def list_changed_event(self) -> Event: return self.__list_changed_event

    @property
    def list_reordered_event(self) -> Event: return self.__list_reordered_event

    def suspend_events(self):
        self.__raise_events = False
        self.__suspended_state = tuple(self.data)

    def resume_events(self):
        self.__raise_events = True
        self.__raise_event_if_changed(self.__suspended_state, self.data)
        self.__suspended_state = None

    def __raise_event_if_changed(self, suspended: tuple, current: list):
        if suspended != current:
            if len(suspended) == len(current) and all(item in current for item in suspended):
                self.__list_reordered_event.raise_event()
            else:
                self.__list_changed_event.raise_event(
                    {index: item for index, item in enumerate(suspended) if item not in current},
                    {index: item for index, item in enumerate(current) if item not in suspended})

    def __setitem__(self, i, item):
        old_item = self.data[i]
        super().__setitem__(i, item)
        if self.__raise_events: self.__list_changed_event.raise_event({i: old_item}, {i: item})

    def __delitem__(self, i):
        old_item = self.data[i]
        super().__delitem__(i)
        if self.__raise_events: self.__list_changed_event.raise_event({i: old_item}, {})

    def __iadd__(self, other):
        si = len(self.data)
        super().__iadd__(other)
        if self.__raise_events: self.__list_changed_event.raise_event({}, {si+i: item for i, item in enumerate(other)})

    def append(self, item):
        index = len(self.data)
        super().append(item)
        if self.__raise_events: self.__list_changed_event.raise_event({}, {index: item})

    def insert(self, i, item):
        super().insert(i, item)
        if self.__raise_events: self.__list_changed_event.raise_event({}, {i: item})

    def pop(self, i=-1):
        item = super().pop(i)
        if self.__raise_events: self.__list_changed_event.raise_event({(len(self.data) if i == -1 else i): item}, {})
        return item

    def remove(self, item):
        index = self.data.index(item)
        super().remove(item)
        if self.__raise_events: self.__list_changed_event.raise_event({index: item}, {})

    def clear(self):
        items = list(self.data)
        super().clear()
        if self.__raise_events: self.__list_changed_event.raise_event({i: item for i, item in enumerate(items)}, {})

    def reverse(self):
        super().reverse()
        if self.__raise_events: self.__list_reordered_event.raise_event()

    def sort(self, *args, **kwds):
        super().sort(*args, **kwds)
        if self.__raise_events: self.__list_reordered_event.raise_event()

    def extend(self, other):
        si = len(self.data)
        super().extend(other)
        if self.__raise_events: self.__list_changed_event.raise_event({}, {si+i: item for i, item in enumerate(other)})