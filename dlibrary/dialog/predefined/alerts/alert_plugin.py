from dlibrary.dialog.predefined.alert import Alert, AlertType
from dlibrary.utility.singleton import SingletonMeta


class PlugInAlerts(object, metaclass=SingletonMeta):
    def __init__(self):
        self.__on_plugin_file_vsexception = None
        self.__on_plugin_file_filenotfounderror = None
        self.__on_plugin_file_permissionerror = None
        self.__on_plugin_file_oserror = None

    @property
    def on_plugin_file_vsexception(self) -> Alert:
        if self.__on_plugin_file_vsexception is None:
            self.__on_plugin_file_vsexception = Alert(
                AlertType.CRITICAL,
                'Something went wrong with this plug-in. It may be corrupt.',
                'Please contact the distributor.')
        return self.__on_plugin_file_vsexception

    @property
    def on_plugin_file_filenotfounderror(self) -> Alert:
        if self.__on_plugin_file_filenotfounderror is None:
            self.__on_plugin_file_filenotfounderror = Alert(
                AlertType.CRITICAL,
                'A plug-in file could not be found.',
                'Make sure all provided plug-in files are in the plug-in folder.')
        return self.__on_plugin_file_filenotfounderror

    @property
    def on_plugin_file_permissionerror(self) -> Alert:
        if self.__on_plugin_file_permissionerror is None:
            self.__on_plugin_file_permissionerror = Alert(
                AlertType.CRITICAL,
                'A plug-in file could not be read.',
                'Make sure all provided plug-in files have read/write permissions.')
        return self.__on_plugin_file_permissionerror

    @property
    def on_plugin_file_oserror(self) -> Alert:
        if self.__on_plugin_file_oserror is None:
            self.__on_plugin_file_oserror = Alert(
                AlertType.CRITICAL,
                'Something went wrong while loading a plug-in file.',
                'Make sure all plug-in files are in the plug-in folder, '
                'have read/write permissions and are not corrupt.')
        return self.__on_plugin_file_oserror