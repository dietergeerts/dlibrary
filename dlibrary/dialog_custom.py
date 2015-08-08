from abc import ABCMeta, abstractmethod

from dlibrary.document import AbstractResourceList
from dlibrary.utility import XmlFileLists, Event, VSException, Convert, SingletonMeta, AbstractPropertyClassDecorator, \
    ObservableField, ObservableMethod, ObservableList, XmlDict
from dlibrary.utility import AbstractXmlFile
from dlibrary.vectorworks import ActivePlugIn
import vs


@XmlFileLists(lists={'control'})
class AbstractActivePlugInDialogXmlFile(AbstractXmlFile, metaclass=ABCMeta):

    def __init__(self, dialog_name: str, active_plugin_type: str):
        """
        :type active_plugin_type: ActivePlugInType(Enum)
        """
        _, file_path = vs.FindFileInPluginFolder(ActivePlugIn().name + active_plugin_type)
        super().__init__(file_path + ActivePlugIn().name + dialog_name + 'Dialog.xml')


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


class Dialog(AbstractDataContext):

    def __init__(self, dialog_file: AbstractActivePlugInDialogXmlFile, data_context: object):
        super().__init__(data_context)
        try:
            view = dialog_file.load()
        except (VSException, FileNotFoundError, PermissionError, OSError):
            raise
        else:
            self.__event_handlers = {}
            self.__dialog_id = self.__create_layout(view)
            self.__dialog_control = ControlFactory().create_controls(
                self.__dialog_id, self.__get_dialog_control(view['dialog']), self)[0]
            vs.SetFirstLayoutItem(self.__dialog_id, self.__dialog_control.control_id)

    @staticmethod
    def __create_layout(view: dict) -> int:
        return vs.CreateLayout(
            Dialog.__create_title(view),
            Convert.str2bool(view['dialog'].get('@help', 'False')),
            view['dialog'].get('@ok', 'Ok'),
            view['dialog'].get('@cancel', 'Cancel'))

    @staticmethod
    def __create_title(view: dict) -> str:
        return ('%s - %s %s' % (
            view['dialog']['@title'], ActivePlugIn().name,
            'v%s' % ActivePlugIn().version if ActivePlugIn().version != '' else ''
        )).strip()  # To remove the space left when there is no version.

    @staticmethod
    def __get_dialog_control(dialog: dict) -> list:
        return [{'group-box': {'@layout': dialog.get('@layout', 'VERTICAL'), 'control': dialog['control']}}]

    def show(self) -> bool:  # 1 for Ok, 2 for Cancel.
        return vs.RunLayoutDialog(self.__dialog_id, lambda item, data: self.__dialog_handler(item, data)) == 1

    def __dialog_handler(self, item, data):
        if item == 12255:
            self.__on_setup()
        elif item == 1:
            self.__on_ok()
        elif item == 2:
            self.__on_cancel()
        elif item in self.__event_handlers:
            self.__event_handlers[item](data)  # VW sends control events with their id.
        return item  # Required by VW!

    def __register_event_handler(self, control_id: int, event_handler: callable):
        self.__event_handlers[control_id] = event_handler

    def __on_setup(self):
        self.__dialog_control.setup(self.__register_event_handler)

    def __on_ok(self):
        pass

    def __on_cancel(self):
        pass


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


@Align(mode=AlignMode.SHIFT)
class Button(AbstractControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_command: str, caption: str):
        """
        :param data_command: Must resolve to an ObservableCommand up the data context tree.
        :raises ValueError: if data_command is not a string, or an empty string.
        :raises ValueError: if caption is not a string, or an empty string.
        """
        if not isinstance(data_command, str) or not data_command:
            raise ValueError('data_command must be a not empty string.')
        if not isinstance(caption, str) or not caption:
            raise ValueError('caption must be a not empty string.')

        super().__init__(dialog_id, control_id, help_text, data_parent, data_context)

        self.__data_command = data_command
        self.__data_command_observable = None
        vs.CreatePushButton(dialog_id, control_id, caption)
        self.__init_observables()

    def _setup(self):
        pass

    def _update(self):
        self.__reset_observables()

    def __init_observables(self):
        self.__setup_observables()

    def __setup_observables(self):
        self.__data_command_observable = self.getattr(self.__data_command)
        """:type: ObservableCommand"""
        # noinspection PyUnresolvedReferences
        self.__data_command_observable.can_execute_changed_event.subscribe(self.__on_can_execute_changed)
        self.__on_can_execute_changed()

    def __reset_observables(self):
        self.__data_command_observable.can_execute_changed_event.unsubscribe(self.__on_can_execute_changed)
        self.__setup_observables()

    def __on_can_execute_changed(self):
        vs.EnableItem(self._dialog_id, self.control_id, self.__data_command_observable.can_execute())

    def _on_control_event(self, data: int):
        self.__data_command_observable.execute()


