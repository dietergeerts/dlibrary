from abc import ABCMeta
from abc import abstractmethod
import importlib

from dlibrary.dialog.observable import ObservableField, ObservableList
from dlibrary.utility import xmltodict as xml_to_dict_util
from dlibrary.utility.eventing import Event
from dlibrary.utility.singleton import SingletonMeta
import vs


class LayoutEnum(object):
    VERTICAL = 1; HORIZONTAL = 2

    @staticmethod
    def from_string(value: str) -> int:
        return {
            'VERTICAL': LayoutEnum.VERTICAL,
            'HORIZONTAL': LayoutEnum.HORIZONTAL
        }.get(value)


class AlignEdgeEnum(object):
    RIGHT = 1; BOTTOM = 2; LEFT = 3


class AlignModeEnum(object):
    RESIZE = 0; SHIFT = 1


class AlignFactory(object, metaclass=SingletonMeta):
    def __init__(self): self.__last_align_id = 10

    def generate_align_id(self) -> int: self.__last_align_id += 1; return self.__last_align_id


class TextAlignEnum(object):
    LEFT = 1; CENTER = 2; RIGHT = 3

    @staticmethod
    def from_string(value: str) -> int:
        return {
            'LEFT': TextAlignEnum.LEFT,
            'CENTER': TextAlignEnum.CENTER,
            'RIGHT': TextAlignEnum.RIGHT
        }.get(value)


class TextStyleEnum(object):
    REGULAR = 0; CAPTION = 1; BOLD = 2; REDUCED = 3

    @staticmethod
    def from_string(value: str) -> int:
        return {
            'REGULAR': TextStyleEnum.REGULAR,
            'CAPTION': TextStyleEnum.CAPTION,
            'BOLD': TextStyleEnum.BOLD,
            'REDUCED': TextStyleEnum.REDUCED
        }.get(value)


class AbstractDataContext(object, metaclass=ABCMeta):
    def __init__(self, data_context: object):
        self.__data_context = data_context
        self.__data_context_changed = Event()

    @property
    def data_context(self) -> object: return self.__data_context

    @property
    def data_context_changed(self) -> Event: return self.__data_context_changed


class AbstractControl(AbstractDataContext, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def can_align(cls, layout: int) -> bool: raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_align_mode(cls, layout: int) -> int: raise NotImplementedError

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str):
        super().__init__(None)
        self.__dialog_id = dialog_id
        self.__control_id = control_id
        vs.SetHelpText(dialog_id, control_id, help_text)
        self.__data_parent = data_parent
        self.__data_context = data_context

    @property
    def _dialog_id(self) -> int: return self.__dialog_id

    @property
    def control_id(self) -> int: return self.__control_id

    @property
    def __data_context_field(self) -> ObservableField:
        return getattr(self.__data_parent.data_context, self.__data_context)

    @property
    def data_context(self) -> object:
        return self.__data_context_field.value if self.__data_context else self.__data_parent.data_context

    def setup(self, register_event_handler: callable):
        register_event_handler(self.control_id, self._on_control_event)
        self.__data_parent.data_context_changed.subscribe(self.__on_parent_data_context_changed)
        self.__reset(); self._setup()

    @abstractmethod
    def _setup(self): raise NotImplementedError

    @abstractmethod
    def _update(self): raise NotImplementedError

    def __reset(self):
        if self.__data_context: self.__data_context_field.field_changed_event.subscribe(self.__on_data_context_changed)

    def __on_parent_data_context_changed(self): self._update(); self.__reset(); self.data_context_changed.raise_event()

    def __on_data_context_changed(self, old_value, new_value): self._update(); self.data_context_changed.raise_event()

    @abstractmethod
    def _on_control_event(self, data: int): raise NotImplementedError


class AbstractGroupControl(AbstractControl):
    @classmethod
    @abstractmethod
    def can_align(cls, layout: int) -> bool: raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_align_mode(cls, layout: int) -> int: raise NotImplementedError

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context)
        self.__controls = tuple()

    def add_controls(self, controls: tuple, layout: int):
        self.__controls = controls
        self.__arrange_controls(layout)
        self.__align_controls(layout)

    def __arrange_controls(self, layout: int):
        for index, control in enumerate(self.__controls):
            if index == 0:
                vs.SetFirstGroupItem(self._dialog_id, self.control_id, control.control_id)
            elif layout == LayoutEnum.HORIZONTAL:
                vs.SetRightItem(self._dialog_id, self.__controls[index - 1].control_id, control.control_id, 0, 0)
            else:
                vs.SetBelowItem(self._dialog_id, self.__controls[index - 1].control_id, control.control_id, 0, 0)

    def __align_controls(self, layout: int):
        align_id = AlignFactory().generate_align_id()
        for control in self.__controls:
            if control.can_align(layout):
                align_edge = AlignEdgeEnum.BOTTOM if layout == LayoutEnum.HORIZONTAL else AlignEdgeEnum.RIGHT
                align_mode = control.get_align_mode(layout)
                vs.AlignItemEdge(self._dialog_id, control.control_id, align_edge, align_id, align_mode)

    def setup(self, register_event_handler: callable):
        super().setup(register_event_handler)
        for control in self.__controls: control.setup(register_event_handler)

    @abstractmethod
    def _setup(self): raise NotImplementedError

    @abstractmethod
    def _update(self): raise NotImplementedError

    @abstractmethod
    def _on_control_event(self, data: int): raise NotImplementedError


