from dlibrary.utility.singleton import SingletonMeta
import vs


class Document(object, metaclass=SingletonMeta):
    @property
    def saved(self): return vs.GetFName() != vs.GetFPathName()