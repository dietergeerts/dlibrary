import vs


class AlertType(object):
    CRITICAL = 0; WARNING = 1; INFO = 2; SUCCESS = 3


class Alert(object):
    def __init__(self, type: AlertType, text: str, advice: str=''):
        self.__type = type; self.__text = text; self.__advice = advice

    def show(self):
        if   self.__type == AlertType.CRITICAL: vs.AlertCritical(self.__text, self.__advice)
        elif self.__type == AlertType.WARNING:  vs.AlertInform(self.__text, self.__advice, False)
        elif self.__type == AlertType.INFO:     vs.AlertInform(self.__text, self.__advice, True)
        elif self.__type == AlertType.SUCCESS:  vs.AlrtDialog(self.__text)