class AbstractFieldControl(AbstractControl):
    @classmethod
    @abstractmethod
    def can_align(cls, layout: int) -> bool: raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_align_mode(cls, layout: int) -> int: raise NotImplementedError

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_value: str, data_items: str, disabled: bool):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context)
        self.__data_value = data_value
        self.__data_items = data_items
        self.__disabled = disabled
        self.__event_handlers = {}
        self.__on_item_changed_handlers = {}
        self.__aggregate_value = None
        self.__multi_value_constant = '##########'

    @property
    def _value(self): return self.__field().value if self.__items is None else self.__aggregate_value

    @_value.setter
    def _value(self, value):
        items = self.__items
        if items is None:
            if self.__field().value != value: self.__field().value = value
        elif self.__aggregate_value == value:  # Happens when we clicked in the field!
            if value == self.__multi_value_constant: self._select_control_value()
        else:
            self.__aggregate_value = value  # Will give the correct result on item changed event for control!
            for item in items: self.__field(item).value = value

    @property
    def __items(self) -> ObservableList: return getattr(self.data_context, self.__data_items, None)

    def __field(self, item: object=None) -> ObservableField:
        return getattr(item or self.data_context, self.__data_value)

    def _setup(self): self.__reset(); vs.EnableTextEdit(self._dialog_id, self.control_id, not self.__disabled)

    def _update(self): self.__clear_event_handlers(); self.__reset()

    def __reset(self): self.__reset_aggregate(); self.__setup_control(); self.__setup_events()

    def __reset_aggregate(self) -> object:
        self.__aggregate_value = None
        if self.__items is not None:
            for index, item in enumerate(self.__items):
                if index == 0: self.__aggregate_value = self.__field(item).value
                elif self.__aggregate_value != self.__field(item).value: self.__aggregate_value = None; break
        self.__aggregate_value = self.__aggregate_value or self.__multi_value_constant
        return self.__aggregate_value

    def __setup_control(self):
        self._set_control_value(self._value)  # VW doesn't persist initial value for some controls.

    def __setup_events(self):
        items = self.__items
        if items is None:
            self.__field().field_changed_event.subscribe(self.__on_field_changed)
            self.__event_handlers[self.__field().field_changed_event] = self.__on_field_changed
        else:
            items.list_changed_event.subscribe(self.__on_items_changed)
            self.__event_handlers[items.list_changed_event] = self.__on_items_changed
            for item in items: self.__add_on_item_changed_handler(item)

    def __on_field_changed(self, old_value, new_value):
        if self._get_control_value() != new_value: self._set_control_value(new_value)

    def __on_items_changed(self, removed: dict, added: dict):
        for item in removed.values(): self.__remove_on_item_changed_handler(item)
        self.__on_field_changed('', self.__reset_aggregate())
        for item in added.values(): self.__add_on_item_changed_handler(item)

    def __add_on_item_changed_handler(self, item: object):
        on_item_changed_handler = lambda old, new: self.__on_field_changed(
            '', self._value if self.__aggregate_value == new else self.__reset_aggregate())
        self.__on_item_changed_handlers[item] = on_item_changed_handler
        self.__field(item).field_changed_event.subscribe(on_item_changed_handler)

    def __remove_on_item_changed_handler(self, item: object):
        self.__field(item).field_changed_event.unsubscribe(self.__on_item_changed_handlers[item])
        del self.__on_item_changed_handlers[item]

    def __clear_event_handlers(self):
        items = list(self.__on_item_changed_handlers.keys())
        for item in items: self.__remove_on_item_changed_handler(item)
        events = list(self.__event_handlers.keys())
        for event in events:
            event.unsubscribe(self.__event_handlers[event])
            del self.__event_handlers[event]

    @abstractmethod
    def _set_control_value(self, value): return NotImplementedError

    @abstractmethod
    def _get_control_value(self): return NotImplementedError

    @abstractmethod
    def _select_control_value(self): raise NotImplementedError

    @abstractmethod
    def _on_control_event(self, data: int): raise NotImplementedError