@Align(mode={Layout.VERTICAL: AlignMode.RESIZE})
class EditText(AbstractFieldControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, data_value: str, data_items: str, width: int, height: int):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled, data_value,
                         data_items)
        if height > 1:
            vs.CreateEditTextBox(dialog_id, control_id, self._value, width, height)
        else:
            vs.CreateEditText(dialog_id, control_id, self._value, width)

    def _set_control_value(self, value):
        vs.SetItemText(self._dialog_id, self.control_id, value)

    def _get_control_value(self):
        return vs.GetItemText(self._dialog_id, self.control_id)

    def _on_control_event(self, data: int):
        self._value = self._get_control_value()


@Align(mode=AlignMode.RESIZE)
class GroupBox(AbstractGroupControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, header: str, border: bool):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled)
        vs.CreateGroupBox(dialog_id, control_id, header, border)

    def _setup(self):
        pass

    def _update(self):
        pass

    def _on_control_event(self, data: int):
        pass


@Align(mode=AlignMode.RESIZE)
class ListBox(AbstractListControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, data_items: str, data_selected_items: str, data_value: str,
                 width: int, height: int):
        super().__init__(dialog_id, control_id, self.__create_help_text(help_text), data_parent, data_context,
                         data_disabled, data_items, data_selected_items, (data_value,))
        self.__data_value = data_value
        vs.CreateListBoxN(dialog_id, control_id, width, height, True)

    @staticmethod
    def __create_help_text(help_text: str) -> str:
        help_text += ' | DELETE: You can delete the selected items with the delete key.'
        help_text += ' | WALK: You can walk through the items with the up and down key.'
        return help_text

    def _on_item_changed(self, index: int, item: object, value_index: int):
        self._remove_control_item(index, item)
        self._add_control_item(index, item)
        self._select_control_item(index, item, item in self._selected_items)

    def _add_control_item(self, index: int, item: object):
        vs.AddChoice(self._dialog_id, self.control_id, self._get_item_value(item, self.__data_value), index)

    def _remove_control_item(self, index: int, item: object):
        vs.RemoveChoice(self._dialog_id, self.control_id, index)

    def _clear_control_items(self):
        vs.DeleteAllItems(self._dialog_id, self.control_id)

    def _select_control_item(self, index: int, item: object, selected: bool):
        vs.SelectChoice(self._dialog_id, self.control_id, index, selected)

    def _on_control_event(self, data: int):
        if data >= 0:
            self.__on_selection()  # Index of last selected, of last if clicked on white space.
        elif -6:
            self.__on_delete_key_pressed()

    def __on_selection(self):
        selected_indexes = []
        index = -1
        while True:
            index = vs.GetSelectedChoiceIndex(self._dialog_id, self.control_id, index+1)
            if index != -1:
                selected_indexes.append(index)
            if index == -1 or index == len(self._items) - 1:
                break
        self._change_selection(tuple(self._items[index] for index in selected_indexes))

    def __on_delete_key_pressed(self):
        self._delete_selected()


class ControlTypeEnum(object):
    STATIC = 1
    RADIO_ICON = 2
    TOGGLE = 3
    TOGGLE_ICON = 4
    STATIC_ICON = 5
    NUMBER = 6
    MULTI_ICON = 7

    @staticmethod
    def from_string(value: str) -> int:
        return {
            'STATIC': ControlTypeEnum.STATIC,
            'RADIO_ICON': ControlTypeEnum.RADIO_ICON,
            'TOGGLE': ControlTypeEnum.TOGGLE,
            'TOGGLE_ICON': ControlTypeEnum.TOGGLE_ICON,
            'STATIC_ICON': ControlTypeEnum.STATIC_ICON,
            'NUMBER': ControlTypeEnum.NUMBER,
            'MULTI_ICON': ControlTypeEnum.MULTI_ICON
        }.get(value)


