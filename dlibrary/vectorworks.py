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

    @staticmethod
    def show_message(message: str):
        vs.Message(message)

    @staticmethod
    def clear_message():
        vs.ClrMessage()

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
        self.__font_style_enabled = False

    @property
    def version(self) -> str:
        return self.__version

    @version.setter
    def version(self, value: str):
        self.__version = value

    @property
    def font_style_enabled(self) -> bool:
        """:rtype: bool"""
        return self.__font_style_enabled

    @font_style_enabled.setter
    def font_style_enabled(self, value: bool):
        """:type value: bool"""
        self.__font_style_enabled = value

    @property
    def name(self) -> str:
        # Singletons will keep it's data throughout the entire Vectorworks session!
        # This result isn't the same during that session, it depends on the active plugin!
        succeeded, name, record_handle = vs.GetPluginInfo()
        if not succeeded:
            raise VSException('GetPluginInfo')
        return name

    @property
    def handle(self) -> vs.Handle:
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

    @property
    def origin(self) -> tuple:
        """:rtype: (float, float)"""
        return vs.GetSymLoc(self.handle)

    @property
    def rotation(self) -> float:
        """:rtype: float"""
        return vs.GetSymRot(self.handle)


class ActivePlugInInfo(object):
    """
    Decorator to initialize the active plugin. This should be used on the main run method of the plugin!
    """

    def __init__(self, version: str, font_style_enabled: bool=False):
        self.__version = version
        self.__font_style_enabled = font_style_enabled

    def __call__(self, function: callable) -> callable:
        def initialize_active_plugin_function(*args, **kwargs):
            ActivePlugIn().version = self.__version
            ActivePlugIn().font_style_enabled = self.__font_style_enabled
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
    VSO_ON_WIDGET_PREP = 41    # Args: -
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

            # Doing extra setup for using reset args, and get them.
            if self.__with_reset_args:
                if event == ActivePlugInEvent.VSO_ON_INITIALIZATION:
                    self.__with_reset_args_on_initialization()
                if event == ActivePlugInEvent.VSO_ON_ADD_STATE:
                    self.__with_reset_args_on_add_state(widget_id)
                if event == ActivePlugInEvent.VSO_ON_RESET:
                    event_args = self.__with_reset_args_on_reset()

            # Get the event handler and execute if found.
            event_handler = self.__events.get(event, None)
            if event_handler is not None:
                self.__execute_event_handler(event_handler, event, widget_id, event_args)

            # After the widget prep event, we need to finish with the following! VW requires this.
            if event == ActivePlugInEvent.VSO_ON_WIDGET_PREP:
                vs.vsoSetEventResult(-8)  # -8 = event handled!

            # Because of a returning bug, font style enabling has to happen in the reset event!
            if event == ActivePlugInEvent.VSO_ON_RESET:
                if ActivePlugIn().font_style_enabled:  # It's disabled by default!
                    vs.SetObjectVariableBoolean(ActivePlugIn().handle, 800, True)

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
    """Abstract base class for object info pallet widgets.
    """

    def __init__(self, visible: callable=None, disabled: callable=None):
        """
        :type visible: () -> bool
        :type disabled: () -> bool
        """
        self.__visible = visible
        self.__disabled = disabled

    @property
    def custom_visibility(self) -> bool:
        """:rtype: bool"""
        return self.__visible is not None

    @abstractmethod
    def add(self, widget_id: int):
        """Adds the widget to the object info pallet, giving it an id.
        """
        pass

    def update(self, widget_id: int):
        """Will be called internally to update the visibility status of the widget, if it has custom visibility.
        The widget_id is given, as I couldn't find a solution to save it here, for some reason it didn't work. -Dieter.
        """
        if self.__visible is not None:
            vis = self.__visible()
            if vis != vs.vsoWidgetGetVisible(widget_id):
                vs.vsoWidgetSetVisible(widget_id, vis)
        if self.__disabled is not None:
            enabled = not self.__disabled()
            if enabled != vs.vsoWidgetGetEnable(widget_id):
                vs.vsoWidgetSetEnable(widget_id, enabled)


class ParameterWidget(AbstractWidget):

    def __init__(self, parameter: str, visible: callable=None, disabled: callable=None):
        """
        :type visible: () -> bool
        :type disabled: () -> bool
        """
        super().__init__(visible, disabled)
        self.__parameter = parameter

    def add(self, widget_id: int):
        if not vs.vsoAddParamWidget(widget_id, self.__parameter, ''):  # '' for using parameter alternate name.
            raise VSException('vsoAddParamWidget(%s, %s, '')' % (widget_id, self.__parameter))


