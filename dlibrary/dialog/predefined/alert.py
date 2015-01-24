import vs


class AlertType(object):
    CRITICAL = 0; WARNING = 1; INFO = 2; SUCCESS = 3


class Alert(object):
    def __init__(self, type: AlertType, text: str, advice: str=''):
        {
            AlertType.CRITICAL: vs.AlertCritical(text, advice),
            AlertType.WARNING:  vs.AlertInform(text, advice, False),
            AlertType.INFO:     vs.AlertInform(text, advice, True),
            AlertType.SUCCESS:  vs.AlrtDialog(text)
        }.get(type)