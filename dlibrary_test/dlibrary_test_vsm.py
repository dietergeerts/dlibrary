from dlibrary.dialog.dialog import Dialog
from dlibrary.dialog.observable import ObservableField, LinkedObservableField, ObservableCommand, ObservableList
from dlibrary.dialog.predefined.alert import Alert
from dlibrary.dialog.predefined.alert import AlertType
from dlibrary.dialog.predefined.alerts.alert_plugin import PlugInAlerts
from dlibrary.dialog.viewmodel import AbstractViewModel, ViewModelList
from dlibrary.utility.exception import VSException

import pydevd
pydevd.settrace('localhost', port=8080, stdoutToServer=True, stderrToServer=True, suspend=False)


def run():
    try:
        items = create_items()
        dialog = Dialog('Main', DLibraryTestVsmViewModel(items))
    except VSException:       PlugInAlerts().on_plugin_file_vsexception.show()
    except FileNotFoundError: PlugInAlerts().on_plugin_file_filenotfounderror.show()
    except PermissionError:   PlugInAlerts().on_plugin_file_permissionerror.show()
    except OSError:           PlugInAlerts().on_plugin_file_oserror.show()
    else:
        if dialog.show(): Alert(AlertType.INFO, 'You closed the dialog through the OK button').show();
        else: Alert(AlertType.INFO, 'You closed the dialog through the CANCEL button').show();
        message = 'The items are now: ' + chr(10)
        for item in items: message += item['@prop_one'] + ' ' + str(item['@prop_two']) + ' | '
        Alert(AlertType.INFO, message).show()


class ChoiceItem(object):
    def __init__(self, number: int, name: str):
        self.__number = number
        self.__name = name

    def __str__(self): return '%s %s' % (str(self.__number), self.__name)


choice1 = ChoiceItem(1, 'one')
choice2 = ChoiceItem(3, 'three')
choice3 = ChoiceItem(2, 'two')
choice4 = ChoiceItem(4, 'four')


def create_items() -> list: return [
    create_item('Some', choice1),
    create_item('Another', choice1),
    create_item('One', choice3)]


def create_item(prop_one: str='', prop_two: object=choice4) -> dict:
    return {'@prop_one': prop_one, '@prop_two': prop_two}


class ItemViewModel(AbstractViewModel):
    def __init__(self, item: dict):
        super().__init__(item)
        self.__prop_one = LinkedObservableField(item, '@prop_one')
        self.__prop_two = LinkedObservableField(item, '@prop_two')

    @property
    def prop_one(self) -> ObservableField: return self.__prop_one

    @property
    def prop_two(self) -> ObservableField: return self.__prop_two


class PredefinedDialogsViewModel(object):
    def __init__(self):
        self.__dialog_text = ObservableField()
        self.__dialog_advice = ObservableField()
        self.__show_alert_critical = ObservableCommand(
            lambda: self.__show_alert(AlertType.CRITICAL), self.__can_show_alert, {self.dialog_text})
        self.__show_alert_warning = ObservableCommand(
            lambda: self.__show_alert(AlertType.WARNING), self.__can_show_alert, {self.dialog_text})
        self.__show_alert_info = ObservableCommand(
            lambda: self.__show_alert(AlertType.INFO), self.__can_show_alert, {self.dialog_text})
        self.__show_alert_success = ObservableCommand(
            lambda: self.__show_alert(AlertType.SUCCESS), self.__can_show_alert, {self.dialog_text})
        self.__show_plugin_alert_vsexception = ObservableCommand(
            lambda: PlugInAlerts().on_plugin_file_vsexception.show())
        self.__show_plugin_alert_filenotfounderror = ObservableCommand(
            lambda: PlugInAlerts().on_plugin_file_filenotfounderror.show())
        self.__show_plugin_alert_permissionerror = ObservableCommand(
            lambda: PlugInAlerts().on_plugin_file_permissionerror.show())
        self.__show_plugin_alert_oserror = ObservableCommand(
            lambda: PlugInAlerts().on_plugin_file_oserror.show())

    @property
    def dialog_text(self) -> ObservableField: return self.__dialog_text

    @property
    def dialog_advice(self) -> ObservableField: return self.__dialog_advice

    @property
    def show_alert_critical(self) -> ObservableCommand: return self.__show_alert_critical

    @property
    def show_alert_warning(self) -> ObservableCommand: return self.__show_alert_warning

    @property
    def show_alert_info(self) -> ObservableCommand: return self.__show_alert_info

    @property
    def show_alert_success(self) -> ObservableCommand: return self.__show_alert_success

    def __can_show_alert(self): return self.__dialog_text.value is not None and self.__dialog_text.value != ''

    def __show_alert(self, type: AlertType): Alert(type, self.__dialog_text.value, self.__dialog_advice.value).show()

    @property
    def show_plugin_alert_vsexception(self) -> ObservableCommand: return self.__show_plugin_alert_vsexception

    @property
    def show_plugin_alert_filenotfounderror(self) -> ObservableCommand: return self.__show_plugin_alert_filenotfounderror

    @property
    def show_plugin_alert_permissionerror(self) -> ObservableCommand: return self.__show_plugin_alert_permissionerror

    @property
    def show_plugin_alert_oserrer(self) -> ObservableCommand: return self.__show_plugin_alert_oserror


class DLibraryTestVsmViewModel(object):
    def __init__(self, items: list):
        self.__available_items = ObservableList([choice1, choice2, choice3])
        self.__list_administration = ObservableField(
            ViewModelList(items, ItemViewModel, create_item, self.__can_add_item, {'prop_one'}))
        self.__predefined_dialogs = ObservableField(PredefinedDialogsViewModel())

    @property
    def available_items(self) -> ObservableList: return self.__available_items

    @property
    def list_administration(self) -> ObservableField: return self.__list_administration

    @property
    def predefined_dialogs(self) -> ObservableField: return self.__predefined_dialogs

    def __can_add_item(self, item): return item['@prop_one'] is not None and item['@prop_one'] != ''