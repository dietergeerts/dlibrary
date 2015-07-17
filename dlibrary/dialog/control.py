from abc import ABCMeta
from abc import abstractmethod
import importlib

from dlibrary.utility.decorator import AbstractPropertyClassDecorator
from dlibrary.utility.observable import ObservableField, ObservableList, ObservableMethod
from dlibrary.utility import xmltodict as xml_to_dict_util
from dlibrary.utility.eventing import Event
from dlibrary.utility.singleton import SingletonMeta
import vs


class Layout(object):
    VERTICAL = 1
    HORIZONTAL = 2

    @staticmethod
    def from_string(value: str) -> int:
        return {
            'VERTICAL': Layout.VERTICAL,
            'HORIZONTAL': Layout.HORIZONTAL
        }.get(value)


class AlignEdgeEnum(object):
    RIGHT = 1
    BOTTOM = 2
    LEFT = 3


class AlignMode(object):
    RESIZE = 0
    SHIFT = 1


class AlignFactory(object, metaclass=SingletonMeta):
    def __init__(self):
        self.__last_align_id = 10

    def generate_align_id(self) -> int:
        self.__last_align_id += 1
        return self.__last_align_id


class Align(AbstractPropertyClassDecorator):
    """
    Decorator to set how a control will be aligned.
    """

    def __init__(self, mode):
        """
        :type mode: AlignMode(Enum) || {Layout(Enum): AlignMode(Enum)}
        """
        super().__init__(mode if isinstance(mode, dict) else {Layout.VERTICAL: mode, Layout.HORIZONTAL: mode})

    @classmethod
    def has_alignment(cls, control: object, layout: int) -> bool:
        """
        :type layout: Layout(Enum)
        """
        return layout in cls._get_property_value(control)

    @classmethod
    def get_alignment(cls, control: object, layout: int) -> int:
        """
        :type layout: Layout(Enum)
        :rtype: AlignMode(Enum)
        """
        return cls._get_property_value(control)[layout]


class TextAlignEnum(object):
    LEFT = 1
    CENTER = 2
    RIGHT = 3

    @staticmethod
    def from_string(value: str) -> int:
        return {
            'LEFT': TextAlignEnum.LEFT,
            'CENTER': TextAlignEnum.CENTER,
            'RIGHT': TextAlignEnum.RIGHT
        }.get(value)


class TextStyleEnum(object):
    REGULAR = 0
    CAPTION = 1
    BOLD = 2
    REDUCED = 3

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
    def data_context_changed(self) -> Event:
        return self.__data_context_changed

    # Will be used only by the topmost one, the Dialog, as all the rest are AbstractControl objects.
    # That's why we use the default to have no error thrown, and an attr should be found if it was declared.
    def getattr(self, name: str, default: object=None) -> object:
        return getattr(self.__data_context, name, default)


class AbstractControl(AbstractDataContext, metaclass=ABCMeta):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str=''):
        super().__init__(None)
        self.__dialog_id = dialog_id
        self.__control_id = control_id
        vs.SetHelpText(dialog_id, control_id, help_text)
        self.__data_parent = data_parent
        self.__data_context = data_context
        self.__data_context_field = None
        """@type: ObservableField"""
        self.__data_disabled = data_disabled
        self.__data_disabled_method = None
        """@type: ObservableMethod"""
        self.__init_data_contexts_and_observables()

    @property
    def _dialog_id(self) -> int:
        return self.__dialog_id

    @property
    def control_id(self) -> int:
        return self.__control_id

    # Overridden from AbstractDataContext, as this is never the topmost one!
    def getattr(self, name: str, default: object=None) -> object:
        try:  # First try to get the attribute from our own data_context.
            if self.__data_context_field is None:
                raise AttributeError()
            return getattr(self.__data_context_field.value, name)
        except AttributeError:  # Then look further up the chain.
            return self.__data_parent.getattr(name, default)

    def setup(self, register_event_handler: callable):
        register_event_handler(self.control_id, self._on_control_event)
        self._setup()
        self._update()

    def __init_data_contexts_and_observables(self):
        self.__data_parent.data_context_changed.subscribe(self.__on_parent_data_context_changed)
        self.__setup_data_contexts_and_observables()

    def __setup_data_contexts_and_observables(self):
        if self.__data_context:
            self.__data_context_field = self.__data_parent.getattr(self.__data_context, ObservableField())
            """@type: ObservableField"""
            self.__data_context_field.field_changed_event.subscribe(self.__on_data_context_changed)
        if self.__data_disabled:
            self.__data_disabled_method = self.getattr(self.__data_disabled, ObservableMethod(lambda: False))
            """@type: ObservableMethod"""
            self.__data_disabled_method.method_changed_event.subscribe(self.__on_data_disabled_method_changed)
            self.__on_data_disabled_method_changed()

    def __reset_data_contexts_and_observables(self):
        if self.__data_context:
            self.__data_context_field.field_changed_event.unsubscribe(self.__on_data_context_changed)
        if self.__data_disabled:
            self.__data_disabled_method.method_changed_event.unsubscribe(self.__on_data_disabled_method_changed)
        self.__setup_data_contexts_and_observables()

    def __on_parent_data_context_changed(self, *args):
        self.__reset_data_contexts_and_observables()
        self._update()
        self.data_context_changed.raise_event(*args)

    def __on_data_context_changed(self, *args):
        self._update()
        self.data_context_changed.raise_event(*args)

    def __on_data_disabled_method_changed(self):
        vs.EnableItem(self._dialog_id, self.control_id, not self.__data_disabled_method.apply())

    @abstractmethod
    def _setup(self):
        raise NotImplementedError

    @abstractmethod
    def _update(self):
        raise NotImplementedError

    @abstractmethod
    def _on_control_event(self, data: int):
        raise NotImplementedError


