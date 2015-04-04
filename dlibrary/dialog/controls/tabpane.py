from dlibrary.dialog.control import AbstractGroupControl, AbstractControl, LayoutEnum, ControlFactory
import vs


class TabPane(AbstractGroupControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return False

    @classmethod
    def get_align_mode(cls, layout: int) -> int:
        return -1

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractControl,
                 data_context: str, header: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context)
        vs.CreateGroupBox(dialog_id, control_id, header, False)
        vs.CreateTabPane(dialog_id, data_parent.control_id, control_id)

    def _setup(self):
        pass

    def _update(self):
        pass

    def _on_control_event(self, data: int):
        pass


# ----------------------------------------------------------------------------------------------------------------------
#   <tab-pane
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       required: @header -> str
#       optional: @layout -> str (LayoutEnum) || 'VERTICAL'>
#           required: <control>
#   </tab-pane>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractControl) -> TabPane:
    control = TabPane(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''), data['@header'])
    control.add_controls(
        ControlFactory().create_controls(dialog_id, data['control'], control),
        LayoutEnum.from_string(data.get('@layout', 'VERTICAL')))
    return control