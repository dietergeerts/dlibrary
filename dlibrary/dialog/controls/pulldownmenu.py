from dlibrary.dialog.control import AbstractFieldControl, LayoutEnum, AlignModeEnum, AbstractDataContext
from dlibrary.dialog.observable import ObservableList
import vs


class PullDownMenu(AbstractFieldControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return layout == LayoutEnum.VERTICAL

    @classmethod
    def get_align_mode(cls, layout: int) -> int:
        return AlignModeEnum.RESIZE

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled: str, data_available_items: str, data_value: str, data_items: str,
                 width: int):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled, data_value,
                         data_items)
        self.__data_available_items = data_available_items
        self.__available_items = None
        vs.CreatePullDownMenu(dialog_id, control_id, width)

    def _update(self):
        self.__reset_control()
        super()._update()

    def __reset_control(self):
        self.__available_items = ObservableList(sorted(  # Make it ObservableList as for index return -1!
            self.getattr(self.__data_available_items, ObservableList()), key=str))
        for index in range(vs.GetChoiceCount(self._dialog_id, self.control_id) - 1, -1, -1):
            vs.RemoveChoice(self._dialog_id, self.control_id, index)
        for index, item in enumerate(self.__available_items):
            vs.AddChoice(self._dialog_id, self.control_id, str(item), index)

    def _set_control_value(self, value):
        vs.SelectChoice(self._dialog_id, self.control_id, self.__available_items.index(value), True)

    def _get_control_value(self):
        index = vs.GetSelectedChoiceIndex(self._dialog_id, self.control_id, 0)
        return self.__available_items[index] if index > -1 else None

    def _on_control_event(self, data: int):
        self._value = self._get_control_value()


# ----------------------------------------------------------------------------------------------------------------------
#   <pull-down-menu
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       optional: @data-disabled -> str (property name of data-context) -> ObservableMethod() -> bool
#       required: @data-available-items -> str (property name of data-context) -> ObservableList
#       required: @data-value -> str (property name of data-context or of an item) -> ObservableField
#       optional: @data-items -> str (property name of data-context) -> ObservableList
#       optional: @width -> int (in chars) || 20/>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> PullDownMenu:
    return PullDownMenu(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
        data.get('@data-disabled', ''), data['@data-available-items'], data['@data-value'], data.get('@data-items', ''),
        data.get('@width', 20))