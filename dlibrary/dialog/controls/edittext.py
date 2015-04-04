from dlibrary.dialog.control import LayoutEnum, AlignModeEnum, AbstractDataContext, AbstractFieldControl
from dlibrary.utility import converter
import vs


class EditText(AbstractFieldControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return layout == LayoutEnum.VERTICAL

    @classmethod
    def get_align_mode(cls, layout: int) -> int:
        return AlignModeEnum.RESIZE

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_value: str, data_items: str, width: int, disabled: bool):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_value, data_items, disabled)
        vs.CreateEditText(dialog_id, control_id, self._value, width)

    def _set_control_value(self, value):
        vs.SetItemText(self._dialog_id, self.control_id, value)

    def _get_control_value(self):
        return vs.GetItemText(self._dialog_id, self.control_id)

    def _on_control_event(self, data: int):
        self._value = self._get_control_value()


# ----------------------------------------------------------------------------------------------------------------------
#   <edit-text
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       required: @data-value -> str (property name of data-context or of an item) -> ObservableField
#       optional: @data-items -> str (property name of data-context) -> ObservableList
#       optional: @width -> int (in chars) || 20
#       optional: @disabled -> bool || False/>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> EditText:
    return EditText(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''), data['@data-value'],
        data.get('@data-items', ''), data.get('@width', 20), converter.str2bool(data.get('@disabled', 'False')))