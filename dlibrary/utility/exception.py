class DException(BaseException):
    pass

class VSException(DException):
    def __init__(self, function: str):
        self.__function = function