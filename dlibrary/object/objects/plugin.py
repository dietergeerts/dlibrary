import os
from dlibrary.utility import xmltodict
from dlibrary.utility.exception import VSException
from dlibrary.utility.singleton import SingletonMeta
import vs


class PlugIn(object, metaclass=SingletonMeta):
    def __init__(self):
        self.__name = None

    def __get_name(self) -> str:
        if self.__name is None:
            succeeded, name, record = vs.GetPluginInfo()
            if not succeeded: raise VSException('GetPluginInfo')
            else: self.__name = name
        return self.__name

    def __get_plugin_file_name(self, name: str) -> str:
        try: file_name = self.__get_name() + name + '.xml'
        except VSException: raise
        else: return file_name

    def __get_drawing_file_name(self) -> str:
        try: file_name = self.__get_name() + '.xml'
        except VSException: raise
        else: return file_name

    def __get_plugin_file_path(self, name: str) -> str:
        exists, path = vs.FindFileInPluginFolder(name)
        if not exists: raise FileNotFoundError
        else: return path + name

    def __get_drawing_file_path(self, name: str) -> str: return vs.GetFPathName()[:-len(vs.GetFName())] + name

    def load_plugin_file(self, name: str, list_elements: set=None, defaults: dict=None) -> dict:
        try:
            path = self.__get_plugin_file_path(self.__get_plugin_file_name(name))
            content = xmltodict.load(path, list_elements or set(), defaults or dict())
        except (VSException, FileNotFoundError, PermissionError, OSError): raise
        else: return content

    def save_plugin_file(self, content: dict, name: str):
        try: path = self.__get_plugin_file_path(self.__get_plugin_file_name(name))
        except VSException: raise
        except FileNotFoundError: raise
        else: xmltodict.save(content, path)

    def load_drawing_file(self, list_elements: set=None, defaults: dict=None) -> dict:
        try:
            path = self.__get_drawing_file_path(self.__get_drawing_file_name())
            if not os.path.isfile(path): content = {'prefs': {}}
            else: content = xmltodict.load(path, list_elements or set(), defaults or dict())
        except (VSException, FileNotFoundError, PermissionError, OSError): raise
        else: return content

    def save_drawing_file(self, content: dict):
        try: path = self.__get_drawing_file_path(self.__get_drawing_file_name())
        except VSException: raise
        else: xmltodict.save(content, path)