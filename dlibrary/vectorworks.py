from dlibrary.dialog.predefined.alert import Alert, AlertType
from dlibrary.utility.singleton import SingletonMeta
import vs


class Vectorworks(object, metaclass=SingletonMeta):

    @property
    def version(self) -> str:
        (major, _, _, _, _) = vs.GetVersionEx()
        return str(major + 1995 if major > 12 else major)

    @property
    def dongle(self) -> str:
        return vs.GetActiveSerialNumber()[-6:]


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
                     'Your license is for Vectorworks version %s' % version,
                     'Contact the plugin distributor to update your license.')

    def __init__(self, version: str, dongles: set):
        self.__version = version
        self.__dongles = dongles
        self.__no_license_alert = self.__create_no_license_alert()
        self.__other_license_alert = self.__create_other_license_alert(version)

    def __call__(self, function: callable) -> callable:
        def secured_function(*args, **kwargs):
            if Vectorworks.dongle not in self.__dongles:
                self.__no_license_alert.show()
            elif Vectorworks.version != self.__version:
                self.__other_license_alert.show()
            else:
                function(*args, **kwargs)
        return secured_function
