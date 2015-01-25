class VSException(BaseException):
    def __init__(self, function: str):
        self.__function = function