class DisplayTypeEnum(object):
    TEXT_ONLY = 0
    ICON_ONLY = 1
    TEXT_AND_ICON = 3

    @staticmethod
    def from_string(value: str) -> int:
        return {
            'TEXT_ONLY': DisplayTypeEnum.TEXT_ONLY,
            'ICON_ONLY': DisplayTypeEnum.ICON_ONLY,
            'TEXT_AND_ICON': DisplayTypeEnum.TEXT_AND_ICON
        }.get(value)


class Column(object):
    def __init__(self, header: str, width: int, control_type: int, display_type: int, text_align: int, data_value: str):
        self.__header = header
        self.__width = width
        self.__control_type = control_type
        self.__display_type = display_type
        self.__text_align = text_align
        self.__data_value = data_value

    @property
    def header(self):
        return self.__header

    @property
    def width(self):
        return self.__width

    @property
    def control_type(self):
        return self.__control_type

    @property
    def display_type(self):
        return self.__display_type

    @property
    def text_align(self):
        return self.__text_align

    @property
    def data_value(self):
        return self.__data_value


@Align(mode=AlignMode.RESIZE)
class ListBrowser(AbstractListControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, data_items: str, data_selected_items: str, index: bool,
                 columns: tuple, width: int,
                 height: int):
        super().__init__(dialog_id, control_id, self.__create_help_text(help_text, index), data_parent, data_context,
                         data_disabled, data_items, data_selected_items, tuple(column.data_value for column in columns))
        self.__index = index
        self.__columns = ((self.__create_index_column(),) + columns) if index else columns
        vs.CreateLB(dialog_id, control_id, width, height)

    @staticmethod
    def __create_help_text(help_text: str, index: bool) -> str:
        help_text += ' | SORTING: You can sort the list by clicking on the appropriate column.'
        help_text += ' | REORDER: You can reorder the list by drag-drop the selected items on the index column' \
                     ' IF no other column is sorted' if index else ''
        help_text += ' | DELETE: You can delete the selected items with the delete key.'
        help_text += ' | WALK: You can walk through the items with the up and down key.'
        return help_text

    @staticmethod
    def __create_index_column() -> Column:
        return Column('#', 30, ControlTypeEnum.NUMBER, DisplayTypeEnum.TEXT_ONLY, TextAlignEnum.RIGHT, '')

    def _setup(self):
        self.__setup_columns()
        self.__setup_drag_drop()
        super()._setup()  # Setup items.
        vs.EnableLBColumnLines(self._dialog_id, self.control_id, True)
        vs.RefreshLB(self._dialog_id, self.control_id)  # Refresh needed to reflect setup.

    def __setup_columns(self):
        for index, column in enumerate(self.__columns):
            vs.InsertLBColumn(self._dialog_id, self.control_id, index, column.header, column.width)
            vs.SetLBControlType(self._dialog_id, self.control_id, index, column.control_type)
            # Display type is set through different functions according to the control type.
            if column.control_type == ControlTypeEnum.STATIC or column.control_type == ControlTypeEnum.NUMBER:
                vs.SetLBItemDisplayType(self._dialog_id, self.control_id, index, column.display_type)
            elif column.control_type != ControlTypeEnum.RADIO_ICON:
                vs.SetLBEditDisplayType(self._dialog_id, self.control_id, index, column.display_type)

    def __setup_drag_drop(self):
        if self.__index:
            vs.EnableLBDragAndDrop(self._dialog_id, self.control_id, True)
            vs.SetLBDragDropColumn(self._dialog_id, self.control_id, 0)
            vs.SetLBSortColumn(self._dialog_id, self.control_id, 0, False)

    def _on_item_changed(self, index: int, item: object, value_index: int):
        column_index = value_index + (1 if self.__index else 0)
        vs.SetLBItemInfo(self._dialog_id, self.control_id, self.__get_control_index(index), column_index,
                         str(self._get_item_value(item, self.__columns[column_index].data_value)), -1)

    def _add_control_item(self, index: int, item: object):
        if self.__index:
            self.__update_index_column(index, +1)
        vs.InsertLBItem(self._dialog_id, self.control_id, index, '')
        for column_index, column in enumerate(self.__columns):
            vs.SetLBItemInfo(
                self._dialog_id, self.control_id, index, column_index,
                (index + 1) if (self.__index and column_index == 0)
                else str(self._get_item_value(item, column.data_value)), -1)
            vs.SetLBItemTextJust(self._dialog_id, self.control_id, index, column_index, column.text_align)
        self.__update_sorting()

    def _remove_control_item(self, index: int, item: object):
        vs.DeleteLBItem(self._dialog_id, self.control_id, self.__get_control_index(index))
        if self.__index:
            self.__update_index_column(index, -1)

    def __update_index_column(self, changed_index, modifier):
        for control_index in range(0, vs.GetNumLBItems(self._dialog_id, self.control_id)):
            item_info = vs.GetLBItemInfo(self._dialog_id, self.control_id, control_index, 0)
            item_index = int(item_info[1]) - 1
            if item_index >= changed_index:
                vs.SetLBItemInfo(
                    self._dialog_id, self.control_id, control_index, 0, item_index + 1 + modifier, item_info[2])

    def __update_sorting(self):
        sort_column = vs.GetLBSortColumn(self._dialog_id, self.control_id)
        if sort_column > -1:
            is_descending = vs.GetLBColumnSortState(self._dialog_id, self.control_id, sort_column) == 1
            vs.SetLBSortColumn(self._dialog_id, self.control_id, sort_column, is_descending)

    def _clear_control_items(self):
        vs.DeleteAllLBItems(self._dialog_id, self.control_id)

    def _select_control_item(self, index: int, item: object, selected: bool):
        index = self.__get_control_index(index)
        vs.SetLBSelection(self._dialog_id, self.control_id, index, index, selected)

    def __get_control_index(self, item_index: int) -> int:
        for control_index in range(0, vs.GetNumLBItems(self._dialog_id, self.control_id)):
            item_info = vs.GetLBItemInfo(self._dialog_id, self.control_id, control_index, 0)
            if int(item_info[1]) - 1 == item_index:
                return control_index

    def _on_control_event(self, data: int):
        event_info = vs.GetLBEventInfo(self._dialog_id, self.control_id)
        # data = tuple(success: bool, eventType: int, rowIndex: int, columnIndex: int)
        if event_info[0]:
            {
                -1: self.__on_dialog_start,
                -2: self.__on_data_change_click,
                -3: self.__on_data_change_all_click,
                -4: self.__on_single_click,
                -5: self.__on_double_click,
                -6: self.__on_delete_key_pressed,
                -7: self.__on_up_key_pressed,
                -8: self.__on_down_key_pressed,
                -9: self.__on_alpha_numeric_key_pressed,
                -10: self.__on_column_header_click,
                -12: self.__on_enter_key_pressed,
                -13: self.__on_data_change_recursive_click,
                -14: self.__on_double_all_click,
                -15: self.__on_double_recursive_click
            }.get(event_info[1])(data, event_info[2], event_info[3])

    def __on_dialog_start(self, data: int, row_index: int, column_index: int):
        pass  # TODO: Does this still happen? I can't catch it!

    def __on_data_change_click(self, data: int, row_index: int, column_index: int):
        pass  # TODO: Investigate and implement if needed.

    def __on_data_change_all_click(self, data: int, row_index: int, column_index: int):
        pass  # TODO: Investigate and implement if needed.

    def __on_single_click(self, data: int, row_index: int, column_index: int):
        if self.__is_drag_drop_event(data):
            self.__on_drag_drop(data, row_index, column_index)
        else:
            self.__on_selection(data, row_index, column_index)

    def __on_double_click(self, data: int, row_index: int, column_index: int):
        pass  # TODO: Doesn't seem to happen? Check with community.

    # noinspection PyUnusedLocal
    def __on_delete_key_pressed(self, data: int, row_index: int, column_index: int):
        # If the last item was selected, then the new last item will become selected without an event!
        self._delete_selected()
        # TODO: Check this out and fix it!
        # self.__on_selection(data, row_index, column_index)

    def __on_up_key_pressed(self, data: int, row_index: int, column_index: int):
        # If nothing is selected, the first one will become selected. If first was selected, it stays selected.
        self.__on_selection(data, row_index, column_index)

    def __on_down_key_pressed(self, data: int, row_index: int, column_index: int):
        # If nothing is selected, the first one will become selected. If last was selected, it stays selected.
        # Orso saw that the row- and columnIndex are always -1 > TODO: Check this.
        self.__on_selection(data, row_index, column_index)

    def __on_alpha_numeric_key_pressed(self, data: int, row_index: int, column_index: int):
        pass  # TODO: Implement search in one of the columns?
        # When using the num pad with an index column, the item with that number becomes selected.
        # So it would be logical to implement something similar.

    # noinspection PyUnusedLocal
    def __on_column_header_click(self, data: int, row_index: int, column_index: int):
        # Only happens when sorting is enabled. Drag-drop can only happen when the index column is sorted!
        if self.__index:
            vs.EnableLBDragAndDrop(
                self._dialog_id, self.control_id, vs.GetLBSortColumn(self._dialog_id, self.control_id) == 0)

    def __on_enter_key_pressed(self, data: int, row_index: int, column_index: int):
        pass  # TODO: Doesn't seem to happen? Check with community.

    def __on_data_change_recursive_click(self, data: int, row_index: int, column_index: int):
        pass  # TODO: investigate and implement when needed.

    def __on_double_all_click(self, data: int, row_index: int, column_index: int):
        pass  # TODO: Doesn't seem to happen? Check with community.

    def __on_double_recursive_click(self, data: int, row_index: int, column_index: int):
        pass  # TODO: investigate and implement when needed.

    @staticmethod
    def __is_drag_drop_event(data: int) -> bool:
        # VW throws a normal -4 event when start dragging, and 3x the -4 event on drop.
        # We can check the data event parameter, as it is -50, 43703408 and -51 on drop.
        return data == -50 or data == 43703408 or data == -51

    # noinspection PyUnusedLocal
    def __on_drag_drop(self, data: int, row_index: int, column_index: int):
        # On the last drop event, data is -51.
        if data == -51:
            self._items.suspend_events()
            items_copy = list(self._items.data)
            reverse = vs.GetLBColumnSortState(self._dialog_id, self.control_id, 0) == 1  # 0: none; -1: 1..n; 1: n..1
            for index in range(0, len(self._items)):
                item_info = vs.GetLBItemInfo(self._dialog_id, self.control_id, index, 0)
                # item_info = tuple(success: bool, itemText: str, itemIcon: int)
                old_index = int(item_info[1]) - 1
                new_index = (len(self._items) - 1 - index) if reverse else index
                self._items[new_index] = items_copy[old_index]
                vs.SetLBItemInfo(self._dialog_id, self.control_id, index, 0, new_index + 1, item_info[2])
            self._items.resume_events()

    # noinspection PyUnusedLocal
    def __on_selection(self, data: int, row_index: int, column_index: int):
        # Beware that the rowIndex can be -1 when clicked on white space!
        selected_indexes = []
        for index in range(0, len(self._items)):
            if vs.IsLBItemSelected(self._dialog_id, self.control_id, index):
                item_info = vs.GetLBItemInfo(self._dialog_id, self.control_id, index, 0)
                selected_indexes.append(int(item_info[1]) - 1)
        self._change_selection(tuple(self._items[index] for index in sorted(selected_indexes)))


