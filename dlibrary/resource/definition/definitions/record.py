from dlibrary.resource.definition.definition import DefinitionTypeEnum
from dlibrary.utility.singleton import SingletonMeta
import vs


class RecordDefinitionField(object):
    def __init__(self, name: str):
        self.__name = name

    def __str__(self):
        return self.__name


class RecordDefinition(object):
    def __init__(self, import_me: callable, handle, name: str):
        self.__import_me = import_me
        self.__handle = handle
        self.__name = name

    def __str__(self) -> str:
        return self.__name

    @property
    def fields(self) -> list:
        if self.__handle is None:  # Indicates not yet imported resource!
            self.__handle = self.__import_me()
        return list(RecordDefinitionField(vs.GetFldName(self.__handle, index))
                    for index in range(1, vs.NumFields(self.__handle) + 1))


class RecordDefinitionRepository(object, metaclass=SingletonMeta):
    # We are not able to cache the resource list, as VW keeps that cache
    # throughout the whole VW session and not the Script session.
    # This has it's impact on all objects, as we can't cache anything!

    @staticmethod
    def get_all() -> list:
        record_definitions = list()
        resource_list, count = vs.BuildResourceList(DefinitionTypeEnum.RECORD_DEFINITION, 0, '')
        for index in range(count, 0, -1):
            handle = vs.GetResourceFromList(resource_list, index)
            name = vs.GetNameFromResourceList(resource_list, index)
            # '__' Indicates a 'hidden' record, mostly __NNA...
            if not name.startswith('__') and (handle is None or not vs.IsPluginFormat(handle)):
                import_me = lambda i=index: vs.ImportResToCurFileN(resource_list, i, lambda s: 1)
                record_definitions.append(RecordDefinition(import_me, handle, name))
        return record_definitions