class AbstractGroupControl(AbstractControl, metaclass=ABCMeta):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled)
        self.__controls = tuple()

    def add_controls(self, controls: tuple, layout: int):
        self.__controls = controls
        self.__arrange_controls(layout)
        self.__align_controls(layout)

    def __arrange_controls(self, layout: int):
        for index, control in enumerate(self.__controls):
            if index == 0:
                vs.SetFirstGroupItem(self._dialog_id, self.control_id, control.control_id)
            elif layout == Layout.HORIZONTAL:
                vs.SetRightItem(self._dialog_id, self.__controls[index - 1].control_id, control.control_id, 0, 0)
            else:
                vs.SetBelowItem(self._dialog_id, self.__controls[index - 1].control_id, control.control_id, 0, 0)

    def __align_controls(self, layout: int):
        """
        :type layout: Layout(Enum)
        """
        align_id = AlignFactory().generate_align_id()
        for control in self.__controls:
            if Align.has_decorator(control) and Align.has_alignment(control, layout):
                align_edge = AlignEdgeEnum.BOTTOM if layout == Layout.HORIZONTAL else AlignEdgeEnum.RIGHT
                align_mode = Align.get_alignment(control, layout)
                vs.AlignItemEdge(self._dialog_id, control.control_id, align_edge, align_id, align_mode)

    def setup(self, register_event_handler: callable):
        super().setup(register_event_handler)
        for control in self.__controls:
            control.setup(register_event_handler)

    @abstractmethod
    def _setup(self):
        raise NotImplementedError

    @abstractmethod
    def _update(self):
        raise NotImplementedError

    @abstractmethod
    def _on_control_event(self, data: int):
        raise NotImplementedError