class ButtonWidget(AbstractWidget):

    def __init__(self, text: str, on_click: callable, reset: bool=False, visible: callable=None):
        """
        :param reset: If true, the pio instance will be reset after the on_click def.
        :type visible: () -> bool
        """
        super().__init__(visible)
        self.__text = text
        self.__on_click = on_click if not reset else lambda : self.__on_click_and_reset(on_click)

    @property
    def on_click(self) -> callable:
        return self.__on_click

    def add(self, widget_id: int):
        if not vs.vsoInsertWidget(widget_id, 12, widget_id, self.__text, 0):  # 12 = Button.
            raise VSException('vsoInsertWidget(%s, 12, %s, %s, 0)' % (widget_id, widget_id, self.__text))

    @staticmethod
    def __on_click_and_reset(on_click: callable):
        on_click()
        vs.ResetObject(ActivePlugIn().handle)


class StaticTextWidget(AbstractWidget):

    def __init__(self, text: str='', visible: callable=None):
        """
        :type visible: () -> bool
        """
        super().__init__(visible)
        self.__text = text

    def add(self, widget_id: int):
        if not vs.vsoInsertWidget(widget_id, 13, widget_id, self.__text, 0):  # 13 = Static text.
            raise VSException('vsoInsertWidget(%s, 13, %s, %s, 0)' % (widget_id, widget_id, self.__text))


class SeparatorWidget(AbstractWidget):

    def __init__(self, text: str='', visible: callable=None):
        """
        :type visible: () -> bool
        """
        super().__init__(visible)
        self.__text = text

    def add(self, widget_id: int):
        if not vs.vsoInsertWidget(widget_id, 100, widget_id, self.__text.upper() + ' ', 0):  # 100 = Separator.
            raise VSException('vsoInsertWidget(%s, 100, %s, %s + \' \', 0)' % (widget_id, widget_id, self.__text))


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
            ActivePlugInEvent.VSO_ON_WIDGET_PREP: self.__on_widget_prep,
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
        custom_visibility = False
        for index, widget in enumerate(self.__info_pallet, 1):
            custom_visibility = custom_visibility or widget.custom_visibility
            widget.add(index)
        if custom_visibility and not vs.SetObjPropVS(12, True):  # 12 = Custom widget visibility!
            raise VSException('SetObjPropVS(12, True)')

    def __init_double_click(self):
        if not vs.SetObjPropCharVS(3, self.__double_click_behaviour):  # 3 = Double click behavior!
            raise VSException('SetObjPropCharVS(3, %s)' % self.__double_click_behaviour)

    def __on_widget_prep(self):
        if self.__info_pallet is not None:
            for index, widget in enumerate(self.__info_pallet, 1):
                widget.update(index)

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
        value = getattr(vs, 'P%s' % name)  # Vectorworks puts parameters inside the v
        # s module!
        # For a boolean value, VW return 1 or 0, while we actually want a bool, so we'll convert if needed.
        record = vs.GetParametricRecord(ActivePlugIn().handle)
        fields = [vs.GetFldName(record, index) for index in range(1, vs.NumFields(record) + 1)]
        is_bool = vs.GetFldType(record, fields.index(name) + 1) == 2
        self.__parameters[name] = value if not is_bool else value == 1
        return self.__parameters[name]

    def _set_parameter(self, name: str, value):
        self.__parameters[name] = value
        vs.SetRField(ActivePlugIn().handle, ActivePlugIn().name, name,
                     value if isinstance(value, str) else vs.Num2Str(-2, value))


class AbstractActivePlugInXmlFile(AbstractXmlFile, metaclass=ABCMeta):

    def __init__(self, active_plugin_type: str, suffix: str):
        """
        :type active_plugin_type: ActivePlugInType(Enum)
        """
        file_path = Vectorworks().get_folder_path_of_plugin_file(ActivePlugIn().name + active_plugin_type)
        super().__init__(os.path.join(file_path, ActivePlugIn().name + suffix + '.xml'))


class AbstractActivePlugInPrefsXmlFile(AbstractActivePlugInXmlFile, metaclass=ABCMeta):

    def __init__(self, active_plugin_type: str):
        """
        :type active_plugin_type: ActivePlugInType(Enum)
        """
        super().__init__(active_plugin_type, 'Prefs')


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
