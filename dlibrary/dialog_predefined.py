import vs


class AlertType(object):
    CRITICAL = 0
    WARNING = 1
    INFO = 2
    SUCCESS = 3


class Alert(object):

    def __init__(self, alert_type: int, text: str, advice: str=''):
        self.__type = alert_type
        self.__text = text
        self.__advice = advice

    def show(self):
        if self.__type == AlertType.CRITICAL:
            vs.AlertCritical(self.__text, self.__advice)
        elif self.__type == AlertType.WARNING:
            vs.AlertInform(self.__text, self.__advice, False)
        elif self.__type == AlertType.INFO:
            vs.AlertInform(self.__text, self.__advice, True)
        elif self.__type == AlertType.SUCCESS:
            vs.AlrtDialog(self.__text)


class PlugInFileVsExceptionAlert(Alert):

    def __init__(self):
        super().__init__(AlertType.CRITICAL,
                         'Something went wrong with this plug-in. It may be corrupt.',
                         'Please contact the distributor.')


class PlugInFileFileNotFoundErrorAlert(Alert):

    def __init__(self):
        super().__init__(AlertType.CRITICAL,
                         'A plug-in file could not be found.',
                         'Make sure all provided plug-in files are in the plug-in folder.')


class PlugInFilePermissionErrorAlert(Alert):

    def __init__(self):
        super().__init__(AlertType.CRITICAL,
                         'A plug-in file could not be read.',
                         'Make sure all provided plug-in files have read/write permissions.')


class PlugInFileOsErrorAlert(Alert):

    def __init__(self):
        super().__init__(AlertType.CRITICAL,
                         'Something went wrong while loading a plug-in file.',
                         'Make sure all plug-in files are in the plug-in folder, '
                         'have read/write permissions and are not corrupt.')
