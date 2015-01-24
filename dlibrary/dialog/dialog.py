from dlibrary.dialog.control import AbstractDataContext, ControlFactory
from dlibrary.object.objects.plugin import PlugIn
from dlibrary.utility.exception import VSException
import vs
import dlibrary.utility.converter as converter


class Dialog(AbstractDataContext):
    def __init__(self, dialog_name: str, data_context: object):
        super().__init__(data_context)
        try: view = PlugIn().load_plugin_file(dialog_name + 'Dialog', set('control'))
        except VSException: raise
        except FileNotFoundError: raise
        except PermissionError: raise
        except OSError: raise
        else:
            self.__event_handlers = {}
            self.__dialog_id = vs.CreateLayout(
                view['dialog']['@title'], converter.str2bool(view['dialog'].get('@help', 'False')),
                view['dialog'].get('@ok', 'Ok'), view['dialog'].get('@cancel', 'Cancel'))
            self.__dialog_control = ControlFactory().create_controls(
                self.__dialog_id, self.__get_dialog_control(view['dialog']), self)[0]
            vs.SetFirstLayoutItem(self.__dialog_id, self.__dialog_control.control_id)

    def __get_dialog_control(self, dialog: dict) -> list:
        return [{'group-box': {'@layout': dialog.get('@layout', 'VERTICAL'), 'control': dialog['control']}}]

    def show(self) -> bool:  # 1 for Ok, 2 for Cancel.
        return vs.RunLayoutDialog(self.__dialog_id, lambda item, data: self.__dialog_handler(item, data)) == 1

    def __dialog_handler(self, item, data):
        if item == 12255: self.__on_setup()
        elif item == 1: self.__on_ok()
        elif item == 2: self.__on_cancel()
        elif item in self.__event_handlers: self.__event_handlers[item](data)  # VW sends control events with their id.
        return item  # Required by VW!

    def __register_event_handler(self, control_id: int, event_handler: callable):
        self.__event_handlers[control_id] = event_handler

    def __on_setup(self): self.__dialog_control.setup(self.__register_event_handler)

    def __on_ok(self): pass

    def __on_cancel(self): pass