"""Used for all Vectorworks related stuff, like settings, and for plug-in objects and their setup and working.
"""

from abc import ABCMeta, abstractmethod
import os

from dlibrary.dialog_predefined import AlertType, Alert
from dlibrary.object import Record
from dlibrary.utility import AbstractXmlFile, SingletonMeta, VSException
import vs


class Platform(object):
    MAC_OS = 1
    WINDOWS = 2


class Vectorworks(object, metaclass=SingletonMeta):

    @property
    def version(self) -> str:
        major, minor, maintenance, platform, build_number = vs.GetVersionEx()
        return str(major + 1995 if major > 12 else major)

    @property
    def platform(self) -> int:
        major, minor, maintenance, platform, build_number = vs.GetVersionEx()
        return platform

    @property
    def dongle(self) -> str:
        return vs.GetActiveSerialNumber()[-6:]

    def get_folder_path_of_plugin_file(self, filename: str) -> str:
        succeeded, file_path = vs.FindFileInPluginFolder(filename)
        return self.__get_os_independent_file_path(file_path)

    def get_folder_path_of_active_document(self) -> str:
        return self.get_file_path_of_active_document()[:-len(vs.GetFName())]

    def get_file_path_of_active_document(self) -> str:
        return self.__get_os_independent_file_path(vs.GetFPathName())

    def __get_os_independent_file_path(self, file_path: str) -> str:
        """
        Patrick Stanford <patstanford@coviana.com> on the VectorScript Discussion List:
        Since Mac OS 10, as they're rewritten it using UNIX kernel, the mac uses Posix natively.
        Since VW predates that, the old calls use HFS paths and need to be converted for newer APIs.
        You can ask VW to do the conversion, as simply replacing the characters are not enough (Posix uses volume
        mounting instead of drive names). This can be done through vs.ConvertHSF2PosixPath().
        """
        if self.platform == Platform.MAC_OS:
            succeeded, file_path = vs.ConvertHSF2PosixPath(file_path)
        return file_path


class ActivePlugInType(object):
    MENU = '.vsm'
    TOOL = '.vst'
    OBJECT = '.vso'


class ActivePlugIn(object, metaclass=SingletonMeta):

    def __init__(self):
        self.__version = ''

    @property
    def version(self) -> str:
        return self.__version

    @version.setter
    def version(self, value: str):
        self.__version = value

    @property
    def name(self) -> str:
        # Singletons will keep it's data throughout the entire Vectorworks session!
        # This result isn't the same during that session, it depends on the active plugin!
        succeeded, name, record_handle = vs.GetPluginInfo()
        if not succeeded:
            raise VSException('GetPluginInfo')
        return name

    @property
    def handle(self):
        # Singletons will keep it's data throughout the entire Vectorworks session!
        # This result isn't the same during that session, it depends on the active plugin!
        succeeded, name, plugin_handle, record_handle, wall_handle = vs.GetCustomObjectInfo()
        if not succeeded:
            # If not succeeded, then it means that it's not an instance, so we want to get the definition handle.
            # TODO: Make the difference in plugin definition and instance clearer, probably more generic!
            plugin_handle = vs.GetObject(self.name)
            # raise VSException('GetCustomObjectInfo')
        return plugin_handle

    @property
    def parameters(self) -> Record:
        # Singletons will keep it's data throughout the entire Vectorworks session!
        # This result isn't the same during that session, it depends on the active plugin!
        succeeded, name, plugin_handle, record_handle, wall_handle = vs.GetCustomObjectInfo()
        # TODO: What if we want this record for a menu or tool plugin?
        if not succeeded:
            raise VSException('GetCustomObjectInfo')
        return Record(record_handle)


class ActivePlugInInfo(object):
    """
    Decorator to initialize the active plugin. This should be used on the main run method of the plugin!
    """

    def __init__(self, version: str):
        self.__version = version

    def __call__(self, function: callable) -> callable:
        def initialize_active_plugin_function(*args, **kwargs):
            ActivePlugIn().version = self.__version
            function(*args, **kwargs)
        return initialize_active_plugin_function


class AbstractResetArgs(object, metaclass=ABCMeta):
    pass


class EmptyResetArgs(AbstractResetArgs):
    pass


class CreationResetArgs(AbstractResetArgs):
    pass


class ParameterChangedResetArgs(AbstractResetArgs):

    def __init__(self, index: int):
        self.__name = ActivePlugIn().parameters.get_field(index).name

    @property
    def name(self) -> str:
        return self.__name


class ActivePlugInEvent(object):
    VSO_ON_RESET = 3           # Args: ResetArgs, if functionality is turned on!
    VSO_ON_INITIALIZATION = 5  # Args: -
    VSO_ON_DOUBLE_CLICK = 7    # Args: -; Will only happen when double click behaviour is set to custom dialog!
    VSO_ON_WIDGET_CLICK = 35   # Args: widget_id
    VSO_ON_ADD_STATE = 44      # Args: widget_id


