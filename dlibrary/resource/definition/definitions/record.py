from dlibrary.resource.definition.definition import DefinitionTypeEnum
from dlibrary.resource.resourcelist import AbstractResourceList, AbstractResource
from dlibrary.utility.observable import ObservableList
import vs


class RecordDefinition(AbstractResource):
    def __init__(self, handle, name: str):
        super().__init__(handle, name)
        self.__fields = ObservableList(vs.GetFldName(self._handle, index)
                                       for index in range(1, vs.NumFields(self._handle) + 1))

    @property
    def fields(self) -> ObservableList:
        return self.__fields


class RecordDefinitionResourceList(AbstractResourceList):
    def __init__(self):
        super().__init__(DefinitionTypeEnum.RECORD_DEFINITION, RecordDefinition)