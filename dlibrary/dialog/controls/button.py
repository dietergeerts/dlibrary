from dlibrary.dialog.control import AbstractControl, AlignModeEnum, AbstractDataContext
import vs


class Button(AbstractControl):
    @classmethod
    def can_align(cls, layout: int) -> bool: return True

    @classmethod
    def get_align_mode(cls, layout: int) -> int: return AlignModeEnum.SHIFT

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_command: str, caption: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context)
        self.__command = data_command
        vs.CreatePushButton(dialog_id, control_id, caption)

    def _setup(self): pass

    def _update(self): pass

    def _on_control_event(self, data: int): getattr(self.data_context, self.__command)()


# ----------------------------------------------------------------------------------------------------------------------
#   <button
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       required: @data-command -> str (function name of parent data-context) -> callable>
#           required: #text -> str
#   </button>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> Button:
    return Button(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''), data['@data-command'],
        data['#text'])