class AbstractFieldControl(AbstractControl, metaclass=ABCMeta):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, data_value: str, data_items: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled)
        self.__data_value = data_value
        self.__data_items = data_items
        self.__value_observable = None
        """@type: ObservableField"""
        self.__items_observable = None
        """@type: ObservableList"""
        self.__item_value_fields = {}
        self.__item_changed_handlers = {}
        self.__aggregate_value = None
        self.__multi_value_constant = '##########'
        self.__init_observables()

    @property
    def _multi_value_constant(self) -> str:
        return self.__multi_value_constant

    @property
    def _value(self):
        return self.__value_observable.value if self.__items_observable is None else self.__aggregate_value

    @_value.setter
    def _value(self, value):
        if self.__data_items == '':
            if self.__value_observable.value != value:
                self.__value_observable.value = value
        else:
            if self.__aggregate_value != value:
                self.__aggregate_value = value  # Will give the correct result on item changed event for control!
                for item in self.__items_observable:
                    self.__item_value_fields[item].value = value

    def _setup(self):
        pass

    def _update(self):
        self.__reset_observables()
        self.__reset_aggregate()
        self.__reset_control()

    def __init_observables(self):
        self.__setup_observables()

    def __setup_observables(self):
        if self.__data_items == '':
            self.__value_observable = self.getattr(self.__data_value, ObservableField())
            """@type: ObservableField"""
            self.__value_observable.field_changed_event.subscribe(self.__on_value_changed)
        else:
            self.__items_observable = self.getattr(self.__data_items, ObservableList())
            """@type: ObservableList"""
            self.__items_observable.list_changed_event.subscribe(self.__on_items_changed)
            for item in self.__items_observable:
                self.__add_item_value_field_and_changed_handler(item)

    def __reset_observables(self):
        if self.__data_items == '':
            self.__value_observable.field_changed_event.unsubscribe(self.__on_value_changed)
            self.__setup_observables()
        else:
            self.__items_observable.list_changed_event.unsubscribe(self.__on_items_changed)
            for item in self.__items_observable:
                self.__remove_item_value_field_and_changed_handler(item)
            self.__setup_observables()

    def __reset_aggregate(self) -> object:
        if self.__data_items != '' and len(self.__items_observable) > 0:
            self.__aggregate_value = self.__item_value_fields[self.__items_observable[0]].value
            for index in range(1, len(self.__items_observable)):
                if self.__aggregate_value != self.__item_value_fields[self.__items_observable[index]].value:
                    self.__aggregate_value = self.__multi_value_constant
                    break
        else:
            self.__aggregate_value = None
        return self.__aggregate_value

    def __reset_control(self):
        self._set_control_value(self._value)  # VW doesn't persist initial value for some controls.

    # noinspection PyUnusedLocal
    def __on_value_changed(self, old_value, new_value):
        # Always check if the control triggered this to prevent infinite loops!
        if self._get_control_value() != new_value:
            self._set_control_value(new_value)

    def __on_items_changed(self, removed: dict, added: dict):
        for item in removed.values():
            self.__remove_item_value_field_and_changed_handler(item)
        for item in added.values():
            self.__add_item_value_field_and_changed_handler(item)
        self.__on_value_changed('', self.__reset_aggregate())

    def __add_item_value_field_and_changed_handler(self, item: object):
        item_changed_handler = lambda old, new: self.__on_value_changed('', self.__reset_aggregate())
        self.__item_changed_handlers[item] = item_changed_handler
        self.__item_value_fields[item] = getattr(item, self.__data_value, ObservableField())
        self.__item_value_fields[item].field_changed_event.subscribe(item_changed_handler)

    def __remove_item_value_field_and_changed_handler(self, item: object):
        self.__item_value_fields.pop(item).field_changed_event.unsubscribe(self.__item_changed_handlers.pop(item))

    @abstractmethod
    def _set_control_value(self, value):
        return NotImplementedError

    @abstractmethod
    def _get_control_value(self):
        return NotImplementedError

    @abstractmethod
    def _on_control_event(self, data: int):
        raise NotImplementedError


