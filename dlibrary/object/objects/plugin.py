from dlibrary.utility import xmltodict
from dlibrary.utility.exception import VSException
from dlibrary.utility.singleton import SingletonMeta
import vs


class PlugIn(object, metaclass=SingletonMeta):
    def __init__(self):
        self.__name = None; """@type: str"""
        self.__preferences = None; """@type: dict"""

    @property
    def __preferences_path(self): return self.__name + 'Prefs.xml'

    def load_preferences(self) -> dict:
        succeeded, name, record = vs.GetPluginInfo()
        if not succeeded: raise VSException('GetPluginInfo')
        else: self.__name = name;
        exists, path = vs.FindFileInPluginFolder(self.__preferences_path)
        if not exists: raise FileNotFoundError
        try: self.__preferences = xmltodict.load(path, set())
        except FileNotFoundError: raise
        except PermissionError: raise
        except OSError: raise
        else: return self.__preferences

    def save(self):
        if self.__preferences is not None: xmltodict.save(self.__preferences, self.__preferences_path)