from abc import ABCMeta, abstractmethod
from collections import UserList
from dlibrary.utility.eventing import Event


class ObservableField(object):
    def __init__(self, default_value=None):
        self.__value = default_value
        self.__field_changed_event = Event()

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if self.__value != value:
            old_value = self.__value
            self.__value = value
            self._on_value_changed(old_value, value)
            self.__field_changed_event.raise_event(old_value, value)

    @property
    def field_changed_event(self) -> Event:
        return self.__field_changed_event

    def _on_value_changed(self, old, new):
        pass


class LinkedObservableField(ObservableField):
    def __init__(self, model: dict, key: str):
        super().__init__(model[key])
        self.__model = model
        self.__key = key

    def _on_value_changed(self, old, new):
        self.__model[self.__key] = new


class ObservableList(UserList):
    def __init__(self, default_list=None):
        super().__init__(default_list)
        self.__raise_events = True
        self.__suspended_state = None
        self.__list_changed_event = Event()
        self.__list_reordered_event = Event()

    @property
    def list_changed_event(self) -> Event:
        return self.__list_changed_event

    @property
    def list_reordered_event(self) -> Event:
        return self.__list_reordered_event

    def suspend_events(self):
        self.__raise_events = False
        self.__suspended_state = tuple(self.data)

    def resume_events(self):
        self.__raise_events = True
        # noinspection PyTypeChecker
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
        if self.__raise_events:
            self.__list_changed_event.raise_event({i: old_item}, {i: item})

    def __delitem__(self, i):
        old_item = self.data[i]
        super().__delitem__(i)
        if self.__raise_events:
            self.__list_changed_event.raise_event({i: old_item}, {})

    def __iadd__(self, other):
        si = len(self.data)
        super().__iadd__(other)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {si+i: item for i, item in enumerate(other)})
        return self

    def append(self, item):
        index = len(self.data)
        super().append(item)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {index: item})

    def insert(self, i, item):
        super().insert(i, item)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {i: item})

    def pop(self, i=-1):
        item = super().pop(i)
        if self.__raise_events:
            self.__list_changed_event.raise_event({(len(self.data) if i == -1 else i): item}, {})
        return item

    def remove(self, item):
        index = self.data.index(item)
        super().remove(item)
        if self.__raise_events:
            self.__list_changed_event.raise_event({index: item}, {})

    def clear(self):
        items = list(self.data)
        super().clear()
        if self.__raise_events:
            self.__list_changed_event.raise_event({i: item for i, item in enumerate(items)}, {})

    def index(self, item, *args):
        try:
            return super().index(item, *args)
        except ValueError:
            return -1

    def reverse(self):
        super().reverse()
        if self.__raise_events:
            self.__list_reordered_event.raise_event()

    def sort(self, *args, **kwds):
        super().sort(*args, **kwds)
        if self.__raise_events:
            self.__list_reordered_event.raise_event()

    def extend(self, other):
        si = len(self.data)
        super().extend(other)
        if self.__raise_events:
            self.__list_changed_event.raise_event({}, {si+i: item for i, item in enumerate(other)})


class LinkedObservableList(ObservableList):
    def __init__(self, model_list: list, pack: callable, unpack: callable):
        super().__init__(pack(model) for model in model_list)
        self.__model_list = model_list
        self.__pack = pack
        self.__unpack = unpack

    def __setitem__(self, i, item):
        super().__setitem__(i, item)
        self.__model_list[i] = self.__unpack(item)

    def __delitem__(self, i):
        super().__delitem__(i)
        del self.__model_list[i]

    def __iadd__(self, other):
        if isinstance(other, UserList):
            self.__model_list += (self.__unpack(item) for item in other.data)
        elif isinstance(other, type(self.data)):
            self.__model_list += (self.__unpack(item) for item in other)
        else:
            self.__model_list += (self.__unpack(item) for item in list(other))
        return super().__iadd__(other)

    def __imul__(self, n):
        self.__model_list *= n
        return super().__imul__(n)

    def append(self, item):
        super().append(item)
        self.__model_list.append(self.__unpack(item))

    def insert(self, i, item):
        super().insert(i, item)
        self.__model_list.insert(i, self.__unpack(item))

    def pop(self, i=-1):
        self.__model_list.pop(i)
        return super().pop(i)

    def remove(self, item):
        super().remove(item)
        self.__model_list.remove(self.__unpack(item))

    def clear(self):
        super().clear()
        self.__model_list.clear()

    def reverse(self):
        super().reverse()
        self.__model_list.reverse()

    def sort(self, *args, **kwds):
        super().sort(*args, **kwds)
        self.__model_list.sort(*args, **kwds)

    def extend(self, other):
        super().extend(other)
        if isinstance(other, UserList):
            self.__model_list.extend(self.__unpack(item) for item in other.data)
        else:
            self.__model_list.extend(self.__unpack(item) for item in other)


class AbstractObservableWithDependencies(object, metaclass=ABCMeta):
    def __init__(self, dependant_observables: set=None):
        if dependant_observables is not None:
            self.__subscribe_to_dependant_observables(dependant_observables)

    def __subscribe_to_dependant_observables(self, dependant_observables: set):
        for observable in dependant_observables:
            if isinstance(observable, ObservableField):
                observable.field_changed_event.subscribe(self._on_dependencies_changed)
            elif isinstance(observable, ObservableList):
                observable.list_changed_event.subscribe(self._on_dependencies_changed)
                observable.list_reordered_event.subscribe(self._on_dependencies_changed)

    @abstractmethod
    def _on_dependencies_changed(self, *args, **kwargs):
        raise NotImplementedError


class ObservableMethod(AbstractObservableWithDependencies):
    def __init__(self, method: callable, dependant_observables: set=None):
        super().__init__(dependant_observables)
        self.__method = method
        self.__method_changed_event = Event()

    @property
    def method_changed_event(self) -> Event:
        return self.__method_changed_event

    def apply(self, *args):
        self.__method(*args)

    # noinspection PyUnusedLocal
    def _on_dependencies_changed(self, *args, **kwargs):
        self.__method_changed_event.raise_event()


class ObservableCommand(AbstractObservableWithDependencies):
    def __init__(self, execute: callable, can_execute: callable=None, dependant_observables: set=None):
        super().__init__(dependant_observables)
        self.__execute = execute
        self.__can_execute = can_execute
        self.__can_execute_changed_event = Event()

    @property
    def can_execute_changed_event(self) -> Event:
        return self.__can_execute_changed_event

    def can_execute(self):
        return self.__can_execute() if self.__can_execute is not None else True

    def execute(self):
        if self.can_execute():
            self.__execute()

    # noinspection PyUnusedLocal
    def _on_dependencies_changed(self, *args, **kwargs):
        self.__can_execute_changed_event.raise_event()