class AbstractListControl(AbstractControl, metaclass=ABCMeta):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, data_items: str, data_selected_items: str, data_values: tuple):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled)
        self.__data_items = data_items
        self.__data_selected_items = data_selected_items
        self.__data_values = data_values
        self.__items_observable = None
        """@type: ObservableList"""
        self.__selected_items_observable = None
        """@type: ObservableList"""
        self.__item_value_fields = {}
        self.__item_changed_handlers = {}
        self.__init_observables()

    @property
    def _items(self) -> ObservableList:
        return self.__items_observable

    @property
    def _selected_items(self) -> ObservableList:
        return self.__selected_items_observable

    def _get_item_value(self, item: object, data_value: str) -> dict:
        return self.__item_value_fields[item][data_value].value

    def _setup(self):
        pass

    def _update(self):
        self.__reset_observables()
        self.__reset_control()

    def __init_observables(self):
        self.__setup_observables()

    def __setup_observables(self):
        self.__items_observable = self.getattr(self.__data_items)
        """@type: ObservableList"""
        self.__selected_items_observable = self.getattr(self.__data_selected_items)
        """@type: ObservableList"""
        self.__items_observable.list_changed_event.subscribe(self.__on_items_changed)
        self.__items_observable.list_reordered_event.subscribe(self.__on_items_reordered)
        self.__selected_items_observable.list_changed_event.subscribe(self.__on_selected_items_changed)
        for item in self.__items_observable:
            self.__add_item_value_fields_and_changed_handlers(item)

    def __reset_observables(self):
        self.__items_observable.list_changed_event.unsubscribe(self.__on_items_changed)
        self.__items_observable.list_reordered_event.unsubscribe(self.__on_items_reordered)
        self.__selected_items_observable.list_changed_event.unsubscribe(self.__on_selected_items_changed)
        for item in self.__items_observable:
            self.__remove_item_value_fields_and_changed_handlers(item)
        self.__setup_observables()

    def __reset_control(self):
        self._clear_control_items()
        for index, item in enumerate(self.__items_observable):
            self._add_control_item(index, item)
            self._select_control_item(index, item, item in self.__selected_items_observable)

    def __on_items_reordered(self):
        self.__reset_control()

    def __on_items_changed(self, removed: dict, added: dict):
        for index in sorted(removed.keys(), reverse=True):
            self.__remove_item_value_fields_and_changed_handlers(removed[index])
            self._remove_control_item(index, removed[index])
        for index in sorted(added.keys(), reverse=False):
            self.__add_item_value_fields_and_changed_handlers(added[index])
            self._add_control_item(index, added[index])

    def __on_selected_items_changed(self, removed: dict, added: dict):
        for item in removed.values():
            if item in self.__items_observable:  # Item can be deselected because of deletion!
                self._select_control_item(self.__items_observable.index(item), item, False)
        for item in added.values():
            self._select_control_item(self.__items_observable.index(item), item, True)

    def __add_item_value_fields_and_changed_handlers(self, item: object):
        if item not in self.__item_value_fields:
            self.__item_value_fields[item] = {}
        if item not in self.__item_changed_handlers:
            self.__item_changed_handlers[item] = {}
        for vindex, data_value in enumerate(self.__data_values):
            iindex = self.__items_observable.index(item)
            item_changed_handler = lambda old, new, vi=vindex, ii=iindex: self._on_item_changed(ii, item, vi)
            self.__item_changed_handlers[item][data_value] = item_changed_handler
            self.__item_value_fields[item][data_value] = getattr(item, data_value, ObservableField())
            self.__item_value_fields[item][data_value].field_changed_event.subscribe(item_changed_handler)

    def __remove_item_value_fields_and_changed_handlers(self, item: object):
        value_fields = self.__item_value_fields.pop(item)
        changed_handlers = self.__item_changed_handlers.pop(item)
        for data_value, field in value_fields.items():
            assert isinstance(field, ObservableField)
            field.field_changed_event.unsubscribe(changed_handlers[data_value])

    @abstractmethod
    def _on_item_changed(self, index: int, item: object, value_index: int):
        raise NotImplementedError

    @abstractmethod
    def _add_control_item(self, index: int, item: object):
        raise NotImplementedError

    @abstractmethod
    def _remove_control_item(self, index: int, item: object):
        raise NotImplementedError

    @abstractmethod
    def _clear_control_items(self):
        raise NotImplementedError

    @abstractmethod
    def _select_control_item(self, index: int, item: object, selected: bool):
        raise NotImplementedError

    @abstractmethod
    def _on_control_event(self, data: int):
        raise NotImplementedError

    def _change_selection(self, new_selection: tuple):
        self.__selected_items_observable.suspend_events()
        self.__selected_items_observable.clear()
        self.__selected_items_observable.extend(new_selection)
        self.__selected_items_observable.resume_events()

    def _delete_selected(self):
        if vs.AlertQuestion('Are you sure you want to delete the selected items?', '', 0, 'Ok', 'Cancel', '', '') == 1:
            max_index = max(self.__items_observable.index(item) for item in self.__selected_items_observable)
            self.__items_observable.suspend_events()
            for item in self.__selected_items_observable:
                self.__items_observable.remove(item)
            self.__items_observable.resume_events()
            # Build-in VW lists will select a new item if possible, mostly the highest selected index!
            # We will mimic this behavior for consistency.
            length = len(self.__items_observable)
            if length > 0:
                self._change_selection((self.__items_observable[max_index if max_index < length else length - 1],))


class ControlFactory(object, metaclass=SingletonMeta):
    def __init__(self):
        self.__last_control_id = 10

    def __generate_control_id(self) -> int:
        self.__last_control_id += 1
        return self.__last_control_id

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