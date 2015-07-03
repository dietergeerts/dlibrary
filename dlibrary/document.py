from dlibrary.utility.singleton import SingletonMeta
import vs


class Document(object, metaclass=SingletonMeta):

    @property
    def saved(self) -> bool:
        return vs.GetFName() != vs.GetFPathName()

    @property
    def filename(self) -> str:
        return vs.GetFName()
