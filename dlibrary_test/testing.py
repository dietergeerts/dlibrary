from dlibrary.utility.singleton import SingletonMeta
import vs


class VectorworksInstance(object, metaclass=SingletonMeta):
    """
    For easy testing, we'll provide this class, which will hold all internal settings as properties.
    With some other functions to provide other functionality to setup our Vectorworks test instance.
    """

    def __init__(self):
        self.__platform = 0
        self.__version_major = 20
        self.__version_minor = 0
        self.__version_maintenance = 0
        self.__version_build = 95668
        self.__serial_number = 'ADF154-1AD457-ADF472-15EA1E'
        self.__active_plugin_name = 'ActivePlugInName'

    @property
    def platform(self) -> int:
        return self.__platform

    @platform.setter
    def platform(self, value: int):
        self.__platform = value

    @property
    def version_major(self) -> int:
        return self.__version_major

    @version_major.setter
    def version_major(self, value: int):
        self.__version_major = value

    @property
    def version_minor(self) -> int:
        return self.__version_minor

    @version_minor.setter
    def version_minor(self, value: int):
        self.__version_minor = value

    @property
    def version_maintenance(self) -> int:
        return self.__version_maintenance

    @version_maintenance.setter
    def version_maintenance(self, value: int):
        self.__version_maintenance = value

    @property
    def version_build(self) -> int:
        return self.__version_build

    @version_build.setter
    def version_build(self, value: int):
        self.__version_build = value

    @property
    def serial_number(self) -> str:
        return self.__serial_number

    @serial_number.setter
    def serial_number(self, value: str):
        self.__serial_number = value

    @property
    def active_plugin_name(self):
        return self.__active_plugin_name

    @active_plugin_name.setter
    def active_plugin_name(self, value):
        self.__active_plugin_name = value


# To be able to test against vs calls, we have to mock them. If they will be deleted, then we'll get errors running our
# tests, so that's an extra benefit. Off course we have to keep obsolete functions in mind. That's why we need to test
# in a live Vectorworks, which we'll do by running a menu command that checks on stuff like that.


class VectorScript(object):
    """
    To make the vs calls use our Vectorworks instance, we'll create mock functions for them.
    We can then substitute the real ones with these.
    """

    @staticmethod
    def get_active_serial_number() -> str:
        return VectorworksInstance().serial_number

    @staticmethod
    def get_version_ex() -> tuple:
        return (VectorworksInstance().version_major,
                VectorworksInstance().version_minor,
                VectorworksInstance().version_maintenance,
                VectorworksInstance().platform,
                VectorworksInstance().version_build)

    @staticmethod
    def get_plugin_info() -> tuple:
        return (True, VectorworksInstance().active_plugin_name, 0)

    @staticmethod
    def initialize():
        vs.GetActiveSerialNumber = VectorScript.get_active_serial_number
        vs.GetPluginInfo = VectorScript.get_plugin_info
        vs.GetVersionEx = VectorScript.get_version_ex