class ActivePlugInEvents(object):
    """
    Decorator to initialize eventing. Basically it's just telling which def has to be called for which event.
    """

    def __init__(self, events: dict, with_reset_args: bool=False):
        self.__events = events
        self.__with_reset_args = with_reset_args

    def __call__(self, function: callable) -> callable:
        def delegate_event_function(*args, **kwargs):
            function(*args, **kwargs)  # Function is executed first to enable extra initialization.
            event, widget_id = vs.vsoGetEventInfo()
            event_args = None  # We only fill this when this feature is enabled!

            if self.__with_reset_args:
                if event == ActivePlugInEvent.VSO_ON_INITIALIZATION:
                    self.__with_reset_args_on_initialization()
                if event == ActivePlugInEvent.VSO_ON_ADD_STATE:
                    self.__with_reset_args_on_add_state(widget_id)
                if event == ActivePlugInEvent.VSO_ON_RESET:
                    event_args = self.__with_reset_args_on_reset()

            event_handler = self.__events.get(event, None)
            if event_handler is not None:
                self.__execute_event_handler(event_handler, event, widget_id, event_args)
        return delegate_event_function

    @staticmethod
    def __with_reset_args_on_initialization():
        vs.SetPrefInt(590, 1)  # 590 = enable state eventing, 1 = reset state events.
        if not vs.SetObjPropVS(18, True):  # 18 = accept states.
            raise VSException('SetObjPropVS')

    @staticmethod
    def __with_reset_args_on_add_state(widget_id: int):
        vs.vsoStateAddCurrent(ActivePlugIn().handle, widget_id)  # Only this MUST be called, nothing else!

    def __with_reset_args_on_reset(self) -> AbstractResetArgs:
        event_args = self.__try_get_creation_reset_args()
        event_args = self.__try_get_parameter_change_reset_args() if event_args is None else event_args
        vs.vsoStateClear(ActivePlugIn().handle)  # EXTREMELY IMPORTANT to have this!
        return event_args if event_args is not None else EmptyResetArgs()

    @staticmethod
    def __try_get_creation_reset_args() -> CreationResetArgs:
        trigger = vs.vsoStateGet(ActivePlugIn().handle, 0)  # 0 = creation. (13 and 16 on 2nd round also happens!)
        return CreationResetArgs() if trigger else None

    @staticmethod
    def __try_get_parameter_change_reset_args() -> ParameterChangedResetArgs:
        trigger, widget_id, parameter_index, old_value = vs.vsoStateGetParamChng(ActivePlugIn().handle)
        return ParameterChangedResetArgs(parameter_index) if trigger else None

    def __execute_event_handler(self, event_handler: callable, event: int, widget_id: int, args: AbstractResetArgs):
        if self.__with_reset_args and event == ActivePlugInEvent.VSO_ON_RESET:
            event_handler(args)
        elif event == ActivePlugInEvent.VSO_ON_ADD_STATE or event == ActivePlugInEvent.VSO_ON_WIDGET_CLICK:
            event_handler(widget_id)
        else:
            event_handler()


class AbstractWidget(object, metaclass=ABCMeta):

    @abstractmethod
    def add(self, widget_id: int):
        pass


class ParameterWidget(AbstractWidget):

    def __init__(self, parameter: str):
        self.__parameter = parameter

    def add(self, widget_id: int):
        if not vs.vsoAddParamWidget(widget_id, self.__parameter, ''):  # '' for using parameter alternate name.
            raise VSException('vsoAddParamWidget(%s, %s, '')' % (widget_id, self.__parameter))


class ButtonWidget(AbstractWidget):

    def __init__(self, text: str, on_click: callable, reset: bool=False):
        """
        :param reset: If true, the pio instance will be reset after the on_click def.
        """
        self.__text = text
        self.__on_click = on_click if not reset else lambda : self.__on_click_and_reset(on_click)

    @property
    def on_click(self) -> callable:
        return self.__on_click

    def add(self, widget_id: int):
        if not vs.vsoInsertWidget(widget_id, 12, widget_id, self.__text, 0):  # 12 = Button.
            raise VSException('vsoAddWidget(%s, 12, %s)' % (widget_id, self.__text))

    @staticmethod
    def __on_click_and_reset(on_click: callable):
        on_click()
        vs.ResetObject(ActivePlugIn().handle)


class DoubleClickBehaviour(object):
    DEFAULT = 0            # The default behaviour for the object type will be used.
    CUSTOM_EVENT = 1       # The VSO_ON_DOUBLE_CLICK event will be thrown.
    PROPERTIES_DIALOG = 2  # Is actually the object info palette that will be shown.
    RESHAPE_MODE = 3       # Go into reshape mode, practical for path shaped objects.


