from dlibrary.dialog.control import AbstractControl, AlignModeEnum, AbstractDataContext
import vs


class Button(AbstractControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return True

    @classmethod
    def get_align_mode(cls, layout: int) -> int:
        return AlignModeEnum.SHIFT

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_command: str, caption: str):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled='')
        self.__data_command = data_command
        self.__data_command_observable = None
        """@type: ObservableCommand"""
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
        self.__data_command_observable.can_execute_changed_event.subscribe(self.__on_can_execute_changed)
        self.__on_can_execute_changed()

    def __reset_observables(self):
        self.__data_command_observable.can_execute_changed_event.unsubscribe(self.__on_can_execute_changed)
        self.__setup_observables()

    def __on_can_execute_changed(self):
        vs.EnableItem(self._dialog_id, self.control_id, self.__data_command_observable.can_execute())

    def _on_control_event(self, data: int):
        self.__data_command_observable.execute()


# ----------------------------------------------------------------------------------------------------------------------
#   <button
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       required: @data-command -> str (property name of parent data-context) -> ObservableCommand>
#           required: #text -> str
#   </button>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> Button:
    return Button(
        dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''), data['@data-command'],
        data['#text'])