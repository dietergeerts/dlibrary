from dlibrary.dialog.predefined.alert import Alert, AlertType
from dlibrary.utility.exception import VSException


def alert_load_plugin_file(load: callable, *args, **kwargs):
    try: value = load(*args, **kwargs)
    except VSException: Alert(
        AlertType.CRITICAL,
        'Something went wrong with this plug-in. It may be corrupt.',
        'Please contact the distributor.'
    ).show(); raise
    except FileNotFoundError: Alert(
        AlertType.CRITICAL,
        'The main dialog file could not be found.',
        'Make sure all provided plug-in files are in the plug-in folder.'
    ).show(); raise
    except PermissionError: Alert(
        AlertType.CRITICAL,
        'The main dialog file could not be read.',
        'Make sure all provided plug-in files have read/write permissions.'
    ).show(); raise
    except OSError: Alert(
        AlertType.CRITICAL,
        'Something went wrong while loading the main dialog file.',
        'Make sure all plug-in files are in the plug-in folder, have read/write permissions and are not corrupt.'
    ).show(); raise
    else: return value