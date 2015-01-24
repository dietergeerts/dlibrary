from dlibrary.utility import xmltodict
from dlibrary.utility.exception import VSException
from dlibrary.utility.singleton import SingletonMeta
import vs


class PlugIn(object, metaclass=SingletonMeta):
    def __init__(self):
        self.__name = None; """@type: str"""

    def __load_info(self):
        if self.__name is None:
            succeeded, name, record = vs.GetPluginInfo()
            if not succeeded: raise VSException('GetPluginInfo')
            else: self.__name = name;

    def __get_file_name(self, name: str) -> str: return self.__name + name + '.xml'

    def __get_file_path(self, name: str) -> str:
        exists, path = vs.FindFileInPluginFolder(name)
        if not exists: raise FileNotFoundError
        else: return path + name

    def load_plugin_file(self, name: str, list_elements: set=None) -> dict:
        try: self.__load_info()
        except VSException: raise
        else:
            try: path = self.__get_file_path(self.__get_file_name(name))
            except FileNotFoundError: raise
            else:
                try: content = xmltodict.load(path, list_elements or set())
                except FileNotFoundError: raise
                except PermissionError: raise
                except OSError: raise
                else: return content

    def save_plugin_file(self, content: dict, name: str):
        try: self.__load_info()
        except VSException: raise
        else:
            try: path = self.__get_file_path(self.__get_file_name(name))
            except FileNotFoundError: raise
            else: xmltodict.save(content, path)