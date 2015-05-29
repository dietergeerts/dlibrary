from dlibrary.dialog.control import AbstractFieldControl, Layout, AlignMode, AbstractDataContext
from dlibrary.resource.resourcelist import AbstractResourceList
from dlibrary.utility.observable import ObservableList
import vs


class PullDownMenu(AbstractFieldControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return layout == Layout.VERTICAL

    @classmethod
    def align_mode(cls, layout: int) -> int:
        return AlignMode.RESIZE

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


# ----------------------------------------------------------------------------------------------------------------------
#   <pull-down-menu
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       optional: @data-disabled -> str (property name of data-context) -> ObservableMethod() -> bool
#       required: @data-available-items -> str (property name of data-context) -> ObservableList OR AbstractResourceList
#       required: @data-value -> str (property name of data-context or of an item) -> ObservableField
#       optional: @data-items -> str (property name of data-context) -> ObservableList
#       optional: @width -> int (in chars) || 20/>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> PullDownMenu:
    return PullDownMenu(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
        data.get('@data-disabled', ''), data['@data-available-items'], data['@data-value'], data.get('@data-items', ''),
        data.get('@width', 20))