from dlibrary.dialog.control import AbstractControl, AlignModeEnum, AbstractDataContext, ControlFactory
import vs


class TabControl(AbstractControl):
    @classmethod
    def can_align(cls, layout: int) -> bool:
        return True

    @classmethod
    def get_align_mode(cls, layout: int) -> int:
        return AlignModeEnum.RESIZE

    def __init__(self, dialog_id: int, control_id: int, help_text: str, data_parent: AbstractDataContext,
                 data_context: str, data_disabled):
        super().__init__(dialog_id, control_id, help_text, data_parent, data_context, data_disabled)
        self.__tab_panes = tuple()
        vs.CreateTabControl(dialog_id, control_id)

    def add_tab_panes(self, tab_panes: tuple):
        self.__tab_panes = tab_panes

    def setup(self, register_event_handler: callable):
        super().setup(register_event_handler)
        for tab_pane in self.__tab_panes:
            tab_pane.setup(register_event_handler)

    def _setup(self):
        pass

    def _update(self):
        pass

    def _on_control_event(self, data: int):
        pass


# ----------------------------------------------------------------------------------------------------------------------
#   <tab-control
#       optional: @help -> str
#       optional: @data-context -> str (property name of parent data-context) -> ObservableField
#       optional: @data-disabled -> str (property name of data-context) -> ObservableMethod() -> bool>
#           required: <tab-pane>
#   </tab-control>
# ----------------------------------------------------------------------------------------------------------------------

def create(dialog_id: int, control_id: int, data: dict, data_parent: AbstractDataContext) -> TabControl:
    control = TabControl(dialog_id, control_id, data.get('@help', ''), data_parent, data.get('@data-context', ''),
                         data.get('@data-disabled', ''))
    control.add_tab_panes(tuple(ControlFactory().create_control(dialog_id, 'tab-pane', tab_pane, control)
                                for tab_pane in data['tab-pane']))
    return control