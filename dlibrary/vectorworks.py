from abc import ABCMeta
import os

from dlibrary.dialog_predefined import AlertType, Alert
from dlibrary.utility import AbstractXmlFile, SingletonMeta, VSException
import vs


class Platform(object):
    MAC_OS = 1
    WINDOWS = 2


class Vectorworks(object, metaclass=SingletonMeta):

    @property
    def version(self) -> str:
        major, minor, maintenance, platform, build_number = vs.GetVersionEx()
        return str(major + 1995 if major > 12 else major)

    @property
    def platform(self) -> int:
        major, minor, maintenance, platform, build_number = vs.GetVersionEx()
        return platform

    @property
    def dongle(self) -> str:
        return vs.GetActiveSerialNumber()[-6:]

    def get_folder_path_of_plugin_file(self, filename: str) -> str:
        succeeded, file_path = vs.FindFileInPluginFolder(filename)
        return self.__get_os_independent_file_path(file_path)

    def get_folder_path_of_active_document(self) -> str:
        return self.get_file_path_of_active_document()[:-len(vs.GetFName())]

    def get_file_path_of_active_document(self) -> str:
        return self.__get_os_independent_file_path(vs.GetFPathName())

    def __get_os_independent_file_path(self, file_path: str) -> str:
        """
        Patrick Stanford <patstanford@coviana.com> on the VectorScript Discussion List:
        Since Mac OS 10, as they're rewritten it using UNIX kernel, the mac uses Posix natively.
        Since VW predates that, the old calls use HFS paths and need to be converted for newer APIs.
        You can ask VW to do the conversion, as simply replacing the characters are not enough (Posix uses volume
        mounting instead of drive names). This can be done through vs.ConvertHSF2PosixPath().
        """
        if self.platform == Platform.MAC_OS:
            succeeded, file_path = vs.ConvertHSF2PosixPath(file_path)
        return file_path


class ActivePlugInType(object):
    MENU = '.vsm'
    TOOL = '.vst'
    OBJECT = '.vso'


class ActivePlugIn(object, metaclass=SingletonMeta):

    def __init__(self):
        self.__version = ''

    @property
    def version(self) -> str:
        return self.__version

    @version.setter
    def version(self, value: str):
        self.__version = value

    @property
    def name(self) -> str:
        # Singletons will keep it's data throughout the entire Vectorworks session!
        # This result isn't the same during that session, it depends on the active plugin!
        succeeded, name, record_handle = vs.GetPluginInfo()
        if not succeeded:
            raise VSException('GetPluginInfo')
        return name

    @property
    def handle(self):
        # Singletons will keep it's data throughout the entire Vectorworks session!
        # This result isn't the same during that session, it depends on the active plugin!
        succeeded, name, plugin_handle, record_handle, wall_handle = vs.GetCustomObjectInfo()
        if not succeeded:
            raise VSException('GetCustomObjectInfo')
        return plugin_handle


class ActivePlugInInfo(object):
    """
    Decorator to initialize the active plugin. This should be used on the main run method of the plugin!
    """

    def __init__(self, version: str):
        self.__version = version

    def __call__(self, function: callable) -> callable:
        def initialize_active_plugin_function(*args, **kwargs):
            ActivePlugIn().version = self.__version
            function(*args, **kwargs)
        return initialize_active_plugin_function


class ActivePlugInEvent(object):
    VSO_ON_RESET = 3


class ActivePlugInEvents(object):
    """
    Decorator to initialize eventing. Basically it's just telling which def has to be called for which event.
    """

    def __init__(self, events: dict):
        self.__events = events

    def __call__(self, function: callable) -> callable:
        def delegate_event_function(*args, **kwargs):
            function(*args, **kwargs)  # Function is executed first to enable extra initialization.
            event, button = vs.vsoGetEventInfo()
            self.__events.get(event, lambda : None)()
        return delegate_event_function


class AbstractActivePlugInParameters(object, metaclass=ABCMeta):
    """
    Vectorworks will always give you the initial values of parameters. So when changing them inside your script,
    you'll still get the initial values. Therefore we'll create some sort of cache to remember the current values.
    """

    def __init__(self):
        self.__parameters = dict()

    def _get_parameter(self, name: str):
        return self.__parameters[name] if name in self.__parameters else self.__store_and_get_parameter(name)

    def __store_and_get_parameter(self, name: str):
        self.__parameters[name] = getattr(vs, 'P%s' % name)  # Vectorworks puts parameters inside the vs module!
        return self.__parameters[name]

    def _set_parameter(self, name: str, value):
        self.__parameters[name] = value
        vs.SetRField(ActivePlugIn().handle, ActivePlugIn().name, name,
                     value if isinstance(value, str) else vs.Num2Str(-2, value))


class AbstractActivePlugInPrefsXmlFile(AbstractXmlFile, metaclass=ABCMeta):

    def __init__(self, active_plugin_type: str):
        """
        :type active_plugin_type: ActivePlugInType(Enum)
        """
        file_path = Vectorworks().get_folder_path_of_plugin_file(ActivePlugIn().name + active_plugin_type)
        super().__init__(os.path.join(file_path, ActivePlugIn().name + 'Prefs.xml'))


class AbstractActivePlugInDrawingXmlFile(AbstractXmlFile, metaclass=ABCMeta):

    def __init__(self):
        super().__init__(os.path.join(Vectorworks().get_folder_path_of_active_document(), ActivePlugIn().name + '.xml'))


class Security(object):
    """
    Decorator to secure a function based on the dongle and VW version running.
    """

    @staticmethod
    def __create_no_license_alert():
        return Alert(AlertType.WARNING,
                     'You have no rights to use this plugin.',
                     'Contact the plugin distributor to acquire a license.')

    @staticmethod
    def __create_other_license_alert(version: str):
        return Alert(AlertType.WARNING,
                     'Your license is for Vectorworks %s' % version,
                     'Contact the plugin distributor to update your license.')

    def __init__(self, version: str, dongles: set=None):
        self.__version = version
        self.__dongles = dongles
        self.__no_license_alert = self.__create_no_license_alert()
        self.__other_license_alert = self.__create_other_license_alert(version)

    def __call__(self, function: callable) -> callable:
        def secured_function(*args, **kwargs):
            if (Vectorworks().dongle not in self.__dongles) if (self.__dongles is not None) else False:
                self.__no_license_alert.show()
            elif Vectorworks().version != self.__version:
                self.__other_license_alert.show()
            else:
                function(*args, **kwargs)
        return secured_function
