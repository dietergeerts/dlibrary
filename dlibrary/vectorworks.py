from dlibrary.dialog.predefined.alert import Alert, AlertType
from dlibrary.utility.exception import VSException
from dlibrary.utility.singleton import SingletonMeta
from dlibrary.utility.xmltodict import AbstractXmlFile
import vs


class Vectorworks(object, metaclass=SingletonMeta):

    @property
    def version(self) -> str:
        (major, _, _, _, _) = vs.GetVersionEx()
        return str(major + 1995 if major > 12 else major)

    @property
    def dongle(self) -> str:
        return vs.GetActiveSerialNumber()[-6:]


class ActivePlugInType(object):
    MENU = '.vsm'
    TOOL = '.vst'
    OBJECT = '.vso'


class ActivePlugIn(object, metaclass=SingletonMeta):

    def __init__(self):
        self.__name = None

    @property
    def name(self):
        # Singletons will keep it's data throughout the entire Vectorworks session!
        # This result isn't the same during that session, it depends on the active plugin!
        succeeded, self.__name, _ = vs.GetPluginInfo()
        if not succeeded:
            raise VSException('GetPluginInfo')
        return self.__name


class AbstractActivePlugInPrefsXmlFile(AbstractXmlFile):

    def __init__(self, active_plugin_type: str):
        """
        :type active_plugin_type: ActivePlugInType(Enum)
        """
        _, file_path = vs.FindFileInPluginFolder(ActivePlugIn().name + active_plugin_type)
        super().__init__(file_path + ActivePlugIn().name + 'Prefs.xml')


class AbstractActivePlugInDrawingXmlFile(AbstractXmlFile):

    def __init__(self):
        super().__init__(vs.GetFPathName()[:-len(vs.GetFName())] + ActivePlugIn().name + '.xml')


class Security(object):
    """
    Decorator to secure a function based on the dongle and VW version running.
    """

    @staticmethod
    def __create_no_license_alert():
        return Alert(AlertType.WARNING,
                     'You have no rights to use this plugin.',
                     'Contact the plugin distributor to aquire a license.')

    @staticmethod
    def __create_other_license_alert(version: str):
        return Alert(AlertType.WARNING,
                     'Your license is for Vectorworks %s' % version,
                     'Contact the plugin distributor to update your license.')

    def __init__(self, version: str, dongles: set):
        self.__version = version
        self.__dongles = dongles
        self.__no_license_alert = self.__create_no_license_alert()
        self.__other_license_alert = self.__create_other_license_alert(version)

    def __call__(self, function: callable) -> callable:
        def secured_function(*args, **kwargs):
            if Vectorworks().dongle not in self.__dongles:
                self.__no_license_alert.show()
            elif Vectorworks().version != self.__version:
                self.__other_license_alert.show()
            else:
                function(*args, **kwargs)
        return secured_function
