from abc import ABCMeta
from dlibrary.utility.observable import ObservableList
import vs


class AbstractResource(object, metaclass=ABCMeta):
    def __init__(self, handle, name: str):
        self.__handle = handle
        self.__name = name

    @property
    def _handle(self) -> str:
        return self.__handle

    @property
    def name(self) -> str:
        return self.__name


class AbstractResourceList(object, metaclass=ABCMeta):
    def __init__(self, resource_type: int, abstract_resource: callable):
        self.__abstract_resource = abstract_resource
        self.__resource_names = ObservableList()
        self.__resource_list, count = vs.BuildResourceList(resource_type, 0, '')
        resources_to_delete = list()
        for index in range(count):
            handle = self.__get_resource(index)
            name = self.__get_resource_name(index)
            # '__' Indicates a 'hidden' record, mostly __NNA...
            if name.startswith('__') or (handle is not None and vs.IsPluginFormat(handle)):
                resources_to_delete.append(index)
            else:
                self.__resource_names.append(name)
        for index in resources_to_delete:
            self.__remove_resource(index)

    @property
    def names(self) -> ObservableList:
        return self.__resource_names

    def get_resource(self, name: str) -> AbstractResource:
        index = self.__resource_names.index(name)
        if index == -1:
            return None
        else:
            handle = self.__get_resource(index) or self.__import_resource(index)
            name = self.__resource_names[index]  # Name could be changed due to import!
            return self.__abstract_resource(handle, name)

    def __get_resource(self, index) -> object:
        return vs.GetResourceFromList(self.__resource_list, index + 1)

    def __get_resource_name(self, index) -> str:
        return vs.GetNameFromResourceList(self.__resource_list, index + 1)

    def __import_resource(self, index) -> object:
        handle = vs.ImportResToCurFileN(self.__resource_list, index + 1, lambda s: 1)  # 1 >> Replace if needed!
        self.__resource_names[index] = vs.GetActualNameFromResourceList(self.__resource_list, index + 1)
        return handle

    def __remove_resource(self, index):
        vs.DeleteResourceFromList(self.__resource_list, index + 1)