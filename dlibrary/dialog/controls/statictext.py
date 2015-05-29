from dlibrary.dialog.control import AbstractControl, Layout, AlignMode, AbstractDataContext, TextStyleEnum
import vs


class StaticText(AbstractControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return layout == Layout.VERTICAL

    @classmethod
    def align_mode(cls, layout: int) -> int:
        return AlignMode.RESIZE

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


# ----------------------------------------------------------------------------------------------------------------------
#   <static-text
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       optional: @width -> int (in chars or -1 for automatic) || -1
#       optional: @style -> str (TextStyleEnum) || 'REGULAR'>
#           required: #text -> str
#   </static-text>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> StaticText:
    return StaticText(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''), data['#text'],
        data.get('@width', -1), TextStyleEnum.from_string(data.get('@style', 'REGULAR')))