class ActivePlugInSetup(object):
    """
    Decorator to setup the active plugin with event-enabled setup things like custom info pallet.
    """

    def __init__(self, info_pallet: list=None, double_click_behaviour: int=DoubleClickBehaviour.DEFAULT):
        """
        :type info_pallet: list[AbstractWidget]
        """
        self.__info_pallet = info_pallet
        self.__double_click_behaviour = double_click_behaviour

    def __call__(self, function: callable) -> callable:
        @ActivePlugInEvents(events={
            ActivePlugInEvent.VSO_ON_INITIALIZATION: self.__on_initialization,
            ActivePlugInEvent.VSO_ON_WIDGET_CLICK: self.__on_widget_click})
        def setup_active_plugin_function(*args, **kwargs):
            function(*args, **kwargs)
        return setup_active_plugin_function

    def __on_initialization(self):
        self.__init_info_pallet() if self.__info_pallet is not None else None
        self.__init_double_click() if self.__double_click_behaviour is not DoubleClickBehaviour.DEFAULT else None

    def __init_info_pallet(self):
        if not vs.SetObjPropVS(8, True):  # 8 = Custom Info Palette property!
            raise VSException('SetObjPropVS(8, True)')
        for index, widget in enumerate(self.__info_pallet, 1):
            widget.add(index)

    def __init_double_click(self):
        if not vs.SetObjPropCharVS(3, self.__double_click_behaviour):  # 3 = Double click behavior!
            raise VSException('SetObjPropCharVS(3, %s)' % self.__double_click_behaviour)

    def __on_widget_click(self, widget_id):
        if self.__info_pallet is not None:
            widget = self.__info_pallet[widget_id - 1]  # We enumerated from 1 at initialization of widgets!
            widget.on_click() if isinstance(widget, ButtonWidget) else None


class AbstractActivePlugInParameters(object, metaclass=ABCMeta):
    """
    Vectorworks will always give you the initial values of parameters. So when changing them inside your script,
    you'll still get the initial values. Therefore we'll create some sort of cache to remember the current values.
    """

    def __init__(self):
        self.__parameters = dict()

    def _get_parameter(self, name: str):
        return self.__parameters[name] if name in self.__parameters else self.__store_and_get_parameter(name)

    def __store_and_get_parameter(self, name: str):
        self.__parameters[name] = getattr(vs, 'P%s' % name)  # Vectorworks puts parameters inside the vs module!
        return self.__parameters[name]

    def _set_parameter(self, name: str, value):
        self.__parameters[name] = value
        vs.SetRField(ActivePlugIn().handle, ActivePlugIn().name, name,
                     value if isinstance(value, str) else vs.Num2Str(-2, value))


class AbstractActivePlugInPrefsXmlFile(AbstractXmlFile, metaclass=ABCMeta):

    def __init__(self, active_plugin_type: str):
        """
        :type active_plugin_type: ActivePlugInType(Enum)
        """
        file_path = Vectorworks().get_folder_path_of_plugin_file(ActivePlugIn().name + active_plugin_type)
        super().__init__(os.path.join(file_path, ActivePlugIn().name + 'Prefs.xml'))


class AbstractActivePlugInDrawingXmlFile(AbstractXmlFile, metaclass=ABCMeta):

    def __init__(self):
        super().__init__(os.path.join(Vectorworks().get_folder_path_of_active_document(), ActivePlugIn().name + '.xml'))


class Security(object):
    """
    Decorator to secure a function based on the dongle and VW version running.
    Make sure you use this as the topmost decorator in order for the check to be the first thing that will happen!
    If your plugin is event enabled, then make sure that you have the following order:
        @ActivePlugInInfo
        @ActivePlugInSetup > before security, as we'll setup the info pallet here!
        @Security
        @ActivePlugInEvents
    This is because everything under @Security will not run if the user has no permission!
    """

    @staticmethod
    def __create_no_license_alert():
        return Alert(AlertType.WARNING,
                     'You have no rights to use this plugin.',
                     'Contact the plugin distributor to acquire a license.')

    @staticmethod
    def __create_other_license_alert(version: str):
        return Alert(AlertType.WARNING,
                     'Your license is for Vectorworks %s' % version,
                     'Contact the plugin distributor to update your license.')

    def __init__(self, version: str, dongles: set=None):
        self.__version = version
        self.__dongles = dongles
        self.__no_license_alert = self.__create_no_license_alert()
        self.__other_license_alert = self.__create_other_license_alert(version)

    def __call__(self, function: callable) -> callable:
        def secured_function(*args, **kwargs):
            if (Vectorworks().dongle not in self.__dongles) if (self.__dongles is not None) else False:
                self.__no_license_alert.show()
            elif Vectorworks().version != self.__version:
                self.__other_license_alert.show()
            else:
                function(*args, **kwargs)
        return secured_function