@Align(mode={Layout.VERTICAL: AlignMode.RESIZE})
class PullDownMenu(AbstractFieldControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, data_available_items: str, data_value: str, data_items: str,
                 width: int):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled, data_value,
                         data_items)
        self.__data_available_items = data_available_items
        self.__available_items_resources_list = None
        """@type: AbstractResourceList"""
        self.__available_items_observable = None
        """@type: ObservableList"""
        self.__item_multi_value = 0
        self.__item_none_existent = 0
        self.__item_none_existent_value = None
        vs.CreatePullDownMenu(dialog_id, control_id, width)
        self.__init_observables()

    def _update(self):
        self.__reset_observables()
        super()._update()

    def __init_observables(self):
        self.__setup_observables()

    def __setup_observables(self):
        available_items = self.getattr(self.__data_available_items, ObservableList())
        if isinstance(available_items, ObservableList):
            self.__available_items_resources_list = None
            self.__available_items_observable = available_items
        elif isinstance(available_items, AbstractResourceList):
            self.__available_items_resources_list = available_items
            self.__available_items_observable = available_items.names
        """@type: ObservableList"""
        self.__available_items_observable.list_changed_event.subscribe(self.__on_available_items_changed)
        self.__available_items_observable.list_reordered_event.subscribe(self.__on_available_items_reordered)
        self.__setup_control()

    def __reset_observables(self):
        self.__available_items_observable.list_changed_event.unsubscribe(self.__on_available_items_changed)
        self.__available_items_observable.list_reordered_event.unsubscribe(self.__on_available_items_reordered)
        self.__clear_control()
        self.__setup_observables()

    # noinspection PyUnusedLocal
    def __on_available_items_changed(self, removed: dict, added: dict):
        for index in sorted(removed.keys(), reverse=True):
            self.__remove_item(index + self.__item_multi_value + self.__item_none_existent)
        for index in sorted(added.keys(), reverse=False):
            self.__add_item(added[index], index + self.__item_multi_value + self.__item_none_existent)
        self._set_control_value(self._value)

    def __on_available_items_reordered(self):
        self.__clear_control()
        self.__setup_control()
        self._set_control_value(self._value)

    def __setup_control(self):
        for index, item in enumerate(self.__available_items_observable):
            self.__add_item(item, index)

    def __clear_control(self):
        self.__item_multi_value = 0
        self.__item_none_existent = 0
        self.__item_none_existent_value = None
        for index in range(vs.GetChoiceCount(self._dialog_id, self.control_id) - 1, -1, -1):
            self.__remove_item(index)

    def __add_item(self, item, index):
        vs.AddChoice(self._dialog_id, self.control_id, str(item), index)

    def __add_item_multi_value(self):
        self.__item_multi_value = 1
        self.__add_item(self._multi_value_constant, 0)

    def __add_item_none_existent(self, value):
        self.__item_none_existent = 1
        self.__item_none_existent_value = value
        self.__add_item(str(value) + ' (None existent)', 0)

    def __remove_item(self, index):
        vs.RemoveChoice(self._dialog_id, self.control_id, index)

    def __remove_item_multi_value(self):
        self.__item_multi_value = 0
        self.__remove_item(0)

    def __remove_item_none_existent(self):
        self.__item_none_existent = 0
        self.__item_none_existent_value = None
        self.__remove_item(0)

    def __try_add_special_items(self, new_value):
        if self.__item_multi_value == 0 and new_value == self._multi_value_constant:
            self.__add_item_multi_value()
        elif self.__item_none_existent == 0 and new_value != self._multi_value_constant:
            self.__add_item_none_existent(new_value)

    def __try_remove_special_items(self, new_value):
        if self.__item_multi_value == 1 and new_value != self._multi_value_constant:
            self.__remove_item_multi_value()
        elif self.__item_none_existent == 1 and new_value != self.__item_none_existent_value:
            self.__remove_item_none_existent()

    def _set_control_value(self, value):
        index = self.__available_items_observable.index(value)
        self.__try_remove_special_items(value)
        if index == -1 and value is not None:
            self.__try_add_special_items(value)
        index += self.__item_multi_value + self.__item_none_existent
        vs.SelectChoice(self._dialog_id, self.control_id, index, True)

    def _get_control_value(self):
        index = vs.GetSelectedChoiceIndex(self._dialog_id, self.control_id, 0)
        if index > 0 or (self.__item_multi_value == 0 and self.__item_none_existent == 0):
            return self.__available_items_observable[index - self.__item_multi_value - self.__item_none_existent]
        elif index == -1:
            return None
        elif self.__item_multi_value == 1:
            return self._multi_value_constant
        elif self.__item_none_existent == 1:
            return self.__item_none_existent_value

    def _on_control_event(self, data: int):
        # It can be that the resource needs to be imported, thus changing names and possibly changing the list.
        if self.__available_items_resources_list is not None:
            value = self.__available_items_resources_list.get_resource(self._get_control_value()).name
        else:
            value = self._get_control_value()
        self.__try_remove_special_items(value)
        self._value = value


