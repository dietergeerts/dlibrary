from dlibrary.dialog.control import AlignModeEnum, AbstractDataContext, AbstractListControl
import vs


class ListBox(AbstractListControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return True

    @classmethod
    def get_align_mode(cls, layout: int) -> int:
        return AlignModeEnum.RESIZE

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


# ----------------------------------------------------------------------------------------------------------------------
#   <list-box
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       optional: @data-disabled -> str (property name of data-context) -> ObservableMethod() -> bool
#       required: @data-items -> str (property name of data-context) -> ObservableList
#       required: @data-selected-items -> str (property name of data-context) -> ObservableList
#       required: @data-value -> str (property name of an item) -> ObservableField
#       optional: @width -> int (in chars) || 40
#       optional: @height -> int (in lines) || 40/>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> ListBox:
    return ListBox(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
        data.get('@data-disabled', ''), data['@data-items'], data['@data-selected-items'], data['@data-value'],
        data.get('@width', 40), data.get('@height', 40))