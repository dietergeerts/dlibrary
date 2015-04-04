from dlibrary.dialog.control import AbstractGroupControl, AlignModeEnum, AbstractDataContext, LayoutEnum, ControlFactory
from dlibrary.utility import converter
import vs


class GroupBox(AbstractGroupControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return True

    @classmethod
    def get_align_mode(cls, layout: int) -> int:
        return AlignModeEnum.RESIZE

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


# ----------------------------------------------------------------------------------------------------------------------
#   <group-box
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       optional: @data-disabled -> str (property name of data-context) -> ObservableMethod() -> bool
#       optional: @header -> str
#       optional: @border -> bool || False
#       optional: @layout -> str (LayoutEnum) || 'VERTICAL'>
#           required: <control>
#   </group-box>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> GroupBox:
    control = GroupBox(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
        data.get('@data-disabled', ''), data.get('@header', ''), converter.str2bool(data.get('@border', 'False')))
    control.add_controls(
        ControlFactory().create_controls(dialog_id, data['control'], control),
        LayoutEnum.from_string(data.get('@layout', 'VERTICAL')))
    return control