class Separator(AbstractControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled='')
        vs.CreateSeparator(dialog_id, control_id, 0)

    def _setup(self):
        pass

    def _update(self):
        pass

    def _on_control_event(self, data: int):
        pass


@Align(mode={Layout.VERTICAL: AlignMode.RESIZE})
class StaticText(AbstractControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, text: str, width: int, style: int):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled='')
        vs.CreateStyledStatic(dialog_id, control_id, text, width, style)

    def _setup(self):
        pass

    def _update(self):
        pass

    def _on_control_event(self, data: int):
        pass


@Align(mode=AlignMode.RESIZE)
class TabControl(AbstractControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled)
        self.__tab_panes = tuple()
        vs.CreateTabControl(dialog_id, control_id)

    def add_tab_panes(self, tab_panes: tuple):
        self.__tab_panes = tab_panes

    def setup(self, register_event_handler: callable):
        super().setup(register_event_handler)
        for tab_pane in self.__tab_panes:
            tab_pane.setup(register_event_handler)

    def _setup(self):
        pass

    def _update(self):
        pass

    def _on_control_event(self, data: int):
        pass


class TabPane(AbstractGroupControl):

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractControl,
                 data_context: str, data_disabled: str, header: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled)
        vs.CreateGroupBox(dialog_id, control_id, header, False)
        vs.CreateTabPane(dialog_id, data_parent.control_id, control_id)

    def _setup(self):
        pass

    def _update(self):
        pass

    def _on_control_event(self, data: int):
        pass