class AbstractListControl(AbstractControl, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def can_align(cls, layout: int) -> bool: raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_align_mode(cls, layout: int) -> int: raise NotImplementedError

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_items: str, data_selected_items: str, data_values: tuple):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context)
        self.__data_items = data_items
        self.__data_selected_items = data_selected_items
        self.__data_values = data_values
        self.__event_handlers = {}
        self.__on_item_changed_handlers = {}

    @property
    def _items(self) -> ObservableList: return getattr(self.data_context, self.__data_items)

    @property
    def _selected_items(self) -> ObservableList: return getattr(self.data_context, self.__data_selected_items)

    def _field(self, item: object, data_value: str) -> ObservableField: return getattr(item, data_value)

    def _setup(self): self.__reset()

    def _update(self): self.__clear_event_handlers(); self.__clear_control_items(); self.__reset()

    def __reset(self): self.__setup_control_items(); self.__setup_events();

    def __setup_control_items(self):
        for index, item in enumerate(self._items):
            self.__add_control_item(index, item)
            self._select_control_item(index, item, item in self._selected_items)

    def __setup_events(self):
        self._items.list_changed_event.subscribe(self.__on_items_changed)
        self.__event_handlers[self._items.list_changed_event] = self.__on_items_changed
        self._items.list_reordered_event.subscribe(self.__on_items_reordered)
        self.__event_handlers[self._items.list_reordered_event] = self.__on_items_reordered
        self._selected_items.list_changed_event.subscribe(self.__on_selected_items_changed)
        self.__event_handlers[self._selected_items.list_changed_event] = self.__on_selected_items_changed

    def __on_items_changed(self, removed: dict, added: dict):
        for index in sorted(removed.keys(), reverse=True): self.__remove_control_item(index, removed[index])
        for index in sorted(added.keys(), reverse=False): self.__add_control_item(index, added[index])

    def __on_items_reordered(self): self.__clear_control_items(); self.__setup_control_items()

    def __on_selected_items_changed(self, removed: dict, added: dict):
        for item in removed.values():  # Item can be deselected because of deletion!
            if item in self._items: self._select_control_item(self._items.index(item), item, False)
        for item in added.values(): self._select_control_item(self._items.index(item), item, True)

    def __add_control_item(self, index: int, item: object):
        self._add_control_item(index, item)
        self.__add_on_item_changed_handlers(index, item)

    def __remove_control_item(self, index: int, item: object):
        self.__remove_on_item_changed_handlers(item)
        self._remove_control_item(index, item)

    def __clear_control_items(self):
        self.__clear_on_item_changed_handlers()
        self._clear_control_items()

    def __add_on_item_changed_handlers(self, index: int, item: object):
        if item not in self.__on_item_changed_handlers: self.__on_item_changed_handlers[item] = {}
        for value_index, data_value in enumerate(self.__data_values):
            on_item_changed_handler = lambda old, new, vi=value_index: self._on_item_changed(index, item, vi)
            self.__on_item_changed_handlers[item][value_index] = on_item_changed_handler
            self._field(item, data_value).field_changed_event.subscribe(on_item_changed_handler)

    def __remove_on_item_changed_handlers(self, item: object):
        for value_index, handler in self.__on_item_changed_handlers[item].items():
            self._field(item, self.__data_values[value_index]).field_changed_event.unsubscribe(handler)
        del self.__on_item_changed_handlers[item]

    def __clear_on_item_changed_handlers(self):
        items = list(self.__on_item_changed_handlers.keys())
        for item in items: self.__remove_on_item_changed_handlers(item)

    def __clear_event_handlers(self):
        events = list(self.__event_handlers.keys())
        for event in events:
            event.unsubscribe(self.__event_handlers[event])
            del self.__event_handlers[event]

    @abstractmethod
    def _on_item_changed(self, index: int, item: object, value_index: int): raise NotImplementedError

    @abstractmethod
    def _add_control_item(self, index: int, item: object): raise NotImplementedError

    @abstractmethod
    def _remove_control_item(self, index: int, item: object): raise NotImplementedError

    @abstractmethod
    def _clear_control_items(self): raise NotImplementedError

    @abstractmethod
    def _select_control_item(self, index: int, item: object, selected: bool): raise NotImplementedError

    @abstractmethod
    def _on_control_event(self, data: int): raise NotImplementedError

    def _change_selection(self, new_selection: tuple):
        self._selected_items.suspend_events()
        self._selected_items.clear()
        self._selected_items.extend(new_selection)
        self._selected_items.resume_events()

    def _delete_selected(self):
        if vs.AlertQuestion('Are you sure you want to delete the selected items?', '', 0, 'Ok', 'Cancel', '', '') == 1:
            self._items.suspend_events()
            max_index = max(self._items.index(item) for item in self._selected_items)
            for item in self._selected_items: self._items.remove(item)
            self._items.resume_events()
            # Build-in VW lists will select a new item if possible, mostly the highest selected index!
            # We will mimic this behavior for consistency.
            length = len(self._items)
            if length > 0: self._change_selection((self._items[max_index if max_index < length else length - 1],))


class ControlFactory(object, metaclass=SingletonMeta):
    def __init__(self): self.__last_control_id = 10

    def __generate_control_id(self) -> int: self.__last_control_id += 1; return self.__last_control_id

    def create_controls(self, dialog_id: int, controls: list, data_parent: AbstractDataContext) -> tuple:
        created = []
        for control in controls:
            for name, data in xml_to_dict_util.filter_elements(control).items():
                created.append(self.create_control(dialog_id, name, data, data_parent))
        return tuple(created)

    def create_control(self, dialog_id: int, name: str, data: dict,
                       data_parent: AbstractDataContext) -> AbstractControl:
        return getattr(
            importlib.import_module('dlibrary.dialog.controls.' + name.replace('-', '')), 'create'
        )(dialog_id, self.__generate_control_id(), data or {}, data_parent)