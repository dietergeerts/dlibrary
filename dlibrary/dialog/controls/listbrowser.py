from dlibrary.dialog.control import AlignMode, AbstractDataContext, TextAlignEnum, AbstractListControl
from dlibrary.utility import converter
import vs


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


class ListBrowser(AbstractListControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return True

    @classmethod
    def align_mode(cls, layout: int) -> int:
        return AlignMode.RESIZE

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


# ----------------------------------------------------------------------------------------------------------------------
#   <list-browser
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       optional: @data-disabled -> str (property name of data-context) -> ObservableMethod() -> bool
#       required: @data-items -> str (property name of data-context) -> ObservableList
#       required: @data-selected-items -> str (property name of data-context) -> ObservableList
#       optional: @index -> bool (has index column) || False
#       optional: @width -> int (in chars) || 80
#       optional: @height -> int (in lines) || 40>
#           optional: <column
#                           required: @header -> str
#                           optional: @width -> int (in pixels) || 120
#                           optional: @control-type -> str (ControlTypeEnum) || 'STATIC'
#                           optional: @display-type -> str (DisplayTypeEnum) || 'TEXT_ONLY'
#                           optional: @text-align -> str (TextAlignEnum) || 'LEFT'
#                           required: @data-value -> str (property name of an item) -> ObservableField/>
#   </list-browser>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> ListBrowser:
    return ListBrowser(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
        data.get('@data-disabled', ''), data['@data-items'], data['@data-selected-items'],
        converter.str2bool(data.get('@index', 'False')),
        tuple(Column(
            column['@header'], column.get('@width', 120),
            ControlTypeEnum.from_string(column.get('@control-type', 'STATIC')),
            DisplayTypeEnum.from_string(column.get('@display-type', 'TEXT_ONLY')),
            TextAlignEnum.from_string(column.get('@text-align', 'LEFT')),
            column['@data-value']) for column in data.get('column', [])),
        data.get('@width', 80), data.get('@height', 40))