class ControlFactory(object, metaclass=SingletonMeta):

    def __init__(self):
        self.__last_control_id = 10

    def __reset_last_control_id(self):
        self.__last_control_id = 10

    def __generate_control_id(self) -> int:
        self.__last_control_id += 1
        return self.__last_control_id

    def create_controls(self, dialog_id: int, controls: list, data_parent: AbstractDataContext) -> tuple:
        self.__reset_last_control_id() if isinstance(data_parent, Dialog) else None
        return tuple(self.create_control(dialog_id, name, data, data_parent)
                     for control in controls for name, data in XmlDict.get_elements(control).items())

    def create_control(self, dialog_id: int, name: str, data: dict,
                       data_parent: AbstractDataContext) -> AbstractControl:
        return getattr(self, '_create_%s' % name.replace('-', '_'))(
            dialog_id, self.__generate_control_id(), data or {}, data_parent)

    @staticmethod
    def _create_button(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> Button:
        """
        <button
            optional: @help         -> str
            optional: @data-context -> str (property up data-context tree) -> ObservableField
            required: @data-command -> str (property up data-context tree) -> ObservableCommand>
                required: #text     -> str
        </button>
        """
        return Button(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                      data['@data-command'], data['#text'])

    @staticmethod
    def _create_edit_text(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> EditText:
        """
        <edit-text
            optional: @help          -> str
            optional: @data-context  -> str (property up data-context tree)            -> ObservableField
            optional: @data-disabled -> str (property up data-context tree)            -> ObservableMethod() -> bool
            required: @data-value    -> str (property up data-context tree or of item) -> ObservableField
            optional: @data-items    -> str (property up data-context tree)            -> ObservableList
            optional: @width         -> int (in chars)                                 || 20
            optional: @height        -> int (in rows)                                  || 1/>
        """
        return EditText(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                        data.get('@data-disabled', ''), data['@data-value'], data.get('@data-items', ''),
                        int(data.get('@width', '20')), int(data.get('@height', '1')))

    @staticmethod
    def _create_group_box(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> GroupBox:
        """
        <group-box
            optional: @help          -> str
            optional: @data-context  -> str (property up data-context tree) -> ObservableField
            optional: @data-disabled -> str (property up data-context tree) -> ObservableMethod() -> bool
            optional: @header        -> str
            optional: @border        -> bool                                || False
            optional: @layout        -> str (LayoutEnum)                    || 'VERTICAL'>
                required: <control>
        </group-box>
        """
        control = GroupBox(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                           data.get('@data-disabled', ''), data.get('@header', ''),
                           Convert.str2bool(data.get('@border', 'False')))
        control.add_controls(ControlFactory().create_controls(dialog_id, data['control'], control),
                             Layout.from_string(data.get('@layout', 'VERTICAL')))
        return control

    @staticmethod
    def _create_list_box(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> ListBox:
        """
        <list-box
            optional: @help                -> str
            optional: @data-context        -> str (property up data-context tree) -> ObservableField
            optional: @data-disabled       -> str (property up data-context tree) -> ObservableMethod() -> bool
            required: @data-items          -> str (property up data-context tree) -> ObservableList
            required: @data-selected-items -> str (property up data-context tree) -> ObservableList
            required: @data-value          -> str (property of item)              -> ObservableField
            optional: @width               -> int (in chars)                      || 40
            optional: @height              -> int (in lines)                      || 40/>
        """
        return ListBox(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                       data.get('@data-disabled', ''), data['@data-items'], data['@data-selected-items'],
                       data['@data-value'], data.get('@width', 40), data.get('@height', 40))

    @staticmethod
    def _create_list_browser(dialog_id: int, control_id: int, data: dict,
                             data_parent: AbstractDataContext) -> ListBrowser:
        """
        <list-browser
            optional: @help                -> str
            optional: @data-context        -> str (property up data-context tree) -> ObservableField
            optional: @data-disabled       -> str (property up data-context tree) -> ObservableMethod() -> bool
            required: @data-items          -> str (property up data-context tree) -> ObservableList
            required: @data-selected-items -> str (property up data-context tree) -> ObservableList
            optional: @index               -> bool (has index column?)            || False
            optional: @width               -> int (in chars)                      || 80
            optional: @height              -> int (in lines)                      || 40>
                optional: <column
                                required: @header       -> str
                                optional: @width        -> int (in pixels)             || 120
                                optional: @control-type -> str (ControlTypeEnum)       || 'STATIC'
                                optional: @display-type -> str (DisplayTypeEnum)       || 'TEXT_ONLY'
                                optional: @text-align   -> str (TextAlignEnum)         || 'LEFT'
                                required: @data-value   -> str (property name of item) -> ObservableField/>
        </list-browser>
        """
        return ListBrowser(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                           data.get('@data-disabled', ''), data['@data-items'], data['@data-selected-items'],
                           Convert.str2bool(data.get('@index', 'False')),
                           tuple(Column(column['@header'], column.get('@width', 120),
                                        ControlTypeEnum.from_string(column.get('@control-type', 'STATIC')),
                                        DisplayTypeEnum.from_string(column.get('@display-type', 'TEXT_ONLY')),
                                        TextAlignEnum.from_string(column.get('@text-align', 'LEFT')),
                                        column['@data-value']) for column in data.get('column', [])),
                           data.get('@width', 80), data.get('@height', 40))

    @staticmethod
    def _create_pull_down_menu(dialog_id: int, control_id: int, data: dict,
                               data_parent: AbstractDataContext) -> PullDownMenu:
        """
        <pull-down-menu
            optional: @help                 -> str
            optional: @data-context         -> str (property up data-context tree)            -> ObservableField
            optional: @data-disabled        -> str (property up data-context tree)            -> ObservableMethod()
                                                                                                    -> bool
            required: @data-available-items -> str (property up data-context tree)            -> ObservableList
                                                                                              OR AbstractResourceList
            required: @data-value           -> str (property up data-context tree or of item) -> ObservableField
            optional: @data-items           -> str (property up data-context tree)            -> ObservableList
            optional: @width                -> int (in chars)                                 || 20/>
        """
        return PullDownMenu(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                            data.get('@data-disabled', ''), data['@data-available-items'], data['@data-value'],
                            data.get('@data-items', ''), data.get('@width', 20))

    @staticmethod
    def _create_separator(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> Separator:
        """
        <separator/>
        """
        return Separator(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''))

    @staticmethod
    def _create_static_text(dialog_id: int, control_id: int, data: dict,
                            data_parent: AbstractDataContext) -> StaticText:
        """
        <static-text
            optional: @help         -> str
            optional: @data-context -> str (property up data-context tree) -> ObservableField
            optional: @width        -> int (in chars or -1 for automatic)  || -1
            optional: @style        -> str (TextStyleEnum)                 || 'REGULAR'>
                required: #text     -> str
        </static-text>
        """
        return StaticText(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                          data['#text'], data.get('@width', -1),
                          TextStyleEnum.from_string(data.get('@style', 'REGULAR')))

    @staticmethod
    def _create_tab_control(dialog_id: int, control_id: int, data: dict,
                            data_parent: AbstractDataContext) -> TabControl:
        """
        <tab-control
            optional: @help          -> str
            optional: @data-context  -> str (property up data-context tree) -> ObservableField
            optional: @data-disabled -> str (property up data-context tree) -> ObservableMethod() -> bool>
                required: <tab-pane>
        </tab-control>
        """
        control = TabControl(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                             data.get('@data-disabled', ''))
        control.add_tab_panes(tuple(ControlFactory().create_control(dialog_id, 'tab-pane', tab_pane, control)
                                    for tab_pane in data['tab-pane']))
        return control

    @staticmethod
    def _create_tab_pane(dialog_id: int, control_id: int, data: dict, data_parent: AbstractControl) -> TabPane:
        """
        <tab-pane
            optional: @help          -> str
            optional: @data-context  -> str (property up data-context tree) -> ObservableField
            optional: @data-disabled -> str (property up data-context tree) -> ObservableMethod() -> bool
            required: @header        -> str
            optional: @layout        -> str (LayoutEnum)                    || 'VERTICAL'>
                required: <control>
        </tab-pane>
        """
        control = TabPane(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                          data.get('@data-disabled', ''), data['@header'])
        control.add_controls(ControlFactory().create_controls(dialog_id, data['control'], control),
                             Layout.from_string(data.get('@layout', 'VERTICAL')))
        return control
