from dlibrary.dialog.control import AbstractDataContext, ControlFactory
import vs
import dlibrary.libs.xmltodict as xml_to_dict
import dlibrary.utility.converter as converter
import dlibrary.utility.xmltodict as xml_to_dict_util


class Dialog(AbstractDataContext):
    def __init__(self, view_file_path: str, data_context: object):
        super().__init__(data_context)
        self.__valid = False
        try:
            with open(view_file_path) as file:
                view = xml_to_dict_util.correct_elements(xml_to_dict.parse(file.read()))
        except FileNotFoundError:
            vs.AlertCritical('Could not find dialog file:', view_file_path)
        except PermissionError:
            vs.AlertCritical('Insufficient permissions on dialog file:', view_file_path)
        except OSError:
            vs.AlertCritical('Contents of dialog file is invalid:', view_file_path)
        # TODO: Check contents of file with an xml schema.
        # TODO: Decide if exceptions should be handled here or by the user of Dialog.
        else:
            self.__valid = True
            self.__event_handlers = {}
            self.__dialog_id = vs.CreateLayout(
                view['dialog']['@title'], converter.str2bool(view['dialog'].get('@help', 'False')),
                view['dialog'].get('@ok', 'Ok'), view['dialog'].get('@cancel', 'Cancel'))
            self.__dialog_control = ControlFactory().create_controls(
                self.__dialog_id, self.__get_dialog_control(view['dialog']), self)[0]
            vs.SetFirstLayoutItem(self.__dialog_id, self.__dialog_control.control_id)

    @property
    def valid(self): return self.__valid

    def __get_dialog_control(self, dialog: dict) -> list:
        return [{'group-box': {'@layout': dialog.get('@layout', 'VERTICAL'), 'control': dialog['control']}}]

    def show(self) -> bool:
        if self.__valid:  # 1 for Ok, 2 for Cancel.
            return vs.RunLayoutDialog(self.__dialog_id, lambda item, data: self.__dialog_handler(item, data)) == 1
        else: return False

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