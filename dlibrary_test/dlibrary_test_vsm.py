import pydevd

from dlibrary.dialog.dialog import Dialog
from dlibrary.resource.definition.definitions.record import RecordDefinitionResourceList
from dlibrary.utility.observable import ObservableField, LinkedObservableField, ObservableCommand, ObservableList, \
    ObservableMethod
from dlibrary.dialog.predefined.alert import Alert
from dlibrary.dialog.predefined.alert import AlertType
from dlibrary.dialog.predefined.alerts.alert_plugin import PlugInAlerts
from dlibrary.dialog.viewmodel import AbstractViewModel, ViewModelList
from dlibrary.utility.exception import VSException

pydevd.settrace('localhost', port=8080, stdoutToServer=True, stderrToServer=True, suspend=False)


def run():
    try:
        items = create_items()
        dialog = Dialog('Main', DLibraryTestVsmViewModel(items))
    except VSException:
        PlugInAlerts().on_plugin_file_vsexception.show()
    except FileNotFoundError:
        PlugInAlerts().on_plugin_file_filenotfounderror.show()
    except PermissionError:
        PlugInAlerts().on_plugin_file_permissionerror.show()
    except OSError:
        PlugInAlerts().on_plugin_file_oserror.show()
    else:
        if dialog.show():
            Alert(AlertType.INFO, 'You closed the dialog through the OK button').show()
        else:
            Alert(AlertType.INFO, 'You closed the dialog through the CANCEL button').show()
        message = 'The items are now: ' + chr(10)
        for item in items:
            message += item['@prop_one'] + ' ' + str(item['@prop_two']) + ' | '
        Alert(AlertType.INFO, message).show()


class ChoiceItem(object):
    def __init__(self, number: int, name: str):
        self.__number = number
        self.__name = name

    def __str__(self):
        return '%s %s' % (str(self.__number), self.__name)


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
    def prop_one(self) -> ObservableField:
        return self.__prop_one

    @property
    def prop_two(self) -> ObservableField:
        return self.__prop_two


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
    def dialog_text(self) -> ObservableField:
        return self.__dialog_text

    @property
    def dialog_advice(self) -> ObservableField:
        return self.__dialog_advice

    @property
    def show_alert_critical(self) -> ObservableCommand:
        return self.__show_alert_critical

    @property
    def show_alert_warning(self) -> ObservableCommand:
        return self.__show_alert_warning

    @property
    def show_alert_info(self) -> ObservableCommand:
        return self.__show_alert_info

    @property
    def show_alert_success(self) -> ObservableCommand:
        return self.__show_alert_success

    def __can_show_alert(self):
        return self.__dialog_text.value is not None and self.__dialog_text.value != ''

    def __show_alert(self, type: AlertType):
        Alert(type, self.__dialog_text.value, self.__dialog_advice.value).show()

    @property
    def show_plugin_alert_vsexception(self) -> ObservableCommand:
        return self.__show_plugin_alert_vsexception

    @property
    def show_plugin_alert_filenotfounderror(self) -> ObservableCommand:
        return self.__show_plugin_alert_filenotfounderror

    @property
    def show_plugin_alert_permissionerror(self) -> ObservableCommand:
        return self.__show_plugin_alert_permissionerror

    @property
    def show_plugin_alert_oserrer(self) -> ObservableCommand:
        return self.__show_plugin_alert_oserror


class RecordDefinitionsViewModel(object):
    def __init__(self):
        self.__record_definitions = RecordDefinitionResourceList()
        self.__record_definition_fields = ObservableList()
        self.__selected_record_definition = ObservableField()
        self.__selected_record_definition.field_changed_event.subscribe(self.__on_selected_record_definition_changed)
        self.__selected_record_definition_field = ObservableField()

    @property
    def record_definitions(self) -> ObservableList:
        return self.__record_definitions

    @property
    def record_definition_fields(self) -> ObservableList:
        return self.__record_definition_fields

    @property
    def selected_record_definition(self) -> ObservableField:
        return self.__selected_record_definition

    @property
    def selected_record_definition_field(self) -> ObservableField:
        return self.__selected_record_definition_field

    # noinspection PyUnusedLocal
    def __on_selected_record_definition_changed(self, oldValue, newValue):
        self.selected_record_definition_field.value = None
        self.record_definition_fields.suspend_events()
        self.record_definition_fields.clear()
        record_definition = self.__record_definitions.get_resource(newValue)
        if record_definition is not None:
            self.record_definition_fields.extend(record_definition.fields)
        self.record_definition_fields.resume_events()


class DLibraryTestVsmViewModel(object):
    def __init__(self, items: list):
        self.__available_items = ObservableList([choice1, choice2, choice3])
        self.__list_administration = ObservableField(
            ViewModelList(items, ItemViewModel, create_item, self.__can_add_item, {'prop_one'}))
        self.__predefined_dialogs = ObservableField(PredefinedDialogsViewModel())
        self.__record_definitions = ObservableField(RecordDefinitionsViewModel())
        self.__always_disabled_method = ObservableMethod(lambda: False)

    @property
    def always_disable(self) -> ObservableMethod:
        return self.__always_disabled_method

    @property
    def available_items(self) -> ObservableList:
        return self.__available_items

    @property
    def list_administration(self) -> ObservableField:
        return self.__list_administration

    @property
    def predefined_dialogs(self) -> ObservableField:
        return self.__predefined_dialogs

    @property
    def record_definitions(self) -> ObservableField:
        return self.__record_definitions

    def __can_add_item(self, item):
        return item['@prop_one'] is not None and item['@prop_one'] != ''